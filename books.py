"""
Book Management module.
FR2 - Administrator can add, update, delete, and view book records.
FR4 - Members can search for books by title, author, category, or ISBN.
FR5 - The system shall display the real-time availability status of books.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import query_all, query_one, execute
from auth import login_required

books_bp = Blueprint("books", __name__)


# ---------------------------------------------------------------
# Search & browse (available to any logged-in user) - FR4, FR5
# ---------------------------------------------------------------
@books_bp.route("/books")
@login_required()
def list_books():
    q = request.args.get("q", "").strip()
    field = request.args.get("field", "title")  # title | author | category | isbn
    category_id = request.args.get("category_id", "")

    sql = """
        SELECT b.Book_ID, b.ISBN, b.Title, b.Author, b.Status,
               c.Category_ID, c.Category_Name
        FROM Book b
        LEFT JOIN Category c ON b.Category_ID = c.Category_ID
        WHERE 1=1
    """
    params = []

    if q:
        column_map = {
            "title": "b.Title",
            "author": "b.Author",
            "isbn": "b.ISBN",
            "category": "c.Category_Name",
        }
        column = column_map.get(field, "b.Title")
        sql += f" AND {column} LIKE %s"
        params.append(f"%{q}%")

    if category_id:
        sql += " AND b.Category_ID = %s"
        params.append(category_id)

    sql += " ORDER BY b.Title"
    books = query_all(sql, params)
    categories = query_all("SELECT * FROM Category ORDER BY Category_Name")

    return render_template(
        "books.html", books=books, categories=categories,
        q=q, field=field, category_id=category_id,
    )


# ---------------------------------------------------------------
# Admin: Add book - FR2
# ---------------------------------------------------------------
@books_bp.route("/admin/books/add", methods=["GET", "POST"])
@login_required(role="admin")
def add_book():
    categories = query_all("SELECT * FROM Category ORDER BY Category_Name")

    if request.method == "POST":
        isbn = request.form.get("isbn", "").strip()
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        category_id = request.form.get("category_id") or None

        if not isbn or not title or not author:
            flash("ISBN, title and author are required.", "error")
            return render_template("add_edit_book.html", categories=categories, book=None)

        existing = query_one("SELECT Book_ID FROM Book WHERE ISBN = %s", (isbn,))
        if existing:
            flash("A book with this ISBN already exists.", "error")
            return render_template("add_edit_book.html", categories=categories, book=None)

        execute(
            "INSERT INTO Book (ISBN, Title, Author, Status, Category_ID) "
            "VALUES (%s, %s, %s, 'Available', %s)",
            (isbn, title, author, category_id),
        )
        flash("Book added successfully.", "success")
        return redirect(url_for("books.list_books"))

    return render_template("add_edit_book.html", categories=categories, book=None)


# ---------------------------------------------------------------
# Admin: Edit / Update book - FR2
# ---------------------------------------------------------------
@books_bp.route("/admin/books/<int:book_id>/edit", methods=["GET", "POST"])
@login_required(role="admin")
def edit_book(book_id):
    categories = query_all("SELECT * FROM Category ORDER BY Category_Name")
    book = query_one("SELECT * FROM Book WHERE Book_ID = %s", (book_id,))

    if not book:
        flash("Book not found.", "error")
        return redirect(url_for("books.list_books"))

    if request.method == "POST":
        isbn = request.form.get("isbn", "").strip()
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        category_id = request.form.get("category_id") or None
        status = request.form.get("status", book["Status"])

        execute(
            "UPDATE Book SET ISBN=%s, Title=%s, Author=%s, Category_ID=%s, Status=%s "
            "WHERE Book_ID = %s",
            (isbn, title, author, category_id, status, book_id),
        )
        flash("Book updated successfully.", "success")
        return redirect(url_for("books.list_books"))

    return render_template("add_edit_book.html", categories=categories, book=book)


# ---------------------------------------------------------------
# Admin: Delete book - FR2
# ---------------------------------------------------------------
@books_bp.route("/admin/books/<int:book_id>/delete", methods=["POST"])
@login_required(role="admin")
def delete_book(book_id):
    active_loan = query_one(
        "SELECT Borrow_ID FROM Borrowing WHERE Book_ID = %s AND Status = 'Borrowed'",
        (book_id,),
    )
    if active_loan:
        flash("Cannot delete a book that is currently borrowed.", "error")
        return redirect(url_for("books.list_books"))

    execute("DELETE FROM Book WHERE Book_ID = %s", (book_id,))
    flash("Book deleted.", "success")
    return redirect(url_for("books.list_books"))
