"""At-rest encryption for Instagram User access tokens."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.config import Settings


class TokenEncryptor:
    def __init__(self, key: str) -> None:
        if not key or not key.strip():
            raise ValueError("TOKEN_ENCRYPTION_KEY is required")
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
