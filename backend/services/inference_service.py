"""
Inference Service
=================
Material-aware YOLO inference.  One cached model per material.
Used by: image upload endpoint, camera service, future endpoints.
"""
import cv2
import numpy as np
import sys
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.services.material_registry import get_material_config

# Per-material model cache  {material_key: YOLO instance}
_model_cache: dict = {}


# Penalty weights for generic materials (fabric, pcb, welding)
# good_weld is not a defect — zero penalty
_GENERIC_PENALTIES = {
    # fabric
    "color_bleeding": 20, "crease": 15, "hole": 30,
    # pcb
    "missing_hole": 25, "mouse_bite": 20, "open_circuit": 30,
    "short": 30, "spur": 15, "spurious_copper": 20,
    # welding
    "bad_weld": 35, "good_weld": 0,
}
_GENERIC_CRITICAL = {"hole", "open_circuit", "short", "bad_weld"}


def _generic_evaluate(detections: list, material: str) -> dict:
    """Generic quality evaluator for fabric, pcb, welding."""
    # Filter out non-defect classes (good_weld)
    real_defects = [d for d in detections if d.get("class_name", "") != "good_weld"]
    defect_count = len(real_defects)

    if defect_count == 0:
        return {
            "quality_score": 100, "severity": "NONE", "status": "PASS",
            "defect_count": 0,
            "remarks": f"No defects detected. {material.capitalize()} meets quality requirements.",
        }

    score        = 100
    has_critical = False
    for d in real_defects:
        name    = d.get("class_name", "").lower()
        penalty = _GENERIC_PENALTIES.get(name, 15)
        score  -= penalty
        if name in _GENERIC_CRITICAL:
            has_critical = True
    score = max(0, min(100, score))

    if has_critical or score < 55:
        status, severity = "FAIL", "HIGH"
    elif score < 80:
        status, severity = "REWORK", "MEDIUM"
    else:
        status, severity = "PASS", "LOW"

    counts = {}
    for d in real_defects:
        n = d.get("class_name", "unknown")
        counts[n] = counts.get(n, 0) + 1
    summary = ", ".join(f"{v}x {k}" for k, v in counts.items())

    remarks = (
        f"Defects detected: {summary}. "
        + ("Immediate corrective action required." if status == "FAIL"
           else "Rework or manual inspection recommended." if status == "REWORK"
           else "Minor issues noted.")
    )
    return {"quality_score": score, "severity": severity, "status": status,
            "defect_count": defect_count, "remarks": remarks}


def get_model(material: str):
    """Return (and cache) the YOLO model for *material*."""
    key = material.lower()
    if key in _model_cache:
        return _model_cache[key]

    cfg = get_material_config(key)
    model_path = cfg["model_path"]

    if not model_path.exists():
        raise RuntimeError(
            f"Model not found for material '{key}': {model_path}"
        )

    from ultralytics import YOLO
    model = YOLO(str(model_path))
    _model_cache[key] = model
    return model


def run_inference(frame: np.ndarray, material: str = "steel") -> dict:
    """
    Run YOLO on a BGR numpy frame for the given material.

    Returns a dict with:
        total_defects, detections, quality_score, status,
        severity, remarks, annotated_jpg, material
    Plus material-specific defect counts (steel: scratches/dents/rust/other).
    """
    key = material.lower()
    cfg = get_material_config(key)
    model = get_model(key)

    results = model(
        frame,
        imgsz=cfg["imgsz"],
        conf=cfg["confidence"],
        verbose=False,
    )
    result    = results[0]
    annotated = result.plot()

    boxes      = result.boxes
    detections = []

    for box in boxes:
        cls_id = int(box.cls[0])
        conf   = float(box.conf[0])
        coords = box.xyxy[0].tolist()
        detections.append({
            "class":      model.names.get(cls_id, f"class_{cls_id}"),
            "class_name": model.names.get(cls_id, f"class_{cls_id}"),
            "confidence": round(conf * 100, 1),
            "cls_id":     cls_id,
            "x1": int(coords[0]),
            "y1": int(coords[1]),
            "x2": int(coords[2]),
            "y2": int(coords[3]),
        })

    total = len(detections)

    # ── Override class names from registry if model uses numeric names ─
    if "class_names" in cfg:
        for d in detections:
            d["class"]      = cfg["class_names"].get(d["cls_id"], d["class"])
            d["class_name"] = d["class"]

    # ── Quality evaluation ────────────────────────────────────────────
    if key == "steel":
        from quality.evaluator import evaluate_quality
        _STEEL_IDX     = {0: "scratches", 1: "dents", 2: "rust", 3: "other"}
        _STEEL_DISPLAY = {0: "Scratches",  1: "Dents",  2: "Rust",  3: "Other"}
        counts = {"scratches": 0, "dents": 0, "rust": 0, "other": 0}
        for d in detections:
            bucket = _STEEL_IDX.get(d["cls_id"], "other")
            counts[bucket] += 1
            d["class"]      = _STEEL_DISPLAY.get(d["cls_id"], d["class"])
            d["class_name"] = d["class"]
        evaluation = evaluate_quality(**counts)
        extra = counts
    elif key == "metal":
        from metal.evaluator import MetalEvaluator
        evaluation = MetalEvaluator().evaluate(detections)
        extra = {"defect_count": total}
    else:
        evaluation = _generic_evaluate(detections, key)
        extra = {"defect_count": total}

    _, jpg = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])

    return {
        "material":      key,
        "total_defects": total,
        "detections":    detections,
        "quality_score": evaluation["quality_score"],
        "status":        evaluation["status"],
        "severity":      evaluation["severity"],
        "remarks":       evaluation["remarks"],
        "annotated_jpg": jpg.tobytes(),
        **extra,
    }


def save_inspection_record(
    detection: dict,
    inspector: str = "AI System",
    material:  str = "steel",
) -> dict:
    """
    Persist an inspection to the correct database and generate a PDF report.
    Returns the full result dict including image_url and report_available.
    """
    key = material.lower()
    cfg = get_material_config(key)

    now           = datetime.now()
    timestamp     = now.strftime("%d-%m-%Y %H:%M:%S")
    inspection_id = now.strftime(f"{cfg['id_prefix']}%Y%m%d%H%M%S%f")
    status        = detection["status"]

    out_dir  = cfg["output_dir"]
    filename = out_dir / f"{inspection_id}_{status}.jpg"
    with open(str(filename), "wb") as f:
        f.write(detection["annotated_jpg"])

    report_path = None

    if key == "steel":
        from quality.inspector import save_inspection
        save_inspection(
            inspection_id = inspection_id,
            timestamp     = timestamp,
            image_path    = str(filename),
            scratches     = detection.get("scratches", 0),
            dents         = detection.get("dents", 0),
            rust          = detection.get("rust", 0),
            other         = detection.get("other", 0),
            total_defects = detection["total_defects"],
            status        = status,
            quality_score = detection["quality_score"],
            severity      = detection["severity"],
            remarks       = detection["remarks"],
            inspector     = inspector,
        )
        try:
            from reports.generate_report import generate_report
            report_path = generate_report(inspection_id)
        except Exception:
            pass
        image_url = f"/api/images/steel/{inspection_id}"

    elif key == "metal":
        from metal.database import save_inspection as metal_save
        metal_save(
            inspection_id = inspection_id,
            timestamp     = timestamp,
            image_path    = str(filename),
            defect_count  = detection["total_defects"],
            quality_score = detection["quality_score"],
            severity      = detection["severity"],
            status        = status,
            remarks       = detection["remarks"],
            defects       = detection["detections"],
            inspector     = inspector,
            material      = cfg["label"],
        )
        try:
            from reports.metal_report import generate_metal_report
            report_path = generate_metal_report(inspection_id)
        except Exception:
            pass
        image_url = f"/api/images/metal/{inspection_id}"

    elif key == "fabric":
        from fabric.database import save_inspection as fabric_save
        fabric_save(
            inspection_id = inspection_id,
            timestamp     = timestamp,
            material      = cfg["label"],
            image_path    = str(filename),
            defect_count  = detection["total_defects"],
            quality_score = detection["quality_score"],
            severity      = detection["severity"],
            status        = status,
            remarks       = detection["remarks"],
            defects       = detection["detections"],
            inspector     = inspector,
        )
        try:
            from reports.generic_report import generate_generic_report
            report_path = generate_generic_report(inspection_id, key)
        except Exception:
            pass
        image_url = f"/api/images/{key}/{inspection_id}"

    elif key == "pcb":
        from pcb.database import save_inspection as pcb_save
        pcb_save(
            inspection_id = inspection_id,
            timestamp     = timestamp,
            material      = cfg["label"],
            image_path    = str(filename),
            defect_count  = detection["total_defects"],
            quality_score = detection["quality_score"],
            severity      = detection["severity"],
            status        = status,
            remarks       = detection["remarks"],
            defects       = detection["detections"],
            inspector     = inspector,
        )
        try:
            from reports.generic_report import generate_generic_report
            report_path = generate_generic_report(inspection_id, key)
        except Exception:
            pass
        image_url = f"/api/images/{key}/{inspection_id}"

    else:  # welding
        from welding.database import save_inspection as welding_save
        welding_save(
            inspection_id = inspection_id,
            timestamp     = timestamp,
            material      = cfg["label"],
            image_path    = str(filename),
            defect_count  = detection["total_defects"],
            quality_score = detection["quality_score"],
            severity      = detection["severity"],
            status        = status,
            remarks       = detection["remarks"],
            defects       = detection["detections"],
            inspector     = inspector,
        )
        try:
            from reports.generic_report import generate_generic_report
            report_path = generate_generic_report(inspection_id, key)
        except Exception:
            pass
        image_url = f"/api/images/{key}/{inspection_id}"

    return {
        "inspection_id":    inspection_id,
        "material":         key,
        "timestamp":        timestamp,
        "status":           status,
        "quality_score":    detection["quality_score"],
        "severity":         detection["severity"],
        "remarks":          detection["remarks"],
        "total_defects":    detection["total_defects"],
        "detections":       detection["detections"],
        "image_url":        image_url,
        "report_available": report_path is not None,
    }
