"""App-side encryption for exchange API keys.

Keys are encrypted with Fernet (AES-128-CBC + HMAC) BEFORE writing to
Supabase. They are never stored in plaintext, even in the database.
Only the backend holds ENCRYPTION_KEY.
"""

from cryptography.fernet import Fernet

from app.core.config import get_settings


def _fernet() -> Fernet:
    return Fernet(get_settings().encryption_key.encode())


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()
