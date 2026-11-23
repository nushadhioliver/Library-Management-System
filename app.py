"""
Web-Based Library Management System
Entry point: run with `python app.py`

Modules (matching Chapter 3.3 of the report):
  - auth.py       User Management (register/login)          FR1
  - books.py      Book Management (CRUD + search)            FR2, FR4, FR5
  - members.py    Member Management (admin)                  FR3
  - borrow.py     Borrowing & Returning + fine calculation    FR6, FR7
  - chatbot.py    AI Chatbot                                  FR8, FR9
  - recommend.py  Rule-based book recommendation              FR9
  - reports.py    Report Management                           FR10
  - fines.py      Fine viewing / payment
  - member.py     Member dashboard
  - admin.py      Admin dashboard
"""

from flask import Flask, render_template, redirect, url_for, session
from config import Config

from auth import auth_bp
from books import books_bp
from members import members_bp
from borrow import borrow_bp
from fines import fines_bp
from reports import reports_bp
from chatbot import chatbot_bp
from member import member_bp
from admin import admin_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(borrow_bp)
    app.register_blueprint(fines_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(member_bp)
    app.register_blueprint(admin_bp)

    @app.route("/")
    def index():
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        if session.get("role") == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("member.dashboard"))

    # Friendly error pages
    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="Page not found."), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("error.html", code=500, message="Something went wrong on our end."), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
