import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.users.models import User
from app.database.models import Role
from app.users.repository import UserRepository, VerificationRepository
from app.users.validators import validate_username
from app.users.schemas import UserRegisterReq
from app.authentication.password import hash_password, generate_secure_token

logger = logging.getLogger("socialpilot.auth.register")

def register_user(db: Session, req: UserRegisterReq) -> User:
    """Register a new user account with validated credentials and role assignment."""
    if req.password != req.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )

    display_name = req.full_name or req.name or "User"
    raw_username = req.username or req.email.split("@")[0]
    clean_username = validate_username(raw_username)

    if UserRepository.get_by_email(db, req.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )

    if UserRepository.get_by_username(db, clean_username):
        clean_username = f"{clean_username}_{generate_secure_token()[:4]}"

    # Resolve requested role (default to Content Creator)
    role_name = req.role_name or "Content Creator"
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        role = Role(name=role_name)
        db.add(role)
        db.commit()
        db.refresh(role)

    hashed_pw = hash_password(req.password)
    user = UserRepository.create_user(
        db,
        email=req.email,
        username=clean_username,
        password_hash=hashed_pw,
        full_name=display_name,
        role_id=role.id,
        is_verified=False
    )

    # Generate email verification record
    verification_token = generate_secure_token()
    VerificationRepository.create_verification_token(db, user.id, verification_token)

    # Check for pending workspace invitations
    from app.database.models import WorkspaceInvitation, TeamMember
    pending_invites = db.query(WorkspaceInvitation).filter(
        WorkspaceInvitation.email == req.email,
        WorkspaceInvitation.status == "pending"
    ).all()

    for inv in pending_invites:
        member = TeamMember(
            team_id=inv.team_id,
            user_id=user.id,
            role_in_team=inv.role_name
        )
        db.add(member)
        inv.status = "accepted"

    if pending_invites:
        db.commit()

    logger.info(f"Registered user {user.email} (ID: {user.id}) with verification token.")

    return user
