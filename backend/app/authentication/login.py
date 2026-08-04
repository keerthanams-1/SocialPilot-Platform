import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Request, Response
from app.core.config import settings
from app.users.repository import UserRepository, SessionRepository, AuditRepository
from app.users.schemas import UserLoginReq, TokenResp
from app.authentication.password import verify_password
from app.authentication.jwt import create_access_token, create_refresh_token

logger = logging.getLogger("socialpilot.auth.login")

def authenticate_user(
    db: Session,
    req: UserLoginReq,
    request: Request,
    response: Response
) -> TokenResp:
    """Authenticate user credentials, log login history, create session, and issue tokens."""
    user = UserRepository.get_by_email(db, req.email)
    ip_addr = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "Unknown")

    if not user or not verify_password(req.password, user.password_hash):
        if user:
            AuditRepository.log_login_attempt(db, user.id, ip=ip_addr, browser=user_agent, device=user_agent, success=False)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password."
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been suspended or deactivated."
        )

    # Log successful login
    AuditRepository.log_login_attempt(db, user.id, ip=ip_addr, browser=user_agent, device=user_agent, success=True)

    # Generate JWT tokens
    access_token = create_access_token(user.id, user.role.name if user.role else "Content Creator")
    refresh_token = create_refresh_token(user.id)

    # Create active session in database
    SessionRepository.create_session(
        db,
        user_id=user.id,
        refresh_token=refresh_token,
        expires_in_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        device_name=user_agent[:100],
        browser=user_agent[:100],
        ip_address=ip_addr
    )

    # Set HttpOnly Secure Cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False  # Set True in HTTPS production
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite="lax",
        secure=False
    )

    logger.info(f"User {user.email} authenticated successfully.")
    return TokenResp(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
