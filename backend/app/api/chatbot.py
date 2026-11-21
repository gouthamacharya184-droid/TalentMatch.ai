from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db, get_optional_current_user
from app.models.all_models import User, Job, Candidate, Resume, MatchingAnalysis
from app.schemas.all_schemas import ChatbotMessageRequest, ChatbotMessageResponse, ChatbotWelcomeResponse
from app.services.chatbot_service import ChatbotService

router = APIRouter(prefix="/chatbot", tags=["AI Copilot"])
chatbot_service = ChatbotService()


@router.post("/chat", response_model=ChatbotMessageResponse)
def chat_with_assistant(
    req: ChatbotMessageRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Recruiter Copilot Chat Endpoint.
    Connects to TalentMatch database and agent reasoning engine to assist recruiters.
    """
    clean_message = req.message.strip()
    if not clean_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if len(clean_message) > 2000:
        raise HTTPException(status_code=400, detail="Message exceeds maximum allowed length of 2000 characters")

    try:
        result = chatbot_service.chat(
            db=db,
            message=clean_message,
            conversation_id=req.conversation_id,
            job_id=req.job_id,
            candidate_id=req.candidate_id,
            page_context=req.page_context,
            user=current_user
        )
        return result
    except Exception as e:
        return ChatbotMessageResponse(
            assistant_message=f"I encountered a temporary service glitch ({str(e)}). Please try asking again in a moment.",
            conversation_id=req.conversation_id or "default-conv",
            relevant_data=None,
            suggestions=["How is the candidate score calculated?", "Show me the top-ranked candidates."],
            mode="fallback"
        )


@router.post("/clear/{conversation_id}")
def clear_conversation(conversation_id: str):
    """Clear in-memory session history for a conversation."""
    chatbot_service.clear_conversation(conversation_id)
    return {"status": "cleared", "conversation_id": conversation_id}


@router.get("/welcome", response_model=ChatbotWelcomeResponse)
def get_welcome_message(
    page_context: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Fetch personalized welcome greeting with live platform statistics."""
    from datetime import datetime, timezone

    total_jobs = db.query(Job).count()
    total_candidates = db.query(Candidate).count()
    total_resumes = db.query(Resume).count()
    avg_score = db.query(func.avg(MatchingAnalysis.overall_score)).scalar() or 0.0

    stats = {
        "total_jobs": total_jobs,
        "total_candidates": total_candidates,
        "total_resumes": total_resumes,
        "avg_score": round(float(avg_score), 1)
    }

    if page_context and "candidate" in page_context.lower():
        welcome_text = (
            f"Hello! Welcome to the Candidate Intelligence Centre. Currently tracking "
            f"**{total_candidates} candidate profiles** with an average score of **{stats['avg_score']}/100**."
        )
    else:
        welcome_text = (
            f"Hello! Welcome to **TalentMatch AI Recruiter Copilot**.\n\n"
            f"I have indexed **{total_candidates} candidate profiles** across **{total_jobs} active job openings** "
            f"with an average match score of **{stats['avg_score']}/100**.\n\n"
            "How can I assist your recruitment workflow today?"
        )

    return {
        "welcome_message": welcome_text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "dynamic",
        "stats": stats
    }


@router.get("/suggestions", response_model=List[str])
def get_suggestions():
    return [
        "How does AI resume matching work?",
        "How is the candidate score calculated?",
        "Show me the top-ranked candidates.",
        "Compare the top two candidates.",
        "What are the missing skills for a candidate?",
        "Explain the recruitment dashboard."
    ]
