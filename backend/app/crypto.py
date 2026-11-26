"""At-rest encryption for Instagram User access tokens."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.config import Settings


def is_valid_fernet_key(key: str | None) -> bool:
    """Return True only if `key` is usable Fernet key material."""
    if not key or not str(key).strip():
        return False
    try:
        Fernet(str(key).strip().encode("utf-8"))
    except Exception:
        return False
    return True


class TokenEncryptor:
    def __init__(self, key: str) -> None:
        if not is_valid_fernet_key(key):
            raise ValueError(
                "TOKEN_ENCRYPTION_KEY must be a valid Fernet key "
                '(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")'
            )
        self._fernet = Fernet(key.strip().encode("utf-8"))

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            raise ValueError("Cannot encrypt empty token")
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        try:
            return self._fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Failed to decrypt token; check TOKEN_ENCRYPTION_KEY") from exc


def encryptor_from_settings(settings: Settings) -> TokenEncryptor:
    return TokenEncryptor(settings.token_encryption_key)
