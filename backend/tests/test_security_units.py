from app.config import Settings, validate_runtime
from app.services.forensics import hash_evidence
from app.services.ratelimit import MemoryRateLimiter
import pytest


def test_memory_rate_limiter_blocks():
    limiter = MemoryRateLimiter(limit=2)
    assert limiter.allow("analyst", now=1)
    assert limiter.allow("analyst", now=2)
    assert limiter.allow("analyst", now=3) is False


def test_known_sha256_vector():
    result = hash_evidence(b"abc", filename="../../etc/passwd")
    assert result.findings[0].attributes["sha256"] == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert result.findings[0].attributes["filename"] == "passwd"
    assert result.findings[0].attributes["content_stored"] is False


def test_production_refuses_fixture_seed():
    settings = Settings(app_env="production", secret_key="x" * 40, seed_dev_fixtures=True)
    with pytest.raises(RuntimeError):
        validate_runtime(settings)
