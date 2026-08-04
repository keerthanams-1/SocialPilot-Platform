import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from app.users.models import (
    User, UserSession, UserLoginHistory,
    EmailVerification, PasswordReset, OAuthAccount
)
from app.core.crypto import encrypt_token, decrypt_token

class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email.lower().strip()).first()

    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username.lower().strip()).first()

    @staticmethod
    def create_user(
        db: Session,
        email: str,
        username: str,
        password_hash: str,
        full_name: str,
        role_id: str,
        is_verified: bool = False
    ) -> User:
        user = User(
            email=email.lower().strip(),
            username=username.lower().strip(),
            password_hash=password_hash,
            full_name=full_name,
            role_id=role_id,
            is_verified=is_verified
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_profile(db: Session, user: User, updates: dict) -> User:
        for key, val in updates.items():
            if val is not None and hasattr(user, key):
                setattr(user, key, val)
        user.updated_at = datetime.utcnow()
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

class SessionRepository:
    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    @classmethod
    def create_session(
        cls,
        db: Session,
        user_id: str,
        refresh_token: str,
        expires_in_days: int,
        device_name: Optional[str] = None,
        browser: Optional[str] = None,
        os: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> UserSession:
        token_hash = cls.hash_token(refresh_token)
        session = UserSession(
            user_id=user_id,
            device_name=device_name,
            browser=browser,
            os=os,
            ip_address=ip_address,
            refresh_token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
            last_active=datetime.utcnow(),
            is_revoked=False
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @classmethod
    def get_by_token(cls, db: Session, refresh_token: str) -> Optional[UserSession]:
        token_hash = cls.hash_token(refresh_token)
        return db.query(UserSession).filter(UserSession.refresh_token_hash == token_hash).first()

    @classmethod
    def revoke_session(cls, db: Session, session_id: str) -> bool:
        session = db.query(UserSession).filter(UserSession.id == session_id).first()
        if session:
            session.is_revoked = True
            db.add(session)
            db.commit()
            return True
        return False

    @classmethod
    def revoke_all_user_sessions(cls, db: Session, user_id: str):
        db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_revoked == False
        ).update({"is_revoked": True})
        db.commit()

    @staticmethod
    def get_user_sessions(db: Session, user_id: str) -> List[UserSession]:
        return db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_revoked == False
        ).all()

class AuditRepository:
    @staticmethod
    def log_login_attempt(
        db: Session,
        user_id: str,
        ip: Optional[str],
        browser: Optional[str],
        device: Optional[str],
        success: bool = True
    ) -> UserLoginHistory:
        log = UserLoginHistory(
            user_id=user_id,
            ip=ip,
            browser=browser,
            device=device,
            success=success,
            login_time=datetime.utcnow()
        )
        db.add(log)
        db.commit()
        return log

class VerificationRepository:
    @staticmethod
    def create_verification_token(db: Session, user_id: str, token: str, expires_in_hours: int = 24) -> EmailVerification:
        record = EmailVerification(
            user_id=user_id,
            verification_token=token,
            expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours),
            verified=False
        )
        db.add(record)
        db.commit()
        return record

    @staticmethod
    def get_by_token(db: Session, token: str) -> Optional[EmailVerification]:
        return db.query(EmailVerification).filter(EmailVerification.verification_token == token).first()

class PasswordResetRepository:
    @staticmethod
    def create_reset_token(db: Session, user_id: str, token: str, expires_in_minutes: int = 60) -> PasswordReset:
        record = PasswordReset(
            user_id=user_id,
            reset_token=token,
            expires_at=datetime.utcnow() + timedelta(minutes=expires_in_minutes),
            used=False
        )
        db.add(record)
        db.commit()
        return record

    @staticmethod
    def get_by_token(db: Session, token: str) -> Optional[PasswordReset]:
        return db.query(PasswordReset).filter(PasswordReset.reset_token == token).first()
