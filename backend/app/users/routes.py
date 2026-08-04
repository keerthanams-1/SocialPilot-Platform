from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_active_user, get_db
from app.database.models import User
from app.database.repositories import UserRepository, RoleRepository
from app.database.schemas import UserOut, UserProfileUpdate, PasswordChange, RoleOut
from app.core.security import get_password_hash, verify_password

router = APIRouter(tags=["User Profile"])

@router.get("/profile", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.put("/profile", response_model=UserOut)
def update_profile(
    user_update: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # If email is changing, make sure it is not taken
    if user_update.email and user_update.email != current_user.email:
        existing = UserRepository.get_by_email(db, email=user_update.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
            
    updated_user = UserRepository.update(db, db_user=current_user, user_update=user_update)
    return updated_user

@router.put("/profile/change-password", status_code=status.HTTP_200_OK)
def change_password(
    pwd_in: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify current password matches
    if not verify_password(pwd_in.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
        
    new_hash = get_password_hash(pwd_in.new_password)
    UserRepository.update_password(db, db_user=current_user, new_password_hash=new_hash)
    return {"detail": "Password successfully updated"}

@router.get("/roles", response_model=List[RoleOut])
def get_roles(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Exposes roles listing to active users for assigning roles in team management."""
    return RoleRepository.get_all(db)
