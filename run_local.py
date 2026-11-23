"""Run the LMS locally with SQLite (no MySQL needed).
    pip install flask
    python run_local.py
Then open http://localhost:5000   (admin: admin@library.com / admin123)"""
import os, webbrowser, threading
import db

if not os.path.exists(db.DB_PATH):
    db.init_from_schema(os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql"))
    import seed; seed.seed_admin()

from app import create_app
if __name__ == "__main__":
    threading.Timer(1.2, lambda: webbrowser.open_new_tab("http://localhost:5000")).start()
    create_app().run(host="127.0.0.1", port=5000, debug=False)
