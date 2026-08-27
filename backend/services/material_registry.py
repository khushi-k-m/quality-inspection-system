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
    },
    "metal": {
        "model_path":   ROOT_DIR / "trained_model" / "metal_surface_model" / "weights" / "best.pt",
        "output_dir":   ROOT_DIR / "output" / "metal_capture",
        "confidence":   0.25,
        "imgsz":        640,
        "id_prefix":    "MINSP",
        "label":        "Metal",
    },
    # Future: "fabric": { ... }
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
