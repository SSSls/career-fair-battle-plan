#!/usr/bin/env python3
"""Deterministically rank career-fair opportunities from typed judgments."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


DEFAULT_WEIGHTS = {
    "role_fit": 0.30,
    "evidence_strength": 0.15,
    "conversation_leverage": 0.25,
    "information_gain": 0.15,
    "user_interest": 0.15,
}

SCORE_FIELDS = (
    "role_fit",
    "evidence_strength",
    "conversation_leverage",
    "information_gain",
)


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    return float(value)


def _bounded(value: Any, field: str, minimum: float, maximum: float) -> float:
    result = _number(value, field)
    if not minimum <= result <= maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return result


def _score_value(judgments: dict[str, Any], field: str) -> float:
    answer = judgments.get(field)
    if not isinstance(answer, dict) or answer.get("type") != "score":
        raise ValueError(f"judgments.{field} must be a score answer")
    return _bounded(answer.get("score"), f"judgments.{field}.score", 0, 4) / 4


def _review_flags(
    opportunity: dict[str, Any], confidence_floor: float, needs_sponsorship: bool
) -> list[str]:
    judgments = opportunity.get("judgments", {})
    flags: list[str] = []

    for name, answer in judgments.items():
        if not isinstance(answer, dict):
            flags.append(name)
            continue
        answer_type = answer.get("type")
        if answer_type in {"choice", "score"}:
            confidence = answer.get("confidence")
            if not isinstance(confidence, (int, float)) or confidence < confidence_floor:
                flags.append(name)
        elif answer_type == "noul":
            probability = answer.get("noul")
            if not isinstance(probability, (int, float)):
                flags.append(name)
                continue
            relevant = name != "sponsorship_evidence_supports_eligibility" or needs_sponsorship
            if relevant and probability < 0.35:
                flags.append(f"negative:{name}")
            elif relevant and probability <= 0.65:
                flags.append(name)

    evidence = opportunity.get("evidence", {})
    if not isinstance(evidence, dict):
        raise ValueError("evidence must be an object")
    if evidence.get("session_status") == "unknown":
        flags.append("session_status")
    if needs_sponsorship and evidence.get("sponsorship_status") == "unknown":
        flags.append("sponsorship_status")
    visit_access = evidence.get("visit_access", "unknown")
    if visit_access not in {"verified", "unknown", "unavailable"}:
        raise ValueError("evidence.visit_access must be verified, unknown, or unavailable")
    if visit_access == "unknown":
        flags.append("visit_access")
    eligibility_unknowns = evidence.get("eligibility_unknowns", [])
    if not isinstance(eligibility_unknowns, list) or not all(
        isinstance(item, str) and item for item in eligibility_unknowns
    ):
        raise ValueError("evidence.eligibility_unknowns must be a list of non-empty strings")
    flags.extend(f"eligibility_unknown:{item}" for item in eligibility_unknowns)

    return sorted(set(flags))


def _validate_weights(weights: dict[str, float]) -> None:
    expected = set(DEFAULT_WEIGHTS)
    if set(weights) != expected:
        raise ValueError(f"weights must contain exactly: {sorted(expected)}")
    total = sum(_bounded(value, f"weights.{key}", 0, 1) for key, value in weights.items())
    if not math.isclose(total, 1.0, abs_tol=1e-9):
        raise ValueError("weights must sum to 1.0")


def _profile_policy(profile: dict[str, Any]) -> tuple[dict[str, Any], str]:
    salary = profile.get(
        "salary", {"minimum": None, "currency": "USD", "hard_constraint": False}
    )
    if not isinstance(salary, dict):
        raise ValueError("candidate_profile.salary must be an object")
    minimum = salary.get("minimum")
    if minimum is not None:
        minimum = _bounded(minimum, "candidate_profile.salary.minimum", 0, 1_000_000_000)
    currency = salary.get("currency", "USD")
    if not isinstance(currency, str) or not currency:
        raise ValueError("candidate_profile.salary.currency must be a non-empty string")
    hard_constraint = salary.get("hard_constraint", False)
    if not isinstance(hard_constraint, bool):
        raise ValueError("candidate_profile.salary.hard_constraint must be true or false")
    headcount_importance = profile.get("headcount_importance", "medium")
    if headcount_importance not in {"low", "medium", "high"}:
        raise ValueError("candidate_profile.headcount_importance must be low, medium, or high")
    return {
        "minimum": minimum,
        "currency": currency,
        "hard_constraint": hard_constraint,
    }, headcount_importance


def _structured_policy(
    evidence: dict[str, Any],
    needs_sponsorship: bool,
    salary_policy: dict[str, Any],
    headcount_importance: str,
    field_prefix: str,
) -> tuple[list[str], list[str], list[str]]:
    """Return hard reasons, review flags, and structured evidence IDs."""
    reasons: list[str] = []
    flags: list[str] = []
    evidence_ids: list[str] = []

    sponsorship = evidence.get("sponsorship")
    if sponsorship is not None:
        if not isinstance(sponsorship, dict):
            raise ValueError(f"{field_prefix}.sponsorship must be an object")
        status = sponsorship.get("status")
        scope = sponsorship.get("scope")
        if status not in {"yes", "no", "unknown"}:
            raise ValueError(f"{field_prefix}.sponsorship.status must be yes, no, or unknown")
        if scope not in {"exact_role", "company_current", "company_history"}:
            raise ValueError(
                f"{field_prefix}.sponsorship.scope must be exact_role, company_current, or company_history"
            )
        evidence_id = sponsorship.get("evidence_id")
        if status != "unknown" and evidence_id is None:
            raise ValueError(
                f"{field_prefix}.sponsorship.evidence_id is required for a definite claim"
            )
        if evidence_id is not None:
            if not isinstance(evidence_id, str) or not evidence_id:
                raise ValueError(f"{field_prefix}.sponsorship.evidence_id must be null or non-empty")
            evidence_ids.append(evidence_id)
        if needs_sponsorship:
            if status == "no" and scope == "exact_role":
                reasons.append("exact_role_no_sponsorship")
            elif status == "unknown":
                flags.append("sponsorship_unknown")
            elif scope != "exact_role":
                flags.append("sponsorship_not_exact_role")
    elif needs_sponsorship:
        # Retain legacy fields, but never treat their absence as a verified positive.
        if evidence.get("explicit_no_sponsorship") is not True:
            flags.append("sponsorship_structured_evidence_missing")

    salary = evidence.get("salary")
    if salary is not None:
        if not isinstance(salary, dict):
            raise ValueError(f"{field_prefix}.salary must be an object")
        source_type = salary.get("source_type")
        if source_type not in {
            "official_exact_role",
            "official_company",
            "secondary",
            "unknown",
        }:
            raise ValueError(f"{field_prefix}.salary.source_type is invalid")
        evidence_id = salary.get("evidence_id")
        if source_type != "unknown" and evidence_id is None:
            raise ValueError(
                f"{field_prefix}.salary.evidence_id is required for a sourced claim"
            )
        if evidence_id is not None:
            if not isinstance(evidence_id, str) or not evidence_id:
                raise ValueError(f"{field_prefix}.salary.evidence_id must be null or non-empty")
            evidence_ids.append(evidence_id)
        salary_max = salary.get("max")
        if salary_max is not None:
            salary_max = _bounded(salary_max, f"{field_prefix}.salary.max", 0, 1_000_000_000)
        salary_min = salary.get("min")
        if salary_min is not None:
            _bounded(salary_min, f"{field_prefix}.salary.min", 0, 1_000_000_000)
        if salary_policy["hard_constraint"] and salary_policy["minimum"] is not None:
            if source_type == "unknown" or salary_max is None:
                flags.append("salary_unknown_for_hard_minimum")
            elif salary.get("currency", "USD") != salary_policy["currency"]:
                flags.append("salary_currency_mismatch")
            elif source_type != "official_exact_role":
                flags.append("salary_not_official_exact_role")
            elif salary_max < salary_policy["minimum"]:
                reasons.append("salary_below_hard_minimum")
    elif salary_policy["hard_constraint"] and salary_policy["minimum"] is not None:
        flags.append("salary_unknown_for_hard_minimum")

    headcount = evidence.get("headcount")
    if headcount is not None:
        if not isinstance(headcount, dict):
            raise ValueError(f"{field_prefix}.headcount must be an object")
        status = headcount.get("status")
        if status not in {"confirmed", "likely", "unknown"}:
            raise ValueError(f"{field_prefix}.headcount.status must be confirmed, likely, or unknown")
        evidence_id = headcount.get("evidence_id")
        if status != "unknown" and evidence_id is None:
            raise ValueError(
                f"{field_prefix}.headcount.evidence_id is required for a definite claim"
            )
        if evidence_id is not None:
            if not isinstance(evidence_id, str) or not evidence_id:
                raise ValueError(f"{field_prefix}.headcount.evidence_id must be null or non-empty")
            evidence_ids.append(evidence_id)
        if headcount_importance == "high" and status != "confirmed":
            flags.append("headcount_unknown" if status == "unknown" else "headcount_not_confirmed")
    elif headcount_importance == "high":
        flags.append("headcount_unknown")

    return reasons, flags, evidence_ids


def _subtract_interval(
    free_intervals: list[tuple[float, float]], busy: dict[str, float]
) -> list[tuple[float, float]]:
    remaining: list[tuple[float, float]] = []
    for start, end in free_intervals:
        if busy["end_minute"] <= start or busy["start_minute"] >= end:
            remaining.append((start, end))
            continue
        if start < busy["start_minute"]:
            remaining.append((start, busy["start_minute"]))
        if busy["end_minute"] < end:
            remaining.append((busy["end_minute"], end))
    return remaining


def _allocate_flexible_visit(
    free_intervals: list[tuple[float, float]], minutes: float
) -> tuple[dict[str, float] | None, list[tuple[float, float]]]:
    for index, (start, end) in enumerate(free_intervals):
        if end - start < minutes:
            continue
        assigned = {"start_minute": start, "end_minute": start + minutes}
        updated = list(free_intervals)
        if math.isclose(start + minutes, end):
            updated.pop(index)
        else:
            updated[index] = (start + minutes, end)
        return assigned, updated
    return None, free_intervals


def build_battle_plan(document: dict[str, Any]) -> dict[str, Any]:
    """Return auditable tiers without making any external action."""
    if not isinstance(document, dict):
        raise ValueError("input must be a JSON object")

    profile = document.get("candidate_profile")
    if not isinstance(profile, dict) or profile.get("approved") is not True:
        raise ValueError("candidate_profile must be explicitly approved before ranking")
    needs_sponsorship = profile.get("needs_sponsorship")
    if not isinstance(needs_sponsorship, bool):
        raise ValueError(
            "candidate_profile.needs_sponsorship must be true or false before ranking"
        )
    salary_policy, headcount_importance = _profile_policy(profile)

    fair = document.get("fair")
    if not isinstance(fair, dict):
        raise ValueError("fair must be an object")
    duration = _bounded(fair.get("duration_minutes"), "fair.duration_minutes", 1, 10080)
    reserve = _bounded(fair.get("reserve_minutes", 0), "fair.reserve_minutes", 0, duration)
    per_visit = _bounded(fair.get("minutes_per_visit", 15), "fair.minutes_per_visit", 1, duration)
    total_capacity = max(0, math.floor((duration - reserve) / per_visit))
    must_capacity = math.floor(total_capacity * 0.7)
    if total_capacity > 0:
        must_capacity = max(1, must_capacity)

    supplied_weights = document.get("weights", {})
    if not isinstance(supplied_weights, dict):
        raise ValueError("weights must be an object")
    weights = dict(DEFAULT_WEIGHTS)
    weights.update(supplied_weights)
    _validate_weights(weights)
    confidence_floor = _bounded(
        document.get("confidence_floor", 0.6), "confidence_floor", 0, 1
    )

    opportunities = document.get("opportunities")
    if not isinstance(opportunities, list):
        raise ValueError("opportunities must be a list")

    evidence_records = document.get("evidence_records", [])
    if not isinstance(evidence_records, list):
        raise ValueError("evidence_records must be a list")
    evidence_record_ids: set[str] = set()
    for index, record in enumerate(evidence_records):
        if not isinstance(record, dict):
            raise ValueError(f"evidence_records[{index}] must be an object")
        claim_id = record.get("claim_id")
        claim = record.get("claim")
        if not isinstance(claim_id, str) or not claim_id:
            raise ValueError(f"evidence_records[{index}].claim_id must be a non-empty string")
        if claim_id in evidence_record_ids:
            raise ValueError(f"duplicate evidence claim_id: {claim_id}")
        if not isinstance(claim, str) or not claim:
            raise ValueError(f"evidence_records[{index}].claim must be a non-empty string")
        evidence_record_ids.add(claim_id)

    evaluated: list[dict[str, Any]] = []
    for index, opportunity in enumerate(opportunities):
        if not isinstance(opportunity, dict):
            raise ValueError(f"opportunities[{index}] must be an object")
        judgments = opportunity.get("judgments")
        if not isinstance(judgments, dict):
            raise ValueError(f"opportunities[{index}].judgments must be an object")

        normalized = {field: _score_value(judgments, field) for field in SCORE_FIELDS}
        user_interest = _bounded(
            opportunity.get("user_interest", 0.5),
            f"opportunities[{index}].user_interest",
            0,
            1,
        )
        composite = sum(normalized[field] * weights[field] for field in SCORE_FIELDS)
        composite += user_interest * weights["user_interest"]

        evidence = opportunity.get("evidence", {})
        if not isinstance(evidence, dict):
            raise ValueError(f"opportunities[{index}].evidence must be an object")
        explicit_disqualifiers = evidence.get("explicit_disqualifiers", [])
        if not isinstance(explicit_disqualifiers, list) or not all(
            isinstance(item, str) and item for item in explicit_disqualifiers
        ):
            raise ValueError(
                f"opportunities[{index}].evidence.explicit_disqualifiers "
                "must be a list of non-empty strings"
            )
        policy_reasons, policy_flags, structured_evidence_ids = _structured_policy(
            evidence,
            needs_sponsorship,
            salary_policy,
            headcount_importance,
            f"opportunities[{index}].evidence",
        )
        blocked = bool(explicit_disqualifiers) or bool(policy_reasons) or user_interest == 0
        blocked = blocked or (
            needs_sponsorship and evidence.get("explicit_no_sponsorship") is True
        )
        reasons: list[str] = []
        if needs_sponsorship and evidence.get("explicit_no_sponsorship") is True:
            reasons.append("explicit_no_sponsorship")
        reasons.extend(explicit_disqualifiers)
        reasons.extend(policy_reasons)
        if user_interest == 0:
            reasons.append("user_opt_out")

        evidence_ids = opportunity.get("evidence_ids", [])
        if not isinstance(evidence_ids, list) or not all(
            isinstance(item, str) and item for item in evidence_ids
        ):
            raise ValueError(
                f"opportunities[{index}].evidence_ids must be a list of non-empty strings"
            )
        evidence_ids = list(dict.fromkeys(evidence_ids + structured_evidence_ids))
        missing_evidence = sorted(set(evidence_ids) - evidence_record_ids)
        if missing_evidence:
            raise ValueError(
                f"opportunities[{index}] references missing evidence IDs: "
                + ", ".join(missing_evidence)
            )

        fixed_session = evidence.get("fixed_session")
        if fixed_session is not None:
            if not isinstance(fixed_session, dict):
                raise ValueError(f"opportunities[{index}].evidence.fixed_session must be an object")
            start = _bounded(
                fixed_session.get("start_minute"),
                f"opportunities[{index}].evidence.fixed_session.start_minute",
                0,
                duration,
            )
            end = _bounded(
                fixed_session.get("end_minute"),
                f"opportunities[{index}].evidence.fixed_session.end_minute",
                0,
                duration,
            )
            if end <= start:
                raise ValueError(
                    f"opportunities[{index}].evidence.fixed_session.end_minute must exceed start_minute"
                )
            fixed_session = {"start_minute": start, "end_minute": end}

        review_flags = sorted(
            set(_review_flags(opportunity, confidence_floor, needs_sponsorship) + policy_flags)
        )
        critical_names = set(SCORE_FIELDS) | {
            "best_area",
            "visit_access",
            "entry_level_accessible",
            "background_pathway_accessible",
        }
        requires_review = any(
            flag in critical_names
            or flag.startswith("negative:")
            or flag.startswith("eligibility_unknown:")
            or (
                needs_sponsorship
                and flag
                in {
                    "sponsorship_status",
                    "sponsorship_evidence_supports_eligibility",
                }
            )
            or flag
            in {
                "sponsorship_unknown",
                "sponsorship_not_exact_role",
                "sponsorship_structured_evidence_missing",
                "salary_unknown_for_hard_minimum",
                "salary_currency_mismatch",
                "salary_not_official_exact_role",
                "headcount_unknown",
                "headcount_not_confirmed",
            }
            for flag in review_flags
        )

        evaluated.append(
            {
                "company": opportunity.get("company", "unknown"),
                "role": opportunity.get("role", "unknown"),
                "best_area": judgments.get("best_area", {}).get("choice", "other"),
                "visit_score": round(composite * 100, 1),
                "normalized_dimensions": {
                    **{key: round(value, 4) for key, value in normalized.items()},
                    "user_interest": user_interest,
                },
                "review_flags": review_flags,
                "reasons": reasons,
                "evidence_ids": evidence_ids,
                "blocked": blocked,
                "_fixed_session": fixed_session,
                "_requires_review": requires_review,
                "_visit_access": evidence.get("visit_access", "unknown"),
                "_role_fit": normalized["role_fit"],
                "_conversation_leverage": normalized["conversation_leverage"],
            }
        )

    evaluated.sort(key=lambda item: (-item["visit_score"], item["company"], item["role"]))

    visit_candidates: list[dict[str, Any]] = []
    for item in evaluated:
        if item["blocked"]:
            item["tier"] = "SKIP"
        elif item["_visit_access"] == "unavailable":
            item["tier"] = "APPLY_ONLINE"
        elif item["_role_fit"] >= 0.75 and item["_conversation_leverage"] < 0.5:
            item["tier"] = "APPLY_ONLINE"
        elif item["visit_score"] >= 55 and item["_conversation_leverage"] >= 0.5:
            visit_candidates.append(item)
        elif item["_role_fit"] >= 0.5:
            item["tier"] = "APPLY_ONLINE"
        else:
            item["tier"] = "SKIP"

    usable_end = duration - reserve
    free_intervals: list[tuple[float, float]] = [(0.0, usable_end)] if usable_end > 0 else []
    scheduled_candidates: list[dict[str, Any]] = []

    for item in [candidate for candidate in visit_candidates if candidate["_fixed_session"]]:
        interval = item["_fixed_session"]
        fits_window = interval["end_minute"] <= usable_end
        fits_free_interval = any(
            start <= interval["start_minute"] and interval["end_minute"] <= end
            for start, end in free_intervals
        )
        if not fits_window or not fits_free_interval:
            item["tier"] = "APPLY_ONLINE"
            item["review_flags"].append(
                "schedule_conflict" if fits_window else "no_schedule_capacity"
            )
            continue
        item["_assigned_session"] = interval
        free_intervals = _subtract_interval(free_intervals, interval)
        scheduled_candidates.append(item)

    for item in [candidate for candidate in visit_candidates if not candidate["_fixed_session"]]:
        assigned, free_intervals = _allocate_flexible_visit(free_intervals, per_visit)
        if assigned is None:
            item["tier"] = "APPLY_ONLINE"
            item["review_flags"].append("no_schedule_capacity")
            continue
        item["_assigned_session"] = assigned
        scheduled_candidates.append(item)

    used_must_slots = 0
    for item in sorted(
        scheduled_candidates,
        key=lambda candidate: (-candidate["visit_score"], candidate["company"], candidate["role"]),
    ):
        if item["_requires_review"]:
            item["tier"] = "IF_TIME"
        elif used_must_slots < must_capacity:
            item["tier"] = "MUST_VISIT"
            used_must_slots += 1
        else:
            item["tier"] = "IF_TIME"

    tier_order = {"MUST_VISIT": 0, "IF_TIME": 1, "APPLY_ONLINE": 2, "SKIP": 3}
    evaluated.sort(
        key=lambda item: (tier_order[item["tier"]], -item["visit_score"], item["company"], item["role"])
    )
    visit_schedule = []
    for item in evaluated:
        if item["tier"] in {"MUST_VISIT", "IF_TIME"} and item.get("_assigned_session"):
            visit_schedule.append(
                {
                    "company": item["company"],
                    "role": item["role"],
                    "fixed": item["_fixed_session"] is not None,
                    **item["_assigned_session"],
                }
            )
        item.pop("blocked")
        item.pop("_fixed_session")
        item.pop("_requires_review")
        item.pop("_assigned_session", None)
        item.pop("_visit_access")
        item.pop("_role_fit")
        item.pop("_conversation_leverage")

    return {
        "capacity": {
            "total_visits": total_capacity,
            "must_visit_limit": must_capacity,
            "duration_minutes": duration,
            "reserve_minutes": reserve,
            "minutes_per_visit": per_visit,
        },
        "weights": weights,
        "visit_schedule": sorted(visit_schedule, key=lambda item: item["start_minute"]),
        "external_actions_require_confirmation": True,
        "opportunities": evaluated,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Input JSON document")
    parser.add_argument("-o", "--output", type=Path, help="Write output JSON to this path")
    args = parser.parse_args(argv)

    try:
        document = json.loads(args.input.read_text(encoding="utf-8"))
        result = build_battle_plan(document)
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
