"""
Member Management module (admin side).
FR3 - The system shall allow the administrator to manage member information.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import query_all, query_one, execute
from auth import login_required

members_bp = Blueprint("members", __name__)


@members_bp.route("/admin/members")
@login_required(role="admin")
def list_members():
    q = request.args.get("q", "").strip()
    sql = "SELECT Member_ID, Name, Email, Phone, Created_At FROM Member WHERE 1=1"
    params = []
    if q:
        sql += " AND (Name LIKE %s OR Email LIKE %s)"
        params += [f"%{q}%", f"%{q}%"]
    sql += " ORDER BY Name"
    members = query_all(sql, params)
    return render_template("members.html", members=members, q=q)


@members_bp.route("/admin/members/<int:member_id>")
@login_required(role="admin")
def member_detail(member_id):
    member = query_one("SELECT * FROM Member WHERE Member_ID = %s", (member_id,))
    if not member:
        flash("Member not found.", "error")
        return redirect(url_for("members.list_members"))

    borrow_history = query_all(
        """
        SELECT br.*, b.Title, b.Author
        FROM Borrowing br
        JOIN Book b ON br.Book_ID = b.Book_ID
        WHERE br.Member_ID = %s
        ORDER BY br.Borrow_Date DESC
        """,
        (member_id,),
    )
    return render_template("member_detail.html", member=member, borrow_history=borrow_history)


@members_bp.route("/admin/members/<int:member_id>/edit", methods=["GET", "POST"])
@login_required(role="admin")
def edit_member(member_id):
    member = query_one("SELECT * FROM Member WHERE Member_ID = %s", (member_id,))
    if not member:
        flash("Member not found.", "error")
        return redirect(url_for("members.list_members"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()

        execute(
            "UPDATE Member SET Name=%s, Email=%s, Phone=%s WHERE Member_ID=%s",
            (name, email, phone, member_id),
        )
        flash("Member details updated.", "success")
        return redirect(url_for("members.member_detail", member_id=member_id))

    return render_template("edit_member.html", member=member)


@members_bp.route("/admin/members/<int:member_id>/delete", methods=["POST"])
@login_required(role="admin")
def delete_member(member_id):
    active_loan = query_one(
        "SELECT Borrow_ID FROM Borrowing WHERE Member_ID = %s AND Status = 'Borrowed'",
        (member_id,),
    )
    if active_loan:
        flash("Cannot delete a member with an active borrowing.", "error")
        return redirect(url_for("members.list_members"))

    execute("DELETE FROM Member WHERE Member_ID = %s", (member_id,))
    flash("Member removed.", "success")
    return redirect(url_for("members.list_members"))
