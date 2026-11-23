"""SQLite stand-in for db.py (sandbox only: no MySQL server available here).
Same public API: query_all / query_one / execute. SQL uses %s placeholders as in the real code."""
import os, re, sqlite3
from datetime import date, datetime
from decimal import Decimal

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.sqlite3")

sqlite3.register_converter("DATE", lambda b: date.fromisoformat(b.decode()))
sqlite3.register_converter("TIMESTAMP", lambda b: datetime.fromisoformat(b.decode()))
sqlite3.register_converter("DATETIME", lambda b: datetime.fromisoformat(b.decode()))
sqlite3.register_converter("DECIMAL", lambda b: Decimal(b.decode()))
sqlite3.register_adapter(date, lambda d: d.isoformat())
sqlite3.register_adapter(datetime, lambda d: d.isoformat(sep=" "))
sqlite3.register_adapter(Decimal, lambda d: str(d))

def get_db():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = lambda cur, row: {d[0]: row[i] for i, d in enumerate(cur.description)}
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def _fix(sql):
    return sql.replace("%s", "?")

def query_all(sql, params=None):
    conn = get_db()
    try:
        return conn.execute(_fix(sql), tuple(params or ())).fetchall()
    finally:
        conn.close()

def query_one(sql, params=None):
    rows = query_all(sql, params)
    return rows[0] if rows else None

def execute(sql, params=None):
    conn = get_db()
    try:
        cur = conn.execute(_fix(sql), tuple(params or ()))
        conn.commit()
        return cur.lastrowid, cur.rowcount
    finally:
        conn.close()

def init_from_schema(schema_path):
    s = open(schema_path, encoding="utf-8").read()
    s = re.sub(r"CREATE DATABASE[^;]*;", "", s)
    s = re.sub(r"USE [^;]*;", "", s)
    s = s.replace("INT AUTO_INCREMENT PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = get_db()
    conn.executescript(s)
    conn.commit()
    conn.close()
