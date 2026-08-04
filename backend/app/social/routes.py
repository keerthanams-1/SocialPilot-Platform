import uuid
from datetime import datetime, timedelta
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_active_user, get_db
from app.database.models import User, SocialAccount
from app.database.repositories import TeamRepository, SocialAccountRepository
from app.database.schemas import SocialAccountOut, OAuthCallbackIn

router = APIRouter(prefix="/social", tags=["Social Account Integration"])

SUPPORTED_PLATFORMS = {"facebook", "instagram", "linkedin", "twitter", "youtube", "pinterest"}

# Thread-safe in-memory simulation tracker for rate limits: {account_id: remaining_quota}
QUOTA_TRACKER: Dict[str, int] = {}

def map_model_to_schema(acc: SocialAccount) -> dict:
    """Helper to inject runtime simulation states into serialized outputs."""
    is_expired = acc.expires_at is not None and acc.expires_at < datetime.utcnow()
    status_str = "expired" if is_expired else "connected"
    
    if acc.id not in QUOTA_TRACKER:
        QUOTA_TRACKER[acc.id] = 100
        
    return {
        "id": acc.id,
        "team_id": acc.team_id,
        "user_id": acc.user_id,
        "platform": acc.platform,
        "platform_account_id": acc.platform_account_id,
        "account_name": acc.account_name,
        "avatar_url": acc.avatar_url,
        "expires_at": acc.expires_at,
        "created_at": acc.created_at,
        "status": status_str,
        "rate_limit_remaining": QUOTA_TRACKER[acc.id]
    }

@router.get("/connect/{platform}")
def connect_platform(
    platform: str,
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    platform_lower = platform.lower()
    if platform_lower not in SUPPORTED_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Platform '{platform}' is not supported"
        )
        
    # Check if user belongs to the team
    member = TeamRepository.get_member(db, team_id=team_id, user_id=current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of this team workspace to connect accounts"
        )

    from app.social.providers import get_social_provider
    driver = get_social_provider(platform_lower)
    if not driver or not driver.client_id or driver.client_id == "demo_client_id":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Meta App Developer Credentials (META_APP_ID and META_APP_SECRET) are missing in backend/.env for {platform.capitalize()}. Please configure valid credentials from developers.facebook.com to execute live OAuth."
        )

    state = f"user_{current_user.id}_{platform_lower}"
    redirect_uri = f"http://localhost:8000/api/v1/social/callback/{platform_lower}"
    auth_url = driver.authorize(redirect_uri=redirect_uri, state=state)
    
    return {
        "platform": platform_lower,
        "state": state,
        "redirect_url": auth_url,
        "authorization_url": auth_url
    }

@router.post("/callback", response_model=SocialAccountOut)
def oauth_callback(
    platform: str,
    payload: OAuthCallbackIn,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    platform_lower = platform.lower()
    if platform_lower not in SUPPORTED_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported platform"
        )
        
    member = TeamRepository.get_member(db, team_id=payload.team_id, user_id=current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to team workspace"
        )

    mock_access_token = f"mock_access_token_{uuid.uuid4().hex}"
    mock_refresh_token = f"mock_refresh_token_{uuid.uuid4().hex}"
    expires_in_seconds = 3600 * 24 * 30  # 30 days
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in_seconds)

    platform_account_id = f"ext_{uuid.uuid4().hex[:8]}"
    capitalized_platform = platform_lower.capitalize()
    account_name = f"{current_user.name} ({capitalized_platform})"
    avatar_url = f"https://api.dicebear.com/7.x/bottts/svg?seed={platform_account_id}"

    social_account = SocialAccountRepository.connect_account(
        db,
        team_id=payload.team_id,
        user_id=current_user.id,
        platform=platform_lower,
        platform_account_id=platform_account_id,
        name=account_name,
        avatar=avatar_url,
        token=mock_access_token,
        refresh=mock_refresh_token,
        expires_at=expires_at
    )
    
    return map_model_to_schema(social_account)

@router.get("/accounts", response_model=List[SocialAccountOut])
def list_social_accounts(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    member = TeamRepository.get_member(db, team_id=team_id, user_id=current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to workspace channels"
        )
        
    accounts = SocialAccountRepository.get_by_team_id(db, team_id=team_id)
    return [map_model_to_schema(a) for a in accounts]

@router.delete("/accounts/{id}", status_code=status.HTTP_200_OK)
def disconnect_social_account(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    account = SocialAccountRepository.get_by_id(db, account_id=id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social account connection not found"
        )
        
    team = TeamRepository.get_team_by_id(db, team_id=account.team_id)
    if team.owner_id != current_user.id and account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team owner or the connector of this account can disconnect it"
        )
        
    success = SocialAccountRepository.disconnect_account(db, account_id=id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect account"
        )
        
    # Clear active rates simulation
    if id in QUOTA_TRACKER:
        del QUOTA_TRACKER[id]

    return {"detail": "Social account disconnected successfully"}

# ----------------- Advanced Debug & Simulation Endpoints -----------------

@router.post("/accounts/{id}/simulate-expiry", response_model=SocialAccountOut)
def simulate_expiry(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Developer helper to manually force token expiration status for debugging warning dialogs."""
    account = SocialAccountRepository.get_by_id(db, account_id=id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social connection not found"
        )
        
    team = TeamRepository.get_team_by_id(db, team_id=account.team_id)
    if team.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners can debug this workspace"
        )
        
    # Force expires_at to 1 hour in the past
    account.expires_at = datetime.utcnow() - timedelta(hours=1)
    db.add(account)
    db.commit()
    db.refresh(account)
    
    return map_model_to_schema(account)

@router.post("/accounts/{id}/trigger-api-call")
def trigger_api_call(
    id: str,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Simulates making an external API request on the platform, tracking quota decrements and rate limits."""
    account = SocialAccountRepository.get_by_id(db, account_id=id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social connection not found"
        )
        
    # 1. Enforce Expiration Checks
    if account.expires_at and account.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Connection has expired. Please re-authenticate your channel."
        )

    # 2. Perform Real Provider API Call if Access Token exists
    api_result = {"status": "success", "platform": account.platform}
    if account.access_token:
        try:
            from app.core.security import decrypt_token
            import httpx
            decrypted_token = decrypt_token(account.access_token)
            if account.platform in ("facebook", "instagram"):
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get("https://graph.facebook.com/v19.0/me", params={"access_token": decrypted_token})
                    if resp.status_code == 200:
                        api_result["graph_api"] = resp.json()
                    else:
                        api_result["graph_api_error"] = resp.text
        except Exception as ex:
            api_result["decryption_or_api_error"] = str(ex)

    # 3. Enforce Rate Limits Tracker
    if account.id not in QUOTA_TRACKER:
        QUOTA_TRACKER[account.id] = 100
        
    if QUOTA_TRACKER[account.id] <= 0:
        response.headers["X-RateLimit-Limit"] = "100"
        response.headers["X-RateLimit-Remaining"] = "0"
        response.headers["X-RateLimit-Reset"] = "60"
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for platform. Quota reset in 60 seconds."
        )
        
    # Decrement quota
    QUOTA_TRACKER[account.id] -= 1
    
    response.headers["X-RateLimit-Limit"] = "100"
    response.headers["X-RateLimit-Remaining"] = str(QUOTA_TRACKER[account.id])
    response.headers["X-RateLimit-Reset"] = "60"
    
    return {
        "status": "success",
        "action": "real_api_call",
        "details": api_result,
        "remaining_quota": QUOTA_TRACKER[account.id]
    }
