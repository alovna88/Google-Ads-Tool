"""Parse the markdown playbook into a structured dict.

The playbook follows the CLAUDE.md.template layout. We extract the
machine-readable fields so audits and LLM analyses can read them
without re-parsing markdown every call.

This is intentionally lightweight — section-level regex parsing, not
a full markdown AST. The playbook is human-authored and tolerates
imprecision; the parser surfaces what it found and leaves the rest
in `_unparsed_sections`.
"""

import re
from typing import Any

SECTION_HEADER_RE = re.compile(r"^##\s+\d+\.\s+(?P<title>.+?)\s*$", re.MULTILINE)
BULLET_FIELD_RE = re.compile(r"^-\s+\*\*(?P<key>[^*]+)\*\*:?\s*(?P<value>.+?)\s*$", re.MULTILINE)


def split_sections(md: str) -> dict[str, str]:
    """Split the playbook into a `{section_title: body_md}` map.

    Section titles are normalized to lower-snake-ish form for stable lookup.
    """
    sections: dict[str, str] = {}
    matches = list(SECTION_HEADER_RE.finditer(md))
    for i, m in enumerate(matches):
        title = _normalize_title(m.group("title"))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        sections[title] = md[start:end].strip()
    return sections


def _normalize_title(title: str) -> str:
    cleaned = title.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned).strip("_")
    return cleaned


def extract_bullet_fields(section_md: str) -> dict[str, str]:
    """Pull `- **Key**: value` lines into a flat dict."""
    out: dict[str, str] = {}
    for m in BULLET_FIELD_RE.finditer(section_md):
        key = _normalize_title(m.group("key"))
        out[key] = _strip_brackets(m.group("value"))
    return out


def _strip_brackets(value: str) -> str:
    """Treat `[PLACEHOLDER]` values as empty — they're unfilled template slots."""
    v = value.strip()
    if v.startswith("[") and v.endswith("]"):
        return ""
    return v


def parse_playbook(md: str) -> dict[str, Any]:
    """Parse a markdown playbook into the structured shape stored in `parsed`.

    Returns at least the keys defined in docs/data-model.md, with empty
    values where fields are missing. Always returns; never raises on
    incomplete input.
    """
    sections = split_sections(md)

    client_identity = extract_bullet_fields(sections.get("client_identity", ""))
    targets = extract_bullet_fields(sections.get("targets", ""))

    parsed: dict[str, Any] = {
        "icp": client_identity.get("icp", ""),
        "product": client_identity.get("product", ""),
        "company": client_identity.get("company", ""),
        "sales_cycle_days": _to_int(client_identity.get("sales_cycle", "")),
        "acv_usd": _to_money(client_identity.get("acv_annual_contract_value", "")),
        "target_cac_usd": _to_money(targets.get("target_cac", "")),
        "target_ltv_cac_ratio": _to_float(targets.get("target_ltv_cac", "")),
        "currency": client_identity.get("currency", "USD"),
        "timezone": client_identity.get("reporting_timezone", "UTC"),
        "google_ads_cid": client_identity.get("google_ads_cid", ""),
        "_unparsed_section_titles": [t for t in sections if t not in {"client_identity", "targets"}],
    }
    return parsed


def _to_int(s: str) -> int | None:
    if not s:
        return None
    m = re.search(r"\d+", s)
    return int(m.group()) if m else None


def _to_float(s: str) -> float | None:
    if not s:
        return None
    m = re.search(r"\d+(?:\.\d+)?", s)
    return float(m.group()) if m else None


def _to_money(s: str) -> int | None:
    if not s:
        return None
    cleaned = re.sub(r"[^\d.]", "", s)
    if not cleaned:
        return None
    try:
        return int(float(cleaned))
    except ValueError:
        return None
