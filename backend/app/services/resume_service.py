import os
import uuid
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.all_models import Candidate, CandidateSkill, Resume, EvidenceReference, utc_now
from app.schemas.all_schemas import ResumeResponse
from app.parsers.pdf_parser import extract_text_from_pdf
from app.parsers.docx_parser import extract_text_from_docx
from app.ai_engine.agents.resume_agent import ResumeIntelligenceAgent
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class ResumeService:
    def __init__(self):
        self.resume_agent = ResumeIntelligenceAgent()

    async def save_uploaded_file(self, upload_file: UploadFile) -> Tuple[str, str, int, Optional[str]]:
        """Save file to storage and return (stored_filename, file_path, file_size, error_msg)."""
        filename = upload_file.filename or "unknown_file"
        ext = os.path.splitext(filename)[1].lower()
        unique_name = f"{uuid.uuid4()}{ext}"
        target_path = os.path.join(settings.UPLOAD_DIR, unique_name)

        try:
            content = await upload_file.read()
            file_size = len(content)

            if file_size == 0:
                return unique_name, target_path, 0, "File is empty (0 bytes)."

            # Magic bytes validation for PDF / DOCX
            if ext == ".pdf":
                if not content.startswith(b"%PDF-"):
                    if content.startswith(b"MZ"):
                        return unique_name, target_path, file_size, "Invalid file content: Executable binary detected instead of PDF."
            elif ext in [".docx", ".doc"]:
                if ext == ".docx" and not content.startswith(b"PK\x03\x04"):
                    return unique_name, target_path, file_size, "Corrupted DOCX: Invalid zip container header."

            with open(target_path, "wb") as f:
                f.write(content)

            return unique_name, target_path, file_size, None
        except Exception as e:
            return unique_name, target_path, 0, f"Failed to save file: {str(e)}"

    def compute_file_hash(self, file_path: str) -> Optional[str]:
        """Compute SHA-256 hash of file on disk."""
        try:
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return None

    def check_duplicate(self, db: Session, original_filename: str, file_size: int, content_hash: Optional[str] = None) -> Optional[Resume]:
        """Check whether an identical resume already exists via hash or filename+size."""
        try:
            if content_hash:
                dup = db.query(Resume).filter(
                    Resume.content_hash == content_hash,
                    Resume.processing_status == "completed"
                ).first()
                if dup:
                    return dup

            return db.query(Resume).filter(
                Resume.original_filename == original_filename,
                Resume.file_size == file_size,
                Resume.processing_status == "completed"
            ).first()
        except Exception as e:
            logger.warning(f"Error checking duplicate for {original_filename}: {e}")
            db.rollback()
            return None

    def create_failed_resume(
        self,
        db: Session,
        original_filename: str,
        stored_filename: str,
        file_size: int,
        error_msg: str,
        user_id: Optional[str] = None
    ) -> ResumeResponse:
        """Create a structured failed response without polluting candidate table."""
        ext = os.path.splitext(original_filename)[1].lower().replace(".", "")
        return ResumeResponse(
            id=str(uuid.uuid4()),
            candidate_id=None,
            original_filename=original_filename,
            filename=original_filename,
            stored_filename=stored_filename,
            file_type=ext or "unknown",
            file_size=file_size,
            processing_status="failed",
            status="failed",
            error_message=error_msg,
            message=error_msg,
            created_at=utc_now()
        )

    def process_resume_file(
        self,
        db: Session,
        file_path: str,
        original_filename: str,
        stored_filename: str,
        file_size: int,
        user_id: Optional[str] = None
    ) -> ResumeResponse:
        """
        Process single uploaded resume using ResumeIntelligenceAgent:
        Extract text -> parse profile & page citations -> atomic Candidate, Skills, Resume & EvidenceReference creation.
        """
        ext = os.path.splitext(original_filename)[1].lower().replace(".", "")
        content_hash = self.compute_file_hash(file_path)

        # 1. Extract text and page decomposition before database transaction
        extracted_text = ""
        page_texts: Dict[str, str] = {}
        page_count = 1
        error_msg = None

        if ext == "pdf":
            pdf_res = extract_text_from_pdf(file_path)
            extracted_text = pdf_res.get("text", "")
            error_msg = pdf_res.get("error")
            page_count = pdf_res.get("page_count", 1)
            # Simple per-page estimation if not granular
            pages_list = extracted_text.split("\f") if "\f" in extracted_text else [extracted_text]
            page_texts = {str(i + 1): p for i, p in enumerate(pages_list) if p.strip()}
            if not page_texts:
                page_texts = {"1": extracted_text}
        elif ext in ["docx", "doc"]:
            docx_res = extract_text_from_docx(file_path)
            extracted_text = docx_res.get("text", "")
            error_msg = docx_res.get("error")
            page_texts = {"1": extracted_text}
        elif ext == "txt":
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    extracted_text = f.read()
                if not extracted_text.strip():
                    error_msg = "Text file is empty or contains only whitespace."
                page_texts = {"1": extracted_text}
            except Exception as e:
                error_msg = f"Failed to read text file: {str(e)}"
        else:
            error_msg = f"Unsupported file format: .{ext}"

        if error_msg or not extracted_text.strip():
            return self.create_failed_resume(
                db=db,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_size=file_size,
                error_msg=error_msg or "Empty document without readable text.",
                user_id=user_id
            )

        # 2. Invoke ResumeIntelligenceAgent
        try:
            profile = self.resume_agent.execute(
                raw_text=extracted_text,
                page_texts=page_texts,
                filename=original_filename,
                file_size=file_size,
                content_hash=content_hash,
                db=db
            )
        except Exception as e:
            logger.error(f"Error in ResumeIntelligenceAgent for {original_filename}: {e}")
            return self.create_failed_resume(
                db=db,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_size=file_size,
                error_msg=f"Resume Agent parsing failed: {str(e)}",
                user_id=user_id
            )

        # 3. Atomic Database Transaction: Candidate + Skills + Projects + Resume + Evidence
        try:
            cand_name = profile.get("name")
            if not cand_name or cand_name.lower() == "candidate":
                clean_name = os.path.splitext(original_filename)[0].replace("_", " ").replace("-", " ").title()
                cand_name = clean_name

            candidate = Candidate(
                user_id=user_id,
                name=cand_name,
                email=profile.get("email"),
                phone=profile.get("phone"),
                location=profile.get("location") or "Not specified",
                education=profile.get("education"),
                total_experience_years=float(profile.get("total_experience_years", 0.0)),
                projects=profile.get("projects", []),
                certifications=profile.get("certifications", []),
                extracted_profile=profile,
                status="new"
            )
            db.add(candidate)
            db.flush()  # assign candidate.id

            # Add skills and create evidence references
            for s in profile.get("skills", []):
                skill_name = s.get("skill_name", "")
                if not skill_name:
                    continue
                
                evidence_type = s.get("evidence_type", "explicit")
                skill_obj = CandidateSkill(
                    candidate_id=candidate.id,
                    skill_name=skill_name,
                    proficiency_level=s.get("proficiency_level", "intermediate"),
                    source="extracted",
                    evidence_type=evidence_type
                )
                db.add(skill_obj)

                # Persist traceable EvidenceReference
                ev_ref = EvidenceReference(
                    candidate_id=candidate.id,
                    criterion=skill_name,
                    criterion_type="skill",
                    snippet=s.get("snippet", f"Identified {skill_name} in candidate profile."),
                    page_number=s.get("source_page", 1),
                    confidence=1.0 if evidence_type in ["explicit", "professional"] else 0.85,
                    evidence_classification=evidence_type
                )
                db.add(ev_ref)

            # Also create evidence references for projects
            for p in profile.get("projects", []):
                if p.get("title"):
                    ev_proj = EvidenceReference(
                        candidate_id=candidate.id,
                        criterion=p["title"],
                        criterion_type="project",
                        snippet=p.get("description", p["title"])[:250],
                        page_number=p.get("source_page", 1),
                        confidence=0.95,
                        evidence_classification="project"
                    )
                    db.add(ev_proj)

            # Create Resume record
            resume = Resume(
                candidate_id=candidate.id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=file_path,
                file_type=ext,
                file_size=file_size,
                page_count=profile.get("page_count", page_count),
                content_hash=content_hash,
                raw_text=extracted_text,
                page_texts=page_texts,
                processing_status="completed",
                error_message=None
            )
            db.add(resume)

            # Single atomic commit
            db.commit()
            db.refresh(resume)

            try:
                NotificationService.log_activity(
                    db=db,
                    action="PARSE_RESUME",
                    entity_type="candidate",
                    entity_id=candidate.id,
                    user_id=user_id,
                    details={"candidate_name": candidate.name, "skills_count": len(profile.get("skills", []))}
                )
            except Exception as log_err:
                logger.warning(f"Failed to log activity: {log_err}")

            return ResumeResponse.model_validate(resume)

        except Exception as e:
            db.rollback()
            logger.error(f"Database error saving resume {original_filename}: {e}", exc_info=True)
            return self.create_failed_resume(
                db=db,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_size=file_size,
                error_msg=f"Database persistence error: {str(e)}",
                user_id=user_id
            )

    def get_resume(self, db: Session, resume_id: str) -> Optional[Resume]:
        return db.query(Resume).filter(Resume.id == resume_id).first()

    def get_resumes(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None
    ) -> tuple:
        query = db.query(Resume)
        if status:
            query = query.filter(Resume.processing_status == status)
        total = query.count()
        resumes = query.order_by(Resume.created_at.desc()).offset(skip).limit(limit).all()
        return resumes, total
