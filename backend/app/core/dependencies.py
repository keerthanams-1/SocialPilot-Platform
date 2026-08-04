from typing import List
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.config import settings
from app.authentication.jwt import decode_jwt_token
from app.database.session import get_db
from app.users.repository import UserRepository
from app.users.models import User

def get_token_from_cookie_or_header(request: Request) -> str:
    """Extract access token from HttpOnly cookie or Authorization header."""
    token = request.cookies.get("access_token")
    if token:
        return token
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = get_token_from_cookie_or_header(request)
    payload = decode_jwt_token(token)
    user_id: str = payload.get("sub")
    token_type: str = payload.get("type")
    
    if user_id is None or token_type != "access":
        raise credentials_exception
        
    user = UserRepository.get_by_id(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive or suspended user"
        )
    return current_user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        user_role = current_user.role.name if current_user.role else "Viewer"
        if user_role == "Administrator" or user_role in self.allowed_roles:
            return current_user
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation forbidden. Required role in: {self.allowed_roles}"
        )

def require_role(allowed_roles: List[str]):
    return Depends(RoleChecker(allowed_roles))

class PermissionChecker:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        permissions_list = [p.name for p in current_user.role.permissions] if current_user.role and hasattr(current_user.role, 'permissions') else []
        if current_user.role and current_user.role.name == "Administrator" or self.required_permission in permissions_list:
            return current_user
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation not permitted. Required permission: '{self.required_permission}'"
        )

def require_permission(permission_name: str):
    return Depends(PermissionChecker(permission_name))
