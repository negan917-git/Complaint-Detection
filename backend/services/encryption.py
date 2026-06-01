import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

_ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")


def _get_cipher():
    if _ENCRYPTION_KEY:
        return Fernet(_ENCRYPTION_KEY.encode())
    return None


def encrypt_token(token: str) -> str | None:
    cipher = _get_cipher()
    if cipher:
        return cipher.encrypt(token.encode()).decode()
    return token


def decrypt_token(encrypted: str) -> str | None:
    cipher = _get_cipher()
    if cipher:
        try:
            return cipher.decrypt(encrypted.encode()).decode()
        except Exception:
            return encrypted
    return encrypted
