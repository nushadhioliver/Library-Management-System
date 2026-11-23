"""
AI Chatbot module.

FR8 - The AI chatbot shall answer users' library-related questions and
      check book availability by searching the database.
FR9 - If a requested book is unavailable, the AI chatbot shall display
      the expected return date and recommend similar available books.

The report specifies the Rasa framework for the chatbot's NLU. This
implementation uses a lightweight, dependency-free rule/intent engine
(keyword + pattern matching) so the whole system runs standalone.
The intent functions below are written so they can be dropped straight
into a Rasa `actions.py` (as custom actions) if the team later wants to
swap in full Rasa NLU for the conversational layer — the database logic
(checking availability, computing return dates, recommending books)
stays identical either way.
"""

import re
from datetime import date
from flask import Blueprint, render_template, request, jsonify, session
from db import query_all, query_one, execute
from auth import login_required
import recommend

chatbot_bp = Blueprint("chatbot", __name__)


# ---------------------------------------------------------------
# Intent patterns (simple rule-based NLU)
# ---------------------------------------------------------------
GREETING_PATTERNS = [r"\bhi\b", r"\bhello\b", r"\bhey\b", r"good (morning|afternoon|evening)"]
THANKS_PATTERNS = [r"\bthanks\b", r"\bthank you\b"]
GOODBYE_PATTERNS = [r"\bbye\b", r"\bgoodbye\b", r"see you"]
AVAILABILITY_PATTERNS = [
    r"is (.+) available",
    r"do you have (.+)",
    r"availability of (.+)",
    r"check (?:if )?(.+) is available",
    r"find (.+)",
    r"search (?:for )?(.+)",
]
HISTORY_PATTERNS = [r"my borrow(ing)? history", r"what have i borrowed", r"my loans"]
FINE_PATTERNS = [r"my fine", r"do i have (a|any) fine", r"overdue fee"]
HELP_PATTERNS = [r"\bhelp\b", r"what can you do", r"how do (i|you)"]


def _matches_any(patterns, text):
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def _extract_book_query(text):
    for pattern in AVAILABILITY_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).strip(" ?.!")
    return None


# ---------------------------------------------------------------
# Core intent handler - FR8 / FR9
# ---------------------------------------------------------------
def generate_response(message, member_id=None):
    text = message.strip()

    if _matches_any(GREETING_PATTERNS, text):
        return "Hello! I can check book availability, tell you when a borrowed book is due back, and recommend similar books. Try: 'Is 1984 available?'"

    if _matches_any(THANKS_PATTERNS, text):
        return "You're welcome! Is there anything else I can help you find?"

    if _matches_any(GOODBYE_PATTERNS, text):
        return "Goodbye! Happy reading."

    if _matches_any(HELP_PATTERNS, text):
        return (
            "I can help you with:\n"
            "• Checking if a book is available (e.g. 'Is Sapiens available?')\n"
            "• Telling you the expected return date if a book is out on loan\n"
            "• Recommending similar available books\n"
            "• Showing your borrowing history ('my borrowing history')\n"
            "• Showing your fines ('do I have any fines?')"
        )

    if _matches_any(HISTORY_PATTERNS, text):
        if not member_id:
            return "Please log in so I can look up your borrowing history."
        rows = query_all(
            """
            SELECT b.Title, br.Borrow_Date, br.Due_Date, br.Status
            FROM Borrowing br JOIN Book b ON br.Book_ID = b.Book_ID
            WHERE br.Member_ID = %s ORDER BY br.Borrow_Date DESC LIMIT 5
            """,
            (member_id,),
        )
        if not rows:
            return "You haven't borrowed any books yet."
        lines = [f"- {r['Title']} ({r['Status']}, due {r['Due_Date']})" for r in rows]
        return "Here is your recent borrowing history:\n" + "\n".join(lines)

    if _matches_any(FINE_PATTERNS, text):
        if not member_id:
            return "Please log in so I can check your fines."
        row = query_one(
            """
            SELECT COALESCE(SUM(f.Amount),0) AS total
            FROM Fine f JOIN Borrowing br ON f.Borrow_ID = br.Borrow_ID
            WHERE br.Member_ID = %s AND f.Paid_Status='Unpaid'
            """,
            (member_id,),
        )
        total = float(row["total"])
        if total <= 0:
            return "You have no outstanding fines. 🎉"
        return f"You currently have {total:.2f} in unpaid fines. Please settle them from the 'My Fines' page."

    # --- Availability check (FR8) + unavailable handling (FR9) ---
    book_query = _extract_book_query(text)
    if book_query:
        return _handle_availability(book_query)

    # Fallback: try treating the whole message as a title search anyway
    fallback_result = _handle_availability(text, silent_fallback=True)
    if fallback_result:
        return fallback_result

    return (
        "I'm not sure I understood that. You can ask me things like "
        "'Is Clean Code available?' or 'help' to see what I can do."
    )


def _handle_availability(book_query, silent_fallback=False):
    books = query_all(
        """
        SELECT b.Book_ID, b.Title, b.Author, b.Status, b.Category_ID, c.Category_Name
        FROM Book b LEFT JOIN Category c ON b.Category_ID = c.Category_ID
        WHERE b.Title LIKE %s OR b.Author LIKE %s OR b.ISBN LIKE %s
        LIMIT 5
        """,
        (f"%{book_query}%", f"%{book_query}%", f"%{book_query}%"),
    )

    if not books:
        if silent_fallback:
            return None
        return f"I couldn't find any book matching \"{book_query}\" in the library catalog."

    replies = []
    for book in books:
        if book["Status"] == "Available":
            replies.append(f"\"{book['Title']}\" by {book['Author']} is available in the library right now.")
        else:
            # FR9: unavailable -> expected return date + recommendation
            loan = query_one(
                "SELECT Due_Date FROM Borrowing WHERE Book_ID = %s AND Status = 'Borrowed' "
                "ORDER BY Due_Date LIMIT 1",
                (book["Book_ID"],),
            )
            due_text = (
                f"expected back around {loan['Due_Date'].strftime('%d %b %Y')}"
                if loan else "expected back soon"
            )
            reply = f"\"{book['Title']}\" by {book['Author']} is currently borrowed — {due_text}."

            similar = recommend.same_category(book["Category_ID"], exclude_book_id=book["Book_ID"])
            if similar:
                titles = ", ".join(f"\"{s['Title']}\" by {s['Author']}" for s in similar)
                reply += f" In the meantime, you might like: {titles}."
            replies.append(reply)

    return "\n".join(replies)


# ---------------------------------------------------------------
# Routes
# ---------------------------------------------------------------
@chatbot_bp.route("/chatbot")
@login_required()
def chatbot_page():
    return render_template("chatbot.html")


@chatbot_bp.route("/api/chatbot", methods=["POST"])
@login_required()
def chatbot_api():
    data = request.get_json(force=True, silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"response": "Please type a question."})

    member_id = session["user_id"] if session.get("role") == "member" else None
    response_text = generate_response(message, member_id=member_id)

    # Persist the interaction (supports the Chatbot_Query table / FR8-FR9 traceability)
    execute(
        "INSERT INTO Chatbot_Query (Member_ID, Question, Response, Query_Date) "
        "VALUES (%s, %s, %s, %s)",
        (member_id, message, response_text, date.today()),
    )

    return jsonify({"response": response_text})
