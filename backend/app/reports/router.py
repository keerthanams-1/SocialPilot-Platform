import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.core.responses import standard_response
from app.users.models import User
from app.reports.scheduler import ReportSchedulerEngine
from app.reports.pdf_generator import PDFReportGenerator
from app.reports.csv_exporter import CSVReportExporter
from app.reports.excel_exporter import ExcelReportExporter

logger = logging.getLogger("socialpilot.reports.router")
router = APIRouter(prefix="/api/v1/reports", tags=["Executive Reports & Data Exporters"])

@router.post("/generate")
def generate_report_endpoint(
    title: str,
    report_type: str = "analytics",
    format: str = "pdf",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate executive report on demand in PDF, CSV, or Excel format."""
    team_id = current_user.team_memberships[0].team_id if current_user.team_memberships else "demo_team"
    report = ReportSchedulerEngine.generate_report(db, team_id, current_user.id, title, report_type, format)

    return standard_response(
        success=True,
        message=f"Report generated successfully in {format.upper()} format",
        data={
            "report_id": report.id,
            "title": report.title,
            "report_type": report.report_type,
            "format": report.format,
            "file_url": report.file_url,
            "status": report.status
        }
    )

@router.get("")
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all generated reports for the current user."""
    from app.database.models import Report
    reports = db.query(Report).filter(Report.user_id == current_user.id).order_by(Report.created_at.desc()).all()
    r_list = []
    for r in reports:
        r_list.append({
            "id": r.id,
            "title": r.title,
            "report_type": r.report_type,
            "format": r.format,
            "file_url": r.file_url,
            "status": r.status,
            "generated_at": r.generated_at.isoformat()
        })

    return standard_response(
        success=True,
        message="Reports listed successfully",
        data={"reports": r_list}
    )

@router.get("/{id}")
def download_report(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download report file stream."""
    from app.database.models import Report
    report = db.query(Report).filter(Report.id == id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    sample_data = {"impressions": 165000, "reach": 98000, "engagements": 15400, "campaign_roi": 340.0, "ctr": 3.4}

    if report.format == "csv":
        csv_str = CSVReportExporter.export_posts_csv([sample_data])
        return Response(content=csv_str, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=report_{id}.csv"})
    elif report.format == "xlsx":
        xlsx_bytes = ExcelReportExporter.export_excel_workbook(report.title, [sample_data])
        return Response(content=xlsx_bytes, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename=report_{id}.xlsx"})
    else:
        pdf_bytes = PDFReportGenerator.generate_pdf(report.title, sample_data)
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=report_{id}.pdf"})

@router.post("/schedule")
def schedule_report_endpoint(
    report_type: str,
    frequency: str,
    recipient_email: str,
    format: str = "pdf",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Schedule recurring report dispatches (Daily, Weekly, Monthly, Quarterly, Yearly)."""
    team_id = current_user.team_memberships[0].team_id if current_user.team_memberships else "demo_team"
    sched = ReportSchedulerEngine.schedule_report(db, team_id, current_user.id, report_type, frequency, recipient_email, format)

    return standard_response(
        success=True,
        message=f"Recurring {frequency} report scheduled",
        data={
            "schedule_id": sched.id,
            "frequency": sched.frequency,
            "recipient_email": sched.recipient_email,
            "next_run_at": sched.next_run_at.isoformat()
        }
    )

@router.delete("/{id}")
def delete_report(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a report entry."""
    from app.database.models import Report
    report = db.query(Report).filter(Report.id == id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    db.delete(report)
    db.commit()
    return standard_response(
        success=True,
        message="Report deleted successfully",
        data={"report_id": id}
    )
