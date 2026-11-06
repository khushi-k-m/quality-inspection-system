from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from backend.services.camera_service import camera_service
from backend.dependencies import get_current_user
import time

router = APIRouter(prefix="/api/camera", tags=["camera"])


class CameraStartRequest(BaseModel):
    material: str = "auto"


class CameraModeRequest(BaseModel):
    material: str = "auto"


class CameraCaptureRequest(BaseModel):
    inspector: Optional[str] = "AI Camera System"


def mjpeg_generator():
    while camera_service._running:
        frame = camera_service.latest_frame_jpg
        if frame:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                frame +
                b"\r\n"
            )
        time.sleep(0.033)  # ~30fps cap


@router.get("/stream")
def camera_stream():
    # No auth on stream endpoint so <img src> works directly in browser
    if not camera_service._running:
        raise HTTPException(status_code=503, detail="Camera not running")
    return StreamingResponse(
        mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/status")
def camera_status(user=Depends(get_current_user)):
    status = camera_service.get_status()
    status["detection"] = camera_service.latest_detection
    return status


@router.post("/start")
def start_camera(body: CameraStartRequest = CameraStartRequest(), user=Depends(get_current_user)):
    result = camera_service.start(body.material)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@router.post("/mode")
def set_camera_mode(body: CameraModeRequest, user=Depends(get_current_user)):
    """Switch active material or auto-detection mode without stopping the camera."""
    result = camera_service.set_mode(body.material)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/stop")
def stop_camera(user=Depends(get_current_user)):
    return camera_service.stop()


@router.post("/capture")
def capture_inspection(body: Optional[CameraCaptureRequest] = None, user=Depends(get_current_user)):
    inspector = body.inspector if body and body.inspector else "AI Camera System"
    result, error = camera_service.capture_and_save(inspector=inspector)
    if error:
        raise HTTPException(status_code=500, detail=error)
    return result
