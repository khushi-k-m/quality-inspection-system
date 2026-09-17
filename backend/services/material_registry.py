"""
Material Registry
=================
Single source of truth for all supported inspection materials.
To add a new material (e.g. Fabric), add one entry to MATERIALS.
"""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent  # project root

MATERIALS = {
    "steel": {
        "model_path":   ROOT_DIR / "trained_model" / "steel_defect_model" / "weights" / "best.pt",
        "output_dir":   ROOT_DIR / "output" / "camera_capture",
        "confidence":   0.40,
        "imgsz":        320,
        "id_prefix":    "INSP",
        "label":        "Steel",
        "db_path":      ROOT_DIR / "database" / "inspection.db",
        "class_names":  {0: "Scratches", 1: "Dents", 2: "Rust", 3: "Other"},
    },
    "metal": {
        "model_path":   ROOT_DIR / "trained_model" / "metal_surface_model" / "weights" / "best.pt",
        "output_dir":   ROOT_DIR / "output" / "metal_capture",
        "confidence":   0.25,
        "imgsz":        640,
        "id_prefix":    "MINSP",
        "label":        "Metal",
        "db_path":      ROOT_DIR / "database" / "metal_inspections.db",
        "class_names":  {0: "inclusion", 1: "oil_spot", 2: "punching_hole", 3: "silk_spot", 4: "water_spot", 5: "welding_line"},
    },
    "fabric": {
        "model_path":   ROOT_DIR / "trained_model" / "fabrics_defect_model" / "weights" / "best.pt",
        "output_dir":   ROOT_DIR / "output" / "fabric_capture",
        "confidence":   0.35,
        "imgsz":        640,
        "id_prefix":    "FINSP",
        "label":        "Fabric",
        "db_path":      ROOT_DIR / "database" / "fabric_inspections.db",
        "class_names":  {0: "color_bleeding", 1: "crease", 2: "hole"},
    },
    "pcb": {
        "model_path":   ROOT_DIR / "trained_model" / "pcb_boards_model" / "weights" / "best.pt",
        "output_dir":   ROOT_DIR / "output" / "pcb_capture",
        "confidence":   0.35,
        "imgsz":        640,
        "id_prefix":    "PINSP",
        "label":        "PCB",
        "db_path":      ROOT_DIR / "database" / "pcb_inspections.db",
        "class_names":  {0: "missing_hole", 1: "mouse_bite", 2: "open_circuit", 3: "short", 4: "spur", 5: "spurious_copper"},
    },
    "welding": {
        "model_path":   ROOT_DIR / "trained_model" / "welding_defect_model" / "weights" / "best.pt",
        "output_dir":   ROOT_DIR / "output" / "welding_capture",
        "confidence":   0.40,
        "imgsz":        640,
        "id_prefix":    "WINSP",
        "label":        "Welding",
        "db_path":      ROOT_DIR / "database" / "welding_inspections.db",
        "class_names":  {0: "bad_weld", 1: "good_weld"},
    },
}

ALLOWED_MATERIALS = set(MATERIALS.keys())


def get_material_config(material: str) -> dict:
    material = material.lower()
    if material not in MATERIALS:
        raise ValueError(
            f"Unsupported material '{material}'. "
            f"Allowed: {sorted(ALLOWED_MATERIALS)}"
        )
    cfg = MATERIALS[material].copy()
    cfg["output_dir"].mkdir(parents=True, exist_ok=True)
    return cfg
