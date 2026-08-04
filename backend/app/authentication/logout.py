import logging
from sqlalchemy.orm import Session
from fastapi import Request, Response
from app.users.repository import SessionRepository

logger = logging.getLogger("socialpilot.auth.logout")

def logout_user(db: Session, request: Request, response: Response) -> dict:
    """Revoke user session and delete HttpOnly authentication cookies."""
    token_val = request.cookies.get("refresh_token")
    if not token_val:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token_val = auth_header.split(" ")[1]

    if token_val:
        db_session = SessionRepository.get_by_token(db, token_val)
        if db_session:
            SessionRepository.revoke_session(db, db_session.id)
            logger.info(f"Revoked session {db_session.id} for user {db_session.user_id}")

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"detail": "Successfully logged out"}
