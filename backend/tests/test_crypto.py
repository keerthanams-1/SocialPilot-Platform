import pytest
from app.core.crypto import encrypt_token, decrypt_token

def test_fernet_crypto_roundtrip():
    """Verify Fernet AES-256 token encryption and decryption returns exact original token."""
    raw_token = "EAABwz1234567890_mock_facebook_oauth_access_token_secure"
    encrypted = encrypt_token(raw_token)
    
    assert encrypted != raw_token
    assert isinstance(encrypted, str)
    
    decrypted = decrypt_token(encrypted)
    assert decrypted == raw_token

def test_crypto_empty_handling():
    """Verify empty or None tokens pass through safely without errors."""
    assert encrypt_token("") == ""
    assert decrypt_token("") == ""
    assert encrypt_token(None) is None
    assert decrypt_token(None) is None

def test_crypto_invalid_data_graceful():
    """Verify invalid ciphertext returns original input gracefully instead of crashing."""
    invalid_ciphertext = "not_valid_fernet_ciphertext"
    result = decrypt_token(invalid_ciphertext)
    assert result == invalid_ciphertext
