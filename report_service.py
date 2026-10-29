from datetime import date
from database.db import get_db

def dashboard_stats():
    today=date.today().isoformat()
    with get_db() as db:
        students=db.execute('SELECT COUNT(*) n FROM students').fetchone()['n']
        total=db.execute('SELECT COUNT(*) n FROM attendance').fetchone()['n']
        present=db.execute('SELECT COUNT(DISTINCT student_ref) n FROM attendance WHERE attendance_date=?',(today,)).fetchone()['n']
    return {'students':students,'total':total,'today':present,'percentage':round(present/students*100,1) if students else 0}

def attendance_rows(query='',day='',status='',limit=500):
    sql='SELECT a.id,s.student_id,s.full_name,a.attendance_date,a.attendance_time,a.status FROM attendance a JOIN students s ON s.id=a.student_ref WHERE 1=1'; args=[]
    if query: sql+=' AND (s.student_id LIKE ? OR s.full_name LIKE ?)'; args += [f'%{query}%',f'%{query}%']
    if day: sql+=' AND a.attendance_date=?'; args.append(day)
    if status: sql+=' AND a.status=?'; args.append(status)
    sql+=' ORDER BY a.attendance_date DESC,a.attendance_time DESC LIMIT ?'; args.append(int(limit))
    with get_db() as db: return db.execute(sql,args).fetchall()

def report_summary():
    with get_db() as db:
        daily=db.execute('SELECT attendance_date,COUNT(*) count FROM attendance GROUP BY attendance_date ORDER BY attendance_date DESC LIMIT 14').fetchall()
        people=db.execute('SELECT s.id,s.student_id,s.full_name,COUNT(a.id) present FROM students s LEFT JOIN attendance a ON a.student_ref=s.id GROUP BY s.id ORDER BY s.full_name').fetchall()
        count=db.execute('SELECT COUNT(*) n FROM students').fetchone()['n']
    days=len(daily)
    return {'daily':list(reversed(daily)),'students':[{'student_id':p['student_id'],'full_name':p['full_name'],'present':p['present'],'percentage':round(p['present']/days*100,1) if days else 0} for p in people],'days':days,'count':count}
