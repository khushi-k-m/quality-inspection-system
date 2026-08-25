"""
Shared YOLO inference logic used by both camera capture and image upload.
"""
import cv2
import numpy as np
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

CLASS_NAMES = {0: "Scratches", 1: "Dents", 2: "Rust", 3: "Other"}
CLASS_KEYS  = {0: "scratches", 1: "dents",  2: "rust", 3: "other"}

_model = None


def get_model():
    global _model
    if _model is not None:
        return _model
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Model not found: {MODEL_PATH}")
    from ultralytics import YOLO
    _model = YOLO(str(MODEL_PATH))
    return _model


def run_inference(frame: np.ndarray) -> dict:
    """
    Run YOLO on a BGR numpy frame.
    Returns detection dict with counts, detections list, quality evaluation,
    and annotated JPEG bytes.
    """
    model = get_model()
    results = model(frame, imgsz=IMAGE_SIZE, conf=CONFIDENCE_THRESHOLD, verbose=False)
    result = results[0]
    annotated = result.plot()

    boxes = result.boxes
    counts = {"scratches": 0, "dents": 0, "rust": 0, "other": 0}
    detections = []

    for box in boxes:
        cls  = int(box.cls[0])
        conf = float(box.conf[0])
        if cls in CLASS_KEYS:
            counts[CLASS_KEYS[cls]] += 1
            detections.append({
                "class":      CLASS_NAMES.get(cls, "Unknown"),
                "confidence": round(conf * 100, 1),
                "cls_id":     cls,
            })

    total = len(boxes)

    # Quality evaluation — same logic as camera_service
    from quality.evaluator import evaluate_quality
    evaluation = evaluate_quality(
        scratches=counts["scratches"],
        dents=counts["dents"],
        rust=counts["rust"],
        other=counts["other"],
    )

    _, jpg = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])

    return {
        "total_defects": total,
        "scratches":     counts["scratches"],
        "dents":         counts["dents"],
        "rust":          counts["rust"],
        "other":         counts["other"],
        "quality_score": evaluation["quality_score"],
        "status":        evaluation["status"],
        "severity":      evaluation["severity"],
        "remarks":       evaluation["remarks"],
        "detections":    detections,
        "annotated_jpg": jpg.tobytes(),
    }


def save_inspection_record(detection: dict, inspector: str = "AI System") -> dict:
    """
    Persist an inspection result to the database and generate a PDF report.
    Returns the full inspection result dict including image_url and report_available.
    """
    now = datetime.now()
    timestamp   = now.strftime("%d-%m-%Y %H:%M:%S")
    inspection_id = now.strftime("INSP%Y%m%d%H%M%S%f")
    status = detection["status"]

    filename = OUTPUT_DIR / f"{inspection_id}_{status}.jpg"
    with open(str(filename), "wb") as f:
        f.write(detection["annotated_jpg"])

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
        inspector=inspector,
    )

    report_path = None
    try:
        from reports.generate_report import generate_report
        report_path = generate_report(inspection_id)
    except Exception:
        pass

    return {
        "inspection_id":  inspection_id,
        "timestamp":      timestamp,
        "status":         status,
        "quality_score":  detection["quality_score"],
        "severity":       detection["severity"],
        "remarks":        detection["remarks"],
        "total_defects":  detection["total_defects"],
        "scratches":      detection["scratches"],
        "dents":          detection["dents"],
        "rust":           detection["rust"],
        "other":          detection["other"],
        "detections":     detection["detections"],
        "image_url":      f"/api/images/{inspection_id}",
        "report_available": report_path is not None,
    }
