from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_optional_current_user
from app.models.all_models import Job, MatchingAnalysis, User
from app.schemas.all_schemas import (
    DashboardStatsResponse,
    MatchingAnalysisResponse,
    PaginatedResponse,
)
from app.services.analytics_service import AnalyticsService
from app.services.report_service import ReportService

router = APIRouter(prefix="/analytics", tags=["Analytics & Reports"])
analytics_service = AnalyticsService()


@router.get("/dashboard", response_model=DashboardStatsResponse)
def get_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return analytics_service.get_dashboard_stats(db)


@router.get("/reports/{job_id}")
def get_reports(
    job_id: str,
    format: str | None = Query(None, pattern="^(csv|xlsx|pdf)$"),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    if format:
        return export_report(job_id=job_id, format=format, db=db, current_user=current_user)
    try:
        return analytics_service.get_job_report_data(db, job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/reports/{job_id}/export")
def export_report(
    job_id: str,
    format: str = Query("csv", pattern="^(csv|xlsx|pdf)$"),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    analyses = (
        db.query(MatchingAnalysis)
        .filter(MatchingAnalysis.job_id == job_id)
        .order_by(MatchingAnalysis.overall_score.desc())
        .all()
    )

    clean_title = "".join(c for c in job.title if c.isalnum() or c in (" ", "_", "-")).rstrip()

    if format == "csv":
        csv_stream = ReportService.export_csv(job, analyses)
        return StreamingResponse(
            iter([csv_stream.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="TalentMatch_{clean_title}_Rankings.csv"'},
        )
    elif format == "xlsx":
        excel_stream = ReportService.export_excel(job, analyses)
        return StreamingResponse(
            excel_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="TalentMatch_{clean_title}_Rankings.xlsx"'},
        )
    elif format == "pdf":
        pdf_stream = ReportService.export_pdf(job, analyses)
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="TalentMatch_{clean_title}_Rankings.pdf"'},
        )


@router.get("/history", response_model=PaginatedResponse[MatchingAnalysisResponse])
def get_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(MatchingAnalysis).order_by(MatchingAnalysis.created_at.desc())
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {"items": items, "total": total, "skip": skip, "limit": limit}
