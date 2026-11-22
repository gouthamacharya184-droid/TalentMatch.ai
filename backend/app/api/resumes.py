import os
import uuid
import shutil
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.api.deps import get_db, get_optional_current_user
from app.models.all_models import User
from app.schemas.all_schemas import ResumeResponse, PaginatedResponse
from app.services.resume_service import ResumeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resumes", tags=["Resumes"])
resume_service = ResumeService()


@router.post("/upload", response_model=List[ResumeResponse])
async def upload_resumes(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Simultaneously upload 1 to 50 candidate resumes (.PDF, .DOCX, .TXT).
    Enforces per-file validation, size limits (15MB), duplicate detection,
    and completely isolated per-file error boundaries.
    """
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided for upload.")

    if len(files) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 resumes allowed per batch.")

    user_id = current_user.id if current_user else None
    results: List[ResumeResponse] = []
    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    for file in files:
        filename = file.filename or "unknown_resume"
        ext = os.path.splitext(filename)[1].lower()

        # 1. File Type Validation
        if ext not in settings.ALLOWED_EXTENSIONS:
            failed_resume = resume_service.create_failed_resume(
                db=db,
                original_filename=filename,
                stored_filename=f"invalid_{uuid.uuid4()}{ext}",
                file_size=0,
                error_msg=f"Unsupported format '{ext}'. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}",
                user_id=user_id
            )
            results.append(failed_resume)
            continue

        try:
            # 2. Save File & Check Content / Size
            stored_name, path, size, save_err = await resume_service.save_uploaded_file(file)

            if save_err:
                failed_resume = resume_service.create_failed_resume(
                    db=db,
                    original_filename=filename,
                    stored_filename=stored_name,
                    file_size=size,
                    error_msg=save_err,
                    user_id=user_id
                )
                results.append(failed_resume)
                continue

            if size > max_size_bytes:
                # Clean up oversized file
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception:
                    pass
                failed_resume = resume_service.create_failed_resume(
                    db=db,
                    original_filename=filename,
                    stored_filename=stored_name,
                    file_size=size,
                    error_msg=f"File exceeds maximum allowed size ({settings.MAX_FILE_SIZE_MB}MB).",
                    user_id=user_id
                )
                results.append(failed_resume)
                continue

            # 3. Duplicate Detection Check against already completed resumes
            existing_dup = resume_service.check_duplicate(db, original_filename=filename, file_size=size)
            if existing_dup:
                results.append(ResumeResponse.model_validate(existing_dup))
                continue

            # 4. Safe Atomic Process Resume
            resume_res = resume_service.process_resume_file(
                db=db,
                file_path=path,
                original_filename=filename,
                stored_filename=stored_name,
                file_size=size,
                user_id=user_id
            )
            results.append(resume_res)

        except Exception as e:
            # Complete isolation guarantee: rollback db session and cleanly return failure for this file
            db.rollback()
            logger.error(f"Unexpected error processing {filename}: {e}", exc_info=True)
            failed_resume = resume_service.create_failed_resume(
                db=db,
                original_filename=filename,
                stored_filename=f"error_{uuid.uuid4()}",
                file_size=0,
                error_msg=f"Upload processing error: {str(e)}",
                user_id=user_id
            )
            results.append(failed_resume)

    return results


@router.post("/load-sample-batch", response_model=List[ResumeResponse])
def load_sample_batch(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Load and parse the 15 pre-generated demo candidate resumes (.PDF and .DOCX).
    Prevents duplicate creation when demo resumes are already loaded.
    """
    user_id = current_user.id if current_user else None
    sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../sample_resumes"))
    if not os.path.exists(sample_dir):
        raise HTTPException(status_code=404, detail="Sample resumes directory not found.")

    files = [f for f in os.listdir(sample_dir) if f.lower().endswith(('.pdf', '.docx', '.txt'))]
    results: List[ResumeResponse] = []

    for fname in sorted(files):
        try:
            src_path = os.path.join(sample_dir, fname)
            size = os.path.getsize(src_path)

            # Prevent duplicate demo insertion
            existing = resume_service.check_duplicate(db, original_filename=fname, file_size=size)
            if existing:
                results.append(ResumeResponse.model_validate(existing))
                continue

            ext = os.path.splitext(fname)[1]
            unique_name = f"demo_{uuid.uuid4()}{ext}"
            dst_path = os.path.join(settings.UPLOAD_DIR, unique_name)
            shutil.copyfile(src_path, dst_path)

            resume = resume_service.process_resume_file(
                db=db,
                file_path=dst_path,
                original_filename=fname,
                stored_filename=unique_name,
                file_size=size,
                user_id=user_id
            )
            results.append(resume)
        except Exception as e:
            db.rollback()
            logger.error(f"Error loading demo resume {fname}: {e}")
            failed = resume_service.create_failed_resume(
                db=db,
                original_filename=fname,
                stored_filename=f"demo_error_{uuid.uuid4()}",
                file_size=0,
                error_msg=f"Failed to load demo resume: {str(e)}",
                user_id=user_id
            )
            results.append(failed)

    return results


@router.get("", response_model=PaginatedResponse[ResumeResponse])
def get_resumes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    resumes, total = resume_service.get_resumes(db, skip=skip, limit=limit, status=status)
    return {
        "items": [ResumeResponse.model_validate(r) for r in resumes],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{resume_id}/status", response_model=ResumeResponse)
def get_resume_status(resume_id: str, db: Session = Depends(get_db)):
    resume = resume_service.get_resume(db, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return ResumeResponse.model_validate(resume)


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(resume_id: str, db: Session = Depends(get_db)):
    """Retrieve full resume details including raw text."""
    resume = resume_service.get_resume(db, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return ResumeResponse.model_validate(resume)



@router.get("/{resume_id}/download")
def download_resume(resume_id: str, db: Session = Depends(get_db)):
    resume = resume_service.get_resume(db, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume record not found")

    # If file is stored in Vercel Blob or external cloud storage
    if resume.file_path and (resume.file_path.startswith("http://") or resume.file_path.startswith("https://")):
        return RedirectResponse(url=resume.file_path, status_code=307)

    if not resume.file_path or not os.path.exists(resume.file_path):
        raise HTTPException(status_code=404, detail="Resume file not found on server")

    # Path traversal defense: ensure file is within sanctioned upload or sample directories
    real_path = os.path.realpath(resume.file_path)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    allowed_roots = [
        os.path.realpath(settings.UPLOAD_DIR),
        os.path.realpath(os.path.join(base_dir, "sample_resumes")),
        os.path.realpath(os.path.join(base_dir, "test_resumes_50")),
        os.path.realpath(os.path.join(base_dir, "test_resumes_edge_cases")),
    ]
    if not any(real_path.startswith(root) for root in allowed_roots):
        raise HTTPException(status_code=403, detail="Access denied: file path is outside authorized storage directory.")

    return FileResponse(
        path=resume.file_path,
        filename=resume.original_filename,
        media_type="application/octet-stream"
    )


@router.get("/{resume_id}/view")
def view_resume(resume_id: str, db: Session = Depends(get_db)):
    """
    Stream resume directly for inline browser viewing (PDF/text).
    """
    resume = resume_service.get_resume(db, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume record not found")

    # If file is stored in Vercel Blob or external cloud storage
    if resume.file_path and (resume.file_path.startswith("http://") or resume.file_path.startswith("https://")):
        return RedirectResponse(url=resume.file_path, status_code=307)

    if not resume.file_path or not os.path.exists(resume.file_path):
        raise HTTPException(status_code=404, detail="Resume file not found on server")

    real_path = os.path.realpath(resume.file_path)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    allowed_roots = [
        os.path.realpath(settings.UPLOAD_DIR),
        os.path.realpath(os.path.join(base_dir, "sample_resumes")),
        os.path.realpath(os.path.join(base_dir, "test_resumes_50")),
        os.path.realpath(os.path.join(base_dir, "test_resumes_edge_cases")),
    ]
    if not any(real_path.startswith(root) for root in allowed_roots):
        raise HTTPException(status_code=403, detail="Access denied: file path is outside authorized storage directory.")

    ext = os.path.splitext(resume.file_path)[1].lower()
    media_type = "application/pdf" if ext == ".pdf" else "text/plain; charset=utf-8" if ext == ".txt" else "application/octet-stream"

    return FileResponse(
        path=resume.file_path,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{resume.original_filename}"'}
    )



@router.delete("/{resume_id}")
def delete_resume(resume_id: str, db: Session = Depends(get_db)):
    resume = resume_service.get_resume(db, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if resume.file_path and (resume.file_path.startswith("http://") or resume.file_path.startswith("https://")):
        resume_service.delete_blob_file(resume.file_path)
    elif resume.file_path and os.path.exists(resume.file_path):
        real_path = os.path.realpath(resume.file_path)
        upload_root = os.path.realpath(settings.UPLOAD_DIR)
        # Prevent deletion outside upload directory
        if real_path.startswith(upload_root):
            try:
                os.remove(real_path)
            except Exception:
                pass

    db.delete(resume)
    db.commit()
    return {"message": "Resume deleted successfully"}
