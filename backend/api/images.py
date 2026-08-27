from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pathlib import Path
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/images", tags=["images"])

ROOT_DIR   = Path(__file__).resolve().parent.parent.parent
STEEL_DIR  = ROOT_DIR / "output" / "camera_capture"
METAL_DIR  = ROOT_DIR / "output" / "metal_capture"

MATERIAL_DIRS = {
    "steel": STEEL_DIR,
    "metal": METAL_DIR,
}


@router.get("/steel/{inspection_id}")
def get_steel_image(inspection_id: str, user=Depends(get_current_user)):
    for suffix in ["PASS", "FAIL", "REWORK"]:
        path = STEEL_DIR / f"{inspection_id}_{suffix}.jpg"
        if path.exists():
            return FileResponse(str(path), media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Steel image not found")


@router.get("/metal/{inspection_id}")
def get_metal_image_legacy(inspection_id: str, user=Depends(get_current_user)):
    for suffix in ["PASS", "FAIL", "REWORK"]:
        path = METAL_DIR / f"{inspection_id}_{suffix}.jpg"
        if path.exists():
            return FileResponse(str(path), media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Metal image not found")


@router.get("/{inspection_id}")
def get_image_auto(inspection_id: str, user=Depends(get_current_user)):
    """Legacy endpoint — tries steel dir first, then metal."""
    for img_dir in [STEEL_DIR, METAL_DIR]:
        for suffix in ["PASS", "FAIL", "REWORK"]:
            path = img_dir / f"{inspection_id}_{suffix}.jpg"
            if path.exists():
                return FileResponse(str(path), media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Image not found")
