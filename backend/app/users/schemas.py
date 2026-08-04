from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserRegisterReq(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    password: str
    confirm_password: str
    full_name: Optional[str] = None
    name: Optional[str] = None
    role_name: Optional[str] = "Content Creator"

class UserLoginReq(BaseModel):
    email: EmailStr
    password: str

class TokenResp(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class ForgotPasswordReq(BaseModel):
    email: EmailStr

class ResetPasswordReq(BaseModel):
    token: str
    new_password: str
    confirm_password: str

class VerifyEmailReq(BaseModel):
    token: str

class UserProfileResp(BaseModel):
    id: str
    uuid: str
    email: str
    username: str
    full_name: str
    name: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: str
    language: str
    status: str
    is_verified: bool
    role_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserProfileUpdateReq(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None

class UserSessionResp(BaseModel):
    id: str
    device_name: Optional[str]
    browser: Optional[str]
    os: Optional[str]
    ip_address: Optional[str]
    last_active: datetime
    is_revoked: bool

    model_config = ConfigDict(from_attributes=True)
