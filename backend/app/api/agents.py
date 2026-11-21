from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.api.deps import get_db
from app.models.all_models import AgentExecution
from app.schemas.all_schemas import AgentExecutionResponse, AgentActivityStats

router = APIRouter(prefix="/agents", tags=["Agent Observability"])


@router.get("/executions", response_model=List[AgentExecutionResponse])
def get_agent_executions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    agent_name: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AgentExecution)
    if agent_name:
        query = query.filter(AgentExecution.agent_name == agent_name)
    if status:
        query = query.filter(AgentExecution.status == status)

    executions = query.order_by(desc(AgentExecution.created_at)).offset(skip).limit(limit).all()
    return executions


@router.get("/stats", response_model=AgentActivityStats)
def get_agent_stats(db: Session = Depends(get_db)):
    total = db.query(AgentExecution).count()
    if total == 0:
        return {
            "total_executions": 0,
            "active_agents": 8,
            "success_rate_percent": 100.0,
            "avg_latency_ms": 0.0,
            "total_tokens_consumed": 0,
            "recent_executions": []
        }

    successful = db.query(AgentExecution).filter(AgentExecution.status.in_(["completed", "fallback"])).count()
    success_rate = round((successful / total) * 100.0, 1)

    avg_lat = db.query(func.avg(AgentExecution.duration_ms)).scalar() or 0.0
    total_tokens = db.query(func.sum(AgentExecution.tokens_used)).scalar() or 0

    recent = db.query(AgentExecution).order_by(desc(AgentExecution.created_at)).limit(10).all()

    # Distinct active agents
    distinct_agents = db.query(AgentExecution.agent_name).distinct().count()

    return {
        "total_executions": total,
        "active_agents": max(8, distinct_agents),
        "success_rate_percent": success_rate,
        "avg_latency_ms": round(float(avg_lat), 1),
        "total_tokens_consumed": int(total_tokens),
        "recent_executions": recent
    }
