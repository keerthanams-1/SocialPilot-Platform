import secrets
import bcrypt
from app.users.validators import validate_password_strength

def hash_password(password: str) -> str:
    """Hash password securely using bcrypt."""
    validate_password_strength(password)
    pw_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against bcrypt hash."""
    pw_bytes = plain_password.encode('utf-8')[:72]
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pw_bytes, hash_bytes)

def generate_secure_token() -> str:
    """Generate cryptographically strong random hex token for resets and verifications."""
    return secrets.token_urlsafe(32)
