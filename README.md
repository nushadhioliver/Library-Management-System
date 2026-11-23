# Library Management System

A web-based library app built with Flask and SQLite. Admins manage books and members. Members borrow books, pay fines, and ask the chatbot about availability.

## Features

- **Admin:** manage books, members, borrowings, fines, and reports
- **Members:** register, browse and borrow books, view and pay fines
- **Chatbot:** answers library questions and checks book availability
- **Recommendations:** suggests similar books

## Requirements

- Python 3
- Flask (`requirements.txt`)

## Run it

```bash
pip install -r requirements.txt
python run_local.py
```

Then open http://localhost:5000. The first run creates the database and an admin account.

**Admin login:** `admin@library.com` / `admin123`. Change this password after your first login.

## Project files

| File | Purpose |
|------|---------|
| `app.py` | Creates the Flask app and registers all modules |
| `run_local.py` | Starts the app with SQLite |
| `config.py` | Settings, including the loan period (14 days) and fine per day (20) |
| `schema.sql` | Database tables (MySQL syntax) |
| `books.py`, `borrow.py`, `members.py`, `fines.py`, `reports.py`, `chatbot.py`, `recommend.py`, `auth.py`, `admin.py`, `member.py` | Feature modules |
| `templates/`, `static/` | HTML pages, CSS, and JavaScript |
