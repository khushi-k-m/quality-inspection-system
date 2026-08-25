from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from backend.dependencies import get_current_user
from backend.database import get_db

router = APIRouter(prefix="/api/reports", tags=["reports"])

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = ROOT_DIR / "output" / "reports"


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
            "report_available": pdf_path.exists()
        })
    return result


@router.get("/{inspection_id}/download")
def download_report(inspection_id: str, user=Depends(get_current_user)):
    pdf_path = REPORTS_DIR / f"{inspection_id}_inspection_report.pdf"

    if not pdf_path.exists():
        # Try to generate it on demand
        try:
            import sys
            sys.path.insert(0, str(ROOT_DIR))
            from reports.generate_report import generate_report
            result = generate_report(inspection_id)
            if result is None:
                raise HTTPException(status_code=404, detail="Report could not be generated")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"{inspection_id}_inspection_report.pdf"
    )
