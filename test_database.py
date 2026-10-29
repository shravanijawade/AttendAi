from database.db import get_db
from datetime import datetime

def test_database_initializes(app):
    with get_db() as db: names={r['name'] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {'students','face_encodings','attendance'} <= names

def test_duplicate_student_id_rejected(app):
    with get_db() as db:
        db.execute('INSERT INTO students(student_id,full_name,created_at) VALUES(?,?,?)',('S1','First',datetime.now().isoformat()))
        try: db.execute('INSERT INTO students(student_id,full_name,created_at) VALUES(?,?,?)',('S1','Second',datetime.now().isoformat()))
        except Exception: pass
        else: assert False, 'Unique student ID constraint should reject duplicate.'
