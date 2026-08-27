"""
Camera service: manages a single shared camera + YOLO inference thread.
Produces MJPEG frames and exposes current detection state.
"""
import threading
import time
import cv2
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.services.material_registry import get_material_config


class CameraService:
    def __init__(self):
        self._lock = threading.Lock()
        self._cap = None
        self._running = False
        self._thread = None
        self.material = "steel"

        # Latest state
        self.latest_frame_jpg = None       # raw JPEG bytes of annotated frame
        self.latest_detection = {
            "fps": 0,
            "total_defects": 0,
            "scratches": 0,
            "dents": 0,
            "rust": 0,
            "other": 0,
            "status": "IDLE",
            "quality_score": 100,
            "severity": "NONE",
            "remarks": "Camera not started.",
            "detections": []
        }
        self.camera_index = -1
        self.model_loaded = False
        self.camera_connected = False
        self.error_message = None

    # --------------------------------------------------
    # MODEL
    # --------------------------------------------------

    def load_model(self, material):
        try:
            from backend.services.inference_service import get_model
            get_model(material)
            self.model_loaded = True
            return True
        except Exception as e:
            self.error_message = f"Model load failed: {e}"
            return False

    # --------------------------------------------------
    # START / STOP
    # --------------------------------------------------

    def start(self, material="steel"):
        with self._lock:
            if self._running:
                return {"success": True, "message": "Already running"}

            try:
                get_material_config(material)
            except ValueError as e:
                return {"success": False, "message": str(e)}

            if not self.load_model(material):
                return {"success": False, "message": self.error_message}

            cap, idx = self._open_camera()
            if cap is None:
                self.camera_connected = False
                return {"success": False, "message": "No camera found"}

            self._cap = cap
            self.camera_index = idx
            self.material = material.lower()
            self.camera_connected = True
            self._running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            return {"success": True, "message": f"Camera started (index {idx})"}

    def stop(self):
        with self._lock:
            self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        if self._cap:
            self._cap.release()
            self._cap = None
        self.camera_connected = False
        self.latest_frame_jpg = None
        self.latest_detection["status"] = "IDLE"
        self.latest_detection["remarks"] = "Camera stopped."
        return {"success": True, "message": "Camera stopped"}

    # --------------------------------------------------
    # CAMERA OPEN
    # --------------------------------------------------

    def _open_camera(self):
        for i in range(5):
            test = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if not test.isOpened():
                test.release()
                continue
            time.sleep(0.5)
            test.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            test.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            for _ in range(5):
                ret, frame = test.read()
                if ret and frame is not None:
                    return test, i
                time.sleep(0.1)
            test.release()
        return None, -1

    # --------------------------------------------------
    # INFERENCE LOOP
    # --------------------------------------------------

    def _loop(self):
        from backend.services.inference_service import run_inference
        _INFER_INTERVAL = 0.5  # run YOLO at most every 500 ms
        last_infer = 0.0

        while self._running:
            if self._cap is None:
                break

            ret, frame = self._cap.read()
            if not ret or frame is None:
                time.sleep(0.05)
                continue

            now = time.time()
            if now - last_infer < _INFER_INTERVAL:
                # Encode raw frame so the stream stays live between inferences
                import cv2 as _cv2
                _, raw_jpg = _cv2.imencode(".jpg", frame, [_cv2.IMWRITE_JPEG_QUALITY, 75])
                with self._lock:
                    if self.latest_frame_jpg is None:
                        self.latest_frame_jpg = raw_jpg.tobytes()
                time.sleep(0.033)
                continue

            t0 = time.time()
            inference = run_inference(frame, material=self.material)
            elapsed = time.time() - t0
            last_infer = time.time()
            fps = round(1 / elapsed if elapsed > 0 else 0, 1)

            detection_state = {
                "material": self.material,
                "fps": fps,
                "total_defects": inference["total_defects"],
                "status": inference["status"],
                "quality_score": inference["quality_score"],
                "severity": inference["severity"],
                "remarks": inference["remarks"],
                "detections": inference["detections"],
                "scratches": inference.get("scratches", 0),
                "dents": inference.get("dents", 0),
                "rust": inference.get("rust", 0),
                "other": inference.get("other", 0),
            }

            with self._lock:
                self.latest_frame_jpg = inference["annotated_jpg"]
                self.latest_detection = detection_state

    # --------------------------------------------------
    # CAPTURE & SAVE
    # --------------------------------------------------

    def capture_and_save(self):
        with self._lock:
            if not self._running or self.latest_frame_jpg is None:
                return None, "Camera not running or no frame available"
            detection = dict(self.latest_detection)
            frame_jpg = self.latest_frame_jpg

        try:
            from backend.services.inference_service import save_inspection_record
            persisted = save_inspection_record(
                {**detection, "annotated_jpg": frame_jpg},
                inspector="Camera",
                material=self.material,
            )
        except Exception as e:
            return None, f"Database save failed: {e}"
        return persisted, None

    # --------------------------------------------------
    # STATUS
    # --------------------------------------------------

    def get_status(self):
        return {
            "running": self._running,
            "camera_connected": self.camera_connected,
            "camera_index": self.camera_index,
            "model_loaded": self.model_loaded,
            "error": self.error_message
        }


# Singleton
camera_service = CameraService()
