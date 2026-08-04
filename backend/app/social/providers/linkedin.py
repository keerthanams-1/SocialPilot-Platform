import logging
import urllib.parse
import httpx
from typing import Dict, Any, List, Optional
from app.social.providers.base import BaseSocialProvider

logger = logging.getLogger("socialpilot.social.linkedin")

class LinkedInProvider(BaseSocialProvider):
    """Official LinkedIn API v2 / Community Management OAuth and Share Publishing Driver."""

    AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    API_URL = "https://api.linkedin.com/v2"

    def authorize(self, redirect_uri: str, state: str, **kwargs) -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "openid profile email w_member_social"
        }
        return f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"

    def callback(self, code: str, redirect_uri: str, **kwargs) -> Dict[str, Any]:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(self.TOKEN_URL, data=data, headers=headers)
            if resp.status_code != 200:
                logger.error(f"LinkedIn OAuth token exchange failed: {resp.text}")
                raise ValueError(f"LinkedIn token exchange error: {resp.text}")
            res = resp.json()
            return {
                "access_token": res["access_token"],
                "refresh_token": res.get("refresh_token", ""),
                "expires_in": res.get("expires_in", 5184000),
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
                return {"access_token": refresh_token_val, "expires_in": 5184000}
            return resp.json()

    def validate_token(self, access_token_val: str) -> bool:
        url = f"{self.API_URL}/userinfo"
        headers = {"Authorization": f"Bearer {access_token_val}"}
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, headers=headers)
            return resp.status_code == 200

    def get_profile(self, access_token_val: str) -> Dict[str, Any]:
        url = f"{self.API_URL}/userinfo"
        headers = {"Authorization": f"Bearer {access_token_val}"}
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code != 200:
                raise ValueError(f"Failed to fetch LinkedIn profile: {resp.text}")
            data = resp.json()
            return {
                "provider_user_id": data.get("sub", "me"),
                "username": data.get("name", "LinkedIn Member"),
                "name": data.get("name", "LinkedIn Member"),
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
        author_urn = kwargs.get("author_urn", "")
        if not author_urn:
            profile = self.get_profile(access_token_val)
            author_urn = f"urn:li:person:{profile['provider_user_id']}"

        url = f"{self.API_URL}/ugcPosts"
        headers = {
            "Authorization": f"Bearer {access_token_val}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        with httpx.Client(timeout=20.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code not in (200, 201):
                logger.error(f"LinkedIn publishing failed: {resp.text}")
                raise ValueError(f"LinkedIn publishing error: {resp.text}")
            res_data = resp.json()
            return {
                "id": res_data.get("id", ""),
                "platform": "linkedin",
                "status": "published",
                "raw_response": res_data
            }

    def disconnect(self, access_token_val: str) -> bool:
        return True
