#!/usr/bin/env python3
"""Run editable intake and ranking scenario matrices against deterministic logic."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise ValueError(f"cannot load {path}")
    spec.loader.exec_module(module)
    return module


def _base_intake() -> dict[str, Any]:
    return {
        "candidate_profile": {
            "approved": True,
            "cv_present": True,
            "school": "Example University",
            "degree": "MS",
            "graduation_date": "2027-05",
            "role_types": ["internship"],
            "target_areas": ["backend-swe"],
            "needs_sponsorship": False,
            "work_authorization": "authorized",
            "locations": ["New York"],
            "salary": {"minimum": None, "currency": "USD", "hard_constraint": False},
            "headcount_importance": "medium",
            "background_type": "traditional",
        },
        "fair": {
            "name": "Example Fair",
            "platform": "generic",
            "date": "2026-10-01",
            "timezone": "America/New_York",
            "format": "virtual",
            "url": "https://example.edu/fair",
            "source_mode": "UPLOAD",
            "company_list_present": True,
            "role_data_present": True,
            "session_data_present": True,
        },
        "access": {
            "user_logged_in": False,
            "authorization_scope": None,
            "credentials_shared": False,
        },
    }


def _base_opportunity(company: str = "Example Co") -> dict[str, Any]:
    return {
        "company": company,
        "role": "Software Intern",
        "user_interest": 1.0,
        "evidence": {"session_status": "verified", "visit_access": "verified"},
        "judgments": {
            "role_fit": {"type": "score", "score": 4, "confidence": 0.9},
            "evidence_strength": {"type": "score", "score": 4, "confidence": 0.9},
            "conversation_leverage": {"type": "score", "score": 4, "confidence": 0.9},
            "information_gain": {"type": "score", "score": 3, "confidence": 0.9},
            "best_area": {"type": "choice", "choice": "backend-swe", "confidence": 0.9},
            "sponsorship_evidence_supports_eligibility": {"type": "noul", "noul": 0.8},
        },
    }


def _base_rank() -> dict[str, Any]:
    return {
        "candidate_profile": {
            "approved": True,
            "needs_sponsorship": False,
            "salary": {"minimum": None, "currency": "USD", "hard_constraint": False},
            "headcount_importance": "medium",
        },
        "fair": {"duration_minutes": 180, "reserve_minutes": 30, "minutes_per_visit": 15},
        "evidence_records": [
            {"claim_id": "sponsor-exact-no", "claim": "Exact role says no sponsorship."},
            {"claim_id": "sponsor-history", "claim": "Company sponsored historically."},
            {"claim_id": "salary-official", "claim": "Official exact-role salary range."},
            {"claim_id": "hc-confirmed", "claim": "Employer confirmed active headcount."},
        ],
        "opportunities": [_base_opportunity()],
    }


def _base_normalize() -> dict[str, Any]:
    return {
        "adapter": "handshake_public_preview",
        "accessed_at": "2026-09-25",
        "source_url": "https://fixtures.invalid/fair-preview",
        "advertised_employer_count": 2,
        "employers": [
            {
                "name": "Example Co",
                "job_titles": ["Software Intern"],
                "work_authorization_text": "Employer is willing to sponsor candidates",
                "session_count": 1,
            }
        ],
    }


def _base_jev_plan() -> dict[str, Any]:
    return {
        "candidate_profile": {
            "approved": True,
            "needs_sponsorship": False,
            "background_transition": "none",
            "target_areas": ["backend-swe", "data-engineering"],
            "demonstrated_strengths": ["Python APIs"],
            "career_stage": "student",
            "hard_constraints": {},
        },
        "opportunities": [
            {
                "company": "Example Co",
                "role": "Software Intern",
                "prefilter_state": "SURVIVES",
                "evidence_level": "EXACT_ROLE",
                "evidence_records": [
                    {
                        "scope": "exact_role",
                        "field": "role",
                        "status": "yes",
                        "source_quality": "primary",
                    }
                ],
                "career_stage_clear": True,
                "material_unknowns": [],
                "conversation_channel": "unavailable",
                "exact_role_sponsorship": "not_needed",
            }
        ],
    }


def _base_jev_validate(validator: Any) -> dict[str, Any]:
    request = {
        "state": {"candidate": {"approved_areas": ["backend-swe"]}},
        "questions": [
            {
                "name": "best_area",
                "type": "choice",
                "options": ["backend-swe", "other"],
            }
        ],
    }
    return {
        "request": request,
        "result": {
            "request_hash": validator.compute_request_hash(request),
            "provenance": "fixture",
            "answers": {
                "best_area": {
                    "type": "choice",
                    "choice": "backend-swe",
                    "confidence": 0.9,
                }
            },
            "observed_at": None,
            "cached_at": None,
            "telemetry": {
                "provider": None,
                "model": None,
                "request_count": 0,
                "question_count": 1,
                "latency_ms": 0,
                "retry_count": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0,
            },
        },
    }


def _run_regression_fixture(
    payload: dict[str, Any], modules: dict[str, Any]
) -> dict[str, Any]:
    case_id = payload.get("case_id")
    if case_id in {"domestic-public-preview", "sponsor-public-preview"}:
        normalized = modules["normalize"].normalize_source(payload["source"])
        sponsor_scopes = sorted(
            {
                record["scope"]
                for record in normalized["evidence_records"]
                if record["field"] == "sponsorship"
            }
        )
        return {
            "decision_state": "PARTIAL",
            "visit_schedule": [],
            "coverage_complete": normalized["coverage"]["complete"],
            "sponsorship_scopes": sponsor_scopes,
        }
    if case_id == "high-evidence":
        rank_input = {
            "candidate_profile": {
                **payload["candidate_profile"],
                "salary": {"minimum": None, "currency": "USD", "hard_constraint": False},
                "headcount_importance": "medium",
            },
            "fair": payload["fair"],
            "opportunities": payload["opportunities"],
            "evidence_records": [],
        }
        plan = modules["rank"].build_battle_plan(rank_input)
        return {
            "decision_state": "FULL",
            "scheduled_companies": [item["company"] for item in plan["visit_schedule"]],
            "unscheduled_companies": [
                item["company"]
                for item in plan["opportunities"]
                if item["route_action"] != "VISIT"
            ],
        }
    if case_id == "transition-sponsor":
        return modules["jev_plan"].build_jev_plan(
            {
                "candidate_profile": payload["candidate_profile"],
                "opportunities": payload["opportunities"],
            }
        )
    if case_id == "sparse-ambiguous":
        return modules["readiness"].build_decision_readiness(
            {"evidence_level": "EMPLOYER_NAME", "visit_access": "unknown"},
            payload["candidate_profile"],
        )
    if case_id == "jev-baseline":
        request = payload["request"]
        result = copy.deepcopy(payload["result"])
        result["request_hash"] = modules["jev_validate"].compute_request_hash(request)
        return modules["jev_validate"].validate_jev_result(request, result)
    raise ValueError(f"unsupported regression fixture: {case_id}")


def _set_path(document: Any, path: str, value: Any) -> None:
    parts = path.split(".")
    target = document
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    last = parts[-1]
    if isinstance(target, list):
        index = int(last)
        if index == len(target):
            target.append(value)
        else:
            target[index] = value
    else:
        target[last] = value


def _replace_sentinels(value: Any) -> Any:
    if value == "__NOW__":
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, list):
        return [_replace_sentinels(item) for item in value]
    if isinstance(value, dict):
        return {key: _replace_sentinels(item) for key, item in value.items()}
    return value


def _get_path(document: Any, path: str) -> Any:
    target = document
    for part in path.split("."):
        target = target[int(part)] if isinstance(target, list) else target[part]
    return target


def _check(actual: dict[str, Any], check: dict[str, Any]) -> tuple[bool, str]:
    path = check["path"]
    value = _get_path(actual, path)
    if "equals" in check:
        passed = value == check["equals"]
        return passed, f"{path} == {check['equals']!r}; actual={value!r}"
    if "contains" in check:
        passed = check["contains"] in value
        return passed, f"{path} contains {check['contains']!r}; actual={value!r}"
    raise ValueError("each check must contain equals or contains")


def run_matrix(path: Path) -> dict[str, Any]:
    matrix = json.loads(path.read_text(encoding="utf-8"))
    scenarios = matrix.get("scenarios")
    if not isinstance(scenarios, list):
        raise ValueError("scenarios must be a list")
    intake = _load_module("matrix_assess_intake", SCRIPT_DIR / "assess_intake.py")
    normalizer = _load_module("matrix_normalize_source", SCRIPT_DIR / "normalize_source.py")
    planner = _load_module("matrix_plan_jev", SCRIPT_DIR / "plan_jev_requests.py")
    validator = _load_module("matrix_validate_jev", SCRIPT_DIR / "validate_jev_results.py")
    readiness = _load_module("matrix_readiness", SCRIPT_DIR / "decision_readiness.py")
    ranker = _load_module("matrix_rank_battle_plan", SCRIPT_DIR / "rank_battle_plan.py")
    modules = {
        "intake": intake,
        "normalize": normalizer,
        "jev_plan": planner,
        "jev_validate": validator,
        "readiness": readiness,
        "rank": ranker,
    }
    runners = {
        "intake": lambda payload: intake.assess_intake(payload),
        "normalize": lambda payload: normalizer.normalize_source(payload),
        "jev_plan": lambda payload: planner.build_jev_plan(payload),
        "jev_validate": lambda payload: validator.validate_jev_result(
            payload["request"], payload["result"]
        ),
        "rank": lambda payload: ranker.build_battle_plan(payload),
        "regression": lambda payload: _run_regression_fixture(payload, modules),
    }
    base_factories = {
        "intake": _base_intake,
        "normalize": _base_normalize,
        "jev_plan": _base_jev_plan,
        "jev_validate": lambda: _base_jev_validate(validator),
        "rank": _base_rank,
    }
    results: list[dict[str, Any]] = []

    for scenario in scenarios:
        kind = scenario.get("kind")
        if kind not in runners:
            raise ValueError(f"unsupported scenario kind: {kind}")
        if "fixture" in scenario:
            fixture_path = REPO_ROOT / scenario["fixture"]
            payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        elif "payload" in scenario:
            payload = copy.deepcopy(scenario["payload"])
        elif kind in base_factories:
            payload = copy.deepcopy(base_factories[kind]())
        else:
            raise ValueError(f"scenario {scenario.get('id')} requires fixture or payload")
        for field, value in scenario.get("changes", {}).items():
            _set_path(payload, field, value)
        payload = _replace_sentinels(payload)
        try:
            actual = runners[kind](payload)
            if "expected_error" in scenario:
                passed = False
                details = ["expected an error but execution succeeded"]
            else:
                checked = [_check(actual, check) for check in scenario.get("checks", [])]
                passed = all(item[0] for item in checked)
                details = [item[1] for item in checked]
        except ValueError as exc:
            expected_error = scenario.get("expected_error")
            passed = isinstance(expected_error, str) and expected_error in str(exc)
            details = [f"error={exc}"]
            actual = {"error": str(exc)}
        results.append(
            {
                "id": scenario.get("id"),
                "description": scenario.get("description"),
                "kind": kind,
                "changes": scenario.get("changes", {}),
                "passed": passed,
                "details": details,
                "actual": actual,
            }
        )

    passed_count = sum(result["passed"] for result in results)
    return {
        "summary": {
            "total": len(results),
            "passed": passed_count,
            "failed": len(results) - passed_count,
        },
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = run_matrix(args.matrix)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
