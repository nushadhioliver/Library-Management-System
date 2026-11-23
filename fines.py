"""
Fine Management module.
Works together with FR7 (borrow.py calculates the fine when a book is returned late).
This module lets members view/pay their fines and lets the admin oversee all fines.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import query_all, query_one, execute
from auth import login_required

fines_bp = Blueprint("fines", __name__)


@fines_bp.route("/my-fines")
@login_required(role="member")
def my_fines():
    member_id = session["user_id"]
    fines = query_all(
        """
        SELECT f.*, b.Title, b.Author, br.Due_Date, br.Return_Date
        FROM Fine f
        JOIN Borrowing br ON f.Borrow_ID = br.Borrow_ID
        JOIN Book b ON br.Book_ID = b.Book_ID
        WHERE br.Member_ID = %s
        ORDER BY f.Issue_Date DESC
        """,
        (member_id,),
    )
    total_unpaid = sum(f["Amount"] for f in fines if f["Paid_Status"] == "Unpaid")
    return render_template("my_fines.html", fines=fines, total_unpaid=total_unpaid)


@fines_bp.route("/my-fines/<int:fine_id>/pay", methods=["POST"])
@login_required(role="member")
def pay_fine(fine_id):
    member_id = session["user_id"]
    # make sure this fine really belongs to the logged-in member
    fine = query_one(
        """
        SELECT f.Fine_ID FROM Fine f
        JOIN Borrowing br ON f.Borrow_ID = br.Borrow_ID
        WHERE f.Fine_ID = %s AND br.Member_ID = %s
        """,
        (fine_id, member_id),
    )
    if not fine:
        flash("Fine not found.", "error")
        return redirect(url_for("fines.my_fines"))

    execute("UPDATE Fine SET Paid_Status='Paid' WHERE Fine_ID=%s", (fine_id,))
    flash("Payment recorded. Thank you.", "success")
    return redirect(url_for("fines.my_fines"))


@fines_bp.route("/admin/fines")
@login_required(role="admin")
def admin_fines():
    status = request.args.get("status", "all")  # all | paid | unpaid
    sql = """
        SELECT f.*, b.Title, m.Name AS Member_Name, m.Email AS Member_Email
        FROM Fine f
        JOIN Borrowing br ON f.Borrow_ID = br.Borrow_ID
        JOIN Book b ON br.Book_ID = b.Book_ID
        JOIN Member m ON br.Member_ID = m.Member_ID
        WHERE 1=1
    """
    params = []
    if status == "paid":
        sql += " AND f.Paid_Status = 'Paid'"
    elif status == "unpaid":
        sql += " AND f.Paid_Status = 'Unpaid'"
    sql += " ORDER BY f.Issue_Date DESC"

    fines = query_all(sql, params)
    return render_template("admin_fines.html", fines=fines, status=status)
