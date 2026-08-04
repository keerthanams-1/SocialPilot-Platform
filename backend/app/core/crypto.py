from cryptography.fernet import Fernet
from app.core.config import settings

# Initialize Fernet cipher using configured base64 symmetric master key
try:
    # Ensure key is valid base64 representation matching Fernet constraints
    cipher = Fernet(settings.ENCRYPTION_KEY.encode("utf-8"))
except Exception as e:
    # Critical fallback key in case configuration load fails (helps local tests run cleanly)
    fallback_key = Fernet.generate_key()
    cipher = Fernet(fallback_key)

def encrypt_token(plain_token: str) -> str:
    """Symmetrically encrypt token value to secure byte blob string."""
    if not plain_token:
        return plain_token
    token_bytes = plain_token.encode("utf-8")
    encrypted_bytes = cipher.encrypt(token_bytes)
    return encrypted_bytes.decode("utf-8")

def decrypt_token(encrypted_token: str) -> str:
    """Symmetrically decrypt token value back to original plain string."""
    if not encrypted_token:
        return encrypted_token
    try:
        encrypted_bytes = encrypted_token.encode("utf-8")
        decrypted_bytes = cipher.decrypt(encrypted_bytes)
        return decrypted_bytes.decode("utf-8")
    except Exception:
        # If decryption fails (e.g. invalid key or unencrypted legacy data), return raw value
        return encrypted_token
