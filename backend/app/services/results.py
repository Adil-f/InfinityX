from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Finding:
    entity_type: str
    value: str
    normalized_value: str
    title: str
    summary: str
    source_id: str
    source_name: str
    confidence: float
    verified: bool
    kind: str
    source_url: str | None = None
    collected_at: datetime | None = None
    attributes: dict = field(default_factory=dict)
    is_fixture: bool = False

    def __post_init__(self) -> None:
        if self.collected_at is None:
            self.collected_at = utcnow()
        if self.kind not in {"fact", "reference"}:
            raise ValueError("kind must be fact or reference")
        if not 0 <= float(self.confidence) <= 1:
            raise ValueError("confidence out of range")

    def as_dict(self) -> dict:
        return {
            "entity_type": self.entity_type,
            "value": self.value,
            "normalized_value": self.normalized_value,
            "title": self.title,
            "summary": self.summary,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "confidence": self.confidence,
            "verified": self.verified,
            "kind": self.kind,
            "attributes": self.attributes,
            "is_fixture": False,
        }


@dataclass
class SourceOutcome:
    source_id: str
    source_name: str
    status: str
    findings: list[Finding] = field(default_factory=list)
    error: str | None = None
    required_env: list[str] = field(default_factory=list)
    message: str | None = None
    details: dict = field(default_factory=dict)

    def unavailable_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "status": self.status,
            "message": self.message or self.error or "Source unavailable",
            "required_env": self.required_env,
        }

    def error_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "message": (self.error or "Source error")[:300],
        }


@dataclass
class ModuleResult:
    query_type: str
    normalized_query: str
    findings: list[Finding] = field(default_factory=list)
    unavailable: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    external_attempted: bool = False
    suggested_module: str | None = None
    status: str = "completed"
    transient: dict = field(default_factory=dict)


def dedupe_findings(findings: list[Finding]) -> list[Finding]:
    best: dict[tuple, Finding] = {}
    for finding in findings:
        key = (finding.source_id, finding.kind, finding.entity_type, finding.normalized_value, finding.title)
        current = best.get(key)
        if current is None or finding.confidence > current.confidence:
            best[key] = finding
    return list(best.values())


def publishable(findings: list[Finding]) -> tuple[list[Finding], bool]:
    clean = []
    blocked = False
    for finding in findings:
        if finding.is_fixture:
            blocked = True
            continue
        clean.append(finding)
    return clean, blocked


def absorb(result: ModuleResult, outcome: SourceOutcome) -> None:
    if outcome.status == "unavailable":
        result.unavailable.append(outcome.unavailable_dict())
        return
    if outcome.status == "error":
        result.errors.append(outcome.error_dict())
        result.findings.extend(outcome.findings)
        return
    result.findings.extend(outcome.findings)
    if outcome.message and outcome.status == "not_checked":
        result.notes.append(outcome.message)
