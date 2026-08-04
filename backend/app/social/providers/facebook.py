import logging
import urllib.parse
import httpx
from typing import Dict, Any, List, Optional
from app.social.providers.base import BaseSocialProvider

logger = logging.getLogger("socialpilot.social.facebook")

class FacebookProvider(BaseSocialProvider):
    """Official Facebook Graph API v19.0 OAuth 2.0 and Publishing Driver."""

    GRAPH_URL = "https://graph.facebook.com/v19.0"

    def authorize(self, redirect_uri: str, state: str, **kwargs) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "response_type": "code",
            "scope": "pages_show_list,pages_read_engagement,pages_manage_posts,public_profile"
        }
        return f"https://www.facebook.com/v19.0/dialog/oauth?{urllib.parse.urlencode(params)}"

    def callback(self, code: str, redirect_uri: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.GRAPH_URL}/oauth/access_token"
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri,
            "code": code
        }
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, params=params)
            if resp.status_code != 200:
                logger.error(f"Facebook OAuth token exchange failed: {resp.text}")
                raise ValueError(f"Facebook token exchange error: {resp.text}")
            data = resp.json()

        # Exchange short-lived token for long-lived 60-day token
        long_lived = self.refresh_token(data["access_token"])
        return {
            "access_token": long_lived.get("access_token", data["access_token"]),
            "refresh_token": long_lived.get("refresh_token", ""),
            "expires_in": long_lived.get("expires_in", 5184000),
            "token_type": "bearer"
        }

    def refresh_token(self, refresh_token_val: str) -> Dict[str, Any]:
        """Exchange short-lived token for long-lived page token."""
        url = f"{self.GRAPH_URL}/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "fb_exchange_token": refresh_token_val
        }
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, params=params)
            if resp.status_code != 200:
                logger.warning(f"Facebook token exchange fallback: {resp.text}")
                return {"access_token": refresh_token_val, "expires_in": 5184000}
            return resp.json()

    def validate_token(self, access_token_val: str) -> bool:
        url = f"{self.GRAPH_URL}/me"
        params = {"access_token": access_token_val}
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, params=params)
            return resp.status_code == 200

    def get_profile(self, access_token_val: str) -> Dict[str, Any]:
        url = f"{self.GRAPH_URL}/me"
        params = {
            "fields": "id,name,picture.width(200).height(200)",
            "access_token": access_token_val
        }
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, params=params)
            if resp.status_code != 200:
                raise ValueError(f"Failed to fetch Facebook profile: {resp.text}")
            data = resp.json()
            picture_url = data.get("picture", {}).get("data", {}).get("url", "")
            return {
                "provider_user_id": data["id"],
                "username": data.get("name", "Facebook User"),
                "name": data.get("name", "Facebook User"),
                "avatar_url": picture_url
            }

    def upload_media(self, access_token_val: str, media_url: str, media_type: str = "image") -> str:
        # Facebook allows direct URL parameter attachment in feed post or photo endpoint
        return media_url

    def publish_post(
        self,
        access_token_val: str,
        content: str,
        media_urls: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        target_id = kwargs.get("target_id", "me")
        url = f"{self.GRAPH_URL}/{target_id}/feed"
        payload = {
            "message": content,
            "access_token": access_token_val
        }
        if media_urls and len(media_urls) > 0:
            payload["link"] = media_urls[0]

        with httpx.Client(timeout=20.0) as client:
            resp = client.post(url, data=payload)
            if resp.status_code not in (200, 201):
                logger.error(f"Facebook publish failed: {resp.text}")
                raise ValueError(f"Facebook publish failed: {resp.text}")
            res_data = resp.json()
            return {
                "id": res_data.get("id", ""),
                "platform": "facebook",
                "status": "published",
                "raw_response": res_data
            }

    def disconnect(self, access_token_val: str) -> bool:
        url = f"{self.GRAPH_URL}/me/permissions"
        params = {"access_token": access_token_val}
        with httpx.Client(timeout=10.0) as client:
            resp = client.delete(url, params=params)
            return resp.status_code == 200
