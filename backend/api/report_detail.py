"""
Report Detail API
=================
GET /api/report-detail/{inspection_id}?material=steel

Returns a fully enriched inspection payload used by the enhanced PDF
generator and (optionally) the frontend.  All calculations happen here
— the frontend never fabricates data.

Response shape
--------------
{
  "inspection_id": str,
  "material": str,
  "timestamp": str,
  "status": str,
  "quality_score": int,
  "severity": str,
  "remarks": str,
  "inspector": str,
  "defects": [
    {
      "defect_class": str,
      "confidence": float,          # 0-100
      "x1": int, "y1": int,
      "x2": int, "y2": int,
      "bbox_area_px": int | null,
      "defect_area_pct": float | null   # bbox / image area * 100, or null
    }, ...
  ],
  "defect_statistics": {
    "total_defects": int,
    "by_type": { "ClassName": {"count": int, "total_area_pct": float|null} },
    "image_width_px": int | null,
    "image_height_px": int | null,
    "image_area_px": int | null,
    "area_pct_available": bool
  },
  "heatmap": {
    "available": bool,
    "method": str,
    "grid": [[float, ...], ...] | null,   # normalised 0-1 intensity grid
    "grid_rows": int | null,
    "grid_cols": int | null,
    "note": str
  },
  "recommendation": {
    "applicable": bool,
    "items": [
      {
        "defect_class": str,
        "method": str,
        "reason": str,
        "expected_outcome": str,
        "reinspect": bool
      }, ...
    ]
  },
  "cost_estimate": {
    "available": bool,
    "total": float | null,
    "currency": str,
    "breakdown": [...],
    "note": str
  },
  "historical": {
    "quality_trend": [...],   # only if ≥2 inspections exist
    "defect_trend": [...],
    "status_distribution": [...],
    "total_inspections": int
  },
  "image_path": str | null
}
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pathlib import Path
import cv2
import numpy as np

from backend.dependencies import get_current_user
from backend.services.rework_config import get_rework_rule, compute_cost_estimate

router = APIRouter(prefix="/api/report-detail", tags=["report-detail"])

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# ── Grid dimensions for heatmap ───────────────────────────────────────
_HEATMAP_ROWS = 20
_HEATMAP_COLS = 20


def _get_record(inspection_id: str, material: str) -> dict:
    """Fetch inspection + defects from the correct database."""
    m = material.lower()
    if m == "steel":
        from backend.database import get_db
        conn = get_db()
        row = conn.execute(
                 """SELECT inspection_id, timestamp, image_path, scratches, dents, rust, other,
                     detections_json,
                      total_defects, status, inspector, quality_score, severity, remarks
               FROM inspections WHERE inspection_id = ?""",
            (inspection_id,),
        ).fetchone()
        conn.close()
        if row is None:
            return None
        d = dict(row)
        d["material"] = "Steel"
        d["defect_count"] = d.get("total_defects", 0)
        # New records retain per-detection coordinates; older rows use counts.
        import json
        try:
            defects = json.loads(d.get("detections_json") or "[]")
        except (TypeError, ValueError):
            defects = []
        if not isinstance(defects, list) or not defects:
            defects = []
            for cls, cnt_key in [("Scratches", "scratches"), ("Dents", "dents"),
                                  ("Rust", "rust"), ("Other", "other")]:
                for _ in range(d.get(cnt_key, 0) or 0):
                    defects.append({
                        "defect_class": cls, "confidence": None,
                        "x1": None, "y1": None, "x2": None, "y2": None,
                    })
        else:
            for defect in defects:
                defect.setdefault("defect_class", defect.get("class_name") or defect.get("class") or "Unknown")
        d["defects"] = defects
        return d

    elif m == "metal":
        from metal.database import get_inspections, get_defects_for_inspection
        records = get_inspections(limit=100000)
        record = next((r for r in records if r["inspection_id"] == inspection_id), None)
        if record is None:
            return None
        record["defects"] = get_defects_for_inspection(inspection_id)
        return record

    elif m == "fabric":
        from fabric.database import get_inspection
        return get_inspection(inspection_id)

    elif m == "pcb":
        from pcb.database import get_inspection
        return get_inspection(inspection_id)

    elif m == "welding":
        from welding.database import get_inspection
        return get_inspection(inspection_id)

    return None


def _get_historical(material: str) -> dict:
    """Return historical analytics for the material."""
    m = material.lower()
    try:
        if m == "steel":
            from backend.api.steel import steel_analytics

            class _FakeUser:
                pass
            # Call the analytics function directly (no HTTP)
            from backend.database import get_db
            from datetime import datetime
            conn = get_db()
            rows = conn.execute(
                "SELECT inspection_id, timestamp, quality_score, total_defects, status FROM inspections ORDER BY id ASC"
            ).fetchall()
            conn.close()
            total = len(rows)
            quality_trend = [
                {"inspection_id": r["inspection_id"], "timestamp": r["timestamp"],
                 "quality_score": r["quality_score"] or 100}
                for r in rows
            ]
            daily: dict = {}
            for r in rows:
                ts = r["timestamp"] or ""
                for fmt in ["%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        k = str(datetime.strptime(ts.strip(), fmt).date())
                        daily[k] = daily.get(k, 0) + (r["total_defects"] or 0)
                        break
                    except ValueError:
                        pass
            status_dist = {}
            for r in rows:
                s = r["status"] or "UNKNOWN"
                status_dist[s] = status_dist.get(s, 0) + 1
            return {
                "total_inspections": total,
                "quality_trend": quality_trend,
                "defect_trend": [{"date": k, "total_defects": v} for k, v in sorted(daily.items())],
                "status_distribution": [{"status": k, "count": v} for k, v in status_dist.items()],
            }

        elif m == "metal":
            from metal.database import _connect
            from datetime import datetime
            conn = _connect()
            rows = conn.execute(
                "SELECT inspection_id, timestamp, quality_score, defect_count, status FROM inspections ORDER BY id ASC"
            ).fetchall()
            conn.close()
            total = len(rows)
            quality_trend = [
                {"inspection_id": r["inspection_id"], "timestamp": r["timestamp"],
                 "quality_score": r["quality_score"] or 100}
                for r in rows
            ]
            daily: dict = {}
            for r in rows:
                ts = r["timestamp"] or ""
                for fmt in ["%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        k = str(datetime.strptime(ts.strip(), fmt).date())
                        daily[k] = daily.get(k, 0) + (r["defect_count"] or 0)
                        break
                    except ValueError:
                        pass
            status_dist = {}
            for r in rows:
                s = r["status"] or "UNKNOWN"
                status_dist[s] = status_dist.get(s, 0) + 1
            return {
                "total_inspections": total,
                "quality_trend": quality_trend,
                "defect_trend": [{"date": k, "total_defects": v} for k, v in sorted(daily.items())],
                "status_distribution": [{"status": k, "count": v} for k, v in status_dist.items()],
            }

        else:
            mod_map = {"fabric": "fabric.database", "pcb": "pcb.database", "welding": "welding.database"}
            import importlib
            mod = importlib.import_module(mod_map[m])
            data = mod.get_analytics()
            return {
                "total_inspections": data.get("total_inspections", 0),
                "quality_trend": data.get("quality_trend", []),
                "defect_trend": data.get("defect_trend", []),
                "status_distribution": data.get("status_distribution", []),
            }
    except Exception:
        return {"total_inspections": 0, "quality_trend": [], "defect_trend": [], "status_distribution": []}


def _build_defect_stats(defects: list, image_path: str | None) -> dict:
    """
    Compute per-defect statistics including bbox area percentage.
    Area percentage = (bbox_w * bbox_h) / (img_w * img_h) * 100
    Only calculated when bbox coords AND image dimensions are available.
    """
    img_w = img_h = img_area = None
    area_pct_available = False

    if image_path and Path(image_path).exists():
        try:
            img = cv2.imread(image_path)
            if img is not None:
                img_h, img_w = img.shape[:2]
                img_area = img_w * img_h
                area_pct_available = True
        except Exception:
            pass

    enriched = []
    by_type: dict = {}

    for d in defects:
        cls = d.get("defect_class") or d.get("class_name") or d.get("class", "unknown")
        conf = d.get("confidence")
        x1, y1, x2, y2 = d.get("x1"), d.get("y1"), d.get("x2"), d.get("y2")

        bbox_area = None
        area_pct = None
        if area_pct_available and None not in (x1, y1, x2, y2):
            bw = max(0, (x2 or 0) - (x1 or 0))
            bh = max(0, (y2 or 0) - (y1 or 0))
            bbox_area = bw * bh
            if img_area and img_area > 0:
                area_pct = round(bbox_area / img_area * 100, 3)

        enriched.append({
            "defect_class": cls,
            "confidence": conf,
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "bbox_area_px": bbox_area,
            "defect_area_pct": area_pct,
        })

        if cls not in by_type:
            by_type[cls] = {"count": 0, "total_area_pct": 0.0 if area_pct_available else None}
        by_type[cls]["count"] += 1
        if area_pct is not None and by_type[cls]["total_area_pct"] is not None:
            by_type[cls]["total_area_pct"] = round(
                by_type[cls]["total_area_pct"] + area_pct, 3
            )

    return {
        "total_defects": len(defects),
        "by_type": by_type,
        "image_width_px": img_w,
        "image_height_px": img_h,
        "image_area_px": img_area,
        "area_pct_available": area_pct_available,
        "enriched_defects": enriched,
    }


def _build_heatmap(defects: list, image_path: str | None) -> dict:
    """
    Build a normalised intensity grid from real bounding-box locations.
    Grid cells accumulate 1 per defect bbox that overlaps the cell.
    Normalised to [0, 1].  Returns null grid if no bbox data available.
    """
    img_w = img_h = None
    if image_path and Path(image_path).exists():
        try:
            img = cv2.imread(image_path)
            if img is not None:
                img_h, img_w = img.shape[:2]
        except Exception:
            pass

    # Check if any defect has valid bbox
    valid = [d for d in defects
             if None not in (d.get("x1"), d.get("y1"), d.get("x2"), d.get("y2"))]

    if not valid:
        return {
            "available": False,
            "method": None,
            "grid": None,
            "grid_rows": None,
            "grid_cols": None,
            "note": (
                "Heatmap unavailable: bounding-box coordinates were not stored "
                "for this inspection. This occurs for Steel inspections where "
                "only defect counts (not per-box coordinates) are persisted."
            ),
        }

    # Use image dimensions if available, else infer from bbox extents
    if img_w is None or img_h is None:
        all_x2 = [d["x2"] for d in valid if d.get("x2")]
        all_y2 = [d["y2"] for d in valid if d.get("y2")]
        img_w = max(all_x2) if all_x2 else 640
        img_h = max(all_y2) if all_y2 else 640

    rows, cols = _HEATMAP_ROWS, _HEATMAP_COLS
    grid = np.zeros((rows, cols), dtype=np.float32)

    cell_w = img_w / cols
    cell_h = img_h / rows

    for d in valid:
        x1, y1, x2, y2 = d["x1"], d["y1"], d["x2"], d["y2"]
        # Find grid cells overlapped by this bbox
        col_start = max(0, int(x1 / cell_w))
        col_end   = min(cols - 1, int(x2 / cell_w))
        row_start = max(0, int(y1 / cell_h))
        row_end   = min(rows - 1, int(y2 / cell_h))
        grid[row_start:row_end + 1, col_start:col_end + 1] += 1.0

    max_val = grid.max()
    if max_val > 0:
        grid = grid / max_val

    return {
        "available": True,
        "method": "Bounding-box accumulation grid (normalised 0–1)",
        "grid": grid.tolist(),
        "grid_rows": rows,
        "grid_cols": cols,
        "note": (
            f"Grid {rows}×{cols} built from {len(valid)} bounding box(es). "
            "Cell intensity = fraction of defect boxes overlapping that cell."
        ),
    }


def _build_recommendations(material: str, defects: list) -> dict:
    """Build rework recommendations from the configured rule table."""
    if not defects:
        return {"applicable": False, "items": []}

    items = []
    seen = set()
    for d in defects:
        cls = d.get("defect_class") or d.get("class_name") or d.get("class", "unknown")
        if cls in seen:
            continue
        seen.add(cls)
        rule = get_rework_rule(material, cls)
        if rule and rule.get("method") != "No rework required":
            items.append({
                "defect_class": cls,
                "method": rule["method"],
                "reason": rule["reason"],
                "expected_outcome": rule["expected_outcome"],
                "reinspect": rule["reinspect"],
            })

    return {"applicable": bool(items), "items": items}


@router.get("/{inspection_id}")
def get_report_detail(
    inspection_id: str,
    material: str = Query(..., description="Material key: steel|metal|fabric|pcb|welding"),
    user=Depends(get_current_user),
):
    record = _get_record(inspection_id, material)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Inspection {inspection_id} not found for material '{material}'")

    defects = record.get("defects", [])
    image_path = record.get("image_path")

    stats = _build_defect_stats(defects, image_path)
    enriched_defects = stats.pop("enriched_defects")

    heatmap = _build_heatmap(enriched_defects, image_path)
    recommendation = _build_recommendations(material, enriched_defects)
    cost_estimate = compute_cost_estimate(material, enriched_defects)
    historical = _get_historical(material)

    # Only include trend if ≥2 inspections exist
    if historical.get("total_inspections", 0) < 2:
        historical["quality_trend"] = []
        historical["defect_trend"] = []

    return {
        "inspection_id": record.get("inspection_id"),
        "material": record.get("material", material),
        "timestamp": record.get("timestamp"),
        "status": record.get("status"),
        "quality_score": record.get("quality_score"),
        "severity": record.get("severity"),
        "remarks": record.get("remarks"),
        "inspector": record.get("inspector", "AI System"),
        "defects": enriched_defects,
        "defect_statistics": stats,
        "heatmap": heatmap,
        "recommendation": recommendation,
        "cost_estimate": cost_estimate,
        "historical": historical,
        "image_path": image_path,
    }
