from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from jose import JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.core.dependencies import get_db
from app.database.repositories import UserRepository, RoleRepository, SessionRepository
from app.database.schemas import UserRegister, UserLogin, Token, UserOut

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    # 1. Check if email exists
    existing_user = UserRepository.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 2. Check or create requested role (default to Content Creator)
    role = RoleRepository.get_by_name(db, name=user_in.role_name)
    if not role:
        # Fallback to create the role dynamically if it doesn't exist
        role = RoleRepository.create(db, name=user_in.role_name)
        
    # 3. Create the user
    user = UserRepository.create(db, user_in=user_in, role_id=role.id)
    return user

@router.post("/login", response_model=Token)
def login(
    response: Response,
    request: Request,
    user_in: UserLogin,
    db: Session = Depends(get_db)
):
    # 1. Authenticate user
    user = UserRepository.get_by_email(db, email=user_in.email)
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
        
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    # Log successful login event
    from app.database.models import AuditLog
    audit_log = AuditLog(
        user_name=user.name,
        user_email=user.email,
        role_name=user.role.name,
        action="LOGIN",
        ip_address=request.client.host if request.client else None
    )
    db.add(audit_log)
    db.commit()

    # 2. Generate tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    # 3. Record session in database for RTR
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    SessionRepository.create_session(
        db, 
        user_id=user.id, 
        refresh_token=refresh_token, 
        expires_in_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        ip=ip,
        ua=ua
    )

    # 4. Set HttpOnly cookies for security
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=False,  # Set True in production (HTTPS)
        samesite="lax"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        secure=False,  # Set True in production (HTTPS)
        samesite="lax"
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh-token", response_model=Token)
def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    # 1. Try to read refresh token from HttpOnly cookie or Request Body
    refresh_token_val = request.cookies.get("refresh_token")
    if not refresh_token_val:
        # Try authorization header or body if cookie not found
        # (Allows non-browser clients to work)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            refresh_token_val = auth_header.split(" ")[1]

    if not refresh_token_val:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )

    # 2. Decode and validate JWT structure
    try:
        payload = decode_token(refresh_token_val)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token signature invalid or expired"
        )

    # 3. Check DB session record
    db_session = SessionRepository.get_session_by_token(db, refresh_token=refresh_token_val)
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found"
        )

    # 4. Refresh Token Rotation (RTR) check:
    # If the token is already marked revoked, it means someone is trying to reuse an old refresh token.
    # Revoke ALL user sessions immediately as a security breach precaution.
    if db_session.is_revoked or db_session.expires_at < datetime.utcnow():
        SessionRepository.revoke_all_user_sessions(db, user_id=user_id)
        # Clear cookies
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or reuse detected. Please re-authenticate."
        )

    # 5. Perform token rotation
    # Revoke the old session
    SessionRepository.revoke_session(db, refresh_token=refresh_token_val)

    # Generate new tokens
    new_access_token = create_access_token(subject=user_id)
    new_refresh_token = create_refresh_token(subject=user_id)

    # Create new session in DB
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    SessionRepository.create_session(
        db,
        user_id=user_id,
        refresh_token=new_refresh_token,
        expires_in_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        ip=ip,
        ua=ua
    )

    # Update cookies
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=False,
        samesite="lax"
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        secure=False,
        samesite="lax"
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    # Retrieve token to revoke session in database
    refresh_token_val = request.cookies.get("refresh_token")
    if not refresh_token_val:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            refresh_token_val = auth_header.split(" ")[1]

    if refresh_token_val:
        db_session = SessionRepository.get_session_by_token(db, refresh_token=refresh_token_val)
        if db_session and db_session.user:
            user = db_session.user
            from app.database.models import AuditLog
            audit_log = AuditLog(
                user_name=user.name,
                user_email=user.email,
                role_name=user.role.name,
                action="LOGOUT",
                ip_address=request.client.host if request.client else None
            )
            db.add(audit_log)
            db.commit()
        SessionRepository.revoke_session(db, refresh_token=refresh_token_val)

    # Clear HttpOnly cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"detail": "Successfully logged out"}

from app.core.dependencies import get_current_active_user
from app.database.models import User

@router.get("/audit-logs")
def get_audit_logs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Security: restrict to Administrators only
    if current_user.role.name != "Administrator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to workspace administrators only"
        )
    
    from app.database.models import AuditLog
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).all()
    return logs
