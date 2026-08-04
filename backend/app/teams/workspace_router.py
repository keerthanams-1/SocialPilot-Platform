import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.core.responses import standard_response
from app.database.models import User, Team, TeamMember, WorkspaceInvitation, Role

router = APIRouter(prefix="/api/v1/workspace", tags=["Workspace Management & Member Invitations"])

class InviteReq(BaseModel):
    team_id: str
    email: EmailStr
    role_name: str = "Marketing Team"

class UpdateMemberRoleReq(BaseModel):
    role_name: str

@router.post("/invite")
def invite_workspace_member(
    req: InviteReq,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Invite a user to the workspace.
    If the email exists in DB: Add user to workspace immediately or send direct invitation.
    If email does not exist: Create a pending WorkspaceInvitation with a secure token.
    No 'User not found' error is thrown.
    """
    team = db.query(Team).filter(Team.id == req.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Workspace team not found.")

    # Search existing user by email
    target_user = db.query(User).filter(User.email == req.email).first()

    if target_user:
        # Check if already a member
        existing_member = db.query(TeamMember).filter(
            TeamMember.team_id == req.team_id,
            TeamMember.user_id == target_user.id
        ).first()

        if existing_member:
            raise HTTPException(status_code=400, detail=f"{req.email} is already a member of this workspace.")

        # Create active workspace membership
        new_member = TeamMember(
            team_id=req.team_id,
            user_id=target_user.id,
            role_in_team=req.role_name
        )
        db.add(new_member)
        db.commit()

        return standard_response(
            success=True,
            message="Invitation Sent Successfully. Member added to workspace.",
            data={
                "member_id": new_member.user_id,
                "email": target_user.email,
                "role": req.role_name,
                "status": "active"
            }
        )

    # Email does NOT exist -> Create pending invitation token
    existing_invitation = db.query(WorkspaceInvitation).filter(
        WorkspaceInvitation.team_id == req.team_id,
        WorkspaceInvitation.email == req.email,
        WorkspaceInvitation.status == "pending"
    ).first()

    if existing_invitation:
        return standard_response(
            success=True,
            message="Invitation email already pending for this address.",
            data={
                "invitation_id": existing_invitation.id,
                "email": req.email,
                "token": existing_invitation.token,
                "status": "pending"
            }
        )

    invitation_token = f"inv_{uuid.uuid4().hex}"
    expires_at = datetime.utcnow() + timedelta(days=7)

    invitation = WorkspaceInvitation(
        team_id=req.team_id,
        email=req.email,
        role_name=req.role_name,
        token=invitation_token,
        status="pending",
        expires_at=expires_at
    )
    db.add(invitation)
    db.commit()

    return standard_response(
        success=True,
        message="Invitation Sent Successfully. Pending registration token generated.",
        data={
            "invitation_id": invitation.id,
            "email": req.email,
            "role": req.role_name,
            "status": "pending",
            "token": invitation_token
        }
    )

@router.get("/members")
def list_workspace_members(
    team_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all workspace active members and pending invitations."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Workspace team not found.")

    members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    invitations = db.query(WorkspaceInvitation).filter(
        WorkspaceInvitation.team_id == team_id,
        WorkspaceInvitation.status == "pending"
    ).all()

    member_list = []
    for m in members:
        user = m.user
        member_list.append({
            "id": m.user_id,
            "user_id": m.user_id,
            "name": user.name if user else "Workspace Member",
            "email": user.email if user else "",
            "role": m.role_in_team,
            "status": "active",
            "joined_at": m.joined_at.isoformat() if m.joined_at else None
        })

    for inv in invitations:
        member_list.append({
            "id": inv.id,
            "user_id": None,
            "name": inv.email.split("@")[0].capitalize(),
            "email": inv.email,
            "role": inv.role_name,
            "status": "pending",
            "joined_at": inv.created_at.isoformat() if inv.created_at else None,
            "token": inv.token
        })

    return standard_response(
        success=True,
        message="Workspace members and invitations retrieved",
        data={"members": member_list}
    )

@router.put("/member/{id}")
def update_workspace_member_role(
    id: str,
    req: UpdateMemberRoleReq,
    team_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update role for an active member or pending invitation."""
    # Check if active team member
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == id
    ).first()

    if member:
        member.role_in_team = req.role_name
        db.commit()
        return standard_response(
            success=True,
            message="Workspace member role updated successfully",
            data={"user_id": id, "role": req.role_name}
        )

    # Check if pending invitation
    invitation = db.query(WorkspaceInvitation).filter(
        WorkspaceInvitation.id == id
    ).first()

    if invitation:
        invitation.role_name = req.role_name
        db.commit()
        return standard_response(
            success=True,
            message="Pending invitation role updated successfully",
            data={"invitation_id": id, "role": req.role_name}
        )

    raise HTTPException(status_code=404, detail="Workspace member or invitation record not found.")

@router.delete("/member/{id}")
def remove_workspace_member(
    id: str,
    team_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove member from workspace or cancel pending invitation."""
    # Check active member
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == id
    ).first()

    if member:
        db.delete(member)
        db.commit()
        return standard_response(
            success=True,
            message="Member removed from workspace",
            data={"user_id": id}
        )

    # Check pending invitation
    invitation = db.query(WorkspaceInvitation).filter(
        WorkspaceInvitation.id == id
    ).first()

    if invitation:
        invitation.status = "cancelled"
        db.delete(invitation)
        db.commit()
        return standard_response(
            success=True,
            message="Pending invitation cancelled",
            data={"invitation_id": id}
        )

    raise HTTPException(status_code=404, detail="Workspace member or invitation not found.")
