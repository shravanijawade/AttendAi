# AI Face Recognition-Based Attendance System — Task 04

A local Flask + SQLite attendance website for Windows and VS Code. It uses **actual face detection and recognition** with OpenCV Zoo's YuNet detector and SFace recognition model. It does not simulate recognition with hardcoded names. The browser sends webcam frames to the local Flask backend, where matching happens.

## Features
- Student registration with ID, name, optional email, and face photo capture/upload
- Real face detection and SFace embeddings, with unknown-person handling
- Live webcam page, automatic attendance, and duplicate prevention per student/day
- Dashboard, student search/details/delete, attendance search/filter, reports/chart, CSV export, settings
- SQLite database initialized automatically and an additional `data/exports/attendance.csv`

## Requirements
- Windows 10/11, Python 3.10 or 3.11 recommended, VS Code
- Webcam for live recognition; image upload can be used for registration
- Internet on first model load to download two ONNX model files into `models/`; after that, models can be used offline

## Install and run
Open the project folder in VS Code, open Terminal, and run:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` and allow camera permission in the browser. Stop with `Ctrl+C`. If `py -3.11` is unavailable, install Python 3.10/3.11 and use `py -m venv .venv`.

**Windows package note:** use `opencv-contrib-python` only. If OpenCV imports are conflicting, run `pip uninstall opencv-python opencv-contrib-python` then `pip install -r requirements.txt` in the active virtual environment.

## How to use
1. Register Student: enter a unique student ID and name, then capture/upload a clear JPG/PNG containing one front-facing face.
2. Live Recognition: click Start camera and look at the camera. Recognition runs every three seconds.
3. A recognized student is marked Present once per local calendar date. Unknown people are never marked present.
4. Search/filter Attendance and use Export CSV to download records.
5. Student details show attendance history. Deleting a student removes linked encodings and attendance records.

## Recognition and privacy
Face **detection** locates a face in an image. Face **recognition** generates a numerical embedding and compares it with registered embeddings. The default `FACE_THRESHOLD = 0.45` is a cosine-distance threshold: lower values are stricter and may miss legitimate matches; higher values may increase false matches. Test under your lighting and camera conditions. No biometric system is perfectly accurate.

The application stores a face embedding rather than the original registration photo. Embeddings are still sensitive biometric data. Get informed consent, restrict access to the computer, and delete data when no longer needed. This is an educational demonstration, not a security-grade identity system.

Report percentages use the number of dates with attendance records as a demo basis. It is **not** an official academic attendance percentage because the application does not know your institution's working-day calendar.

## Settings
- `FACE_THRESHOLD`: recognition strictness.
- `CAMERA_INDEX`: reference setting; the page uses browser camera access, so select a device in browser permissions if necessary.
- `ATTENDANCE_COOLDOWN`: initial scan interval reference; actual duplicate protection is the database unique constraint.
- `EXPORT_DIR`: path for automatic CSV copy.

Settings page changes apply until the server restarts. Edit `config.py` for persistent defaults.

## Troubleshooting
- **Model download fails:** check internet/firewall, then download the two model files named in `services/face_service.py` from OpenCV Zoo and place them in `models/` using the exact filenames.
- **`FaceDetectorYN` missing:** install `opencv-contrib-python` in the active virtual environment and avoid installing both OpenCV wheel variants.
- **Camera denied:** allow camera permission for `127.0.0.1`, close other camera apps, and reload. Browser camera access is supported on localhost.
- **No face found:** improve lighting, face the camera, move closer, and use a single-face image.
- **False match/missed match:** adjust threshold carefully and register a clear face. Have a human verify records.
- **Port busy:** close the other app using port 5000 or change the port in `app.py`.

## Tests
Install pytest and run `python -m pytest -q`. Tests cover database initialization, unique student IDs, duplicate attendance, date filtering, CSV export, and invalid/unknown image handling without a webcam. Actual face-model recognition requires the ONNX models and is exercised when using the live page.

## Structure
```text
face_attendance_system/
├── app.py, config.py, requirements.txt, README.md
├── database/db.py
├── services/face_service.py, attendance_service.py, report_service.py
├── templates/ (dashboard, registration, live recognition, attendance, students, details, reports, settings)
├── static/css/style.css, static/js/camera.js, main.js, charts.js
├── models/ (ONNX files downloaded on first use)
├── instance/attendance.db (created automatically)
├── data/exports/attendance.csv
└── tests/
```
