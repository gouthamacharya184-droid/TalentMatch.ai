from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db, get_current_user, get_optional_current_user
from app.models.all_models import Campaign, Job, Candidate, MatchingAnalysis, User, generate_uuid, utc_now
from app.schemas.all_schemas import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    PaginatedResponse
)

router = APIRouter(prefix="/campaigns", tags=["Recruitment Campaigns"])


@router.get("", response_model=PaginatedResponse[CampaignResponse])
def get_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Campaign)
    if status:
        query = query.filter(Campaign.status == status)
    if search:
        query = query.filter(Campaign.name.ilike(f"%{search}%") | Campaign.department.ilike(f"%{search}%"))

    total = query.count()
    campaigns = query.order_by(Campaign.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "items": campaigns,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("", response_model=CampaignResponse)
def create_campaign(
    camp_in: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    user_id = current_user.id if current_user else None
    campaign = Campaign(
        id=generate_uuid(),
        user_id=user_id,
        name=camp_in.name,
        department=camp_in.department,
        description=camp_in.description,
        target_hires=camp_in.target_hires,
        status=camp_in.status,
        target_date=camp_in.target_date,
        settings=camp_in.settings,
        created_at=utc_now()
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: str,
    camp_in: CampaignUpdate,
    db: Session = Depends(get_db)
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    update_data = camp_in.model_dump(exclude_unset=True) if hasattr(camp_in, "model_dump") else camp_in.dict(exclude_unset=True)
    for field, val in update_data.items():
        setattr(campaign, field, val)

    campaign.updated_at = utc_now()
    db.commit()
    db.refresh(campaign)
    return campaign


@router.delete("/{campaign_id}")
def delete_campaign(campaign_id: str, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    db.delete(campaign)
    db.commit()
    return {"message": "Campaign deleted successfully"}
