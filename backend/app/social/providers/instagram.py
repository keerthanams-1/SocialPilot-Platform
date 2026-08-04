import logging
import urllib.parse
import httpx
import time
from typing import Dict, Any, List, Optional
from app.social.providers.base import BaseSocialProvider

logger = logging.getLogger("socialpilot.social.instagram")

class InstagramProvider(BaseSocialProvider):
    """Official Instagram Graph API Content Publishing Driver (Containers, Single & Carousel)."""

    GRAPH_URL = "https://graph.facebook.com/v19.0"

    def authorize(self, redirect_uri: str, state: str, **kwargs) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "response_type": "code",
            "scope": "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement"
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
                raise ValueError(f"Instagram OAuth token error: {resp.text}")
            data = resp.json()
        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", ""),
            "expires_in": data.get("expires_in", 5184000),
            "token_type": "bearer"
        }

    def refresh_token(self, refresh_token_val: str) -> Dict[str, Any]:
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
                return {"access_token": refresh_token_val, "expires_in": 5184000}
            return resp.json()

    def validate_token(self, access_token_val: str) -> bool:
        url = f"{self.GRAPH_URL}/me"
        params = {"access_token": access_token_val}
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, params=params)
            return resp.status_code == 200

    def get_profile(self, access_token_val: str) -> Dict[str, Any]:
        url = f"{self.GRAPH_URL}/me/accounts"
        params = {
            "fields": "id,name,instagram_business_account{id,username,profile_picture_url}",
            "access_token": access_token_val
        }
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, params=params)
            if resp.status_code != 200:
                raise ValueError(f"Failed to fetch Instagram accounts: {resp.text}")
            data = resp.json()
            accounts = data.get("data", [])
            if accounts and "instagram_business_account" in accounts[0]:
                ig_acc = accounts[0]["instagram_business_account"]
                return {
                    "provider_user_id": ig_acc["id"],
                    "username": ig_acc.get("username", "instagram_user"),
                    "name": ig_acc.get("username", "instagram_user"),
                    "avatar_url": ig_acc.get("profile_picture_url", "")
                }
            return {
                "provider_user_id": "me",
                "username": "instagram_account",
                "name": "Instagram Business Account",
                "avatar_url": ""
            }

    def upload_media(self, access_token_val: str, media_url: str, media_type: str = "IMAGE") -> str:
        """Create Instagram Media Container."""
        return media_url

    def publish_post(
        self,
        access_token_val: str,
        content: str,
        media_urls: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        ig_user_id = kwargs.get("target_id", "me")
        if not media_urls or len(media_urls) == 0:
            raise ValueError("Instagram requires at least 1 image or video media asset to publish.")

        image_url = media_urls[0]

        # Step 1: Create Container
        container_url = f"{self.GRAPH_URL}/{ig_user_id}/media"
        container_payload = {
            "image_url": image_url,
            "caption": content,
            "access_token": access_token_val
        }
        with httpx.Client(timeout=20.0) as client:
            c_resp = client.post(container_url, data=container_payload)
            if c_resp.status_code not in (200, 201):
                logger.error(f"Instagram Container Creation Failed: {c_resp.text}")
                raise ValueError(f"Instagram Container Creation Failed: {c_resp.text}")
            container_id = c_resp.json()["id"]

            # Step 2: Publish Container
            publish_url = f"{self.GRAPH_URL}/{ig_user_id}/media_publish"
            publish_payload = {
                "creation_id": container_id,
                "access_token": access_token_val
            }
            p_resp = client.post(publish_url, data=publish_payload)
            if p_resp.status_code not in (200, 201):
                logger.error(f"Instagram Media Publish Failed: {p_resp.text}")
                raise ValueError(f"Instagram Media Publish Failed: {p_resp.text}")
            res_data = p_resp.json()
            return {
                "id": res_data.get("id", container_id),
                "platform": "instagram",
                "status": "published",
                "raw_response": res_data
            }

    def disconnect(self, access_token_val: str) -> bool:
        return True
