from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from jose import jwt, JWTError
from fastapi import HTTPException, status
from app.core.config import settings

def create_jwt_token(data: Dict[str, Any], expires_delta: timedelta) -> str:
    """Encode payload claims into signed JWT token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

import uuid

def create_access_token(subject: str, role_name: str) -> str:
    """Generate short-lived access token containing user identity and role claim."""
    payload = {
        "sub": subject,
        "role": role_name,
        "type": "access",
        "jti": str(uuid.uuid4())
    }
    return create_jwt_token(payload, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

def create_refresh_token(subject: str) -> str:
    """Generate long-lived refresh token for token rotation (RTR)."""
    payload = {
        "sub": subject,
        "type": "refresh",
        "jti": str(uuid.uuid4())
    }
    return create_jwt_token(payload, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))

def decode_jwt_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT payload structure and expiration."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token signature invalid or expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
