import os
from app.social.providers.base import BaseSocialProvider
from app.social.providers.facebook import FacebookProvider
from app.social.providers.instagram import InstagramProvider
from app.social.providers.linkedin import LinkedInProvider
from app.social.providers.twitter import TwitterProvider
from app.social.providers.youtube import YouTubeProvider
from app.social.providers.google import GoogleProvider
from app.core.config import settings

PROVIDERS_MAP = {
    "facebook": (FacebookProvider, settings.FACEBOOK_CLIENT_ID, settings.FACEBOOK_CLIENT_SECRET),
    "instagram": (InstagramProvider, settings.INSTAGRAM_CLIENT_ID, settings.INSTAGRAM_CLIENT_SECRET),
    "linkedin": (LinkedInProvider, settings.LINKEDIN_CLIENT_ID, settings.LINKEDIN_CLIENT_SECRET),
    "twitter": (TwitterProvider, settings.TWITTER_CLIENT_ID, settings.TWITTER_CLIENT_SECRET),
    "youtube": (YouTubeProvider, settings.YOUTUBE_CLIENT_ID, settings.YOUTUBE_CLIENT_SECRET),
    "google": (GoogleProvider, settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET),
}

def get_social_provider(provider_name: str) -> BaseSocialProvider:
    """Factory helper to instantiate driver for requested provider."""
    clean_name = provider_name.lower().strip()
    if clean_name not in PROVIDERS_MAP:
        raise ValueError(f"Unsupported social provider: '{provider_name}'. Supported: {list(PROVIDERS_MAP.keys())}")
    
    cls, client_id, client_secret = PROVIDERS_MAP[clean_name]

    if clean_name in ("facebook", "instagram"):
        client_id = (
            settings.META_APP_ID or
            settings.FACEBOOK_CLIENT_ID or
            settings.INSTAGRAM_CLIENT_ID or
            os.getenv("META_APP_ID") or
            os.getenv("FACEBOOK_CLIENT_ID") or
            os.getenv("INSTAGRAM_CLIENT_ID")
        )
        client_secret = (
            settings.META_APP_SECRET or
            settings.FACEBOOK_CLIENT_SECRET or
            settings.INSTAGRAM_CLIENT_SECRET or
            os.getenv("META_APP_SECRET") or
            os.getenv("FACEBOOK_CLIENT_SECRET") or
            os.getenv("INSTAGRAM_CLIENT_SECRET")
        )
    elif clean_name in ("youtube", "google"):
        client_id = settings.GOOGLE_CLIENT_ID or settings.YOUTUBE_CLIENT_ID or os.getenv("GOOGLE_CLIENT_ID") or os.getenv("YOUTUBE_CLIENT_ID")
        client_secret = settings.GOOGLE_CLIENT_SECRET or settings.YOUTUBE_CLIENT_SECRET or os.getenv("GOOGLE_CLIENT_SECRET") or os.getenv("YOUTUBE_CLIENT_SECRET")
    elif clean_name == "linkedin":
        client_id = settings.LINKEDIN_CLIENT_ID or os.getenv("LINKEDIN_CLIENT_ID")
        client_secret = settings.LINKEDIN_CLIENT_SECRET or os.getenv("LINKEDIN_CLIENT_SECRET")
    elif clean_name in ("twitter", "x"):
        client_id = settings.X_CLIENT_ID or settings.TWITTER_CLIENT_ID or os.getenv("X_API_KEY") or os.getenv("TWITTER_CLIENT_ID")
        client_secret = settings.X_CLIENT_SECRET or settings.TWITTER_CLIENT_SECRET or os.getenv("X_API_SECRET") or os.getenv("TWITTER_CLIENT_SECRET")

    return cls(client_id=client_id or "", client_secret=client_secret or "")
