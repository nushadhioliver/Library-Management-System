"""
Borrowing and Returning module.
FR6 - The system shall allow members to borrow and return books.
FR7 - The system shall automatically calculate overdue fines for late book returns.
"""

from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import query_all, query_one, execute
from auth import login_required
from config import Config

borrow_bp = Blueprint("borrow", __name__)


# ---------------------------------------------------------------
# Member: borrow a book - FR6
# ---------------------------------------------------------------
@borrow_bp.route("/borrow/<int:book_id>", methods=["POST"])
@login_required(role="member")
def borrow_book(book_id):
    member_id = session["user_id"]

    book = query_one("SELECT * FROM Book WHERE Book_ID = %s", (book_id,))
    if not book:
        flash("Book not found.", "error")
        return redirect(url_for("books.list_books"))

    if book["Status"] != "Available":
        flash("Sorry, this book is currently borrowed by someone else.", "error")
        return redirect(url_for("books.list_books"))

    # Prevent a member from borrowing the same book twice at once
    already = query_one(
        "SELECT Borrow_ID FROM Borrowing WHERE Member_ID=%s AND Book_ID=%s AND Status='Borrowed'",
        (member_id, book_id),
    )
    if already:
        flash("You already have this book on loan.", "error")
        return redirect(url_for("books.list_books"))

    borrow_date = date.today()
    due_date = borrow_date + timedelta(days=Config.LOAN_PERIOD_DAYS)

    execute(
        "INSERT INTO Borrowing (Member_ID, Book_ID, Borrow_Date, Due_Date, Status) "
        "VALUES (%s, %s, %s, %s, 'Borrowed')",
        (member_id, book_id, borrow_date, due_date),
    )
    execute("UPDATE Book SET Status = 'Borrowed' WHERE Book_ID = %s", (book_id,))

    flash(f"Book borrowed. Please return it by {due_date.strftime('%d %b %Y')}.", "success")
    return redirect(url_for("member.my_borrowings"))


# ---------------------------------------------------------------
# Member: return a book - FR6 + FR7 (auto fine calculation)
# ---------------------------------------------------------------
@borrow_bp.route("/return/<int:borrow_id>", methods=["POST"])
@login_required(role="member")
def return_book(borrow_id):
    member_id = session["user_id"]

    loan = query_one(
        "SELECT * FROM Borrowing WHERE Borrow_ID = %s AND Member_ID = %s",
        (borrow_id, member_id),
    )
    if not loan or loan["Status"] != "Borrowed":
        flash("Active loan not found.", "error")
        return redirect(url_for("member.my_borrowings"))

    return_date = date.today()
    execute(
        "UPDATE Borrowing SET Return_Date=%s, Status='Returned' WHERE Borrow_ID=%s",
        (return_date, borrow_id),
    )
    execute("UPDATE Book SET Status='Available' WHERE Book_ID=%s", (loan["Book_ID"],))

    # FR7 - automatic overdue fine calculation
    fine_amount = calculate_fine(loan["Due_Date"], return_date)
    if fine_amount > 0:
        execute(
            "INSERT INTO Fine (Borrow_ID, Amount, Issue_Date, Paid_Status) "
            "VALUES (%s, %s, %s, 'Unpaid')",
            (borrow_id, fine_amount, return_date),
        )
        flash(
            f"Book returned. It was {(return_date - loan['Due_Date']).days} day(s) overdue — "
            f"a fine of {fine_amount:.2f} has been applied.",
            "error",
        )
    else:
        flash("Book returned on time. Thank you!", "success")

    return redirect(url_for("member.my_borrowings"))


def calculate_fine(due_date, return_date):
    """
    FR7 helper: returns the fine amount (float) for a book returned on `return_date`
    against a `due_date`. Zero if returned on time or early.
    """
    overdue_days = (return_date - due_date).days
    if overdue_days <= 0:
        return 0.0
    return round(overdue_days * Config.FINE_PER_DAY, 2)


# ---------------------------------------------------------------
# Admin: view all active/overdue loans
# ---------------------------------------------------------------
@borrow_bp.route("/admin/borrowings")
@login_required(role="admin")
def all_borrowings():
    status = request.args.get("status", "all")  # all | borrowed | overdue | returned
    sql = """
        SELECT br.*, b.Title, b.Author, m.Name AS Member_Name, m.Email AS Member_Email
        FROM Borrowing br
        JOIN Book b ON br.Book_ID = b.Book_ID
        JOIN Member m ON br.Member_ID = m.Member_ID
        WHERE 1=1
    """
    params = []
    today = date.today()

    if status == "borrowed":
        sql += " AND br.Status = 'Borrowed'"
    elif status == "returned":
        sql += " AND br.Status = 'Returned'"
    elif status == "overdue":
        sql += " AND br.Status = 'Borrowed' AND br.Due_Date < %s"
        params.append(today)

    sql += " ORDER BY br.Borrow_Date DESC"
    loans = query_all(sql, params)

    # annotate overdue flag for the template
    for loan in loans:
        loan["is_overdue"] = (
            loan["Status"] == "Borrowed" and loan["Due_Date"] < today
        )

    return render_template("borrowings.html", loans=loans, status=status)
