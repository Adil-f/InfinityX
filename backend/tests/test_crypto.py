import pytest
from cryptography.fernet import Fernet

from app.crypto import TokenEncryptor


def test_encrypt_decrypt_roundtrip():
    key = Fernet.generate_key().decode()
    enc = TokenEncryptor(key)
    token = "EAACEdEose0.fake-instagram-user-token"
    cipher = enc.encrypt(token)
    assert cipher != token
    assert enc.decrypt(cipher) == token


def test_rejects_empty_key():
    with pytest.raises(ValueError):
        TokenEncryptor("")


def test_rejects_invalid_fernet_material():
    from app.crypto import is_valid_fernet_key

    assert is_valid_fernet_key("not-a-fernet-key") is False
    with pytest.raises(ValueError):
        TokenEncryptor("not-a-fernet-key")


def test_rejects_empty_plaintext():
    key = Fernet.generate_key().decode()
    enc = TokenEncryptor(key)
    with pytest.raises(ValueError):
        enc.encrypt("")


def test_wrong_key_fails_decrypt():
    enc_a = TokenEncryptor(Fernet.generate_key().decode())
    enc_b = TokenEncryptor(Fernet.generate_key().decode())
    cipher = enc_a.encrypt("secret-token")
    with pytest.raises(ValueError):
        enc_b.decrypt(cipher)
