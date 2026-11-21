from __future__ import annotations

import hashlib
import math
import re
from collections import Counter

from app.services.results import Finding, ModuleResult


def _shannon(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def safe_filename(name: str | None) -> str | None:
    if not name:
        return None
    base = name.replace("\\", "/").split("/")[-1]
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", base)[:120]
    return cleaned or None


def hash_evidence(content: bytes, filename: str | None = None) -> ModuleResult:
    result = ModuleResult(query_type="forensics", normalized_query=f"{len(content)} bytes", external_attempted=False)
    if not content:
        result.status = "rejected"
        result.errors.append({"source_id": "evidence_hash", "source_name": "Evidence hashing", "message": "No content was provided"})
        return result
    if len(content) > 1_048_576:
        result.status = "rejected"
        result.errors.append({"source_id": "evidence_hash", "source_name": "Evidence hashing", "message": "Content exceeds the 1 MB local hashing limit"})
        return result
    sha256 = hashlib.sha256(content).hexdigest()
    sha1 = hashlib.sha1(content).hexdigest()
    md5 = hashlib.md5(content).hexdigest()
    result.normalized_query = sha256
    result.notes.append("Hashes were computed locally. The content was not stored and was not sent to a provider.")
    result.findings.append(
        Finding(
            entity_type="hash",
            value=sha256,
            normalized_value=sha256,
            title="SHA-256",
            summary=f"SHA-256 of the supplied bytes ({len(content)} bytes). This is an integrity hash, not a malware verdict.",
            source_id="evidence_hash",
            source_name="Local evidence hashing",
            confidence=1.0,
            verified=True,
            kind="fact",
            attributes={
                "sha256": sha256,
                "sha1": sha1,
                "md5": md5,
                "size_bytes": len(content),
                "shannon_entropy": round(_shannon(content), 4),
                "filename": safe_filename(filename),
                "content_stored": False,
            },
        )
    )
    return result
