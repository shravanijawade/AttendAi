from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from pathlib import Path
from datetime import datetime, date
import base64, json, io, csv
from config import Config
from database.db import init_db, get_db
from services.face_service import FaceService, FaceServiceError
from services.attendance_service import mark_attendance
from services.report_service import dashboard_stats, attendance_rows, report_summary

app=Flask(__name__); app.config.from_object(Config)
Path(Config.EXPORT_DIR).mkdir(parents=True,exist_ok=True); Path(Config.MODEL_DIR).mkdir(parents=True,exist_ok=True)
init_db(); face_service=FaceService(Config.MODEL_DIR,Config.FACE_THRESHOLD)

def image_bytes(data):
    if not data or ',' not in data: raise ValueError('Capture or upload a face image first.')
    try: raw=base64.b64decode(data.split(',',1)[1],validate=True)
    except Exception as e: raise ValueError('Invalid image data.') from e
    if len(raw)>5*1024*1024: raise ValueError('Image is too large. Maximum is 5 MB.')
    return raw

@app.route('/')
def dashboard(): return render_template('dashboard.html',stats=dashboard_stats(),recent=attendance_rows(limit=8))
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        sid=request.form.get('student_id','').strip(); name=request.form.get('full_name','').strip(); email=request.form.get('email','').strip() or None
        if not sid or len(sid)>40 or not name or len(name)>120:
            flash('Enter a valid student ID and full name.','danger'); return redirect(url_for('register'))
        try:
            enc=face_service.encode_bytes(image_bytes(request.form.get('image_data','')))
            with get_db() as db:
                if db.execute('SELECT 1 FROM students WHERE student_id=?',(sid,)).fetchone():
                    flash('That student ID is already registered.','danger'); return redirect(url_for('register'))
                cur=db.execute('INSERT INTO students(student_id,full_name,email,created_at) VALUES(?,?,?,?)',(sid,name,email,datetime.now().isoformat(timespec='seconds')))
                db.execute('INSERT INTO face_encodings(student_ref,encoding_json,created_at) VALUES(?,?,?)',(cur.lastrowid,json.dumps(enc.tolist()),datetime.now().isoformat(timespec='seconds')))
            flash(f'{name} registered successfully.','success'); return redirect(url_for('students'))
        except (ValueError,FaceServiceError) as e: flash(str(e),'danger'); return redirect(url_for('register'))
    return render_template('register.html')
@app.route('/live')
def live(): return render_template('live_recognition.html')
@app.post('/api/recognize')
def recognize():
    try:
        enc=face_service.encode_bytes(image_bytes((request.get_json(silent=True) or {}).get('image','')))
        with get_db() as db: rows=db.execute('SELECT s.id,s.student_id,s.full_name,f.encoding_json FROM students s JOIN face_encodings f ON f.student_ref=s.id').fetchall()
        if not rows: return jsonify(ok=True,recognized=False,message='No students registered yet.')
        best=None; distance=999
        for row in rows:
            d=face_service.distance(enc,json.loads(row['encoding_json']))
            if d<distance: best=row; distance=d
        if best is None or distance>app.config['FACE_THRESHOLD']:
            return jsonify(ok=True,recognized=False,message='Unknown Person',distance=round(distance,3))
        result=mark_attendance(best['id'])
        return jsonify(ok=True,recognized=True,name=best['full_name'],student_id=best['student_id'],distance=round(distance,3),attendance=result['message'],marked=result['marked'])
    except (ValueError,FaceServiceError) as e: return jsonify(ok=False,error=str(e)),400
    except Exception:
        app.logger.exception('Recognition failed'); return jsonify(ok=False,error='Recognition failed. Check model files and dependencies.'),500
@app.route('/attendance')
def attendance():
    q=request.args.get('q','').strip(); day=request.args.get('date','').strip(); status=request.args.get('status','').strip()
    return render_template('attendance.html',rows=attendance_rows(q,day,status),q=q,selected_date=day,selected_status=status)
@app.route('/students')
def students():
    q=request.args.get('q','').strip()
    with get_db() as db: rows=db.execute('SELECT s.*,(SELECT COUNT(*) FROM attendance a WHERE a.student_ref=s.id) attendance_count FROM students s WHERE s.student_id LIKE ? OR s.full_name LIKE ? ORDER BY s.full_name',(f'%{q}%',f'%{q}%')).fetchall()
    return render_template('students.html',students=rows,q=q)
@app.route('/students/<int:student_ref>')
def student_detail(student_ref):
    with get_db() as db:
        student=db.execute('SELECT * FROM students WHERE id=?',(student_ref,)).fetchone(); history=db.execute('SELECT * FROM attendance WHERE student_ref=? ORDER BY attendance_date DESC LIMIT 100',(student_ref,)).fetchall()
    if not student: flash('Student not found.','danger'); return redirect(url_for('students'))
    return render_template('student_detail.html',student=student,history=history)
@app.post('/students/<int:student_ref>/delete')
def delete_student(student_ref):
    with get_db() as db: db.execute('DELETE FROM students WHERE id=?',(student_ref,))
    flash('Student and linked attendance/encoding records deleted.','success'); return redirect(url_for('students'))
@app.route('/reports')
def reports(): return render_template('reports.html',summary=report_summary())
@app.route('/settings',methods=['GET','POST'])
def settings():
    if request.method=='POST':
        try:
            threshold=float(request.form.get('threshold','0.45')); cooldown=int(request.form.get('cooldown','3')); camera=int(request.form.get('camera_index','0'))
            if not .1<=threshold<=1: raise ValueError('Threshold must be between 0.1 and 1.0.')
            if not 1<=cooldown<=3600: raise ValueError('Scan interval must be 1–3600 seconds.')
            if not 0<=camera<=10: raise ValueError('Camera index must be 0–10.')
            app.config['FACE_THRESHOLD']=threshold; app.config['ATTENDANCE_COOLDOWN']=cooldown; app.config['CAMERA_INDEX']=camera; face_service.threshold=threshold
            flash('Settings applied until the server restarts.','success')
        except ValueError as e: flash(str(e),'danger')
        return redirect(url_for('settings'))
    return render_template('settings.html',threshold=app.config['FACE_THRESHOLD'],cooldown=app.config['ATTENDANCE_COOLDOWN'],camera_index=app.config['CAMERA_INDEX'])
@app.route('/export.csv')
def export_csv():
    rows=attendance_rows(request.args.get('q','').strip(),request.args.get('date','').strip(),request.args.get('status','').strip(),10000)
    out=io.StringIO(); writer=csv.writer(out); writer.writerow(['Student ID','Student Name','Date','Time','Status'])
    for r in rows: writer.writerow([r['student_id'],r['full_name'],r['attendance_date'],r['attendance_time'],r['status']])
    return send_file(io.BytesIO(out.getvalue().encode('utf-8-sig')),mimetype='text/csv',as_attachment=True,download_name=f'attendance_{date.today().isoformat()}.csv')
@app.get('/health')
def health(): return jsonify(ok=True,database='ready',recognition_models='loaded' if face_service.ready else 'download-on-first-use')
if __name__=='__main__': app.run(host='127.0.0.1',port=5000,debug=True)
