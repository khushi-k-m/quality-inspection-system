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
from backend.api.fabric      import router as fabric_router
from backend.api.pcb         import router as pcb_router
from backend.api.welding     import router as welding_router
from backend.api.report_detail import router as report_detail_router
from backend.database        import db_status
from backend.services.camera_service import camera_service

from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="SteelVision AI API",
    description="AI-Powered Multi-Material Industrial Quality Inspection System",
    version="2.0.0",
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema.setdefault("components", {})
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in schema.get("paths", {}).values():
        for operation in path.values():
            if isinstance(operation, dict):
                operation["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi

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
app.include_router(fabric_router)      # /api/fabric/*
app.include_router(pcb_router)         # /api/pcb/*
app.include_router(welding_router)     # /api/welding/*
app.include_router(inspections_router) # /api/inspections  (legacy)
app.include_router(analytics_router)   # /api/analytics    (legacy)
app.include_router(reports_router)     # /api/reports      (legacy)
app.include_router(camera_router)
app.include_router(images_router)
app.include_router(report_detail_router)  # /api/report-detail/*


@app.on_event("startup")
def initialize_databases():
    from backend.auth import initialize_auth_database
    initialize_auth_database()
    from quality.database import create_database
    create_database()
    from metal.database import create_database as create_metal_database
    create_metal_database()
    from fabric.database import create_database as create_fabric_database
    create_fabric_database()
    from pcb.database import create_database as create_pcb_database
    create_pcb_database()
    from welding.database import create_database as create_welding_database
    create_welding_database()


@app.get("/health")
def health():
    from backend.services.material_registry import MATERIALS, get_model_status
    from metal.database import db_status as metal_db_status

    models = get_model_status()

    # Check database files exist
    db_files = {
        "database_steel":   MATERIALS["steel"]["db_path"].exists(),
        "database_metal":   MATERIALS["metal"]["db_path"].exists(),
        "database_fabric":  MATERIALS["fabric"]["db_path"].exists(),
        "database_pcb":     MATERIALS["pcb"]["db_path"].exists(),
        "database_welding": MATERIALS["welding"]["db_path"].exists(),
    }

    return {
        "status":           "online",
        "database_steel":   "online" if db_status() else "error",
        "database_metal":   "online" if metal_db_status() else "error",
        "database_fabric":  "online" if db_files["database_fabric"] else "error",
        "database_pcb":     "online" if db_files["database_pcb"] else "error",
        "database_welding": "online" if db_files["database_welding"] else "error",
        "models":           {mat: "ready" if ok else "not_found" for mat, ok in models.items()},
        # legacy keys
        "database":         "online" if db_status() else "error",
        "model":            "ready" if models.get("steel") else "not_found",
        "camera":           "connected" if camera_service.camera_connected else "disconnected",
        "camera_running":   camera_service._running,
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

    try:
        from fabric.database import create_database as fabric_create_db
        fabric_create_db()
    except Exception as e:
        print(f"Fabric DB init warning: {e}")

    try:
        from pcb.database import create_database as pcb_create_db
        pcb_create_db()
    except Exception as e:
        print(f"PCB DB init warning: {e}")

    try:
        from welding.database import create_database as welding_create_db
        welding_create_db()
    except Exception as e:
        print(f"Welding DB init warning: {e}")

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1,
    )
