"""Real face detection/recognition using OpenCV Zoo YuNet + SFace models."""
from pathlib import Path
import urllib.request
import cv2
import numpy as np

MODEL_URLS = {
 'face_detection_yunet_2023mar.onnx': 'https://github.com/opencv/opencv_zoo/raw/refs/heads/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx',
 'face_recognition_sface_2021dec.onnx': 'https://github.com/opencv/opencv_zoo/raw/refs/heads/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx'
}
class FaceServiceError(Exception): pass
class FaceService:
    def __init__(self, model_dir, threshold=0.45):
        self.model_dir = Path(model_dir); self.model_dir.mkdir(parents=True, exist_ok=True)
        self.threshold = threshold; self.detector = None; self.recognizer = None; self.ready = False
        # Load/download model files on first recognition request, not at app startup.
    def _model(self, name):
        path = self.model_dir / name
        if path.exists() and path.stat().st_size > 100_000: return path
        try:
            req = urllib.request.Request(MODEL_URLS[name], headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as response: data = response.read()
            if len(data) < 100_000: raise RuntimeError('Downloaded model file is too small.')
            path.write_bytes(data); return path
        except Exception as exc:
            raise FaceServiceError(f'Cannot download {name}. Check internet, or put the ONNX model in the models folder. Details: {exc}') from exc
    def _load(self):
        if not hasattr(cv2, 'FaceDetectorYN') or not hasattr(cv2, 'FaceRecognizerSF'):
            raise FaceServiceError('Install opencv-contrib-python. Do not install opencv-python alongside it.')
        detector = self._model('face_detection_yunet_2023mar.onnx')
        recognizer = self._model('face_recognition_sface_2021dec.onnx')
        self.detector = cv2.FaceDetectorYN.create(str(detector), '', (320,320), 0.8, 0.3, 5000)
        self.recognizer = cv2.FaceRecognizerSF.create(str(recognizer), '')
        self.ready = True
    def encode_bytes(self, raw):
        if not self.ready: self._load()
        image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if image is None: raise FaceServiceError('Invalid image. Upload a JPG or PNG.')
        h, w = image.shape[:2]
        if min(h,w) < 80: raise FaceServiceError('Image is too small. Use a clear face photo.')
        self.detector.setInputSize((w,h)); _, faces = self.detector.detect(image)
        if faces is None or len(faces) == 0: raise FaceServiceError('No face detected. Use a clear, front-facing photo.')
        if len(faces) > 1: raise FaceServiceError('More than one face detected. Use a photo with one person.')
        aligned = self.recognizer.alignCrop(image, faces[0])
        return self.recognizer.feature(aligned).flatten().astype(np.float32)
    @staticmethod
    def distance(a, b):
        a=np.asarray(a,dtype=np.float32).reshape(-1); b=np.asarray(b,dtype=np.float32).reshape(-1)
        return float(1 - np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)+1e-12))
