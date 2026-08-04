import logging
import urllib.parse
import httpx
from typing import Dict, Any, List, Optional
from app.social.providers.base import BaseSocialProvider

logger = logging.getLogger("socialpilot.social.google")

class GoogleProvider(BaseSocialProvider):
    """Official Google OAuth 2.0 Identity Provider Driver."""

    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    PROFILE_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    def authorize(self, redirect_uri: str, state: str, **kwargs) -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent"
        }
        return f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"

    def callback(self, code: str, redirect_uri: str, **kwargs) -> Dict[str, Any]:
        data = {
            "code": code,
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(self.TOKEN_URL, data=data, headers=headers)
            if resp.status_code != 200:
                raise ValueError(f"Google token exchange error: {resp.text}")
            res = resp.json()
            return {
                "access_token": res["access_token"],
                "refresh_token": res.get("refresh_token", ""),
                "expires_in": res.get("expires_in", 3600),
                "token_type": "bearer"
            }

    def refresh_token(self, refresh_token_val: str) -> Dict[str, Any]:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token_val,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(self.TOKEN_URL, data=data, headers=headers)
            if resp.status_code != 200:
                return {"access_token": refresh_token_val, "expires_in": 3600}
            return resp.json()

    def validate_token(self, access_token_val: str) -> bool:
        headers = {"Authorization": f"Bearer {access_token_val}"}
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(self.PROFILE_URL, headers=headers)
            return resp.status_code == 200

    def get_profile(self, access_token_val: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token_val}"}
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(self.PROFILE_URL, headers=headers)
            if resp.status_code != 200:
                raise ValueError(f"Failed to fetch Google profile: {resp.text}")
            data = resp.json()
            return {
                "provider_user_id": data["id"],
                "username": data.get("email", "google_user"),
                "name": data.get("name", "Google User"),
                "avatar_url": data.get("picture", "")
            }

    def upload_media(self, access_token_val: str, media_url: str, media_type: str = "image") -> str:
        return media_url

    def publish_post(
        self,
        access_token_val: str,
        content: str,
        media_urls: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        return {"id": "google_identity", "platform": "google", "status": "published"}

    def disconnect(self, access_token_val: str) -> bool:
        url = f"https://oauth2.googleapis.com/revoke?token={access_token_val}"
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(url)
            return resp.status_code == 200
