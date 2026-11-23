"""
Report Management module.
FR10 - The system shall allow the administrator to generate reports
       on books, members, and borrowing transactions.
"""

from datetime import date
from flask import Blueprint, render_template, Response
from db import query_all, query_one
from auth import login_required
import csv
import io

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/admin/reports")
@login_required(role="admin")
def dashboard_reports():
    stats = {
        "total_books": query_one("SELECT COUNT(*) AS c FROM Book")["c"],
        "available_books": query_one("SELECT COUNT(*) AS c FROM Book WHERE Status='Available'")["c"],
        "borrowed_books": query_one("SELECT COUNT(*) AS c FROM Book WHERE Status='Borrowed'")["c"],
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

    most_borrowed = query_all(
        """
        SELECT b.Title, b.Author, COUNT(*) AS times_borrowed
        FROM Borrowing br JOIN Book b ON br.Book_ID = b.Book_ID
        GROUP BY br.Book_ID
        ORDER BY times_borrowed DESC
        LIMIT 5
        """
    )

    return render_template("reports.html", stats=stats, most_borrowed=most_borrowed)


@reports_bp.route("/admin/reports/export/<report_type>")
@login_required(role="admin")
def export_report(report_type):
    """
    Exports a CSV report. report_type in {books, members, borrowing, fines}
    """
    queries = {
        "books": (
            "SELECT b.Book_ID, b.ISBN, b.Title, b.Author, b.Status, c.Category_Name "
            "FROM Book b LEFT JOIN Category c ON b.Category_ID = c.Category_ID "
            "ORDER BY b.Title",
            "books_report.csv",
        ),
        "members": (
            "SELECT Member_ID, Name, Email, Phone, Created_At FROM Member ORDER BY Name",
            "members_report.csv",
        ),
        "borrowing": (
            "SELECT br.Borrow_ID, m.Name AS Member, b.Title AS Book, "
            "br.Borrow_Date, br.Due_Date, br.Return_Date, br.Status "
            "FROM Borrowing br "
            "JOIN Member m ON br.Member_ID = m.Member_ID "
            "JOIN Book b ON br.Book_ID = b.Book_ID "
            "ORDER BY br.Borrow_Date DESC",
            "borrowing_report.csv",
        ),
        "fines": (
            "SELECT f.Fine_ID, m.Name AS Member, b.Title AS Book, "
            "f.Amount, f.Issue_Date, f.Paid_Status "
            "FROM Fine f "
            "JOIN Borrowing br ON f.Borrow_ID = br.Borrow_ID "
            "JOIN Member m ON br.Member_ID = m.Member_ID "
            "JOIN Book b ON br.Book_ID = b.Book_ID "
            "ORDER BY f.Issue_Date DESC",
            "fines_report.csv",
        ),
    }

    if report_type not in queries:
        return "Unknown report type", 404

    sql, filename = queries[report_type]
    rows = query_all(sql)

    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
