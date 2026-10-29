import sqlite3
from contextlib import contextmanager
from pathlib import Path
from config import Config

@contextmanager
def get_db():
    Path(Config.INSTANCE_DIR).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS students (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          student_id TEXT NOT NULL UNIQUE,
          full_name TEXT NOT NULL, email TEXT,
          created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS face_encodings (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          student_ref INTEGER NOT NULL,
          encoding_json TEXT NOT NULL, created_at TEXT NOT NULL,
          FOREIGN KEY(student_ref) REFERENCES students(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS attendance (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          student_ref INTEGER NOT NULL, attendance_date TEXT NOT NULL,
          attendance_time TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Present',
          created_at TEXT NOT NULL, UNIQUE(student_ref, attendance_date),
          FOREIGN KEY(student_ref) REFERENCES students(id) ON DELETE CASCADE);
        CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(attendance_date);
        CREATE INDEX IF NOT EXISTS idx_students_name ON students(full_name);
        ''')
