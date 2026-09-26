#!/usr/bin/env python3
"""Validate Jev result typing, provenance, cache identity, and telemetry."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PROVENANCE_VALUES = {"live", "fixture", "fallback", "cache"}
TELEMETRY_FIELDS = (
    "request_count",
    "question_count",
    "latency_ms",
    "retry_count",
    "input_tokens",
    "output_tokens",
    "cost_usd",
)
CACHE_MAX_AGE = timedelta(days=7)


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    return float(value)


def _bounded(value: Any, field: str, minimum: float, maximum: float) -> float:
    result = _number(value, field)
    if not minimum <= result <= maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return result


def _ordered_range(
    value: Any, field: str, minimum: float, maximum: float
) -> list[float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{field} must contain two values")
    lower = _bounded(value[0], f"{field}[0]", minimum, maximum)
    upper = _bounded(value[1], f"{field}[1]", minimum, maximum)
    if lower > upper:
        raise ValueError(f"{field} must be ordered")
    return [lower, upper]


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be an ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def compute_request_hash(request: dict[str, Any]) -> str:
    """Return a stable hash of only the state and ordered question contract."""
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    if "state" not in request or "questions" not in request:
        raise ValueError("request must contain state and questions")
    normalized = {"state": request["state"], "questions": request["questions"]}
    encoded = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_choice(question: dict[str, Any], answer: dict[str, Any], field: str) -> None:
    options = question.get("options")
    if not isinstance(options, list) or not all(isinstance(item, str) for item in options):
        raise ValueError(f"{field} question options must be strings")
    if answer.get("choice") not in options:
        raise ValueError(f"{field}.choice must be one of the question options")
    _bounded(answer.get("confidence"), f"{field}.confidence", 0, 1)
    if "confidence_range" in answer:
        _ordered_range(answer["confidence_range"], f"{field}.confidence_range", 0, 1)


def _validate_score(question: dict[str, Any], answer: dict[str, Any], field: str) -> None:
    minimum = _number(question.get("minimum"), f"{field}.question.minimum")
    maximum = _number(question.get("maximum"), f"{field}.question.maximum")
    if minimum >= maximum:
        raise ValueError(f"{field} question score bounds are invalid")
    _bounded(answer.get("score"), f"{field}.score", minimum, maximum)
    _bounded(answer.get("confidence"), f"{field}.confidence", 0, 1)
    if "score_range" in answer:
        _ordered_range(answer["score_range"], f"{field}.score_range", minimum, maximum)
    if "confidence_range" in answer:
        _ordered_range(answer["confidence_range"], f"{field}.confidence_range", 0, 1)


def _validate_noul(answer: dict[str, Any], field: str) -> None:
    _bounded(answer.get("noul"), f"{field}.noul", 0, 1)
    if "probability_range" in answer:
        _ordered_range(answer["probability_range"], f"{field}.probability_range", 0, 1)


def _validate_answers(request: dict[str, Any], answers: Any) -> None:
    questions = request.get("questions")
    if not isinstance(questions, list):
        raise ValueError("request.questions must be a list")
    if not isinstance(answers, dict):
        raise ValueError("result.answers must be an object")
    question_by_name: dict[str, dict[str, Any]] = {}
    for index, question in enumerate(questions):
        if not isinstance(question, dict):
            raise ValueError(f"request.questions[{index}] must be an object")
        name = question.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError(f"request.questions[{index}].name must be a string")
        if name in question_by_name:
            raise ValueError(f"duplicate question name: {name}")
        question_by_name[name] = question
    missing = sorted(set(question_by_name) - set(answers))
    extra = sorted(set(answers) - set(question_by_name))
    if missing:
        raise ValueError("missing answers: " + ", ".join(missing))
    if extra:
        raise ValueError("extra answers: " + ", ".join(extra))
    for name, question in question_by_name.items():
        answer = answers[name]
        if not isinstance(answer, dict):
            raise ValueError(f"answers.{name} must be an object")
        expected_type = question.get("type")
        if answer.get("type") != expected_type:
            raise ValueError(f"answers.{name}.type must be {expected_type}")
        if expected_type == "choice":
            _validate_choice(question, answer, f"answers.{name}")
        elif expected_type == "score":
            _validate_score(question, answer, f"answers.{name}")
        elif expected_type == "noul":
            _validate_noul(answer, f"answers.{name}")
        else:
            raise ValueError(f"unsupported question type: {expected_type}")


def _validate_telemetry(
    telemetry: Any, provenance: str, question_count: int
) -> dict[str, Any]:
    if not isinstance(telemetry, dict):
        raise ValueError("result.telemetry must be an object")
    provider = telemetry.get("provider")
    model = telemetry.get("model")
    if provenance == "live":
        if not isinstance(provider, str) or not provider:
            raise ValueError("live telemetry.provider is required")
        if not isinstance(model, str) or not model:
            raise ValueError("live telemetry.model is required")
    elif provenance in {"fixture", "fallback"} and (provider is not None or model is not None):
        raise ValueError(f"{provenance} result cannot claim a live provider or model")
    normalized = dict(telemetry)
    for field in TELEMETRY_FIELDS:
        value = telemetry.get(field, 0)
        if field in {"request_count", "question_count", "retry_count", "input_tokens", "output_tokens"}:
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"telemetry.{field} must be a non-negative integer")
        else:
            _bounded(value, f"telemetry.{field}", 0, float("inf"))
        normalized[field] = value
    if normalized["question_count"] != question_count:
        raise ValueError("telemetry.question_count must match request questions")
    return normalized


def validate_jev_result(
    request: dict[str, Any], result: dict[str, Any]
) -> dict[str, Any]:
    """Validate a result without converting judgments into source evidence."""
    if not isinstance(result, dict):
        raise ValueError("result must be an object")
    expected_hash = compute_request_hash(request)
    if result.get("request_hash") != expected_hash:
        raise ValueError("result.request_hash does not match the normalized request")
    provenance = result.get("provenance")
    if provenance not in PROVENANCE_VALUES:
        raise ValueError(f"result.provenance must be one of: {sorted(PROVENANCE_VALUES)}")
    if provenance == "live":
        _timestamp(result.get("observed_at"), "result.observed_at")
    if provenance == "cache":
        cached_at = _timestamp(result.get("cached_at"), "result.cached_at")
        now = datetime.now(timezone.utc)
        if cached_at > now + timedelta(minutes=5) or now - cached_at > CACHE_MAX_AGE:
            raise ValueError("cached Jev result is stale")
    _validate_answers(request, result.get("answers"))
    telemetry = _validate_telemetry(
        result.get("telemetry"), provenance, len(request["questions"])
    )
    return {
        "request_hash": expected_hash,
        "provenance": provenance,
        "answers": result["answers"],
        "observed_at": result.get("observed_at"),
        "cached_at": result.get("cached_at"),
        "telemetry": telemetry,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON object with request and result")
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        validated = validate_jev_result(payload["request"], payload["result"])
    except (OSError, KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(validated, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
