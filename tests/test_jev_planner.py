import importlib.util
from datetime import datetime, timezone
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PLANNER_SCRIPT = ROOT / "career-fair-battle-plan" / "scripts" / "plan_jev_requests.py"
VALIDATOR_SCRIPT = ROOT / "career-fair-battle-plan" / "scripts" / "validate_jev_results.py"


def load_planner():
    spec = importlib.util.spec_from_file_location("plan_jev_requests", PLANNER_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_jev_results", VALIDATOR_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def minimal_request():
    return {
        "state": {
            "candidate": {"approved_areas": ["backend-swe"]},
            "opportunity": {"company": "Example Co", "role": "Software Intern"},
        },
        "questions": [
            {
                "name": "best_area",
                "type": "choice",
                "options": ["backend-swe", "other"],
            },
            {"name": "role_fit", "type": "score", "minimum": 0, "maximum": 4},
            {"name": "entry_level_accessible", "type": "noul"},
        ],
    }


def minimal_result(request_hash, provenance="fixture"):
    timestamp = datetime.now(timezone.utc).isoformat()
    return {
        "request_hash": request_hash,
        "provenance": provenance,
        "answers": {
            "best_area": {"type": "choice", "choice": "backend-swe", "confidence": 0.9},
            "role_fit": {
                "type": "score",
                "score": 3.5,
                "confidence": 0.85,
                "score_range": [3.0, 4.0],
                "confidence_range": [0.8, 0.9],
            },
            "entry_level_accessible": {
                "type": "noul",
                "noul": 0.8,
                "probability_range": [0.7, 0.9],
            },
        },
        "observed_at": timestamp if provenance == "live" else None,
        "cached_at": timestamp if provenance == "cache" else None,
        "telemetry": {
            "provider": "typesafe" if provenance == "live" else None,
            "model": "jev" if provenance == "live" else None,
            "request_count": 1 if provenance == "live" else 0,
            "question_count": 3,
            "latency_ms": 25 if provenance == "live" else 0,
            "retry_count": 0,
            "input_tokens": 100 if provenance == "live" else 0,
            "output_tokens": 30 if provenance == "live" else 0,
            "cost_usd": 0.001 if provenance == "live" else 0,
        },
    }


def base_planner_document():
    return {
        "candidate_profile": {
            "approved": True,
            "needs_sponsorship": False,
            "background_transition": "none",
            "target_areas": ["backend-swe", "data-engineering"],
            "demonstrated_strengths": ["Python APIs", "SQL pipelines"],
            "career_stage": "student",
            "hard_constraints": {"location": ["United States"]},
            "raw_cv_text": "This full resume must never enter a Jev request.",
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


class JevPlannerTests(unittest.TestCase):
    def test_dynamic_plan_omits_irrelevant_questions(self):
        payload = base_planner_document()

        plan = load_planner().build_jev_plan(payload)
        request = plan["requests"][0]
        names = [question["name"] for question in request["questions"]]

        self.assertEqual(names, ["best_area", "role_fit", "evidence_strength"])
        self.assertNotIn("sponsorship_evidence_supports_eligibility", names)
        self.assertNotIn("conversation_leverage", names)
        self.assertEqual(plan["state"], "READY_FOR_JEV")
        self.assertIsNone(plan["provider"])
        self.assertIsNone(plan["model"])

    def test_transition_unknowns_and_plausible_channel_add_only_relevant_questions(self):
        payload = base_planner_document()
        payload["candidate_profile"].update(
            {"needs_sponsorship": True, "background_transition": "major"}
        )
        payload["opportunities"][0].update(
            {
                "career_stage_clear": False,
                "material_unknowns": ["headcount", "sponsorship"],
                "conversation_channel": "plausible",
                "exact_role_sponsorship": "unknown",
            }
        )

        request = load_planner().build_jev_plan(payload)["requests"][0]
        names = [question["name"] for question in request["questions"]]

        self.assertEqual(
            names,
            [
                "best_area",
                "role_fit",
                "evidence_strength",
                "conversation_leverage",
                "information_gain",
                "entry_level_accessible",
                "background_pathway_accessible",
                "sponsorship_evidence_supports_eligibility",
            ],
        )

    def test_resolved_exact_role_sponsorship_omits_sponsorship_question(self):
        payload = base_planner_document()
        payload["candidate_profile"]["needs_sponsorship"] = True
        payload["opportunities"][0]["exact_role_sponsorship"] = "yes"

        names = [
            question["name"]
            for question in load_planner().build_jev_plan(payload)["requests"][0][
                "questions"
            ]
        ]

        self.assertNotIn("sponsorship_evidence_supports_eligibility", names)

    def test_all_prefiltered_leads_need_no_jev_call(self):
        payload = base_planner_document()
        payload["opportunities"][0]["prefilter_state"] = "BLOCKED"

        plan = load_planner().build_jev_plan(payload)

        self.assertEqual(plan["state"], "NOT_NEEDED")
        self.assertEqual(plan["requests"], [])
        self.assertEqual(plan["question_count"], 0)

    def test_unapproved_or_unresolved_profile_stops(self):
        for changes in (
            {"approved": False},
            {"needs_sponsorship": None},
        ):
            with self.subTest(changes=changes):
                payload = base_planner_document()
                payload["candidate_profile"].update(changes)
                plan = load_planner().build_jev_plan(payload)
                self.assertEqual(plan["state"], "STOP")
                self.assertEqual(plan["requests"], [])

    def test_request_state_is_condensed_and_excludes_raw_cv(self):
        payload = base_planner_document()

        state = load_planner().build_jev_plan(payload)["requests"][0]["state"]

        self.assertNotIn("raw_cv_text", state["candidate"])
        self.assertEqual(
            set(state["candidate"]),
            {
                "approved_areas",
                "demonstrated_strengths",
                "background_transition",
                "career_stage",
                "hard_constraints",
            },
        )
        self.assertEqual(state["opportunity"]["evidence_summary"][0]["scope"], "exact_role")

    def test_best_area_choice_is_bounded_to_approved_areas_plus_other(self):
        request = load_planner().build_jev_plan(base_planner_document())["requests"][0]
        best_area = request["questions"][0]

        self.assertEqual(best_area["type"], "choice")
        self.assertEqual(
            best_area["options"], ["backend-swe", "data-engineering", "other"]
        )


class JevResultValidatorTests(unittest.TestCase):
    def test_hash_mismatched_cache_is_rejected(self):
        request = minimal_request()
        result = minimal_result("0" * 64, provenance="cache")

        with self.assertRaisesRegex(ValueError, "request_hash"):
            load_validator().validate_jev_result(request, result)

    def test_fixture_result_cannot_claim_live_provider(self):
        validator = load_validator()
        request = minimal_request()
        result = minimal_result(
            validator.compute_request_hash(request), provenance="fixture"
        )
        result["telemetry"]["provider"] = "live-jev"

        with self.assertRaisesRegex(ValueError, "fixture"):
            validator.validate_jev_result(request, result)

    def test_stale_cache_timestamp_is_rejected(self):
        validator = load_validator()
        request = minimal_request()
        result = minimal_result(validator.compute_request_hash(request), provenance="cache")
        result["cached_at"] = "2000-01-01T00:00:00+00:00"

        with self.assertRaisesRegex(ValueError, "stale"):
            validator.validate_jev_result(request, result)

    def test_missing_extra_and_wrong_type_answers_are_rejected(self):
        validator = load_validator()
        request = minimal_request()
        request_hash = validator.compute_request_hash(request)
        mutations = []
        missing = minimal_result(request_hash)
        missing["answers"].pop("role_fit")
        mutations.append((missing, "missing"))
        extra = minimal_result(request_hash)
        extra["answers"]["unexpected"] = {"type": "noul", "noul": 0.5}
        mutations.append((extra, "extra"))
        wrong_type = minimal_result(request_hash)
        wrong_type["answers"]["role_fit"] = {"type": "noul", "noul": 0.5}
        mutations.append((wrong_type, "type"))

        for result, message in mutations:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    validator.validate_jev_result(request, result)

    def test_choice_score_noul_and_ranges_are_bounded(self):
        validator = load_validator()
        request = minimal_request()
        request_hash = validator.compute_request_hash(request)
        mutations = []
        invalid_choice = minimal_result(request_hash)
        invalid_choice["answers"]["best_area"]["choice"] = "security"
        mutations.append((invalid_choice, "options"))
        invalid_choice_confidence = minimal_result(request_hash)
        invalid_choice_confidence["answers"]["best_area"]["confidence"] = 1.1
        mutations.append((invalid_choice_confidence, "confidence"))
        invalid_score = minimal_result(request_hash)
        invalid_score["answers"]["role_fit"]["score"] = 5
        mutations.append((invalid_score, "score"))
        reversed_range = minimal_result(request_hash)
        reversed_range["answers"]["role_fit"]["score_range"] = [4, 2]
        mutations.append((reversed_range, "ordered"))
        invalid_noul = minimal_result(request_hash)
        invalid_noul["answers"]["entry_level_accessible"]["noul"] = -0.1
        mutations.append((invalid_noul, "noul"))

        for result, message in mutations:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    validator.validate_jev_result(request, result)

    def test_negative_telemetry_and_noninteger_retry_are_rejected(self):
        validator = load_validator()
        request = minimal_request()
        request_hash = validator.compute_request_hash(request)
        for field, value in (
            ("latency_ms", -1),
            ("input_tokens", -1),
            ("output_tokens", -1),
            ("cost_usd", -0.1),
            ("retry_count", 0.5),
        ):
            with self.subTest(field=field):
                result = minimal_result(request_hash, provenance="live")
                result["telemetry"][field] = value
                with self.assertRaisesRegex(ValueError, field):
                    validator.validate_jev_result(request, result)

    def test_valid_live_fixture_and_cache_results_preserve_provenance(self):
        validator = load_validator()
        request = minimal_request()
        request_hash = validator.compute_request_hash(request)
        for provenance in ("live", "fixture", "cache"):
            with self.subTest(provenance=provenance):
                validated = validator.validate_jev_result(
                    request, minimal_result(request_hash, provenance=provenance)
                )
                self.assertEqual(validated["provenance"], provenance)
                self.assertEqual(validated["request_hash"], request_hash)
                self.assertEqual(validated["telemetry"]["question_count"], 3)


if __name__ == "__main__":
    unittest.main()
