from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_active_user, get_db
from app.database.models import User, Team, TeamMember
from app.database.repositories import TeamRepository, UserRepository
from app.database.schemas import TeamOut, TeamCreate, TeamMemberAdd, TeamMemberOut

router = APIRouter(prefix="/teams", tags=["Team Management"])

@router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    team_in: TeamCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    team = TeamRepository.create_team(db, team_in=team_in, owner_id=current_user.id)
    return team

@router.post("/{id}/members", response_model=TeamMemberOut, status_code=status.HTTP_201_CREATED)
def add_team_member(
    id: str,
    member_in: TeamMemberAdd,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # 1. Fetch team
    team = TeamRepository.get_team_by_id(db, team_id=id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
        
    # 2. Check if current user is owner of the team
    if team.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team owner can add members"
        )
        
    # 3. Resolve user to invite by email
    invitee = UserRepository.get_by_email(db, email=member_in.email)
    if not invitee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist"
        )
        
    # 4. Check if user is already a member of the team
    existing_membership = TeamRepository.get_member(db, team_id=id, user_id=invitee.id)
    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this team"
        )
        
    # 5. Add user to the team
    membership = TeamRepository.add_member(
        db,
        team_id=id,
        user_id=invitee.id,
        role_in_team=member_in.role_in_team
    )
    
    # Return mapping
    return {
        "user_id": invitee.id,
        "name": invitee.name,
        "email": invitee.email,
        "role_in_team": membership.role_in_team,
        "joined_at": membership.joined_at
    }

@router.delete("/{id}/members/{user_id}", status_code=status.HTTP_200_OK)
def remove_team_member(
    id: str,
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # 1. Fetch team
    team = TeamRepository.get_team_by_id(db, team_id=id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
        
    # 2. Safety check: Owner cannot be removed from their own team
    if team.owner_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The owner cannot be removed from the team"
        )
        
    # 3. Permission check: Only the team owner can remove members, OR a user can leave the team
    if team.owner_id != current_user.id and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to remove this member"
        )
        
    # 4. Perform removal
    success = TeamRepository.remove_member(db, team_id=id, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in team"
        )
        
    return {"detail": "Member removed from team successfully"}

@router.get("/my-teams", response_model=List[TeamOut])
def get_my_teams(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all team workspaces the user owns or belongs to."""
    teams = db.query(Team).join(TeamMember).filter(TeamMember.user_id == current_user.id).all()
    return teams

@router.get("/{id}", response_model=TeamOut)
def get_team_details(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve full workspace member details if authorized."""
    team = TeamRepository.get_team_by_id(db, team_id=id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team workspace not found"
        )
        
    member = TeamRepository.get_member(db, team_id=id, user_id=current_user.id)
    if team.owner_id != current_user.id and not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to team workspace"
        )
    return team

@router.put("/{id}", response_model=TeamOut)
def update_team(
    id: str,
    team_in: TeamCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update team workspace name details."""
    team = TeamRepository.get_team_by_id(db, team_id=id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team workspace not found"
        )
        
    # Check if current user has settings edit permission (Owner or Admin)
    # Since we set permission 'settings:edit' for Admin and Business User, let's verify if they have it
    # We can check if they are owner or member with admin status
    member = TeamRepository.get_member(db, team_id=id, user_id=current_user.id)
    is_owner = team.owner_id == current_user.id
    is_admin_member = member and member.role_in_team == "admin"
    
    if not is_owner and not is_admin_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team workspace owners or administrators can edit settings"
        )
        
    team.name = team_in.name
    db.add(team)
    db.commit()
    db.refresh(team)
    return team
