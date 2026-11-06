"""
Camera service: manages a single shared camera + YOLO inference thread.
Produces MJPEG frames and exposes current detection state with real-time
material auto-detection and dynamic model switching.
"""
from collections import deque
import threading
import time
import cv2
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.services.material_registry import get_material_config, ALLOWED_MATERIALS
from backend.services.material_classifier import classify_material


class CameraService:
    def __init__(self):
        self._lock = threading.Lock()
        self._cap = None
        self._running = False
        self._thread = None
        self.material = "steel"
        self.auto_mode = False
        self.detected_material = "steel"
        self.material_confidence = 100.0
        self.material_probabilities = {}
        self._classification_history = deque(maxlen=5)

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
            "detections": [],
            "material": "steel",
            "auto_mode": False,
            "detected_material": "steel",
            "material_confidence": 100.0,
            "material_probabilities": {},
        }
        self.camera_index = -1
        self.model_loaded = False
        self.camera_connected = False
        self.error_message = None

    # --------------------------------------------------
    # MODEL
    # --------------------------------------------------

    def load_model(self, material: str) -> bool:
        try:
            from backend.services.inference_service import get_model
            get_model(material)
            self.model_loaded = True
            return True
        except Exception as e:
            self.error_message = f"Model load failed: {e}"
            return False

    # --------------------------------------------------
    # START / STOP / SWITCH
    # --------------------------------------------------

    def start(self, material: str = "steel") -> dict:
        with self._lock:
            if self._running:
                # If already running and a new material is requested, update material/mode
                return self._apply_material_change_locked(material)

            mat_clean = (material or "steel").lower().strip()
            if mat_clean == "auto":
                self.auto_mode = True
                active_material = "steel"  # starting model until auto-detection classifies frame
            else:
                self.auto_mode = False
                active_material = mat_clean

            try:
                get_material_config(active_material)
            except ValueError as e:
                return {"success": False, "message": str(e)}

            if not self.load_model(active_material):
                return {"success": False, "message": self.error_message}

            cap, idx = self._open_camera()
            if cap is None:
                self.camera_connected = False
                return {"success": False, "message": self.error_message or "No camera found"}

            self._cap = cap
            self.camera_index = idx
            self.material = active_material
            self.detected_material = active_material
            self.material_confidence = 100.0
            self._classification_history.clear()
            self.camera_connected = True
            self._running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            mode_desc = "Auto-Detect Mode" if self.auto_mode else f"Locked: {active_material.upper()}"
            return {"success": True, "message": f"Camera started (index {idx}) in {mode_desc}"}

    def _apply_material_change_locked(self, material: str) -> dict:
        mat_clean = (material or "steel").lower().strip()
        if mat_clean == "auto":
            self.auto_mode = True
            return {"success": True, "message": "Switched to Auto-Detect Material mode"}

        if mat_clean not in ALLOWED_MATERIALS:
            return {"success": False, "message": f"Unsupported material '{mat_clean}'"}

        self.auto_mode = False
        if mat_clean != self.material:
            if self.load_model(mat_clean):
                self.material = mat_clean
                self.detected_material = mat_clean
                self.material_confidence = 100.0
                return {"success": True, "message": f"Switched active material to {mat_clean.upper()}"}
            else:
                return {"success": False, "message": self.error_message or "Failed to load model"}
        return {"success": True, "message": f"Already set to {mat_clean.upper()}"}

    def set_mode(self, material: str) -> dict:
        """Switch material mode on the fly while streaming."""
        with self._lock:
            return self._apply_material_change_locked(material)

    def stop(self) -> dict:
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
        backends = [
            ("DirectShow", cv2.CAP_DSHOW),
            ("Media Foundation", cv2.CAP_MSMF),
            ("Default", cv2.CAP_ANY),
        ]
        attempts = []

        for backend_name, backend in backends:
            for i in range(5):
                test = cv2.VideoCapture(i, backend)
                if not test.isOpened():
                    test.release()
                    attempts.append(f"{backend_name}[{i}]: unavailable")
                    continue
                time.sleep(0.3)
                test.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                test.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                for _ in range(5):
                    ret, frame = test.read()
                    if ret and frame is not None:
                        return test, i
                    time.sleep(0.08)
                test.release()
                attempts.append(f"{backend_name}[{i}]: no frame")

        self.error_message = (
            "No usable camera found on this machine. "
            f"Tried: {', '.join(attempts) if attempts else 'no camera backend available'}"
        )
        return None, -1

    # --------------------------------------------------
    # INFERENCE & CLASSIFICATION LOOP
    # --------------------------------------------------

    def _loop(self):
        from backend.services.inference_service import run_inference, _generic_evaluate
        from quality.evaluator import evaluate_quality
        from metal.evaluator import MetalEvaluator

        _INFER_INTERVAL = 0.35  # run YOLO inference every ~350 ms
        _CLASSIFY_INTERVAL = 0.60  # run material classification check every ~600 ms

        last_infer = 0.0
        last_classify = 0.0
        fps = 0.0

        cached_detections = []
        cached_eval = {
            "status": "PASS",
            "quality_score": 100,
            "severity": "NONE",
            "remarks": f"No defects detected. {self.material.capitalize()} meets quality requirements.",
            "total_defects": 0,
            "scratches": 0,
            "dents": 0,
            "rust": 0,
            "other": 0,
        }

        while self._running:
            if self._cap is None:
                break

            ret, frame = self._cap.read()
            if not ret or frame is None:
                time.sleep(0.03)
                continue

            h, w = frame.shape[:2]

            # ── 1. Define Inspection Region of Interest (ROI) ───────────
            rx1 = int(w * 0.10)
            ry1 = int(h * 0.10)
            rx2 = int(w * 0.90)
            ry2 = int(h * 0.90)
            roi_frame = frame[ry1:ry2, rx1:rx2]

            now = time.time()

            # ── 2. Real-Time Material Auto-Detection (Classifier) ────────
            if now - last_classify >= _CLASSIFY_INTERVAL:
                try:
                    c_result = classify_material(roi_frame if roi_frame.size > 0 else frame)
                    if c_result.get("is_valid"):
                        pred_mat = c_result.get("detected_material")
                        pred_conf = c_result.get("confidence", 0.0)
                        self.detected_material = pred_mat
                        self.material_confidence = pred_conf
                        self.material_probabilities = c_result.get("probabilities", {})

                        self._classification_history.append(pred_mat)

                        # Auto-switching in auto mode:
                        # Require at least 3 matching classifications in window to switch
                        if self.auto_mode and len(self._classification_history) >= 3:
                            counts = {}
                            for m in self._classification_history:
                                counts[m] = counts.get(m, 0) + 1
                            dominant_mat, dominant_count = max(counts.items(), key=lambda item: item[1])

                            if dominant_count >= 3 and dominant_mat != self.material and dominant_mat in ALLOWED_MATERIALS:
                                # Switch active model smoothly
                                if self.load_model(dominant_mat):
                                    self.material = dominant_mat
                                    print(f"[CameraService] Auto-switched inspection model to: {dominant_mat.upper()} ({pred_conf:.1f}%)")
                except Exception as ex:
                    print(f"[CameraService] Material classification error: {ex}")
                last_classify = now

            # ── 3. Run Material-Specific YOLO Defect Inference ──────────
            if now - last_infer >= _INFER_INTERVAL:
                t0 = time.time()
                try:
                    active_mat = self.material
                    raw_result = run_inference(frame, material=active_mat)
                    elapsed = time.time() - t0
                    fps = round(1.0 / elapsed if elapsed > 0 else 0, 1)

                    # Filter detections: keep ONLY those inside ROI meeting confidence
                    min_conf = 45.0 if active_mat == "steel" else 35.0
                    filtered = []
                    for d in raw_result.get("detections", []):
                        cx = (d["x1"] + d["x2"]) / 2
                        cy = (d["y1"] + d["y2"]) / 2
                        conf = float(d.get("confidence", 0))
                        if (rx1 <= cx <= rx2) and (ry1 <= cy <= ry2) and (conf >= min_conf):
                            filtered.append(d)

                    total_filtered = len(filtered)

                    # Recompute quality metrics on filtered detections
                    extra_counts = {}
                    if total_filtered == 0:
                        evaluation = {
                            "quality_score": 100,
                            "severity": "NONE",
                            "status": "PASS",
                            "remarks": f"No defects detected. {active_mat.capitalize()} product meets quality requirements.",
                        }
                        if active_mat == "steel":
                            extra_counts = {"scratches": 0, "dents": 0, "rust": 0, "other": 0}
                        else:
                            extra_counts = {"defect_count": 0}
                    else:
                        if active_mat == "steel":
                            _STEEL_IDX = {0: "scratches", 1: "dents", 2: "rust", 3: "other"}
                            _STEEL_DISPLAY = {0: "Scratches", 1: "Dents", 2: "Rust", 3: "Other"}
                            counts = {"scratches": 0, "dents": 0, "rust": 0, "other": 0}
                            for d in filtered:
                                bucket = _STEEL_IDX.get(d.get("cls_id", 3), "other")
                                counts[bucket] += 1
                                d["class"] = _STEEL_DISPLAY.get(d.get("cls_id", 3), d.get("class", "Other"))
                                d["class_name"] = d["class"]
                            evaluation = evaluate_quality(**counts)
                            extra_counts = counts
                        elif active_mat == "metal":
                            evaluation = MetalEvaluator().evaluate(filtered)
                            extra_counts = {"defect_count": total_filtered}
                        else:
                            evaluation = _generic_evaluate(filtered, active_mat)
                            extra_counts = {"defect_count": total_filtered}

                    cached_detections = filtered
                    cached_eval = {
                        "status": evaluation["status"],
                        "quality_score": evaluation["quality_score"],
                        "severity": evaluation["severity"],
                        "remarks": evaluation["remarks"],
                        "total_defects": total_filtered,
                        **extra_counts,
                    }

                    detection_state = {
                        "material": active_mat,
                        "auto_mode": self.auto_mode,
                        "detected_material": self.detected_material,
                        "material_confidence": self.material_confidence,
                        "material_probabilities": self.material_probabilities,
                        "fps": fps,
                        "detections": cached_detections,
                        **cached_eval,
                    }
                    with self._lock:
                        self.latest_detection = detection_state

                except Exception as e:
                    print(f"[CameraService] Inference error: {e}")

                last_infer = time.time()

            # ── 4. Render Live Stream HUD with Cyber-Inspection Graphics ─
            display_frame = frame.copy()

            # Draw Inspection Target Zone boundary
            zone_color = (0, 230, 230)
            cv2.rectangle(display_frame, (rx1, ry1), (rx2, ry2), zone_color, 1)

            # High-tech corner bracket guides
            corner_len = int(min(w, h) * 0.05)
            for (cx, cy, dx, dy) in [
                (rx1, ry1, 1, 1), (rx2, ry1, -1, 1),
                (rx1, ry2, 1, -1), (rx2, ry2, -1, -1)
            ]:
                cv2.line(display_frame, (cx, cy), (cx + dx * corner_len, cy), (0, 255, 255), 2)
                cv2.line(display_frame, (cx, cy), (cx, cy + dy * corner_len), (0, 255, 255), 2)

            # Zone label
            active_label = self.material.upper()
            zone_text = f"[{active_label} INSPECTION ZONE]"
            cv2.putText(display_frame, zone_text, (rx1 + 8, ry1 + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 255), 1)

            # Floating Auto-Detection Badge in upper-right of inspection zone
            if self.auto_mode:
                badge_text = f"AUTO-DETECT: {self.detected_material.upper()} ({self.material_confidence:.0f}%)"
                badge_size = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)[0]
                bx = rx2 - badge_size[0] - 12
                by = ry1 + 22
                cv2.rectangle(display_frame, (bx - 6, by - 16), (bx + badge_size[0] + 6, by + 6), (20, 20, 20), -1)
                cv2.rectangle(display_frame, (bx - 6, by - 16), (bx + badge_size[0] + 6, by + 6), (0, 200, 255), 1)
                cv2.putText(display_frame, badge_text, (bx, by), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 220, 255), 1)

            # Draw filtered defect bounding boxes
            for d in cached_detections:
                bx1, by1 = max(0, int(d["x1"])), max(0, int(d["y1"]))
                bx2, by2 = min(w, int(d["x2"])), min(h, int(d["y2"]))
                dname = d.get("class", "Defect")
                dconf = d.get("confidence", 0)
                is_crit = str(dname).lower() in {"rust", "hole", "short", "bad_weld"}
                box_color = (0, 0, 255) if is_crit else (0, 140, 255)
                cv2.rectangle(display_frame, (bx1, by1), (bx2, by2), box_color, 2)
                tag = f"{dname} {dconf:.0f}%"
                cv2.rectangle(display_frame, (bx1, max(0, by1 - 18)), (bx1 + len(tag) * 9, by1), box_color, -1)
                cv2.putText(display_frame, tag, (bx1 + 3, max(14, by1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

            # Top HUD status bar
            cur_status = cached_eval.get("status", "PASS")
            cur_score = cached_eval.get("quality_score", 100)
            cv2.rectangle(display_frame, (0, 0), (w, 32), (18, 18, 18), -1)
            mode_tag = "[AUTO]" if self.auto_mode else "[LOCKED]"
            hud = f"MATERIAL: {active_label} {mode_tag} | STATUS: {cur_status} | DEFECTS: {len(cached_detections)} | SCORE: {cur_score}% | FPS: {fps}"
            hud_color = (100, 255, 100) if cur_status == "PASS" else (80, 80, 255) if cur_status == "FAIL" else (0, 200, 255)
            cv2.putText(display_frame, hud, (12, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.48, hud_color, 1)

            # Encode and update stream buffer
            _, encoded = cv2.imencode(".jpg", display_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            with self._lock:
                self.latest_frame_jpg = encoded.tobytes()

            time.sleep(0.02)

    # --------------------------------------------------
    # CAPTURE & SAVE
    # --------------------------------------------------

    def capture_and_save(self, inspector: str = "AI Camera System"):
        with self._lock:
            if not self._running or self.latest_frame_jpg is None:
                return None, "Camera not running or no frame available"
            detection = dict(self.latest_detection)
            frame_jpg = self.latest_frame_jpg
            active_material = self.material

        status = detection.get("status")
        if status in {"INVALID_IMAGE", "INVALID_MATERIAL", "MATERIAL_UNVERIFIED"}:
            return None, detection.get("remarks") or "Inspection rejected because the image failed validation."

        try:
            from backend.services.inference_service import save_inspection_record
            persisted = save_inspection_record(
                {**detection, "annotated_jpg": frame_jpg},
                inspector=inspector,
                material=active_material,
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
            "material": self.material,
            "auto_mode": self.auto_mode,
            "detected_material": self.detected_material,
            "material_confidence": self.material_confidence,
            "model_loaded": self.model_loaded,
            "error": self.error_message,
        }


# Singleton
camera_service = CameraService()
