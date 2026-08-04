import os
import base64
from typing import List, Union, Optional
from cryptography.fernet import Fernet
from pydantic import AnyHttpUrl, Field, field_validator, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "SocialPilot SaaS Platform"
    API_V1_STR: str = "/api/v1"
    
    # Application Security & Cryptography Vault
    SECRET_KEY: str = Field(default="production_secret_key_must_be_set_in_env_vault_32bytes")
    ENCRYPTION_KEY: str = Field(default_factory=lambda: Fernet.generate_key().decode())
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Short-lived access token
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # RTR refresh token lifespan
    
    # PostgreSQL Configuration
    POSTGRES_SERVER: str = Field(default="localhost")
    POSTGRES_USER: str = Field(default="socialpilot")
    POSTGRES_PASSWORD: str = Field(default="socialpilot_pass_secure_2026")
    POSTGRES_DB: str = Field(default="socialpilot_db")
    POSTGRES_PORT: int = Field(default=5432)
    DATABASE_URL: Optional[str] = None

    # MongoDB Configuration
    MONGODB_URL: str = Field(default="mongodb://localhost:27017")
    MONGODB_DB_NAME: str = Field(default="socialpilot_analytics")

    # Redis Configuration (Celery Broker & Cache)
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

    # Official Social API OAuth Credentials (Loaded from .env)
    META_APP_ID: Optional[str] = None
    META_APP_SECRET: Optional[str] = None
    FACEBOOK_CLIENT_ID: Optional[str] = None
    FACEBOOK_CLIENT_SECRET: Optional[str] = None
    INSTAGRAM_CLIENT_ID: Optional[str] = None
    INSTAGRAM_CLIENT_SECRET: Optional[str] = None
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    X_CLIENT_ID: Optional[str] = None
    X_CLIENT_SECRET: Optional[str] = None
    TWITTER_CLIENT_ID: Optional[str] = None
    TWITTER_CLIENT_SECRET: Optional[str] = None
    YOUTUBE_CLIENT_ID: Optional[str] = None
    YOUTUBE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        if isinstance(v, str) and v.strip():
            return v
        values = info.data
        server = values.get("POSTGRES_SERVER", "localhost")
        user = values.get("POSTGRES_USER", "socialpilot")
        password = values.get("POSTGRES_PASSWORD", "socialpilot_pass_secure_2026")
        db = values.get("POSTGRES_DB", "socialpilot_db")
        port = values.get("POSTGRES_PORT", 5432)
        return f"postgresql://{user}:{password}@{server}:{port}/{db}"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
