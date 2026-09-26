#!/usr/bin/env python3
"""Build minimal, typed Jev request plans after deterministic prefiltering."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCORE_QUESTIONS = {
    "role_fit": "How strongly does this role fit the approved candidate profile?",
    "evidence_strength": "How strongly does the supplied evidence support the match?",
    "conversation_leverage": "How much can a fair conversation improve this candidate's outcome?",
    "information_gain": "How much useful uncertainty could this interaction resolve?",
}
NOUL_QUESTIONS = {
    "entry_level_accessible": "Is this opportunity realistically accessible at the candidate's career stage?",
    "background_pathway_accessible": "Is the candidate's background transition a plausible pathway into this role?",
    "sponsorship_evidence_supports_eligibility": "Does the evidence support sponsorship eligibility for this exact role?",
}


def _non_empty_strings(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValueError(f"{field} must be a non-empty list of strings")
    return [item.strip() for item in value]


def _question_names(profile: dict[str, Any], opportunity: dict[str, Any]) -> list[str]:
    names = ["best_area", "role_fit"]
    if opportunity.get("evidence_records"):
        names.append("evidence_strength")
    if opportunity.get("conversation_channel") in {"verified", "plausible"}:
        names.append("conversation_leverage")
    if opportunity.get("material_unknowns"):
        names.append("information_gain")
    if not opportunity.get("career_stage_clear", False):
        names.append("entry_level_accessible")
    if profile.get("background_transition") in {"adjacent", "major"}:
        names.append("background_pathway_accessible")
    if (
        profile["needs_sponsorship"]
        and opportunity.get("exact_role_sponsorship") == "unknown"
    ):
        names.append("sponsorship_evidence_supports_eligibility")
    return names


def _build_question(name: str, areas: list[str]) -> dict[str, Any]:
    if name == "best_area":
        return {
            "name": name,
            "type": "choice",
            "prompt": "Which approved target area best matches this opportunity?",
            "options": list(dict.fromkeys(areas + ["other"])),
        }
    if name in SCORE_QUESTIONS:
        return {
            "name": name,
            "type": "score",
            "prompt": SCORE_QUESTIONS[name],
            "minimum": 0,
            "maximum": 4,
        }
    if name in NOUL_QUESTIONS:
        return {
            "name": name,
            "type": "noul",
            "prompt": NOUL_QUESTIONS[name],
        }
    raise ValueError(f"unsupported Jev question: {name}")


def _evidence_summary(records: Any) -> list[dict[str, Any]]:
    if records is None:
        return []
    if not isinstance(records, list):
        raise ValueError("opportunity.evidence_records must be a list")
    summary: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"opportunity.evidence_records[{index}] must be an object")
        summary.append(
            {
                "scope": record.get("scope", "unverified"),
                "field": record.get("field", "unknown"),
                "status": record.get("status", "unknown"),
                "source_quality": record.get("source_quality", "unverified"),
            }
        )
    return summary


def _condensed_state(
    profile: dict[str, Any], opportunity: dict[str, Any], areas: list[str]
) -> dict[str, Any]:
    strengths = profile.get("demonstrated_strengths", [])
    if not isinstance(strengths, list):
        raise ValueError("candidate_profile.demonstrated_strengths must be a list")
    hard_constraints = profile.get("hard_constraints", {})
    if not isinstance(hard_constraints, dict):
        raise ValueError("candidate_profile.hard_constraints must be an object")
    material_unknowns = opportunity.get("material_unknowns", [])
    if not isinstance(material_unknowns, list):
        raise ValueError("opportunity.material_unknowns must be a list")
    return {
        "candidate": {
            "approved_areas": areas,
            "demonstrated_strengths": strengths,
            "background_transition": profile.get("background_transition", "unknown"),
            "career_stage": profile.get("career_stage", "unknown"),
            "hard_constraints": {
                **hard_constraints,
                "needs_sponsorship": profile["needs_sponsorship"],
            },
        },
        "opportunity": {
            "company": opportunity.get("company", "unknown"),
            "role": opportunity.get("role", "unknown"),
            "evidence_level": opportunity.get("evidence_level", "EMPLOYER_NAME"),
            "evidence_summary": _evidence_summary(
                opportunity.get("evidence_records", [])
            ),
            "material_unknowns": material_unknowns,
            "conversation_channel": opportunity.get(
                "conversation_channel", "unknown"
            ),
        },
    }


def build_jev_plan(document: dict[str, Any]) -> dict[str, Any]:
    """Return typed requests without claiming an unobserved provider call."""
    if not isinstance(document, dict):
        raise ValueError("input must be a JSON object")
    profile = document.get("candidate_profile")
    opportunities = document.get("opportunities")
    if not isinstance(profile, dict):
        raise ValueError("candidate_profile must be an object")
    if not isinstance(opportunities, list):
        raise ValueError("opportunities must be a list")
    if profile.get("approved") is not True or not isinstance(
        profile.get("needs_sponsorship"), bool
    ):
        return {
            "state": "STOP",
            "provider": None,
            "model": None,
            "request_count": 0,
            "question_count": 0,
            "requests": [],
        }
    areas = _non_empty_strings(profile.get("target_areas"), "candidate_profile.target_areas")
    requests: list[dict[str, Any]] = []
    for index, opportunity in enumerate(opportunities):
        if not isinstance(opportunity, dict):
            raise ValueError(f"opportunities[{index}] must be an object")
        prefilter_state = opportunity.get("prefilter_state", "SURVIVES")
        if prefilter_state not in {"BLOCKED", "SURVIVES"}:
            raise ValueError(f"opportunities[{index}].prefilter_state is invalid")
        if prefilter_state == "BLOCKED":
            continue
        names = _question_names(profile, opportunity)
        questions = [_build_question(name, areas) for name in names]
        company = opportunity.get("company", "unknown")
        role = opportunity.get("role", "unknown")
        requests.append(
            {
                "request_id": f"opportunity-{index + 1}",
                "subject": {"company": company, "role": role},
                "state": _condensed_state(profile, opportunity, areas),
                "questions": questions,
            }
        )
    return {
        "state": "READY_FOR_JEV" if requests else "NOT_NEEDED",
        "provider": None,
        "model": None,
        "request_count": len(requests),
        "question_count": sum(len(request["questions"]) for request in requests),
        "requests": requests,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args(argv)
    try:
        document = json.loads(args.input.read_text(encoding="utf-8"))
        result = build_jev_plan(document)
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
