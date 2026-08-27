import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.auth        import router as auth_router
from backend.api.inspections import router as inspections_router   # legacy steel
from backend.api.analytics   import router as analytics_router     # legacy steel
from backend.api.reports     import router as reports_router       # legacy steel
from backend.api.camera      import router as camera_router
from backend.api.images      import router as images_router
from backend.api.steel       import router as steel_router
from backend.api.metal       import router as metal_router
from backend.database        import db_status
from backend.services.camera_service import camera_service

app = FastAPI(
    title="SteelVision AI API",
    description="AI-Powered Multi-Material Industrial Quality Inspection System",
    version="2.0.0",
)

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

# ── Routers ────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(steel_router)       # /api/steel/*
app.include_router(metal_router)       # /api/metal/*
app.include_router(inspections_router) # /api/inspections  (legacy)
app.include_router(analytics_router)   # /api/analytics    (legacy)
app.include_router(reports_router)     # /api/reports      (legacy)
app.include_router(camera_router)
app.include_router(images_router)


@app.on_event("startup")
def initialize_databases():
    from backend.auth import initialize_auth_database
    initialize_auth_database()
    from quality.database import create_database
    create_database()
    from metal.database import create_database as create_metal_database
    create_metal_database()


@app.get("/health")
def health():
    from backend.services.material_registry import MATERIALS
    from metal.database import db_status as metal_db_status

    models = {
        mat: cfg["model_path"].exists()
        for mat, cfg in MATERIALS.items()
    }

    return {
        "status":          "online",
        "database_steel":  "online" if db_status() else "error",
        "database_metal":  "online" if metal_db_status() else "error",
        "models":          {mat: "ready" if ok else "not_found"
                            for mat, ok in models.items()},
        # legacy keys kept for frontend compatibility
        "database":        "online" if db_status() else "error",
        "model":           "ready" if models.get("steel") else "not_found",
        "camera":          "connected" if camera_service.camera_connected else "disconnected",
        "camera_running":  camera_service._running,
    }


if __name__ == "__main__":
    import uvicorn

    # Init databases
    try:
        from quality.database import create_database
        create_database()
    except Exception as e:
        print(f"Steel DB init warning: {e}")

    try:
        from metal.database import create_database as metal_create_db
        metal_create_db()
    except Exception as e:
        print(f"Metal DB init warning: {e}")

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1,
    )
