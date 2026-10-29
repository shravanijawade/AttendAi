from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
class Config:
    SECRET_KEY = 'local-college-project-change-this-key'
    MAX_CONTENT_LENGTH = 7 * 1024 * 1024
    DATABASE = str(BASE_DIR / 'instance' / 'attendance.db')
    INSTANCE_DIR = str(BASE_DIR / 'instance')
    EXPORT_DIR = str(BASE_DIR / 'data' / 'exports')
    MODEL_DIR = str(BASE_DIR / 'models')
    FACE_THRESHOLD = 0.45
    CAMERA_INDEX = 0
    ATTENDANCE_COOLDOWN = 3
