"""
Camera service: manages a single shared camera + YOLO inference thread.
Produces MJPEG frames and exposes current detection state.
"""
import threading
import time
import cv2
import sys
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

MODEL_PATH = ROOT_DIR / "trained_model" / "steel_defect_model" / "weights" / "best.pt"
OUTPUT_DIR = ROOT_DIR / "output" / "camera_capture"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONFIDENCE_THRESHOLD = 0.40
IMAGE_SIZE = 320


class CameraService:
    def __init__(self):
        self._lock = threading.Lock()
        self._cap = None
        self._model = None
        self._running = False
        self._thread = None

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

    def load_model(self):
        if self._model is not None:
            return True
        if not MODEL_PATH.exists():
            self.error_message = f"Model not found: {MODEL_PATH}"
            return False
        try:
            from ultralytics import YOLO
            self._model = YOLO(str(MODEL_PATH))
            self.model_loaded = True
            return True
        except Exception as e:
            self.error_message = f"Model load failed: {e}"
            return False

    # --------------------------------------------------
    # START / STOP
    # --------------------------------------------------

    def start(self):
        with self._lock:
            if self._running:
                return {"success": True, "message": "Already running"}

            if not self.load_model():
                return {"success": False, "message": self.error_message}

            cap, idx = self._open_camera()
            if cap is None:
                self.camera_connected = False
                return {"success": False, "message": "No camera found"}

            self._cap = cap
            self.camera_index = idx
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
        while self._running:
            if self._cap is None:
                break

            ret, frame = self._cap.read()
            if not ret or frame is None:
                time.sleep(0.05)
                continue

            t0 = time.time()

            results = self._model(
                frame,
                imgsz=IMAGE_SIZE,
                conf=CONFIDENCE_THRESHOLD,
                verbose=False
            )
            result = results[0]
            annotated = result.plot()

            elapsed = time.time() - t0
            fps = round(1 / elapsed if elapsed > 0 else 0, 1)

            # Count defects
            boxes = result.boxes
            counts = {"scratches": 0, "dents": 0, "rust": 0, "other": 0}
            detections = []

            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                names = {0: "Scratches", 1: "Dents", 2: "Rust", 3: "Other"}
                keys = {0: "scratches", 1: "dents", 2: "rust", 3: "other"}
                if cls in keys:
                    counts[keys[cls]] += 1
                    detections.append({
                        "class": names.get(cls, "Unknown"),
                        "confidence": round(conf * 100, 1),
                        "cls_id": cls
                    })

            total = len(boxes)

            # Quality evaluation
            if total == 0:
                score, status, severity = 100, "PASS", "NONE"
                remarks = "No defects detected. Product meets quality requirements."
            elif counts["rust"] > 0:
                score, status, severity = 70, "FAIL", "CRITICAL"
                remarks = "Rust detected. Product requires immediate inspection."
            elif total > 2:
                score, status, severity = 65, "FAIL", "HIGH"
                remarks = "Multiple defects detected. Product does not meet quality requirements."
            else:
                score = max(0, 100 - counts["scratches"] * 10 - counts["dents"] * 15 - counts["other"] * 10)
                status, severity = "REWORK", "MEDIUM"
                remarks = "Minor defects detected. Product requires rework."

            detection_state = {
                "fps": fps,
                "total_defects": total,
                "scratches": counts["scratches"],
                "dents": counts["dents"],
                "rust": counts["rust"],
                "other": counts["other"],
                "status": status,
                "quality_score": score,
                "severity": severity,
                "remarks": remarks,
                "detections": detections
            }

            # Encode frame as JPEG
            _, jpg = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])

            with self._lock:
                self.latest_frame_jpg = jpg.tobytes()
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

        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y %H:%M:%S")
        inspection_id = now.strftime("INSP%Y%m%d%H%M%S%f")
        status = detection["status"]

        filename = OUTPUT_DIR / f"{inspection_id}_{status}.jpg"

        # Write JPEG bytes directly
        with open(str(filename), "wb") as f:
            f.write(frame_jpg)

        # Save to database
        try:
            from quality.inspector import save_inspection
            save_inspection(
                inspection_id=inspection_id,
                timestamp=timestamp,
                image_path=str(filename),
                scratches=detection["scratches"],
                dents=detection["dents"],
                rust=detection["rust"],
                other=detection["other"],
                total_defects=detection["total_defects"],
                status=status,
                quality_score=detection["quality_score"],
                severity=detection["severity"],
                remarks=detection["remarks"],
                inspector="AI System"
            )
        except Exception as e:
            return None, f"Database save failed: {e}"

        # Generate PDF report
        report_path = None
        try:
            from reports.generate_report import generate_report
            report_path = generate_report(inspection_id)
        except Exception:
            pass

        return {
            "inspection_id": inspection_id,
            "timestamp": timestamp,
            "status": status,
            "quality_score": detection["quality_score"],
            "severity": detection["severity"],
            "remarks": detection["remarks"],
            "total_defects": detection["total_defects"],
            "scratches": detection["scratches"],
            "dents": detection["dents"],
            "rust": detection["rust"],
            "other": detection["other"],
            "detections": detection["detections"],
            "image_url": f"/api/images/{inspection_id}",
            "report_available": report_path is not None
        }, None

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
