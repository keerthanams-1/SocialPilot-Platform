from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.users.repository import SessionRepository
from app.users.schemas import UserSessionResp

def list_active_sessions(db: Session, user_id: str) -> List[UserSessionResp]:
    """Retrieve all active device sessions for authenticated user."""
    sessions = SessionRepository.get_user_sessions(db, user_id)
    return [UserSessionResp.model_validate(s) for s in sessions]

def revoke_device_session(db: Session, user_id: str, session_id: str) -> dict:
    """Revoke specific device session by ID."""
    session = SessionRepository.revoke_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )
    return {"detail": "Session revoked successfully."}
