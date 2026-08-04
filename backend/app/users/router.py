from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.dependencies import get_current_active_user
from app.users.models import User
from app.users.repository import UserRepository
from app.users.schemas import UserProfileResp, UserProfileUpdateReq, UserSessionResp
from app.authentication.session import list_active_sessions, revoke_device_session

router = APIRouter(prefix="/users", tags=["User & Session Management"])

@router.get("/profile", response_model=UserProfileResp)
def get_user_profile(current_user: User = Depends(get_current_active_user)):
    """Retrieve authenticated user profile."""
    role_name = current_user.role.name if current_user.role else "Viewer"
    return UserProfileResp(
        id=current_user.id,
        uuid=current_user.uuid,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        name=current_user.name,
        phone=current_user.phone,
        avatar_url=current_user.avatar_url,
        timezone=current_user.timezone,
        language=current_user.language,
        status=current_user.status,
        is_verified=current_user.is_verified,
        role_name=role_name,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

@router.put("/profile", response_model=UserProfileResp)
def update_user_profile(
    req: UserProfileUpdateReq,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update profile fields for authenticated user."""
    updated_user = UserRepository.update_profile(
        db,
        current_user,
        req.model_dump(exclude_unset=True)
    )
    role_name = updated_user.role.name if updated_user.role else "Viewer"
    return UserProfileResp(
        id=updated_user.id,
        uuid=updated_user.uuid,
        email=updated_user.email,
        username=updated_user.username,
        full_name=updated_user.full_name,
        name=updated_user.name,
        phone=updated_user.phone,
        avatar_url=updated_user.avatar_url,
        timezone=updated_user.timezone,
        language=updated_user.language,
        status=updated_user.status,
        is_verified=updated_user.is_verified,
        role_name=role_name,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at
    )

@router.get("/sessions", response_model=List[UserSessionResp])
def get_user_sessions_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List active device sessions for current user."""
    return list_active_sessions(db, current_user.id)

@router.delete("/sessions/{session_id}")
def delete_user_session_endpoint(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Revoke a specific device session."""
    return revoke_device_session(db, current_user.id, session_id)
