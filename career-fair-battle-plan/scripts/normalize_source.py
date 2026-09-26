#!/usr/bin/env python3
"""Normalize visible career-fair sources into scoped evidence records."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Callable


EVIDENCE_LEVELS = {
    "EMPLOYER_NAME": 0,
    "EMPLOYER_CARD": 1,
    "TITLE_ONLY": 2,
    "EXACT_ROLE": 3,
    "SESSION_VERIFIED": 4,
}
VALID_SCOPES = {
    "event",
    "employer_event_card",
    "company_current",
    "company_history",
    "exact_role",
    "exact_session",
}
VALID_FIELDS = {
    "employer",
    "role",
    "sponsorship",
    "headcount",
    "salary",
    "eligibility",
    "session",
}
VALID_STATUSES = {"yes", "no", "unknown"}
VALID_QUALITY = {"primary", "government", "reputable_secondary", "anecdotal", "unverified"}
VALID_FRESHNESS = {"current", "stale", "unknown"}


def _iso_date(value: Any, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO date") from exc
    return parsed.isoformat()


def _text(value: Any, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _coverage(visible: int, advertised: Any, explicitly_complete: bool = False) -> dict[str, Any]:
    if advertised is not None:
        if isinstance(advertised, bool) or not isinstance(advertised, int) or advertised < 0:
            raise ValueError("advertised_employer_count must be a non-negative integer")
    complete = bool(explicitly_complete or (advertised is not None and visible == advertised))
    return {"visible": visible, "advertised": advertised, "complete": complete}


def _base_record(
    document: dict[str, Any],
    *,
    claim_id: str,
    scope: str,
    field: str,
    status: str,
    source_quality: str = "primary",
    published_at: str | None = None,
    freshness: str = "unknown",
    claim: str,
) -> dict[str, Any]:
    if scope not in VALID_SCOPES:
        raise ValueError(f"invalid evidence scope: {scope}")
    if field not in VALID_FIELDS:
        raise ValueError(f"invalid evidence field: {field}")
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid evidence status: {status}")
    if source_quality not in VALID_QUALITY:
        raise ValueError(f"invalid source_quality: {source_quality}")
    if freshness not in VALID_FRESHNESS:
        raise ValueError(f"invalid freshness: {freshness}")
    source_url = document.get("source_url")
    artifact_reference = document.get("artifact_reference")
    if source_url is None and artifact_reference is None:
        raise ValueError("source_url or artifact_reference is required")
    return {
        "claim_id": _text(claim_id, "claim_id"),
        "claim": _text(claim, "claim"),
        "scope": scope,
        "field": field,
        "status": status,
        "source_quality": source_quality,
        "source_url": _text(source_url, "source_url", optional=True),
        "artifact_reference": _text(
            artifact_reference, "artifact_reference", optional=True
        ),
        "published_at": _iso_date(published_at, "published_at", optional=True),
        "accessed_at": _iso_date(document.get("accessed_at"), "accessed_at"),
        "freshness": freshness,
    }


def _assert_unique(records: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for record in records:
        claim_id = record["claim_id"]
        if claim_id in seen:
            raise ValueError(f"duplicate evidence claim_id: {claim_id}")
        seen.add(claim_id)


def strongest_evidence_level(records: list[dict[str, Any]]) -> str:
    """Return the strongest level justified by record scope, never by wording."""
    level = "EMPLOYER_NAME"
    for record in records:
        scope = record.get("scope")
        field = record.get("field")
        status = record.get("status")
        if scope == "exact_session" and field == "session" and status in {"yes", "available"}:
            candidate = "SESSION_VERIFIED"
        elif scope == "exact_role" and field in {
            "role",
            "sponsorship",
            "eligibility",
            "salary",
            "headcount",
        }:
            candidate = "EXACT_ROLE"
        elif scope == "employer_event_card" and field == "role":
            candidate = "TITLE_ONLY"
        elif scope == "employer_event_card":
            candidate = "EMPLOYER_CARD"
        else:
            candidate = "EMPLOYER_NAME"
        if EVIDENCE_LEVELS[candidate] > EVIDENCE_LEVELS[level]:
            level = candidate
    return level


def _sponsorship_status(text: str) -> str:
    lowered = text.casefold()
    if "willing to sponsor" in lowered or "sponsorship available" in lowered:
        return "yes"
    if "no sponsorship" in lowered or "without sponsorship" in lowered:
        return "no"
    return "unknown"


def _normalize_handshake_public_preview(document: dict[str, Any]) -> dict[str, Any]:
    employers = document.get("employers", [])
    if not isinstance(employers, list):
        raise ValueError("employers must be a list")
    records: list[dict[str, Any]] = []
    leads: list[dict[str, Any]] = []
    for employer_index, employer in enumerate(employers):
        if not isinstance(employer, dict):
            raise ValueError(f"employers[{employer_index}] must be an object")
        name = _text(employer.get("name"), f"employers[{employer_index}].name")
        employer_id = f"employer-card-{employer_index + 1}"
        employer_records = [
            _base_record(
                document,
                claim_id=employer_id,
                scope="employer_event_card",
                field="employer",
                status="yes",
                claim=f"{name} is visible on the event employer card.",
            )
        ]
        auth_text = employer.get("work_authorization_text")
        if auth_text:
            auth_text = _text(auth_text, "work_authorization_text")
            employer_records.append(
                _base_record(
                    document,
                    claim_id=f"{employer_id}-sponsorship",
                    scope="employer_event_card",
                    field="sponsorship",
                    status=_sponsorship_status(auth_text),
                    claim=auth_text,
                )
            )
        titles = employer.get("job_titles", [])
        if not isinstance(titles, list) or not all(isinstance(item, str) and item.strip() for item in titles):
            raise ValueError("job_titles must be a list of non-empty strings")
        for title_index, title in enumerate(titles):
            employer_records.append(
                _base_record(
                    document,
                    claim_id=f"{employer_id}-title-{title_index + 1}",
                    scope="employer_event_card",
                    field="role",
                    status="yes",
                    claim=f"Employer card lists title: {title.strip()}.",
                )
            )
        session_count = employer.get("session_count", 0)
        if isinstance(session_count, bool) or not isinstance(session_count, int) or session_count < 0:
            raise ValueError("session_count must be a non-negative integer")
        if session_count:
            employer_records.append(
                _base_record(
                    document,
                    claim_id=f"{employer_id}-session-advertised",
                    scope="employer_event_card",
                    field="session",
                    status="unknown",
                    claim=f"Employer card advertises {session_count} session(s); time and access are unverified.",
                )
            )
        records.extend(employer_records)
        role_titles = [item.strip() for item in titles] or [None]
        for title in role_titles:
            leads.append(
                {
                    "company": name,
                    "role": title,
                    "evidence_level": strongest_evidence_level(employer_records),
                    "visit_access": "unknown",
                    "session_status": "unknown",
                    "evidence_ids": [record["claim_id"] for record in employer_records],
                }
            )
    _assert_unique(records)
    return {
        "adapter": "handshake_public_preview",
        "source_mode": "PUBLIC_PREVIEW",
        "coverage": _coverage(len(employers), document.get("advertised_employer_count")),
        "access_requirements": [],
        "leads": leads,
        "evidence_records": records,
    }


def _normalize_official_school(document: dict[str, Any]) -> dict[str, Any]:
    fair = document.get("fair", {})
    if not isinstance(fair, dict):
        raise ValueError("fair must be an object")
    _text(fair.get("name"), "fair.name")
    if fair.get("date") is not None:
        _iso_date(fair.get("date"), "fair.date")
    employers = document.get("employers", [])
    if not isinstance(employers, list):
        raise ValueError("employers must be a list")
    records: list[dict[str, Any]] = []
    leads: list[dict[str, Any]] = []
    for index, employer in enumerate(employers):
        if not isinstance(employer, dict):
            raise ValueError(f"employers[{index}] must be an object")
        name = _text(employer.get("name"), f"employers[{index}].name")
        record = _base_record(
            document,
            claim_id=f"official-employer-{index + 1}",
            scope="event",
            field="employer",
            status="yes",
            claim=f"Official event page names {name}.",
        )
        records.append(record)
        leads.append(
            {
                "company": name,
                "role": None,
                "evidence_level": "EMPLOYER_NAME",
                "visit_access": "unknown",
                "session_status": "unknown",
                "evidence_ids": [record["claim_id"]],
            }
        )
    login_required = document.get("login_required_for_employer_list") is True
    explicitly_complete = document.get("employer_list_kind") == "complete" and not login_required
    coverage = _coverage(
        len(employers), document.get("advertised_employer_count"), explicitly_complete
    )
    if document.get("employer_list_kind") == "featured_only" or login_required:
        coverage["complete"] = False
    _assert_unique(records)
    return {
        "adapter": "official_school",
        "source_mode": "PUBLIC_WEB",
        "fair": fair,
        "coverage": coverage,
        "access_requirements": ["login_required_for_employer_list"] if login_required else [],
        "leads": leads,
        "evidence_records": records,
    }


def _normalize_handshake_authenticated(document: dict[str, Any]) -> dict[str, Any]:
    employers = document.get("employers", [])
    if not isinstance(employers, list):
        raise ValueError("employers must be a list")
    records: list[dict[str, Any]] = []
    leads: list[dict[str, Any]] = []
    for employer_index, employer in enumerate(employers):
        name = _text(employer.get("name"), f"employers[{employer_index}].name")
        roles = employer.get("roles", [])
        sessions = employer.get("sessions", [])
        if not isinstance(roles, list) or not isinstance(sessions, list):
            raise ValueError("roles and sessions must be lists")
        employer_records: list[dict[str, Any]] = []
        for role in roles:
            source_id = _text(role.get("source_id"), "role.source_id")
            title = _text(role.get("title"), "role.title")
            employer_records.append(
                _base_record(
                    document,
                    claim_id=source_id,
                    scope="exact_role",
                    field="role",
                    status="yes",
                    claim=f"Authenticated event UI links exact role: {title}.",
                )
            )
        verified_session: dict[str, Any] | None = None
        for session in sessions:
            source_id = _text(session.get("source_id"), "session.source_id")
            status = session.get("status")
            usable = (
                status == "available"
                and isinstance(session.get("start_minute"), (int, float))
                and isinstance(session.get("end_minute"), (int, float))
                and bool(session.get("channel"))
            )
            employer_records.append(
                _base_record(
                    document,
                    claim_id=source_id,
                    scope="exact_session",
                    field="session",
                    status="yes" if usable else "no" if status == "full" else "unknown",
                    claim=f"Authenticated event UI session status: {status or 'unknown'}.",
                )
            )
            if usable and verified_session is None:
                verified_session = dict(session)
        records.extend(employer_records)
        role_items = roles or [{"title": None}]
        for role in role_items:
            level = strongest_evidence_level(employer_records)
            lead = {
                "company": name,
                "role": role.get("title"),
                "evidence_level": level,
                "visit_access": "verified" if verified_session else "unknown",
                "session_status": verified_session.get("status") if verified_session else "unknown",
                "evidence_ids": [record["claim_id"] for record in employer_records],
            }
            if verified_session:
                lead["fixed_session"] = {
                    "start_minute": verified_session["start_minute"],
                    "end_minute": verified_session["end_minute"],
                    "channel": verified_session["channel"],
                }
            leads.append(lead)
    _assert_unique(records)
    return {
        "adapter": "handshake_authenticated_read_only",
        "source_mode": "AUTHENTICATED_READ_ONLY",
        "coverage": _coverage(
            len(employers),
            document.get("advertised_employer_count"),
            document.get("employer_list_kind") == "complete",
        ),
        "access_requirements": [],
        "leads": leads,
        "evidence_records": records,
    }


def _normalize_external_role(document: dict[str, Any]) -> dict[str, Any]:
    roles = document.get("roles", [])
    if not isinstance(roles, list):
        raise ValueError("roles must be a list")
    records: list[dict[str, Any]] = []
    leads: list[dict[str, Any]] = []
    for index, role in enumerate(roles):
        if not isinstance(role, dict):
            raise ValueError(f"roles[{index}] must be an object")
        source_id = _text(role.get("source_id"), f"roles[{index}].source_id")
        company = _text(role.get("company"), f"roles[{index}].company")
        title = _text(role.get("role"), f"roles[{index}].role", optional=True)
        scope = role.get("scope", "exact_role" if title else "company_current")
        role_records: list[dict[str, Any]] = []
        if title:
            role_records.append(
                _base_record(
                    document,
                    claim_id=source_id,
                    scope="exact_role",
                    field="role",
                    status="yes",
                    source_quality=role.get("source_quality", "primary"),
                    published_at=role.get("published_at"),
                    freshness=role.get("freshness", "current"),
                    claim=f"Current source lists exact role: {title}.",
                )
            )
        sponsorship = role.get("sponsorship")
        if sponsorship is not None:
            role_records.append(
                _base_record(
                    document,
                    claim_id=source_id if not title else f"{source_id}-sponsorship",
                    scope=scope,
                    field="sponsorship",
                    status=sponsorship,
                    source_quality=role.get("source_quality", "primary"),
                    published_at=role.get("published_at"),
                    freshness=role.get("freshness", "unknown"),
                    claim=f"Source reports sponsorship status {sponsorship} at {scope} scope.",
                )
            )
        if not role_records:
            role_records.append(
                _base_record(
                    document,
                    claim_id=source_id,
                    scope=scope,
                    field="employer",
                    status="yes",
                    source_quality=role.get("source_quality", "primary"),
                    published_at=role.get("published_at"),
                    freshness=role.get("freshness", "unknown"),
                    claim=f"Source names employer {company}.",
                )
            )
        records.extend(role_records)
        leads.append(
            {
                "company": company,
                "role": title,
                "evidence_level": strongest_evidence_level(role_records),
                "visit_access": "unknown",
                "session_status": "unknown",
                "evidence_ids": [record["claim_id"] for record in role_records],
            }
        )
    _assert_unique(records)
    return {
        "adapter": "external_role_research",
        "source_mode": "PUBLIC_WEB",
        "coverage": _coverage(len(roles), len(roles), True),
        "access_requirements": [],
        "leads": leads,
        "evidence_records": records,
    }


ADAPTERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "handshake_public_preview": _normalize_handshake_public_preview,
    "official_school": _normalize_official_school,
    "handshake_authenticated_read_only": _normalize_handshake_authenticated,
    "external_role_research": _normalize_external_role,
}


def normalize_source(document: dict[str, Any]) -> dict[str, Any]:
    """Normalize a visible or supplied source without promoting evidence scope."""
    if not isinstance(document, dict):
        raise ValueError("source input must be a JSON object")
    adapter = document.get("adapter")
    if adapter not in ADAPTERS:
        raise ValueError(f"unsupported source adapter: {adapter}")
    _iso_date(document.get("accessed_at"), "accessed_at")
    return ADAPTERS[adapter](document)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        result = normalize_source(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
