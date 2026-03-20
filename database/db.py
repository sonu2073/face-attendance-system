import sqlite3
import os
import json
import hashlib
from datetime import date, datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "attendance.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    UNIQUE NOT NULL,
            password TEXT    NOT NULL,
            email    TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            roll_no     TEXT    UNIQUE,
            department  TEXT,
            encoding    TEXT    NOT NULL,
            photo_path  TEXT,
            created_at  TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            date       TEXT    NOT NULL,
            time       TEXT    NOT NULL,
            status     TEXT    DEFAULT 'Present',
            UNIQUE(student_id, date),
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Default admin: admin / admin123
    pw_hash = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("""
        INSERT OR IGNORE INTO admins (username, password, email)
        VALUES (?, ?, ?)
    """, ("admin", pw_hash, ""))

    # Default email settings
    defaults = [
        ("smtp_host",  "smtp.gmail.com"),
        ("smtp_port",  "587"),
        ("smtp_user",  ""),
        ("smtp_pass",  ""),
        ("report_to",  ""),
        ("send_time",  "18:00"),
    ]
    for k, v in defaults:
        c.execute("INSERT OR IGNORE INTO settings (key,value) VALUES (?,?)", (k, v))

    conn.commit()
    conn.close()


# ─── Admin ────────────────────────────────────────────────────────────────────

def verify_admin(username: str, password: str) -> bool:
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = get_conn()
    row = conn.execute(
        "SELECT id FROM admins WHERE username=? AND password=?",
        (username, pw_hash)
    ).fetchone()
    conn.close()
    return row is not None


def change_password(username: str, new_password: str):
    pw_hash = hashlib.sha256(new_password.encode()).hexdigest()
    conn = get_conn()
    conn.execute("UPDATE admins SET password=? WHERE username=?", (pw_hash, username))
    conn.commit()
    conn.close()


def get_admin_email(username: str) -> str:
    conn = get_conn()
    row = conn.execute("SELECT email FROM admins WHERE username=?", (username,)).fetchone()
    conn.close()
    return row["email"] if row else ""


def set_admin_email(username: str, email: str):
    conn = get_conn()
    conn.execute("UPDATE admins SET email=? WHERE username=?", (email, username))
    conn.commit()
    conn.close()


# ─── Students ─────────────────────────────────────────────────────────────────

def add_student(name: str, roll_no: str, department: str, encoding, photo_path: str = "") -> int:
    enc_json = json.dumps(encoding.tolist())
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO students (name, roll_no, department, encoding, photo_path) VALUES (?,?,?,?,?)",
        (name, roll_no, department, enc_json, photo_path)
    )
    sid = cur.lastrowid
    conn.commit()
    conn.close()
    return sid


def get_all_students():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM students ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_student_by_id(sid: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_student(sid: int):
    conn = get_conn()
    conn.execute("DELETE FROM attendance WHERE student_id=?", (sid,))
    conn.execute("DELETE FROM students WHERE id=?", (sid,))
    conn.commit()
    conn.close()


def load_encodings():
    """Return list of (student_id, name, np_encoding)."""
    import numpy as np
    conn = get_conn()
    rows = conn.execute("SELECT id, name, encoding FROM students").fetchall()
    conn.close()
    result = []
    for r in rows:
        enc = np.array(json.loads(r["encoding"]))
        result.append((r["id"], r["name"], enc))
    return result


# ─── Attendance ───────────────────────────────────────────────────────────────

def mark_attendance(student_id: int) -> bool:
    """Returns True if newly marked, False if already marked today."""
    today = date.today().isoformat()
    now   = datetime.now().strftime("%H:%M:%S")
    conn  = get_conn()
    try:
        conn.execute(
            "INSERT INTO attendance (student_id, date, time) VALUES (?,?,?)",
            (student_id, today, now)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_today_attendance():
    today = date.today().isoformat()
    conn  = get_conn()
    rows  = conn.execute("""
        SELECT s.name, s.roll_no, s.department, a.time
        FROM   attendance a
        JOIN   students s ON s.id = a.student_id
        WHERE  a.date = ?
        ORDER  BY a.time
    """, (today,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_attendance_by_date(d: str):
    conn = get_conn()
    rows = conn.execute("""
        SELECT s.name, s.roll_no, s.department, a.time, a.status
        FROM   attendance a
        JOIN   students s ON s.id = a.student_id
        WHERE  a.date = ?
        ORDER  BY a.time
    """, (d,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_attendance_range(from_date: str, to_date: str):
    conn = get_conn()
    rows = conn.execute("""
        SELECT a.date, s.name, s.roll_no, s.department, a.time, a.status
        FROM   attendance a
        JOIN   students s ON s.id = a.student_id
        WHERE  a.date BETWEEN ? AND ?
        ORDER  BY a.date, a.time
    """, (from_date, to_date)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_weekly_stats():
    """Returns list of (date, present_count) for last 7 days."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT date, COUNT(*) as cnt
        FROM   attendance
        WHERE  date >= date('now','-6 days')
        GROUP  BY date
        ORDER  BY date
    """).fetchall()
    conn.close()
    return [(r["date"], r["cnt"]) for r in rows]


def get_dashboard_counts():
    today = date.today().isoformat()
    conn  = get_conn()
    total   = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    present = conn.execute(
        "SELECT COUNT(*) FROM attendance WHERE date=?", (today,)
    ).fetchone()[0]
    conn.close()
    return total, present, total - present


# ─── Settings ─────────────────────────────────────────────────────────────────

def get_setting(key: str, default: str = "") -> str:
    conn = get_conn()
    row  = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()
