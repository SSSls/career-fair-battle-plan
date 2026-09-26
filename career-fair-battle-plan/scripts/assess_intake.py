#!/usr/bin/env python3
"""Assess whether candidate and fair inputs are ready for read-only ingestion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SOURCE_MODES = {
    "UPLOAD",
    "PUBLIC_WEB",
    "PUBLIC_PREVIEW",
    "AUTHENTICATED_READ_ONLY",
}
AUTHENTICATION_STATES = {"NOT_REQUIRED", "LOGGED_OUT", "LOGGED_IN", "UNKNOWN"}
REGISTRATION_STATES = {"NOT_REQUIRED", "NOT_REGISTERED", "REGISTERED", "UNKNOWN"}
AUTHORIZATION_SCOPES = {"NONE", "READ_ONLY"}
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


def _normalized_access(source_mode: str, access: dict[str, Any]) -> dict[str, Any]:
    explicit_authentication = access.get("authentication_state")
    legacy_logged_in = access.get("user_logged_in")
    if explicit_authentication is None:
        if source_mode == "AUTHENTICATED_READ_ONLY":
            authentication_state = (
                "LOGGED_IN"
                if legacy_logged_in is True
                else "LOGGED_OUT"
                if legacy_logged_in is False
                else "UNKNOWN"
            )
        else:
            authentication_state = "NOT_REQUIRED"
    else:
        authentication_state = explicit_authentication
    if authentication_state not in AUTHENTICATION_STATES:
        raise ValueError(
            "access.authentication_state must be one of: "
            f"{sorted(AUTHENTICATION_STATES)}"
        )

    default_registration = (
        "NOT_REQUIRED" if source_mode in {"UPLOAD", "PUBLIC_WEB"} else "UNKNOWN"
    )
    registration_state = access.get("registration_state", default_registration)
    if registration_state not in REGISTRATION_STATES:
        raise ValueError(
            "access.registration_state must be one of: "
            f"{sorted(REGISTRATION_STATES)}"
        )

    legacy_scope = access.get("authorization_scope")
    authorization_scope = (
        "READ_ONLY" if legacy_scope == "read_only" else legacy_scope or "NONE"
    )
    if authorization_scope not in AUTHORIZATION_SCOPES:
        raise ValueError(
            "access.authorization_scope must be one of: "
            f"{sorted(AUTHORIZATION_SCOPES)}"
        )
    mutation_allowed = access.get("mutation_allowed", False)
    if mutation_allowed is not False:
        raise ValueError("access.mutation_allowed must be false for this read-only skill")
    if authentication_state == "LOGGED_OUT" and authorization_scope == "READ_ONLY":
        raise ValueError(
            "access.authentication_state LOGGED_OUT contradicts READ_ONLY authorization"
        )

    return {
        "source_mode": source_mode,
        "authentication_state": authentication_state,
        "registration_state": registration_state,
        "authorization_scope": authorization_scope,
        "mutation_allowed": False,
    }


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
            "decision_state": "STOP",
            "permitted_actions": ["Draft or revise the candidate profile"],
            "next_actions": ["Ask the user to correct and explicitly approve the profile."],
        }

    source_mode = fair.get("source_mode")
    if source_mode is None:
        return {
            **common,
            "state": "NEED_FAIR_SOURCE",
            "decision_state": "STOP",
            "permitted_actions": ["Explain the four supported source modes"],
            "next_actions": ["Ask for an export, public URL, or user-opened authenticated tab."],
        }
    if source_mode not in SOURCE_MODES:
        raise ValueError(f"fair.source_mode must be one of: {sorted(SOURCE_MODES)}")

    access_state = _normalized_access(source_mode, access)

    platform = fair.get("platform", "generic")
    if not isinstance(platform, str) or not platform:
        raise ValueError("fair.platform must be a non-empty string")
    requires_login = source_mode == "AUTHENTICATED_READ_ONLY"

    if requires_login:
        if access_state["authentication_state"] != "LOGGED_IN":
            return {
                **common,
                "state": "NEED_USER_LOGIN",
                "decision_state": "STOP",
                "access_state": access_state,
                "permitted_actions": ["Ask the user to open Handshake and log in themselves"],
                "next_actions": ["Wait until the user confirms the authenticated tab is open."],
            }
        if access_state["authorization_scope"] != "READ_ONLY":
            return {
                **common,
                "state": "NEED_READ_ONLY_AUTHORIZATION",
                "decision_state": "STOP",
                "access_state": access_state,
                "permitted_actions": ["Ask for permission to inspect the visible authenticated tab"],
                "next_actions": ["Obtain explicit read-only authorization for this fair."],
            }
        permitted = ["Read visible employer, role, and session data"]
    elif source_mode in {"PUBLIC_WEB", "PUBLIC_PREVIEW"}:
        permitted = ["Read public event, employer, role, and session pages"]
    else:
        permitted = ["Read user-supplied exports, documents, screenshots, and text"]

    return {
        **common,
        "state": "READY_FOR_INGESTION",
        "decision_state": "PARTIAL",
        "source_mode": source_mode,
        "access_state": access_state,
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
