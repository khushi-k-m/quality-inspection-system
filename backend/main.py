import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.auth import router as auth_router
from backend.api.inspections import router as inspections_router
from backend.api.analytics import router as analytics_router
from backend.api.reports import router as reports_router
from backend.api.camera import router as camera_router
from backend.api.images import router as images_router
from backend.database import db_status
from backend.services.camera_service import camera_service

app = FastAPI(
    title="SteelVision AI API",
    description="AI-Powered Industrial Quality Inspection System",
    version="1.0.0"
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(inspections_router)
app.include_router(analytics_router)
app.include_router(reports_router)
app.include_router(camera_router)
app.include_router(images_router)


@app.get("/health")
def health():
    model_path = ROOT_DIR / "trained_model" / "steel_defect_model" / "weights" / "best.pt"
    return {
        "status": "online",
        "database": "online" if db_status() else "error",
        "model": "ready" if model_path.exists() else "not_found",
        "camera": "connected" if camera_service.camera_connected else "disconnected",
        "camera_running": camera_service._running
    }


if __name__ == "__main__":
    import uvicorn
    # Initialize database on startup
    try:
        from quality.database import create_database
        create_database()
    except Exception as e:
        print(f"DB init warning: {e}")

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1  # Must be 1 — camera is a singleton thread
    )
