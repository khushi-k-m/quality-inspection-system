from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Any
from pathlib import Path
from backend.dependencies import get_current_user
from backend.database import get_db

router = APIRouter(prefix="/api/reports", tags=["reports"])

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = ROOT_DIR / "output" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class CustomizeReportRequest(BaseModel):
    material: Optional[str] = None
    client_name: Optional[str] = None
    po_number: Optional[str] = None
    batch_id: Optional[str] = None
    facility: Optional[str] = None
    company_name: Optional[str] = None
    inspector: Optional[str] = None


@router.get("")
def list_reports(user=Depends(get_current_user)):
    conn = get_db()
    rows = conn.execute(
        """SELECT inspection_id, timestamp, status, quality_score
           FROM inspections ORDER BY id DESC"""
    ).fetchall()
    conn.close()

    result = []
    for row in rows:
        iid = row["inspection_id"]
        pdf_path = REPORTS_DIR / f"{iid}_inspection_report.pdf"

        result.append({
            "inspection_id": iid,
            "timestamp": row["timestamp"],
            "status": row["status"],
            "quality_score": row["quality_score"],
            "report_available": pdf_path.exists(),
        })

    return result


@router.get("/{inspection_id}/download")
def download_report(
    inspection_id: str,
    material: Optional[str] = None,
    client_name: Optional[str] = None,
    company_name: Optional[str] = None,
    po_number: Optional[str] = None,
    batch_id: Optional[str] = None,
    inspector: Optional[str] = None,
    user=Depends(get_current_user),
):
    pdf_path = REPORTS_DIR / f"{inspection_id}_inspection_report.pdf"

    customer_details = {}
    if client_name:
        customer_details["client_name"] = client_name
    if po_number:
        customer_details["po_number"] = po_number
    if batch_id:
        customer_details["batch_id"] = batch_id
    if inspector:
        customer_details["inspector"] = inspector

    company_details = {}
    if company_name:
        company_details["name"] = company_name

    try:
        from reports.enhanced_report import generate_enhanced_report

        result = generate_enhanced_report(
            inspection_id,
            material=material,
            customer_details=customer_details if customer_details else None,
            company_details=company_details if company_details else None,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Report could not be generated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"{inspection_id}_inspection_report.pdf",
    )


@router.post("/{inspection_id}/generate")
def generate_custom_report(
    inspection_id: str,
    body: CustomizeReportRequest,
    user=Depends(get_current_user),
):
    """Generate or refresh 2-page report with custom customer and company metadata."""
    customer_details = {k: v for k, v in {
        "client_name": body.client_name,
        "po_number": body.po_number,
        "batch_id": body.batch_id,
        "facility": body.facility,
        "inspector": body.inspector,
    }.items() if v}

    company_details = {}
    if body.company_name:
        company_details["name"] = body.company_name

    try:
        from reports.enhanced_report import generate_enhanced_report
        pdf_path = generate_enhanced_report(
            inspection_id,
            material=body.material,
            customer_details=customer_details if customer_details else None,
            company_details=company_details if company_details else None,
        )
        return {
            "success": True,
            "inspection_id": inspection_id,
            "pdf_path": pdf_path,
            "download_url": f"/api/reports/{inspection_id}/download",
            "thermal_sheet_url": f"/api/reports/{inspection_id}/thermal-sheet",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {e}")


@router.get("/{inspection_id}/thermal-sheet")
def get_thermal_sheet(inspection_id: str, user=Depends(get_current_user)):
    """Return the false-color thermal sheet JPEG image for the inspection."""
    thermal_path = REPORTS_DIR / f"{inspection_id}_thermal_sheet.jpg"
    if not thermal_path.exists():
        # Try generating it
        try:
            from reports.enhanced_report import generate_enhanced_report
            generate_enhanced_report(inspection_id)
        except Exception:
            pass

    if not thermal_path.exists():
        raise HTTPException(status_code=404, detail="Thermal sheet not found")

    return FileResponse(
        path=str(thermal_path),
        media_type="image/jpeg",
        filename=f"{inspection_id}_thermal_sheet.jpg",
    )