from __future__ import annotations

from app.security import DISCLAIMER
from app.services.ai import analyze


def render_report(*, title: str, purpose: str, lawful_basis: str, findings: list[dict], unavailable: list[dict]) -> str:
    analysis = analyze(findings, unavailable)
    lines = [
        f"# {title}",
        "",
        "## Scope",
        f"- Purpose: {purpose}",
        f"- Lawful basis: {lawful_basis}",
        "- Collection: public sources and configured authorized providers only.",
        "",
        "## Disclaimer",
        DISCLAIMER,
        "",
        "## Verified observations",
    ]
    if not analysis["facts"]:
        lines.append("No verified observations are stored for this investigation.")
    for fact in analysis["facts"]:
        lines.append(
            f"- **{fact['title']}** ({fact['source_id']}, confidence {fact['confidence']}): {fact['summary']}"
        )
    lines.append("")
    lines.append("## References that were not verified")
    if not analysis["references"]:
        lines.append("None.")
    for item in analysis["references"]:
        lines.append(f"- **{item['title']}**: {item['summary']}")
    lines.append("")
    lines.append("## Hypotheses")
    if not analysis["hypotheses"]:
        lines.append("None generated from the verified observations.")
    for item in analysis["hypotheses"]:
        lines.append(f"- {item['statement']} (confidence {item['confidence']})")
    lines.append("")
    lines.append("## Contradictions")
    if not analysis["contradictions"]:
        lines.append("No contradiction rule fired.")
    for item in analysis["contradictions"]:
        lines.append(f"- {item['statement']}")
    lines.append("")
    lines.append("## Sources that were unavailable or not configured")
    if not unavailable:
        lines.append("None recorded on the stored jobs.")
    for item in unavailable:
        env = ", ".join(item.get("required_env") or [])
        extra = f" Required env: {env}." if env else ""
        lines.append(f"- {item.get('source_name') or item.get('source_id')}: {item.get('message')}{extra}")
    lines.append("")
    lines.append("## Lawful next sources")
    for item in analysis["next_sources"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Timeline")
    if not analysis["timeline"]:
        lines.append("No verified timestamps.")
    for item in analysis["timeline"]:
        lines.append(f"- {item.get('collected_at')}: {item.get('title')} ({item.get('source_id')})")
    lines.append("")
    return "\n".join(lines)
