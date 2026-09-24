#!/usr/bin/env python3
"""Assess whether candidate and fair inputs are ready for read-only ingestion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SOURCE_MODES = {"UPLOAD", "PUBLIC_WEB", "AUTHENTICATED_READ_ONLY"}
PROFILE_FIELDS = (
    "cv_present",
    "school",
    "degree",
    "graduation_date",
    "role_types",
    "target_areas",
    "needs_sponsorship",
    "work_authorization",
)
FAIR_FIELDS = ("name", "date", "timezone", "format")
FORBIDDEN_ACTIONS = [
    "Request or store passwords",
    "Handle MFA codes or solve CAPTCHAs",
    "Bypass authentication or use hidden private endpoints",
    "Register, waitlist, message, apply, upload, or mutate a profile without confirmation",
]


def _missing_profile_fields(profile: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in PROFILE_FIELDS:
        value = profile.get(field)
        if value is None or value == "" or value == [] or value is False and field == "cv_present":
            missing.append(f"candidate_profile.{field}")
    return missing


def _missing_fair_fields(fair: dict[str, Any]) -> list[str]:
    missing = [f"fair.{field}" for field in FAIR_FIELDS if not fair.get(field)]
    if not fair.get("source_mode"):
        missing.append("fair.source_mode")
    for field in ("company_list_present", "role_data_present", "session_data_present"):
        if fair.get(field) is not True:
            missing.append(f"fair.{field}")
    return missing


def assess_intake(document: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic intake/access state without external side effects."""
    if not isinstance(document, dict):
        raise ValueError("input must be a JSON object")
    profile = document.get("candidate_profile")
    fair = document.get("fair")
    access = document.get("access", {})
    if not isinstance(profile, dict):
        raise ValueError("candidate_profile must be an object")
    if not isinstance(fair, dict):
        raise ValueError("fair must be an object")
    if not isinstance(access, dict):
        raise ValueError("access must be an object")
    if access.get("credentials_shared") is True:
        raise ValueError("credentials must not be requested, accepted, or stored")

    profile_missing = _missing_profile_fields(profile)
    fair_missing = _missing_fair_fields(fair)
    common = {
        "missing_fields": profile_missing + fair_missing,
        "forbidden_actions": FORBIDDEN_ACTIONS,
        "external_mutations_require_confirmation": True,
    }

    if profile.get("approved") is not True or profile_missing:
        return {
            **common,
            "state": "PROFILE_REVIEW",
            "permitted_actions": ["Draft or revise the candidate profile"],
            "next_actions": ["Ask the user to correct and explicitly approve the profile."],
        }

    source_mode = fair.get("source_mode")
    if source_mode is None:
        return {
            **common,
            "state": "NEED_FAIR_SOURCE",
            "permitted_actions": ["Explain the three supported source modes"],
            "next_actions": ["Ask for an export, public URL, or user-opened authenticated tab."],
        }
    if source_mode not in SOURCE_MODES:
        raise ValueError(f"fair.source_mode must be one of: {sorted(SOURCE_MODES)}")

    platform = fair.get("platform", "generic")
    if not isinstance(platform, str) or not platform:
        raise ValueError("fair.platform must be a non-empty string")
    handshake_live_fetch = platform.lower() == "handshake" and source_mode != "UPLOAD"
    requires_login = source_mode == "AUTHENTICATED_READ_ONLY" or handshake_live_fetch
    effective_source_mode = (
        "AUTHENTICATED_READ_ONLY" if requires_login else source_mode
    )

    if requires_login:
        if access.get("user_logged_in") is not True:
            return {
                **common,
                "state": "NEED_USER_LOGIN",
                "permitted_actions": ["Ask the user to open Handshake and log in themselves"],
                "next_actions": ["Wait until the user confirms the authenticated tab is open."],
            }
        if access.get("authorization_scope") != "read_only":
            return {
                **common,
                "state": "NEED_READ_ONLY_AUTHORIZATION",
                "permitted_actions": ["Ask for permission to inspect the visible authenticated tab"],
                "next_actions": ["Obtain explicit read-only authorization for this fair."],
            }
        permitted = ["Read visible employer, role, and session data"]
    elif source_mode == "PUBLIC_WEB":
        permitted = ["Read public event, employer, role, and session pages"]
    else:
        permitted = ["Read user-supplied exports, documents, screenshots, and text"]

    return {
        **common,
        "state": "READY_FOR_INGESTION",
        "source_mode": effective_source_mode,
        "permitted_actions": permitted,
        "next_actions": [
            "Ingest available data and preserve missing role or session fields as unknown."
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        result = assess_intake(payload)
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
