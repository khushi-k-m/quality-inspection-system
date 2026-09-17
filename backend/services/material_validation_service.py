"""
Material Validation Service
============================
Provides pre-inspection validation before the defect model runs.

IMPORTANT — HONEST LIMITATION STATEMENT
-----------------------------------------
The five existing defect models are single-domain defect detectors. They are
trained on defects within their own material class and do not reliably
identify material class from a generic input image. It is therefore unsafe to
accept a zero-defect result as PASS without first checking that the image
contains a real product and matches the selected material.

This file does two things conservatively:
1. Reject blank / empty / featureless images before any quality decision.
2. Reject obvious material mismatches by comparing the selected material's
   model against the other material models using real inference evidence.

This is still a heuristic, not a true multi-class material classifier. If a
proper training dataset for steel/metal/fabric/pcb/welding + background is
added later, this module is the natural integration point.
"""

import cv2
import numpy as np

from backend.services.material_registry import MATERIALS

# ── Validation configuration (single source of truth) ─────────────────────
# Blank/uniform images score: lap=0.0, entropy≈0, edge=0.0.
# Real low-texture materials (fabric, metal) score: lap≥1, entropy≥4, edge≥0.
# Entropy is the most reliable discriminator. Lap and edge thresholds are
# set near-zero so only truly featureless frames fail the 2-of-3 vote.
VALIDATION_CONFIG = {
    "min_laplacian_variance": 0.5,   # only pure blank (0.0) fails
    "min_entropy": 1.0,              # blank=-0.0; real images always >4
    "min_edge_fraction": 0.0001,     # only pure blank (0.0) fails
    "mismatch_confidence_threshold": 0.70,
    "mismatch_min_detections": 1,
}

# ── Status constants ───────────────────────────────────────────────────────
STATUS_INVALID_IMAGE    = "INVALID_IMAGE"
STATUS_INVALID_MATERIAL = "INVALID_MATERIAL"
STATUS_UNVERIFIED       = "MATERIAL_UNVERIFIED"

REASON_NO_PRODUCT     = "NO_PRODUCT_DETECTED"
REASON_WRONG_MATERIAL  = "WRONG_MATERIAL"
REASON_LOW_CONFIDENCE = "LOW_CONFIDENCE"
REASON_BLANK_IMAGE    = "BLANK_IMAGE"


def _image_entropy(gray: np.ndarray) -> float:
    """Shannon entropy of pixel intensity histogram."""
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    hist = hist[hist > 0]
    prob = hist / hist.sum()
    return float(-np.sum(prob * np.log2(prob)))


def _laplacian_variance(gray: np.ndarray) -> float:
    """Variance of Laplacian — measures image sharpness / texture."""
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _edge_fraction(gray: np.ndarray) -> float:
    """Fraction of pixels that are Canny edges."""
    edges = cv2.Canny(gray, 50, 150)
    return float(np.count_nonzero(edges)) / edges.size


def check_image_content(frame: np.ndarray) -> dict:
    """Reject empty or featureless frames before running the defect model."""
    if frame is None or frame.size == 0:
        return {
            "has_content": False,
            "reason": REASON_BLANK_IMAGE,
            "laplacian_var": 0.0,
            "entropy": 0.0,
            "edge_fraction": 0.0,
            "message": "Image is empty or could not be decoded.",
        }

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
    lap_var = _laplacian_variance(gray)
    entropy = _image_entropy(gray)
    edge_frac = _edge_fraction(gray)

    cfg = VALIDATION_CONFIG
    lap_ok = lap_var >= cfg["min_laplacian_variance"]
    ent_ok = entropy >= cfg["min_entropy"]
    edge_ok = edge_frac >= cfg["min_edge_fraction"]
    passed = sum([lap_ok, ent_ok, edge_ok])
    has_content = passed >= 2

    if not has_content:
        return {
            "has_content": False,
            "reason": REASON_NO_PRODUCT,
            "laplacian_var": round(lap_var, 2),
            "entropy": round(entropy, 3),
            "edge_fraction": round(edge_frac, 4),
            "message": (
                "No valid inspection product detected. "
                "The image appears blank, empty, or too featureless. "
                "Please position the product clearly inside the camera frame."
            ),
        }

    return {
        "has_content": True,
        "reason": None,
        "laplacian_var": round(lap_var, 2),
        "entropy": round(entropy, 3),
        "edge_fraction": round(edge_frac, 4),
        "message": "Image content detected.",
    }


def _material_label(material: str) -> str:
    return str(material).capitalize()


def build_invalid_image_response(selected_material: str, content_check: dict) -> dict:
    """Standard INVALID_IMAGE response."""
    return {
        "success": False,
        "inspection_valid": False,
        "selected_material": selected_material,
        "detected_material": None,
        "material_confidence": 0.0,
        "material_valid": False,
        "product_detected": False,
        "status": STATUS_INVALID_IMAGE,
        "reason": content_check.get("reason", REASON_NO_PRODUCT),
        "message": (
            f"No valid {_material_label(selected_material)} product detected. "
            "Please position the product clearly inside the camera frame."
        ),
        "validation_detail": {
            "laplacian_variance": content_check.get("laplacian_var"),
            "entropy": content_check.get("entropy"),
            "edge_fraction": content_check.get("edge_fraction"),
        },
    }


def build_invalid_material_response(selected_material: str, detected_material: str, confidence: float | None) -> dict:
    """Standard INVALID_MATERIAL response for an obvious material mismatch."""
    selected_label = _material_label(selected_material)
    detected_label = _material_label(detected_material) if detected_material else "Unknown"
    return {
        "success": False,
        "inspection_valid": False,
        "selected_material": selected_material,
        "detected_material": detected_material,
        "material_confidence": confidence if confidence is not None else 0.0,
        "material_valid": False,
        "product_detected": True,
        "status": STATUS_INVALID_MATERIAL,
        "reason": REASON_WRONG_MATERIAL,
        "message": (
            f"Selected material is {selected_label}, but the input appears to contain {detected_label}. "
            f"Please show a {selected_label} product or select {detected_label}."
        ),
    }


def build_unverified_response(selected_material: str) -> dict:
    """Explicit state when an image is not blank but the material cannot be confirmed."""
    return {
        "success": False,
        "inspection_valid": False,
        "selected_material": selected_material,
        "detected_material": None,
        "material_confidence": 0.0,
        "material_valid": False,
        "product_detected": True,
        "status": STATUS_UNVERIFIED,
        "reason": REASON_LOW_CONFIDENCE,
        "message": (
            f"Material could not be verified reliably for {_material_label(selected_material)}. "
            "Please provide a clearer image of the selected material."
        ),
    }


def build_valid_response(selected_material: str, inference_result: dict) -> dict:
    """Wrap an accepted inspection result in the standard response contract."""
    return {
        "success": True,
        "inspection_valid": True,
        "selected_material": selected_material,
        "detected_material": selected_material,
        "material_confidence": inference_result.get("material_confidence"),
        "material_valid": True,
        "product_detected": True,
        **inference_result,
    }


def _detect_obvious_mismatch(frame: np.ndarray, material: str, selected_result: dict) -> dict | None:
    """
    Conservative mismatch heuristic using real model outputs.

    A mismatch is only flagged when the SELECTED model found ZERO detections
    but another model fires with high confidence. If the selected model found
    anything at all, we trust it — cross-firing between defect models is a
    known limitation and falsely rejecting a valid inspection is worse than
    missing a mismatch in the ambiguous case.
    """
    from backend.services.inference_service import run_inference

    material_key = str(material).lower()
    selected_total = int(selected_result.get("total_defects", 0) or 0)

    # If the selected model detected something, accept the result.
    if selected_total > 0:
        return None

    # Selected model found nothing — check whether another model fires
    # confidently, which would indicate the wrong material was shown.
    candidates = []
    for other_material in MATERIALS:
        if other_material == material_key:
            continue
        try:
            other_result = run_inference(frame, other_material)
        except Exception:
            continue
        dets = other_result.get("detections", [])
        if not dets:
            continue
        max_conf = max(float(d.get("confidence", 0.0)) / 100.0 for d in dets)
        if max_conf < VALIDATION_CONFIG["mismatch_confidence_threshold"]:
            continue
        candidates.append({
            "material": other_material,
            "max_conf": max_conf,
            "total": int(other_result.get("total_defects", 0) or 0),
        })

    if not candidates:
        return None

    best = max(candidates, key=lambda item: (item["max_conf"], item["total"]))
    if best["total"] >= VALIDATION_CONFIG["mismatch_min_detections"]:
        return {
            "detected_material": best["material"],
            "confidence": best["max_conf"],
        }

    return None


def validate_inference_result(frame: np.ndarray, material: str, inference_result: dict) -> dict:
    """Apply blank-image and mismatch checks before accepting the defect result."""
    content = check_image_content(frame)
    if not content["has_content"]:
        return build_invalid_image_response(material, content)

    mismatch = _detect_obvious_mismatch(frame, material, inference_result)
    if mismatch is not None:
        return build_invalid_material_response(material, mismatch["detected_material"], mismatch["confidence"])

    # If the selected model produced a result but the frame is not blank and no
    # obvious mismatch is seen, accept the inspection as valid. This preserves the
    # established quality logic for real products.
    return build_valid_response(material, inference_result)


def validate_and_run_inference(frame: np.ndarray, material: str) -> dict:
    """Central entry point: validate the image and then run the selected material model."""
    from backend.services.inference_service import run_inference

    content = check_image_content(frame)
    if not content["has_content"]:
        return build_invalid_image_response(material, content)

    inference = run_inference(frame, material)
    return validate_inference_result(frame, material, inference)
