from fastapi import APIRouter, Depends, status, Request, Response
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.users.schemas import (
    UserRegisterReq, UserLoginReq, TokenResp, UserProfileResp,
    ForgotPasswordReq, ResetPasswordReq, VerifyEmailReq
)
from app.authentication.register import register_user
from app.authentication.login import authenticate_user
from app.authentication.refresh import rotate_refresh_token
from app.authentication.logout import logout_user
from app.authentication.verification import verify_user_email
from app.authentication.password_reset import request_password_reset, execute_password_reset

router = APIRouter(prefix="/auth", tags=["Authentication Engine"])

@router.post("/register", response_model=UserProfileResp, status_code=status.HTTP_201_CREATED)
def register_endpoint(req: UserRegisterReq, db: Session = Depends(get_db)):
    """Register a new production user account."""
    user = register_user(db, req)
    role_name = user.role.name if user.role else "Content Creator"
    return UserProfileResp(
        id=user.id,
        uuid=user.uuid,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        name=user.name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        timezone=user.timezone,
        language=user.language,
        status=user.status,
        is_verified=user.is_verified,
        role_name=role_name,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@router.post("/login", response_model=TokenResp)
def login_endpoint(req: UserLoginReq, request: Request, response: Response, db: Session = Depends(get_db)):
    """Authenticate user credentials and set HttpOnly cookies."""
    return authenticate_user(db, req, request, response)

@router.post("/logout")
def logout_endpoint(request: Request, response: Response, db: Session = Depends(get_db)):
    """Revoke current user session and delete cookies."""
    return logout_user(db, request, response)

@router.post("/refresh", response_model=TokenResp)
@router.post("/refresh-token", response_model=TokenResp)
def refresh_endpoint(request: Request, response: Response, db: Session = Depends(get_db)):
    """Perform Refresh Token Rotation (RTR)."""
    return rotate_refresh_token(db, request, response)

@router.post("/forgot-password")
def forgot_password_endpoint(req: ForgotPasswordReq, db: Session = Depends(get_db)):
    """Request password reset token."""
    return request_password_reset(db, req)

@router.post("/reset-password")
def reset_password_endpoint(req: ResetPasswordReq, db: Session = Depends(get_db)):
    """Execute password reset using reset token."""
    return execute_password_reset(db, req)

@router.post("/verify-email")
def verify_email_endpoint(req: VerifyEmailReq, db: Session = Depends(get_db)):
    """Verify email address with verification token."""
    return verify_user_email(db, req.token)
