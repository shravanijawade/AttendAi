from datetime import datetime
import csv
from pathlib import Path
from config import Config
from database.db import get_db

def mark_attendance(student_ref):
    now=datetime.now(); day=now.date().isoformat(); clock=now.strftime('%H:%M:%S')
    with get_db() as db:
        cur=db.execute('INSERT OR IGNORE INTO attendance(student_ref,attendance_date,attendance_time,status,created_at) VALUES(?,?,?,?,?)',(student_ref,day,clock,'Present',now.isoformat(timespec='seconds')))
        row=db.execute('SELECT s.student_id,s.full_name,a.attendance_date,a.attendance_time,a.status FROM attendance a JOIN students s ON s.id=a.student_ref WHERE a.student_ref=? AND a.attendance_date=?',(student_ref,day)).fetchone()
        marked=cur.rowcount == 1
    if marked:
        path=Path(Config.EXPORT_DIR)/'attendance.csv'; path.parent.mkdir(parents=True,exist_ok=True)
        is_new=not path.exists() or path.stat().st_size == 0
        with path.open('a',newline='',encoding='utf-8-sig') as f:
            writer=csv.writer(f)
            if is_new: writer.writerow(['Student ID','Student Name','Date','Time','Status'])
            writer.writerow([row['student_id'],row['full_name'],row['attendance_date'],row['attendance_time'],row['status']])
        return {'marked':True,'message':'Attendance marked successfully.'}
    return {'marked':False,'message':'Attendance Already Marked.'}
