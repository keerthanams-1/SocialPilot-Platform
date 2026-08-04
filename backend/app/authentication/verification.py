from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.users.repository import VerificationRepository, UserRepository

def verify_user_email(db: Session, token: str) -> dict:
    """Validate email verification token and activate user account verification state."""
    record = VerificationRepository.get_by_token(db, token)
    if not record or record.verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already processed verification token."
        )

    if record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired."
        )

    record.verified = True
    db.add(record)

    user = UserRepository.get_by_id(db, record.user_id)
    if user:
        user.is_verified = True
        db.add(user)

    db.commit()
    return {"detail": "Email verified successfully."}
