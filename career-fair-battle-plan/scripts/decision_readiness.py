#!/usr/bin/env python3
"""Calculate evidence-scoped decision readiness without changing source facts."""

from __future__ import annotations

from typing import Any


MATCH_CONFIDENCE_CAPS = {
    "EMPLOYER_NAME": 0.35,
    "EMPLOYER_CARD": 0.49,
    "TITLE_ONLY": 0.59,
    "EXACT_ROLE": 1.0,
    "SESSION_VERIFIED": 1.0,
}
EVIDENCE_CONFIDENCE = {
    "EMPLOYER_NAME": 0.35,
    "EMPLOYER_CARD": 0.49,
    "TITLE_ONLY": 0.59,
    "EXACT_ROLE": 0.90,
    "SESSION_VERIFIED": 0.95,
}
CAP_LABELS = {
    "EMPLOYER_NAME": "employer_name_cap",
    "EMPLOYER_CARD": "employer_card_cap",
    "TITLE_ONLY": "title_only_cap",
}
VERIFIED_ROUTE_CONFIDENCE = 0.80
PRIORITY_SCORE_THRESHOLD = 3.0


def _bounded(value: Any, field: str, minimum: float = 0.0, maximum: float = 1.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    result = float(value)
    if not minimum <= result <= maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return result


def _stop(reason: str) -> dict[str, Any]:
    return {
        "decision_state": "STOP",
        "evidence_confidence": 0.0,
        "match_confidence": 0.0,
        "visit_access_confidence": 0.0,
        "decision_confidence": 0.0,
        "route_ready": False,
        "confidence_caps": [],
        "review_flags": [reason],
    }


def _role_fit_confidence(
    judgments: dict[str, Any], review_flags: list[str]
) -> float:
    role_fit = judgments.get("role_fit")
    if role_fit is None:
        review_flags.append("role_fit_missing")
        return 0.0
    if not isinstance(role_fit, dict) or role_fit.get("type") != "score":
        raise ValueError("judgments.role_fit must be a score answer")
    _bounded(role_fit.get("score"), "judgments.role_fit.score", 0.0, 4.0)
    confidence = _bounded(
        role_fit.get("confidence"), "judgments.role_fit.confidence"
    )
    score_range = role_fit.get("score_range")
    if score_range is not None:
        if (
            not isinstance(score_range, list)
            or len(score_range) != 2
        ):
            raise ValueError("judgments.role_fit.score_range must contain two values")
        lower = _bounded(
            score_range[0], "judgments.role_fit.score_range[0]", 0.0, 4.0
        )
        upper = _bounded(
            score_range[1], "judgments.role_fit.score_range[1]", 0.0, 4.0
        )
        if lower > upper:
            raise ValueError("judgments.role_fit.score_range must be ordered")
        if lower < PRIORITY_SCORE_THRESHOLD <= upper:
            review_flags.append("range_crosses_priority_threshold:role_fit")
    return confidence


def build_decision_readiness(
    opportunity: dict[str, Any], candidate_profile: dict[str, Any]
) -> dict[str, Any]:
    """Return decision state, independent confidences, caps, and review flags."""
    if not isinstance(opportunity, dict):
        raise ValueError("opportunity must be an object")
    if not isinstance(candidate_profile, dict):
        raise ValueError("candidate_profile must be an object")
    if candidate_profile.get("approved") is not True:
        return _stop("candidate_profile_not_approved")
    if not isinstance(candidate_profile.get("needs_sponsorship"), bool):
        return _stop("needs_sponsorship_unresolved")

    evidence_level = opportunity.get("evidence_level", "EMPLOYER_NAME")
    if evidence_level not in MATCH_CONFIDENCE_CAPS:
        raise ValueError(f"invalid evidence_level: {evidence_level}")
    review_flags: list[str] = []
    confidence_caps: list[str] = []
    evidence_confidence = EVIDENCE_CONFIDENCE[evidence_level]
    judgments = opportunity.get("judgments", {})
    if not isinstance(judgments, dict):
        raise ValueError("opportunity.judgments must be an object")
    raw_match_confidence = _role_fit_confidence(judgments, review_flags)
    match_confidence = min(raw_match_confidence, MATCH_CONFIDENCE_CAPS[evidence_level])
    cap_label = CAP_LABELS.get(evidence_level)
    if cap_label:
        confidence_caps.append(cap_label)

    unresolved_hard_facts = opportunity.get("unresolved_hard_facts", [])
    if not isinstance(unresolved_hard_facts, list) or not all(
        isinstance(item, str) and item for item in unresolved_hard_facts
    ):
        raise ValueError("opportunity.unresolved_hard_facts must be a list of strings")
    if evidence_level in {"EXACT_ROLE", "SESSION_VERIFIED"} and unresolved_hard_facts:
        match_confidence = min(match_confidence, 0.79)
        confidence_caps.append("unresolved_hard_facts_cap")
        review_flags.extend(f"hard_fact_unknown:{item}" for item in unresolved_hard_facts)

    visit_access = opportunity.get("visit_access", "unknown")
    if visit_access not in {"verified", "unknown", "unavailable"}:
        raise ValueError("opportunity.visit_access must be verified, unknown, or unavailable")
    default_access_confidence = {
        "verified": 0.90,
        "unknown": 0.20,
        "unavailable": 0.90,
    }[visit_access]
    visit_access_confidence = _bounded(
        opportunity.get("visit_access_confidence", default_access_confidence),
        "opportunity.visit_access_confidence",
    )
    route_ready = (
        evidence_level == "SESSION_VERIFIED"
        and visit_access == "verified"
        and visit_access_confidence >= VERIFIED_ROUTE_CONFIDENCE
    )
    if visit_access == "verified" and visit_access_confidence < VERIFIED_ROUTE_CONFIDENCE:
        review_flags.append("visit_access_below_verified_threshold")
    elif visit_access == "unknown":
        review_flags.append("visit_access_unknown")

    decision_state = (
        "FULL" if evidence_level in {"EXACT_ROLE", "SESSION_VERIFIED"} else "PARTIAL"
    )
    decision_confidence = min(evidence_confidence, match_confidence)
    return {
        "decision_state": decision_state,
        "evidence_confidence": round(evidence_confidence, 4),
        "match_confidence": round(match_confidence, 4),
        "visit_access_confidence": round(visit_access_confidence, 4),
        "decision_confidence": round(decision_confidence, 4),
        "route_ready": route_ready,
        "confidence_caps": sorted(set(confidence_caps)),
        "review_flags": sorted(set(review_flags)),
    }
