import logging
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.users.repository import UserRepository, PasswordResetRepository
from app.authentication.password import hash_password, generate_secure_token
from app.users.schemas import ForgotPasswordReq, ResetPasswordReq

logger = logging.getLogger("socialpilot.auth.password_reset")

def request_password_reset(db: Session, req: ForgotPasswordReq) -> dict:
    """Generate password reset token for requested email."""
    user = UserRepository.get_by_email(db, req.email)
    if user:
        token = generate_secure_token()
        PasswordResetRepository.create_reset_token(db, user.id, token)
        logger.info(f"Generated password reset token for {user.email}")
        return {"detail": "Password reset token generated successfully.", "reset_token": token}
    
    # Generic success response to avoid user enumeration
    return {"detail": "If the email is registered, a password reset token has been sent."}

def execute_password_reset(db: Session, req: ResetPasswordReq) -> dict:
    """Execute password reset using valid reset token."""
    if req.new_password != req.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match."
        )

    record = PasswordResetRepository.get_by_token(db, req.token)
    if not record or record.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )

    if record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired."
        )

    user = UserRepository.get_by_id(db, record.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    user.password_hash = hash_password(req.new_password)
    user.updated_at = datetime.utcnow()
    record.used = True

    db.add(user)
    db.add(record)
    db.commit()

    logger.info(f"Password reset successful for user {user.email}")
    return {"detail": "Password reset successfully. You may now log in with your new password."}
