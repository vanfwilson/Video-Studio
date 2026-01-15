"""
Token encryption/decryption utilities using Fernet symmetric encryption.
Requires APP_ENCRYPTION_KEY environment variable (base64-encoded 32-byte key).
"""
import base64
from typing import Optional
from cryptography.fernet import Fernet
from app.config import settings


def _get_fernet() -> Optional[Fernet]:
    """Get Fernet instance if encryption key is configured."""
    if not settings.APP_ENCRYPTION_KEY:
        return None
    try:
        return Fernet(settings.APP_ENCRYPTION_KEY.encode())
    except Exception:
        return None


def encrypt_text(plain: Optional[str]) -> Optional[str]:
    """Encrypt text using Fernet. Returns plain text if no key configured."""
    if not plain:
        return plain
    f = _get_fernet()
    if not f:
        return plain
    return f.encrypt(plain.encode()).decode()


def decrypt_text(cipher: Optional[str]) -> Optional[str]:
    """Decrypt text using Fernet. Returns cipher text if no key configured."""
    if not cipher:
        return cipher
    f = _get_fernet()
    if not f:
        return cipher
    try:
        return f.decrypt(cipher.encode()).decode()
    except Exception:
        # If decryption fails, assume it's already plain text
        return cipher


def generate_encryption_key() -> str:
    """Generate a new Fernet encryption key (for setup)."""
    return Fernet.generate_key().decode()
