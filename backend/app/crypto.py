"""Token encryption utilities using Fernet symmetric encryption."""
import os
from typing import Optional
from cryptography.fernet import Fernet

_key: Optional[bytes] = None

def _get_fernet() -> Optional[Fernet]:
    global _key
    if _key is None:
        raw = os.getenv("APP_ENCRYPTION_KEY", "").strip()
        if raw:
            _key = raw.encode() if isinstance(raw, str) else raw
    if _key:
        return Fernet(_key)
    return None

def encrypt_text(plaintext: Optional[str]) -> Optional[str]:
    """Encrypt text. Returns plaintext if no key configured."""
    if not plaintext:
        return plaintext
    f = _get_fernet()
    if not f:
        return plaintext  # no encryption configured
    return f.encrypt(plaintext.encode()).decode()

def decrypt_text(ciphertext: Optional[str]) -> Optional[str]:
    """Decrypt text. Returns ciphertext if no key configured."""
    if not ciphertext:
        return ciphertext
    f = _get_fernet()
    if not f:
        return ciphertext  # no encryption configured
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except Exception:
        # If decryption fails, might be plaintext from before encryption was enabled
        return ciphertext
