from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_active_user, get_db
from app.database.models import User
from app.database.repositories import TeamRepository, CampaignRepository
from app.database.schemas import CampaignCreate, CampaignUpdate, CampaignOut

router = APIRouter(prefix="/campaigns", tags=["Campaign Management"])

@router.post("", response_model=CampaignOut)
def create_campaign(
    payload: CampaignCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # 1. Enforce team membership
    member = TeamRepository.get_member(db, team_id=payload.team_id, user_id=current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to team workspace"
        )
        
    # 2. Timeline validation
    if payload.end_date < payload.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign end date cannot be earlier than its start date"
        )

    campaign = CampaignRepository.create_campaign(db, campaign_data=payload)
    return campaign

@router.get("", response_model=List[CampaignOut])
def list_campaigns(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Enforce team access
    member = TeamRepository.get_member(db, team_id=team_id, user_id=current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to team workspace"
        )
        
    return CampaignRepository.get_by_team(db, team_id=team_id)

@router.get("/{id}", response_model=CampaignOut)
def get_campaign_details(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    campaign = CampaignRepository.get_by_id(db, campaign_id=id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
        
    member = TeamRepository.get_member(db, team_id=campaign.team_id, user_id=current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to campaign workspace"
        )
        
    return campaign

@router.put("/{id}", response_model=CampaignOut)
def update_campaign(
    id: str,
    payload: CampaignUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    campaign = CampaignRepository.get_by_id(db, campaign_id=id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
        
    member = TeamRepository.get_member(db, team_id=campaign.team_id, user_id=current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to campaign workspace"
        )

    # Date ordering validation if changing dates
    start = payload.start_date or campaign.start_date
    end = payload.end_date or campaign.end_date
    if end < start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign end date cannot be earlier than its start date"
        )

    updated = CampaignRepository.update_campaign(db, campaign_id=id, updates=payload)
    return updated

@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_campaign(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    campaign = CampaignRepository.get_by_id(db, campaign_id=id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
        
    member = TeamRepository.get_member(db, team_id=campaign.team_id, user_id=current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to campaign workspace"
        )

    CampaignRepository.delete_campaign(db, campaign_id=id)
    return {"detail": "Campaign deleted successfully and posts unlinked"}
