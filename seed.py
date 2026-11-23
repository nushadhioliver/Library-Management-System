"""
Run this ONCE after creating the database from schema.sql:

    python seed.py

It creates the default administrator account with a securely hashed
password (schema.sql intentionally does not contain a real password hash).

Default admin login:
    email:    admin@library.com
    password: admin123
(Please change this password after your first login in a real deployment.)
"""

from werkzeug.security import generate_password_hash
from db import execute, query_one


def seed_admin():
    existing = query_one("SELECT Admin_ID FROM Admin WHERE Email = %s", ("admin@library.com",))
    hashed = generate_password_hash("admin123")

    if existing:
        execute("UPDATE Admin SET Password = %s WHERE Admin_ID = %s", (hashed, existing["Admin_ID"]))
        print("Existing admin password reset to 'admin123'.")
    else:
        execute(
            "INSERT INTO Admin (Name, Email, Password) VALUES (%s, %s, %s)",
            ("Library Admin", "admin@library.com", hashed),
        )
        print("Admin account created: admin@library.com / admin123")


if __name__ == "__main__":
    seed_admin()
