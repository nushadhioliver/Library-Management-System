"""
Administrator dashboard.
"""

from datetime import date
from flask import Blueprint, render_template
from db import query_one, query_all
from auth import login_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/dashboard")
@login_required(role="admin")
def dashboard():
    stats = {
        "total_books": query_one("SELECT COUNT(*) AS c FROM Book")["c"],
        "available_books": query_one("SELECT COUNT(*) AS c FROM Book WHERE Status='Available'")["c"],
        "total_members": query_one("SELECT COUNT(*) AS c FROM Member")["c"],
        "active_loans": query_one("SELECT COUNT(*) AS c FROM Borrowing WHERE Status='Borrowed'")["c"],
        "overdue_loans": query_one(
            "SELECT COUNT(*) AS c FROM Borrowing WHERE Status='Borrowed' AND Due_Date < %s",
            (date.today(),),
        )["c"],
        "unpaid_fines": query_one(
            "SELECT COALESCE(SUM(Amount),0) AS s FROM Fine WHERE Paid_Status='Unpaid'"
        )["s"],
    }

    recent_loans = query_all(
        """
        SELECT br.*, b.Title, m.Name AS Member_Name
        FROM Borrowing br
        JOIN Book b ON br.Book_ID = b.Book_ID
        JOIN Member m ON br.Member_ID = m.Member_ID
        ORDER BY br.Borrow_Date DESC LIMIT 5
        """
    )

    return render_template("admin_dashboard.html", stats=stats, recent_loans=recent_loans)
