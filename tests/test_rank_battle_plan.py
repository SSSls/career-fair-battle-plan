import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "career-fair-battle-plan" / "scripts" / "rank_battle_plan.py"


def load_ranker():
    spec = importlib.util.spec_from_file_location("rank_battle_plan", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def opportunity(
    company,
    role,
    *,
    role_fit=4,
    evidence_strength=3,
    conversation_leverage=3,
    information_gain=2,
    confidence=0.9,
    explicit_no_sponsorship=False,
    sponsorship_probability=0.7,
):
    return {
        "company": company,
        "role": role,
        "user_interest": 1.0,
        "evidence": {
            "explicit_no_sponsorship": explicit_no_sponsorship,
            "session_status": "verified",
            "visit_access": "verified",
        },
        "judgments": {
            "role_fit": {"type": "score", "score": role_fit, "confidence": confidence},
            "evidence_strength": {
                "type": "score",
                "score": evidence_strength,
                "confidence": confidence,
            },
            "conversation_leverage": {
                "type": "score",
                "score": conversation_leverage,
                "confidence": confidence,
            },
            "information_gain": {
                "type": "score",
                "score": information_gain,
                "confidence": confidence,
            },
            "best_area": {
                "type": "choice",
                "choice": "software-engineering",
                "confidence": confidence,
            },
            "sponsorship_evidence_supports_eligibility": {
                "type": "noul",
                "noul": sponsorship_probability,
            },
        },
    }


def document(*opportunities, needs_sponsorship=False, duration=180, reserve=30, per_visit=15):
    return {
        "candidate_profile": {
            "approved": True,
            "needs_sponsorship": needs_sponsorship,
        },
        "fair": {
            "duration_minutes": duration,
            "reserve_minutes": reserve,
            "minutes_per_visit": per_visit,
        },
        "opportunities": list(opportunities),
    }


class BattlePlanTests(unittest.TestCase):
    def test_unknown_visit_access_never_gets_fixed_or_flexible_schedule(self):
        ranker = load_ranker()
        item = opportunity("Unknown Access Co", "Software Intern")
        item["evidence"].update(
            {"visit_access": "unknown", "session_status": "unknown"}
        )

        plan = ranker.build_battle_plan(document(item))
        result = plan["opportunities"][0]

        self.assertEqual(result["route_action"], "CHECK_SESSION")
        self.assertNotIn("assigned_session", result)
        self.assertFalse(
            any(
                visit["company"] == "Unknown Access Co"
                for visit in plan["visit_schedule"]
            )
        )
        self.assertEqual(result["evidence"]["visit_access"], "unknown")
        self.assertEqual(result["evidence"]["session_status"], "unknown")

    def test_verified_flexible_booth_is_schedulable(self):
        plan = load_ranker().build_battle_plan(
            document(opportunity("Flexible Co", "Software Intern"))
        )

        result = plan["opportunities"][0]
        self.assertEqual(result["route_action"], "VISIT")
        self.assertIn("assigned_session", result)
        self.assertFalse(plan["visit_schedule"][0]["fixed"])

    def test_verified_fixed_session_preserves_exact_interval(self):
        item = opportunity("Fixed Co", "Software Intern")
        item["evidence"]["fixed_session"] = {"start_minute": 30, "end_minute": 45}

        plan = load_ranker().build_battle_plan(document(item))

        result = plan["opportunities"][0]
        self.assertEqual(result["assigned_session"], {"start_minute": 30.0, "end_minute": 45.0})
        self.assertTrue(plan["visit_schedule"][0]["fixed"])

    def test_full_session_routes_to_apply_online(self):
        item = opportunity("Full Session Co", "Software Intern")
        item["evidence"].update(
            {"visit_access": "unavailable", "session_status": "full"}
        )

        result = load_ranker().build_battle_plan(document(item))["opportunities"][0]

        self.assertEqual(result["tier"], "APPLY_ONLINE")
        self.assertEqual(result["route_action"], "APPLY_ONLINE")
        self.assertEqual(result["route_exclusion_reason"], "visit_channel_unavailable")

    def test_low_visit_access_confidence_never_enters_schedule(self):
        item = opportunity("Low Confidence Co", "Software Intern")
        item["visit_access_confidence"] = 0.79

        plan = load_ranker().build_battle_plan(document(item))
        result = plan["opportunities"][0]

        self.assertEqual(result["route_action"], "CHECK_SESSION")
        self.assertEqual(result["route_exclusion_reason"], "visit_access_confidence_below_0.80")
        self.assertEqual(plan["visit_schedule"], [])

    def test_exact_evidence_scope_survives_output(self):
        item = opportunity("Scoped Co", "Software Intern")
        item["evidence_ids"] = ["role-exact"]
        payload = document(item)
        payload["evidence_records"] = [
            {
                "claim_id": "role-exact",
                "claim": "Exact role is current.",
                "scope": "exact_role",
                "field": "role",
                "status": "yes",
            }
        ]

        result = load_ranker().build_battle_plan(payload)["opportunities"][0]

        self.assertEqual(result["evidence_records"][0]["scope"], "exact_role")

    def test_exact_role_no_sponsorship_filters_before_jev_scores_are_required(self):
        ranker = load_ranker()
        item = {
            "company": "Blocked Co",
            "role": "Software Intern",
            "user_interest": 1.0,
            "evidence_level": "EXACT_ROLE",
            "evidence_ids": ["sponsor-no"],
            "evidence": {
                "sponsorship": {
                    "status": "no",
                    "scope": "exact_role",
                    "evidence_id": "sponsor-no",
                },
                "visit_access": "unknown",
                "session_status": "unknown",
            },
            "judgments": {},
        }
        payload = document(item, needs_sponsorship=True)
        payload["evidence_records"] = [
            {"claim_id": "sponsor-no", "claim": "Exact role says no."}
        ]

        result = ranker.build_battle_plan(payload)["opportunities"][0]

        self.assertEqual(result["prefilter_state"], "BLOCKED")
        self.assertEqual(result["tier"], "SKIP")
        self.assertFalse(result["jev_required"])
        self.assertEqual(result["evidence_ids"], ["sponsor-no"])

    def test_user_opt_out_filters_without_judgments(self):
        item = {
            "company": "Avoided Co",
            "role": "Sales",
            "user_interest": 0.0,
            "evidence_level": "TITLE_ONLY",
            "evidence": {"visit_access": "unknown", "session_status": "unknown"},
            "judgments": {},
        }

        result = load_ranker().build_battle_plan(document(item))["opportunities"][0]

        self.assertEqual(result["prefilter_state"], "BLOCKED")
        self.assertIn("user_opt_out", result["reasons"])
        self.assertFalse(result["jev_required"])

    def test_exact_eligibility_mismatches_filter_without_judgments(self):
        for reason in ("citizenship", "clearance", "minimum_experience"):
            with self.subTest(reason=reason):
                item = {
                    "company": f"Blocked {reason}",
                    "role": "Engineer",
                    "user_interest": 1.0,
                    "evidence_level": "EXACT_ROLE",
                    "evidence": {
                        "explicit_disqualifiers": [reason],
                        "visit_access": "verified",
                        "session_status": "verified",
                    },
                    "judgments": {},
                }
                result = load_ranker().build_battle_plan(document(item))["opportunities"][0]
                self.assertEqual(result["prefilter_state"], "BLOCKED")
                self.assertIn(reason, result["reasons"])
                self.assertFalse(result["jev_required"])

    def test_duplicate_role_is_audited_and_filtered(self):
        first = opportunity("Duplicate Co", "Software Intern")
        second = opportunity("Duplicate Co", "Software Intern")

        results = load_ranker().build_battle_plan(document(first, second))["opportunities"]
        duplicate = next(item for item in results if "duplicate_role" in item["reasons"])

        self.assertEqual(duplicate["prefilter_state"], "BLOCKED")
        self.assertEqual(duplicate["tier"], "SKIP")
        self.assertFalse(duplicate["jev_required"])

    def test_unavailable_visit_channel_filters_route_to_apply_online(self):
        item = {
            "company": "Online Only Co",
            "role": "Software Intern",
            "user_interest": 1.0,
            "evidence_level": "EXACT_ROLE",
            "evidence": {"visit_access": "unavailable", "session_status": "full"},
            "judgments": {},
        }

        result = load_ranker().build_battle_plan(document(item))["opportunities"][0]

        self.assertEqual(result["prefilter_state"], "BLOCKED")
        self.assertEqual(result["tier"], "APPLY_ONLINE")
        self.assertIn("visit_channel_unavailable", result["reasons"])
        self.assertFalse(result["jev_required"])

    def test_employer_card_no_sponsorship_does_not_hard_filter(self):
        item = {
            "company": "Card Scope Co",
            "role": "Software Intern",
            "user_interest": 1.0,
            "evidence_level": "TITLE_ONLY",
            "evidence_ids": ["card-sponsor-no"],
            "evidence": {
                "sponsorship": {
                    "status": "no",
                    "scope": "employer_event_card",
                    "evidence_id": "card-sponsor-no",
                },
                "visit_access": "unknown",
                "session_status": "unknown",
            },
            "judgments": {},
        }
        payload = document(item, needs_sponsorship=True)
        payload["evidence_records"] = [
            {"claim_id": "card-sponsor-no", "claim": "Employer card language."}
        ]

        result = load_ranker().build_battle_plan(payload)["opportunities"][0]

        self.assertEqual(result["prefilter_state"], "SURVIVES")
        self.assertNotEqual(result["tier"], "SKIP")
        self.assertEqual(result["decision_state"], "PARTIAL")
        self.assertTrue(result["jev_required"])
        self.assertIn("sponsorship_not_exact_role", result["review_flags"])

    def test_rejects_unapproved_candidate_profile(self):
        ranker = load_ranker()
        payload = document(opportunity("A", "SWE"))
        payload["candidate_profile"]["approved"] = False

        with self.assertRaisesRegex(ValueError, "approved"):
            ranker.build_battle_plan(payload)

    def test_explicit_no_sponsorship_blocks_only_when_needed(self):
        ranker = load_ranker()
        blocked = opportunity("BlockedCo", "SWE", explicit_no_sponsorship=True)

        needs = ranker.build_battle_plan(document(blocked, needs_sponsorship=True))
        does_not_need = ranker.build_battle_plan(document(blocked, needs_sponsorship=False))

        self.assertEqual(needs["opportunities"][0]["tier"], "SKIP")
        self.assertIn("explicit_no_sponsorship", needs["opportunities"][0]["reasons"])
        self.assertNotEqual(does_not_need["opportunities"][0]["tier"], "SKIP")

    def test_unknown_sponsorship_is_review_not_rejection(self):
        ranker = load_ranker()
        unknown = opportunity("UnknownCo", "Data Intern", sponsorship_probability=0.5)

        plan = ranker.build_battle_plan(document(unknown, needs_sponsorship=True))

        result = plan["opportunities"][0]
        self.assertNotEqual(result["tier"], "SKIP")
        self.assertIn("sponsorship_evidence_supports_eligibility", result["review_flags"])

    def test_candidate_sponsorship_need_must_be_resolved_before_ranking(self):
        ranker = load_ranker()
        payload = document(opportunity("A", "SWE"))
        payload["candidate_profile"]["needs_sponsorship"] = None

        with self.assertRaisesRegex(ValueError, "needs_sponsorship"):
            ranker.build_battle_plan(payload)

    def test_capacity_is_derived_from_time_and_never_fixed_at_fifteen(self):
        ranker = load_ranker()
        items = [opportunity(f"Co{i}", "SWE") for i in range(20)]

        plan = ranker.build_battle_plan(document(*items, duration=90, reserve=15, per_visit=15))

        self.assertEqual(plan["capacity"]["total_visits"], 5)
        must_count = sum(item["tier"] == "MUST_VISIT" for item in plan["opportunities"])
        visit_count = sum(item["tier"] in {"MUST_VISIT", "IF_TIME"} for item in plan["opportunities"])
        self.assertLessEqual(must_count, 3)
        self.assertLessEqual(visit_count, 5)

    def test_high_role_fit_with_low_booth_leverage_is_apply_online(self):
        ranker = load_ranker()
        online = opportunity(
            "OnlineCo",
            "Backend Intern",
            role_fit=4,
            evidence_strength=4,
            conversation_leverage=0,
            information_gain=0,
        )

        plan = ranker.build_battle_plan(document(online))

        self.assertEqual(plan["opportunities"][0]["tier"], "APPLY_ONLINE")

    def test_zero_user_interest_skips_even_when_resume_fits(self):
        ranker = load_ranker()
        avoided = opportunity("FactoryCo", "Manufacturing Engineer")
        avoided["user_interest"] = 0

        plan = ranker.build_battle_plan(document(avoided))

        result = plan["opportunities"][0]
        self.assertEqual(result["tier"], "SKIP")
        self.assertIn("user_opt_out", result["reasons"])

    def test_explicit_disqualifier_blocks_and_unknown_eligibility_is_flagged(self):
        ranker = load_ranker()
        blocked = opportunity("SeniorCo", "Security Engineer")
        blocked["evidence"]["explicit_disqualifiers"] = ["minimum_experience"]
        uncertain = opportunity("GovCo", "Cyber Intern")
        uncertain["evidence"]["eligibility_unknowns"] = ["citizenship"]

        plan = ranker.build_battle_plan(document(blocked, uncertain))
        by_company = {item["company"]: item for item in plan["opportunities"]}

        self.assertEqual(by_company["SeniorCo"]["tier"], "SKIP")
        self.assertIn("minimum_experience", by_company["SeniorCo"]["reasons"])
        self.assertNotEqual(by_company["GovCo"]["tier"], "SKIP")
        self.assertIn("eligibility_unknown:citizenship", by_company["GovCo"]["review_flags"])

    def test_low_choice_or_score_confidence_is_surfaced(self):
        ranker = load_ranker()
        uncertain = opportunity("UnsureCo", "Analyst", confidence=0.4)

        plan = ranker.build_battle_plan(document(uncertain))

        flags = plan["opportunities"][0]["review_flags"]
        self.assertIn("role_fit", flags)
        self.assertIn("best_area", flags)
        self.assertNotEqual(plan["opportunities"][0]["tier"], "MUST_VISIT")

    def test_confident_negative_entry_accessibility_cannot_be_must_visit(self):
        ranker = load_ranker()
        inaccessible = opportunity("SeniorCo", "Senior Engineer")
        inaccessible["judgments"]["entry_level_accessible"] = {
            "type": "noul",
            "noul": 0.05,
        }

        plan = ranker.build_battle_plan(document(inaccessible))

        result = plan["opportunities"][0]
        self.assertNotEqual(result["tier"], "MUST_VISIT")
        self.assertIn("negative:entry_level_accessible", result["review_flags"])

    def test_uncertain_entry_accessibility_cannot_be_must_visit(self):
        ranker = load_ranker()
        uncertain = opportunity("MaybeCo", "Entry Engineer")
        uncertain["judgments"]["entry_level_accessible"] = {
            "type": "noul",
            "noul": 0.5,
        }

        plan = ranker.build_battle_plan(document(uncertain))

        result = plan["opportunities"][0]
        self.assertNotEqual(result["tier"], "MUST_VISIT")
        self.assertIn("entry_level_accessible", result["review_flags"])

    def test_unavailable_visit_access_routes_to_apply_online(self):
        ranker = load_ranker()
        full = opportunity("FullCo", "SWE")
        full["evidence"]["session_status"] = "full"
        full["evidence"]["visit_access"] = "unavailable"

        plan = ranker.build_battle_plan(document(full))

        self.assertEqual(plan["opportunities"][0]["tier"], "APPLY_ONLINE")

    def test_overlapping_fixed_sessions_keep_only_higher_value_visit(self):
        ranker = load_ranker()
        higher = opportunity("HighCo", "SWE", role_fit=4)
        lower = opportunity("LowCo", "SWE", role_fit=3)
        higher["evidence"]["fixed_session"] = {"start_minute": 15, "end_minute": 30}
        lower["evidence"]["fixed_session"] = {"start_minute": 20, "end_minute": 35}

        plan = ranker.build_battle_plan(document(higher, lower, duration=60, reserve=0))
        by_company = {item["company"]: item for item in plan["opportunities"]}

        self.assertIn(by_company["HighCo"]["tier"], {"MUST_VISIT", "IF_TIME"})
        self.assertEqual(by_company["LowCo"]["tier"], "APPLY_ONLINE")
        self.assertIn("schedule_conflict", by_company["LowCo"]["review_flags"])

    def test_apply_online_fixed_session_does_not_block_a_visit_candidate(self):
        ranker = load_ranker()
        online = opportunity(
            "OnlineHigh",
            "SWE",
            role_fit=4,
            evidence_strength=4,
            conversation_leverage=0,
            information_gain=0,
        )
        visit = opportunity("VisitLower", "SWE", role_fit=3)
        online["evidence"]["fixed_session"] = {"start_minute": 15, "end_minute": 30}
        visit["evidence"]["fixed_session"] = {"start_minute": 15, "end_minute": 30}

        plan = ranker.build_battle_plan(document(online, visit, duration=60, reserve=0))
        by_company = {item["company"]: item for item in plan["opportunities"]}

        self.assertEqual(by_company["OnlineHigh"]["tier"], "APPLY_ONLINE")
        self.assertIn(by_company["VisitLower"]["tier"], {"MUST_VISIT", "IF_TIME"})
        self.assertNotIn("schedule_conflict", by_company["VisitLower"]["review_flags"])

    def test_long_fixed_session_consumes_real_minute_budget(self):
        ranker = load_ranker()
        fixed = opportunity("WorkshopCo", "SWE", role_fit=4)
        flexible = opportunity("FlexibleCo", "SWE", role_fit=3)
        fixed["evidence"]["fixed_session"] = {"start_minute": 0, "end_minute": 60}

        plan = ranker.build_battle_plan(document(fixed, flexible, duration=60, reserve=0))
        by_company = {item["company"]: item for item in plan["opportunities"]}

        self.assertIn(by_company["WorkshopCo"]["tier"], {"MUST_VISIT", "IF_TIME"})
        self.assertEqual(by_company["FlexibleCo"]["tier"], "APPLY_ONLINE")
        self.assertIn("no_schedule_capacity", by_company["FlexibleCo"]["review_flags"])

    def test_cli_round_trips_json(self):
        payload = document(opportunity("CLI Co", "SWE"))
        with tempfile.TemporaryDirectory() as tmp:
            input_path = pathlib.Path(tmp) / "input.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), str(input_path)],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        output = json.loads(completed.stdout)
        self.assertEqual(output["opportunities"][0]["company"], "CLI Co")
        self.assertTrue(output["external_actions_require_confirmation"])

    def test_cli_reports_malformed_optional_objects_without_traceback(self):
        payload = document(opportunity("Bad Co", "SWE"))
        payload["weights"] = None
        with tempfile.TemporaryDirectory() as tmp:
            input_path = pathlib.Path(tmp) / "input.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), str(input_path)],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("weights", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_evidence_ids_are_preserved_for_auditable_output(self):
        ranker = load_ranker()
        item = opportunity("Audited Co", "SWE")
        item["evidence_ids"] = ["role-1", "session-1"]
        payload = document(item)
        payload["evidence_records"] = [
            {"claim_id": "role-1", "claim": "The role exists."},
            {"claim_id": "session-1", "claim": "The session exists."},
        ]

        plan = ranker.build_battle_plan(payload)

        self.assertEqual(plan["opportunities"][0]["evidence_ids"], ["role-1", "session-1"])

    def test_evidence_ids_must_reference_existing_records(self):
        ranker = load_ranker()
        item = opportunity("Broken Audit", "SWE")
        item["evidence_ids"] = ["missing-claim"]
        payload = document(item)
        payload["evidence_records"] = [
            {"claim_id": "different-claim", "claim": "Something else"}
        ]

        with self.assertRaisesRegex(ValueError, "missing-claim"):
            ranker.build_battle_plan(payload)


if __name__ == "__main__":
    unittest.main()
