#!/usr/bin/env python3
"""Run editable intake and ranking scenario matrices against deterministic logic."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent


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


def _set_path(document: Any, path: str, value: Any) -> None:
    parts = path.split(".")
    target = document
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    last = parts[-1]
    if isinstance(target, list):
        target[int(last)] = value
    else:
        target[last] = value


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
    ranker = _load_module("matrix_rank_battle_plan", SCRIPT_DIR / "rank_battle_plan.py")
    results: list[dict[str, Any]] = []

    for scenario in scenarios:
        kind = scenario.get("kind")
        payload = copy.deepcopy(_base_intake() if kind == "intake" else _base_rank())
        for field, value in scenario.get("changes", {}).items():
            _set_path(payload, field, value)
        try:
            actual = (
                intake.assess_intake(payload)
                if kind == "intake"
                else ranker.build_battle_plan(payload)
            )
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
