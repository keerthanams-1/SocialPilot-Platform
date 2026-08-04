import logging
import base64
import hashlib
import os
import urllib.parse
import httpx
from typing import Dict, Any, List, Optional
from app.social.providers.base import BaseSocialProvider

logger = logging.getLogger("socialpilot.social.twitter")

class TwitterProvider(BaseSocialProvider):
    """Official X (Twitter) API v2 OAuth 2.0 PKCE Driver."""

    AUTH_URL = "https://twitter.com/i/oauth2/authorize"
    TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
    API_URL = "https://api.twitter.com/2"

    @staticmethod
    def generate_pkce_verifier_and_challenge():
        """Generate PKCE code verifier and S256 code challenge."""
        code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').replace('=', '')
        digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(digest).decode('utf-8').replace('=', '')
        return code_verifier, code_challenge

    def authorize(self, redirect_uri: str, state: str, **kwargs) -> str:
        code_challenge = kwargs.get("code_challenge", "challenge123")
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "tweet.read tweet.write users.read offline.access",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        return f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"

    def callback(self, code: str, redirect_uri: str, **kwargs) -> Dict[str, Any]:
        code_verifier = kwargs.get("code_verifier", "verifier123")
        data = {
            "code": code,
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(self.TOKEN_URL, data=data, headers=headers, auth=(self.client_id, self.client_secret))
            if resp.status_code != 200:
                logger.error(f"Twitter OAuth PKCE token exchange failed: {resp.text}")
                raise ValueError(f"Twitter token exchange error: {resp.text}")
            res = resp.json()
            return {
                "access_token": res["access_token"],
                "refresh_token": res.get("refresh_token", ""),
                "expires_in": res.get("expires_in", 7200),
                "token_type": "bearer"
            }

    def refresh_token(self, refresh_token_val: str) -> Dict[str, Any]:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token_val,
            "client_id": self.client_id
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(self.TOKEN_URL, data=data, headers=headers, auth=(self.client_id, self.client_secret))
            if resp.status_code != 200:
                return {"access_token": refresh_token_val, "expires_in": 7200}
            return resp.json()

    def validate_token(self, access_token_val: str) -> bool:
        url = f"{self.API_URL}/users/me"
        headers = {"Authorization": f"Bearer {access_token_val}"}
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, headers=headers)
            return resp.status_code == 200

    def get_profile(self, access_token_val: str) -> Dict[str, Any]:
        url = f"{self.API_URL}/users/me?user.fields=profile_image_url,username,name"
        headers = {"Authorization": f"Bearer {access_token_val}"}
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code != 200:
                raise ValueError(f"Failed to fetch Twitter profile: {resp.text}")
            data = resp.json().get("data", {})
            return {
                "provider_user_id": data.get("id", "me"),
                "username": data.get("username", "twitter_user"),
                "name": data.get("name", "X User"),
                "avatar_url": data.get("profile_image_url", "")
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
        url = f"{self.API_URL}/tweets"
        headers = {
            "Authorization": f"Bearer {access_token_val}",
            "Content-Type": "application/json"
        }
        payload = {"text": content}
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code not in (200, 201):
                logger.error(f"Twitter Tweet publishing failed: {resp.text}")
                raise ValueError(f"Twitter Tweet publishing error: {resp.text}")
            res_data = resp.json().get("data", {})
            return {
                "id": res_data.get("id", ""),
                "platform": "twitter",
                "status": "published",
                "raw_response": res_data
            }

    def disconnect(self, access_token_val: str) -> bool:
        url = "https://api.twitter.com/2/oauth2/revoke"
        data = {
            "token": access_token_val,
            "token_type_hint": "access_token",
            "client_id": self.client_id
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(url, data=data, headers=headers, auth=(self.client_id, self.client_secret))
            return resp.status_code == 200
