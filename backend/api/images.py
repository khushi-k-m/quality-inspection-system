from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pathlib import Path
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/images", tags=["images"])

ROOT_DIR      = Path(__file__).resolve().parent.parent.parent
STEEL_DIR     = ROOT_DIR / "output" / "camera_capture"
METAL_DIR     = ROOT_DIR / "output" / "metal_capture"
FABRIC_DIR    = ROOT_DIR / "output" / "fabric_capture"
PCB_DIR       = ROOT_DIR / "output" / "pcb_capture"
WELDING_DIR   = ROOT_DIR / "output" / "welding_capture"

MATERIAL_DIRS = {
    "steel":   STEEL_DIR,
    "metal":   METAL_DIR,
    "fabric":  FABRIC_DIR,
    "pcb":     PCB_DIR,
    "welding": WELDING_DIR,
}


def _find_image(img_dir: Path, inspection_id: str):
    for suffix in ["PASS", "FAIL", "REWORK"]:
        path = img_dir / f"{inspection_id}_{suffix}.jpg"
        if path.exists():
            return path
    return None


@router.get("/steel/{inspection_id}")
def get_steel_image(inspection_id: str, user=Depends(get_current_user)):
    path = _find_image(STEEL_DIR, inspection_id)
    if path:
        return FileResponse(str(path), media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Steel image not found")


@router.get("/metal/{inspection_id}")
def get_metal_image(inspection_id: str, user=Depends(get_current_user)):
    path = _find_image(METAL_DIR, inspection_id)
    if path:
        return FileResponse(str(path), media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Metal image not found")


@router.get("/fabric/{inspection_id}")
def get_fabric_image(inspection_id: str, user=Depends(get_current_user)):
    path = _find_image(FABRIC_DIR, inspection_id)
    if path:
        return FileResponse(str(path), media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Fabric image not found")


@router.get("/pcb/{inspection_id}")
def get_pcb_image(inspection_id: str, user=Depends(get_current_user)):
    path = _find_image(PCB_DIR, inspection_id)
    if path:
        return FileResponse(str(path), media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="PCB image not found")


@router.get("/welding/{inspection_id}")
def get_welding_image(inspection_id: str, user=Depends(get_current_user)):
    path = _find_image(WELDING_DIR, inspection_id)
    if path:
        return FileResponse(str(path), media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Welding image not found")


@router.get("/{inspection_id}")
def get_image_auto(inspection_id: str, user=Depends(get_current_user)):
    """Legacy endpoint — searches all material dirs."""
    for img_dir in MATERIAL_DIRS.values():
        path = _find_image(img_dir, inspection_id)
        if path:
            return FileResponse(str(path), media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Image not found")


@router.get("/thermal/{inspection_id}")
def get_thermal_image(inspection_id: str, user=Depends(get_current_user)):
    """Return the false-color thermal sheet image."""
    path = ROOT_DIR / "output" / "reports" / f"{inspection_id}_thermal_sheet.jpg"
    if path.exists():
        return FileResponse(str(path), media_type="image/jpeg")
    try:
        from reports.enhanced_report import generate_enhanced_report
        generate_enhanced_report(inspection_id)
        if path.exists():
            return FileResponse(str(path), media_type="image/jpeg")
    except Exception:
        pass
    raise HTTPException(status_code=404, detail="Thermal image not found")

