import logging
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Request, Response
from app.core.config import settings
from app.users.repository import UserRepository, SessionRepository
from app.users.schemas import TokenResp
from app.authentication.jwt import decode_jwt_token, create_access_token, create_refresh_token

logger = logging.getLogger("socialpilot.auth.refresh")

def rotate_refresh_token(db: Session, request: Request, response: Response) -> TokenResp:
    """Execute Refresh Token Rotation (RTR). If reuse is detected, revoke all user sessions."""
    token_val = request.cookies.get("refresh_token")
    if not token_val:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token_val = auth_header.split(" ")[1]

    if not token_val:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing."
        )

    payload = decode_jwt_token(token_val)
    user_id = payload.get("sub")
    token_type = payload.get("type")

    if not user_id or token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token type."
        )

    db_session = SessionRepository.get_by_token(db, token_val)
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found."
        )

    # Security Breach Detection: If token is revoked or expired, revoke ALL sessions for this user
    if db_session.is_revoked or db_session.expires_at < datetime.utcnow():
        logger.warning(f"RTR Security Alert: Token reuse or expired session for user {user_id}. Revoking all sessions.")
        SessionRepository.revoke_all_user_sessions(db, user_id)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session revoked due to security violation or token reuse detected."
        )

    # Revoke old session
    SessionRepository.revoke_session(db, db_session.id)

    user = UserRepository.get_by_id(db, user_id)
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive."
        )

    # Issue new token pair
    new_access_token = create_access_token(user.id, user.role.name if user.role else "Content Creator")
    new_refresh_token = create_refresh_token(user.id)

    # Create new rotated session
    user_agent = request.headers.get("user-agent", "Unknown")
    ip_addr = request.client.host if request.client else None
    SessionRepository.create_session(
        db,
        user_id=user.id,
        refresh_token=new_refresh_token,
        expires_in_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        device_name=user_agent[:100],
        browser=user_agent[:100],
        ip_address=ip_addr
    )

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite="lax",
        secure=False
    )

    return TokenResp(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
