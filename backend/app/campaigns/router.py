import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.core.responses import standard_response
from app.users.models import User
from app.campaigns.schemas import CampaignCreate, CampaignUpdate, CampaignOut, CampaignMemberCreate
from app.campaigns.repository import CampaignRepository
from app.campaigns.service import CampaignService

logger = logging.getLogger("socialpilot.campaigns.router")
router = APIRouter(prefix="/api/v1/campaigns", tags=["Campaigns & Content Strategy"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_campaign(
    payload: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new multi-platform marketing campaign."""
    from app.database.models import TeamMember
    member = db.query(TeamMember).filter(TeamMember.team_id == payload.team_id, TeamMember.user_id == current_user.id).first()
    if not member and (not current_user.role or current_user.role.name != "Administrator"):
        raise HTTPException(status_code=403, detail="Access denied to create campaigns in this workspace")

    campaign = CampaignRepository.create_campaign(db, payload)
    return standard_response(
        success=True,
        message="Campaign created successfully",
        data={"campaign_id": campaign.id, "name": campaign.name, "status": campaign.status},
        status_code=201
    )

@router.get("")
def list_campaigns(
    team_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all active and archived campaigns for a team workspace."""
    from app.database.models import TeamMember
    member = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id).first()
    if not member and (not current_user.role or current_user.role.name != "Administrator"):
        raise HTTPException(status_code=403, detail="Access denied to team workspace campaigns")

    campaigns = CampaignRepository.list_by_team(db, team_id)
    c_list = []
    for c in campaigns:
        c_list.append({
            "id": c.id,
            "team_id": c.team_id,
            "name": c.name,
            "description": c.description,
            "start_date": c.start_date.isoformat(),
            "end_date": c.end_date.isoformat(),
            "budget": c.budget,
            "status": c.status
        })

    return standard_response(
        success=True,
        message="Campaigns listed successfully",
        data={"campaigns": c_list}
    )

@router.get("/{id}")
def get_campaign_detail(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve detailed campaign metadata, post counts, and performance metrics."""
    campaign = CampaignRepository.get_by_id(db, id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    summary = CampaignService.get_campaign_summary(db, id)
    return standard_response(
        success=True,
        message="Campaign details retrieved",
        data=summary
    )

@router.put("/{id}")
def update_campaign(
    id: str,
    payload: CampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update campaign parameters, date boundaries, and budget allocations."""
    campaign = CampaignRepository.update_campaign(db, id, payload)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return standard_response(
        success=True,
        message="Campaign updated successfully",
        data={"campaign_id": campaign.id, "name": campaign.name, "status": campaign.status}
    )

@router.delete("/{id}")
def delete_campaign(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete campaign and unlink associated posts."""
    ok = CampaignRepository.delete_campaign(db, id)
    if not ok:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return standard_response(
        success=True,
        message="Campaign deleted successfully",
        data={"campaign_id": id}
    )

class AssignPostsReq(BaseModel):
    post_ids: List[str]

@router.post("/{id}/assign-posts")
def assign_posts_to_campaign(
    id: str,
    payload: AssignPostsReq,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate campaign and assign posts to campaign in DB."""
    from app.database.models import Campaign, Post, CampaignMember
    campaign = db.query(Campaign).filter(Campaign.id == id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    posts = db.query(Post).filter(Post.id.in_(payload.post_ids)).all()
    for p in posts:
        p.campaign_id = id
    
    member = db.query(CampaignMember).filter(
        CampaignMember.campaign_id == id,
        CampaignMember.user_id == current_user.id
    ).first()
    if not member:
        member = CampaignMember(
            campaign_id=id,
            user_id=current_user.id,
            role_in_campaign="manager"
        )
        db.add(member)
    
    db.commit()

    return standard_response(
        success=True,
        message=f"Successfully assigned {len(posts)} posts to campaign '{campaign.name}'",
        data={
            "campaign_id": id,
            "assigned_count": len(posts),
            "post_ids": payload.post_ids
        }
    )

@router.post("/{id}/members")
def add_campaign_member(
    id: str,
    payload: CampaignMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign team collaborator to campaign with specific campaign role."""
    member = CampaignRepository.add_member(db, campaign_id=id, user_id=payload.user_id, role_in_campaign=payload.role_in_campaign)
    return standard_response(
        success=True,
        message="Campaign member added successfully",
        data={"campaign_id": id, "user_id": member.user_id, "role": member.role_in_campaign}
    )
