from datetime import datetime,date
from database.db import get_db
from services.attendance_service import mark_attendance
from services.report_service import attendance_rows

def add_student():
    with get_db() as db:
        cur=db.execute('INSERT INTO students(student_id,full_name,created_at) VALUES(?,?,?)',('T'+datetime.now().strftime('%H%M%S%f'),'Test Student',datetime.now().isoformat()))
        return cur.lastrowid

def test_duplicate_attendance_prevented(app):
    sid=add_student(); assert mark_attendance(sid)['marked'] is True; assert mark_attendance(sid)['marked'] is False
    with get_db() as db: assert db.execute('SELECT COUNT(*) n FROM attendance WHERE student_ref=? AND attendance_date=?',(sid,date.today().isoformat())).fetchone()['n']==1

def test_date_filter(app):
    sid=add_student(); mark_attendance(sid)
    assert any(r['attendance_date']==date.today().isoformat() for r in attendance_rows(day=date.today().isoformat()))

def test_csv_export(client):
    response=client.get('/export.csv'); assert response.status_code==200 and b'Student ID' in response.data

def test_invalid_image_is_not_recognized(client):
    response=client.post('/api/recognize',json={'image':'invalid'})
    assert response.status_code==400
