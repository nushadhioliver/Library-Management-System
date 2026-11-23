"""
Authentication module.
FR1 - The system shall allow users to register and log in securely.

Handles both Library Member and Administrator accounts.
Passwords are never stored or compared in plain text (werkzeug hashing).
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import query_one, execute

auth_bp = Blueprint("auth", __name__)


# ---------------------------------------------------------------
# Member registration
# ---------------------------------------------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # --- validation ---
        if not name or not email or not password:
            flash("Name, email and password are required.", "error")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template("register.html")

        existing = query_one("SELECT Member_ID FROM Member WHERE Email = %s", (email,))
        if existing:
            flash("An account with this email already exists.", "error")
            return render_template("register.html")

        hashed = generate_password_hash(password)
        execute(
            "INSERT INTO Member (Name, Email, Phone, Password) VALUES (%s, %s, %s, %s)",
            (name, email, phone, hashed),
        )
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


# ---------------------------------------------------------------
# Login (single form, role selector for Member vs Admin)
# ---------------------------------------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "member")  # 'member' or 'admin'

        table = "Admin" if role == "admin" else "Member"
        id_col = "Admin_ID" if role == "admin" else "Member_ID"

        user = query_one(f"SELECT * FROM {table} WHERE Email = %s", (email,))

        if user and check_password_hash(user["Password"], password):
            session.clear()
            session["user_id"] = user[id_col]
            session["name"] = user["Name"]
            session["email"] = user["Email"]
            session["role"] = role
            flash(f"Welcome back, {user['Name']}!", "success")
            return redirect(url_for("admin.dashboard" if role == "admin" else "member.dashboard"))

        flash("Invalid email or password.", "error")
        return render_template("login.html")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


# ---------------------------------------------------------------
# Helper decorators used across the app
# ---------------------------------------------------------------
def login_required(role=None):
    """
    Decorator factory. Use as:
        @login_required()               -> any logged in user
        @login_required(role="admin")   -> admin only
        @login_required(role="member")  -> member only
    """
    from functools import wraps

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.", "error")
                return redirect(url_for("auth.login"))
            if role and session.get("role") != role:
                flash("You are not authorized to view that page.", "error")
                return redirect(url_for("auth.login"))
            return view_func(*args, **kwargs)
        return wrapped
    return decorator
