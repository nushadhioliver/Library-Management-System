"""
Library Member views: dashboard, my borrowings, recommendations for them.
"""

from datetime import date
from flask import Blueprint, render_template, session
from db import query_all, query_one
from auth import login_required
import recommend

member_bp = Blueprint("member", __name__)


@member_bp.route("/member/dashboard")
@login_required(role="member")
def dashboard():
    member_id = session["user_id"]

    active_loans = query_all(
        """
        SELECT br.*, b.Title, b.Author
        FROM Borrowing br JOIN Book b ON br.Book_ID = b.Book_ID
        WHERE br.Member_ID = %s AND br.Status = 'Borrowed'
        ORDER BY br.Due_Date
        """,
        (member_id,),
    )
    for loan in active_loans:
        loan["is_overdue"] = loan["Due_Date"] < date.today()

    unpaid_total = query_one(
        """
        SELECT COALESCE(SUM(f.Amount),0) AS total
        FROM Fine f JOIN Borrowing br ON f.Borrow_ID = br.Borrow_ID
        WHERE br.Member_ID = %s AND f.Paid_Status = 'Unpaid'
        """,
        (member_id,),
    )["total"]

    recommendations = recommend.for_member(member_id)

    return render_template(
        "member_dashboard.html",
        active_loans=active_loans,
        unpaid_total=unpaid_total,
        recommendations=recommendations,
    )


@member_bp.route("/member/my-borrowings")
@login_required(role="member")
def my_borrowings():
    member_id = session["user_id"]
    loans = query_all(
        """
        SELECT br.*, b.Title, b.Author
        FROM Borrowing br JOIN Book b ON br.Book_ID = b.Book_ID
        WHERE br.Member_ID = %s
        ORDER BY br.Borrow_Date DESC
        """,
        (member_id,),
    )
    for loan in loans:
        loan["is_overdue"] = loan["Status"] == "Borrowed" and loan["Due_Date"] < date.today()

    return render_template("my_borrowings.html", loans=loans)
