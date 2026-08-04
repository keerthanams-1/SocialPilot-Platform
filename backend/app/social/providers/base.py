from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseSocialProvider(ABC):
    """
    Abstract Base Class for official social media platform API drivers.
    All platform providers must implement these mandatory interfaces.
    """

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    @abstractmethod
    def authorize(self, redirect_uri: str, state: str, **kwargs) -> str:
        """Construct official OAuth 2.0 authorization URL for user consent."""
        pass

    @abstractmethod
    def callback(self, code: str, redirect_uri: str, **kwargs) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        pass

    @abstractmethod
    def refresh_token(self, refresh_token_val: str) -> Dict[str, Any]:
        """Refresh expired access token using refresh token."""
        pass

    @abstractmethod
    def validate_token(self, access_token_val: str) -> bool:
        """Validate whether token is currently active and unrevoked."""
        pass

    @abstractmethod
    def get_profile(self, access_token_val: str) -> Dict[str, Any]:
        """Fetch user or page channel profile metadata."""
        pass

    @abstractmethod
    def publish_post(
        self,
        access_token_val: str,
        content: str,
        media_urls: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Publish post content to the target social media platform."""
        pass

    @abstractmethod
    def upload_media(
        self,
        access_token_val: str,
        media_url: str,
        media_type: str = "image"
    ) -> str:
        """Upload media asset and return container ID or media ID."""
        pass

    @abstractmethod
    def disconnect(self, access_token_val: str) -> bool:
        """Revoke application permissions and disconnect account."""
        pass
