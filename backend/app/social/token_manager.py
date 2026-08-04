import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.users.models import OAuthAccount
from app.core.crypto import encrypt_token, decrypt_token
from app.social.providers import get_social_provider

logger = logging.getLogger("socialpilot.social.token_manager")

class TokenManager:
    """Manages Fernet AES-256 encrypted token lifecycle, decryption, and automatic background refresh."""

    @staticmethod
    def store_oauth_account(
        db: Session,
        user_id: str,
        provider: str,
        provider_user_id: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        scope: Optional[str] = None,
        expires_in_seconds: int = 3600,
        account_name: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> OAuthAccount:
        """Encrypt and store OAuth tokens into user database."""
        enc_access = encrypt_token(access_token)
        enc_refresh = encrypt_token(refresh_token) if refresh_token else None
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in_seconds)

        existing = db.query(OAuthAccount).filter(
            OAuthAccount.user_id == user_id,
            OAuthAccount.provider == provider
        ).first()

        if existing:
            existing.provider_user_id = provider_user_id
            existing.access_token = enc_access
            if enc_refresh:
                existing.refresh_token = enc_refresh
            existing.scope = scope or existing.scope
            existing.expires_at = expires_at
            if account_name:
                existing.account_name = account_name
            if avatar_url:
                existing.avatar_url = avatar_url
            existing.connected = True
            db.commit()
            db.refresh(existing)
            logger.info(f"Updated OAuth tokens for {provider} account {provider_user_id}.")
            return existing
        else:
            new_acc = OAuthAccount(
                user_id=user_id,
                provider=provider,
                provider_user_id=provider_user_id,
                account_name=account_name,
                avatar_url=avatar_url,
                access_token=enc_access,
                refresh_token=enc_refresh,
                scope=scope,
                expires_at=expires_at,
                connected=True
            )
            db.add(new_acc)
            db.commit()
            db.refresh(new_acc)
            logger.info(f"Stored new OAuth tokens for {provider} account {provider_user_id}.")
            return new_acc

    @staticmethod
    def get_valid_access_token(db: Session, account: OAuthAccount) -> str:
        """Decrypt access token and trigger automatic refresh if token is expired or within 1 hour of expiration."""
        raw_access = decrypt_token(account.access_token)
        raw_refresh = decrypt_token(account.refresh_token) if account.refresh_token else ""

        # Check if expired or within 1 hour of expiry
        buffer_time = datetime.utcnow() + timedelta(hours=1)
        if account.expires_at and account.expires_at <= buffer_time and raw_refresh:
            logger.info(f"Token for {account.provider} account {account.id} is near expiration. Triggering refresh.")
            try:
                provider_driver = get_social_provider(account.provider)
                refreshed = provider_driver.refresh_token(raw_refresh)
                new_access = refreshed.get("access_token")
                new_refresh = refreshed.get("refresh_token", raw_refresh)
                expires_in = refreshed.get("expires_in", 3600)

                if new_access:
                    account.access_token = encrypt_token(new_access)
                    if new_refresh:
                        account.refresh_token = encrypt_token(new_refresh)
                    account.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                    db.commit()
                    return new_access
            except Exception as exc:
                logger.error(f"Failed auto-refresh for {account.provider}: {exc}")

        return raw_access

    @staticmethod
    def refresh_all_expiring_tokens(db: Session) -> int:
        """Background job helper scanning all active OAuth accounts and refreshing near-expiry tokens."""
        buffer_time = datetime.utcnow() + timedelta(hours=2)
        expiring_accounts = db.query(OAuthAccount).filter(
            OAuthAccount.connected == True,
            OAuthAccount.expires_at <= buffer_time
        ).all()

        count = 0
        for acc in expiring_accounts:
            try:
                TokenManager.get_valid_access_token(db, acc)
                count += 1
            except Exception as e:
                logger.error(f"Error during bulk refresh for account {acc.id}: {e}")
        return count
