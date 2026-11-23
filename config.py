"""
Configuration for the Library Management System.
Reads DB credentials from environment variables when present,
falling back to sensible local defaults for development.
"""

import os


class Config:
    # Flask
    SECRET_KEY = os.environ.get("LMS_SECRET_KEY", "dev-secret-key-change-me")

    # MySQL connection
    DB_HOST = os.environ.get("LMS_DB_HOST", "localhost")
    DB_USER = os.environ.get("LMS_DB_USER", "root")
    DB_PASSWORD = os.environ.get("LMS_DB_PASSWORD", "your_password")
    DB_NAME = os.environ.get("LMS_DB_NAME", "library_db")
    DB_PORT = int(os.environ.get("LMS_DB_PORT", 3306))

    # Library business rules
    LOAN_PERIOD_DAYS = 14        # Due_Date = Borrow_Date + 14 days
    FINE_PER_DAY = 20.00         # currency units per day overdue
