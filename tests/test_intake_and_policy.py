import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
INTAKE_SCRIPT = ROOT / "career-fair-battle-plan" / "scripts" / "assess_intake.py"
RANK_SCRIPT = ROOT / "career-fair-battle-plan" / "scripts" / "rank_battle_plan.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def complete_intake(mode="UPLOAD"):
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
        },
        "fair": {
            "name": "Example Fair",
            "platform": "generic",
            "date": "2026-10-01",
            "timezone": "America/New_York",
            "format": "virtual",
            "url": "https://example.edu/fair",
            "source_mode": mode,
            "company_list_present": True,
            "role_data_present": True,
            "session_data_present": True,
        },
        "access": {
            "user_logged_in": mode != "AUTHENTICATED_READ_ONLY",
            "authorization_scope": None,
            "credentials_shared": False,
        },
    }


def opportunity():
    return {
        "company": "Example Co",
        "role": "Software Intern",
        "user_interest": 1.0,
        "evidence": {
            "session_status": "verified",
            "visit_access": "verified",
        },
        "judgments": {
            "role_fit": {"type": "score", "score": 4, "confidence": 0.9},
            "evidence_strength": {"type": "score", "score": 4, "confidence": 0.9},
            "conversation_leverage": {"type": "score", "score": 4, "confidence": 0.9},
            "information_gain": {"type": "score", "score": 3, "confidence": 0.9},
            "best_area": {"type": "choice", "choice": "backend-swe", "confidence": 0.9},
            "sponsorship_evidence_supports_eligibility": {"type": "noul", "noul": 0.8},
        },
    }


def rank_document(item, *, needs_sponsorship=False, salary=None, headcount_importance="medium"):
    return {
        "candidate_profile": {
            "approved": True,
            "needs_sponsorship": needs_sponsorship,
            "salary": salary
            or {"minimum": None, "currency": "USD", "hard_constraint": False},
            "headcount_importance": headcount_importance,
        },
        "fair": {"duration_minutes": 180, "reserve_minutes": 30, "minutes_per_visit": 15},
        "opportunities": [item],
    }


class IntakeGateTests(unittest.TestCase):
    def test_unapproved_profile_stops_at_profile_review(self):
        intake = load_module("assess_intake", INTAKE_SCRIPT)
        payload = complete_intake()
        payload["candidate_profile"]["approved"] = False

        result = intake.assess_intake(payload)

        self.assertEqual(result["state"], "PROFILE_REVIEW")

    def test_missing_fair_source_requests_source_without_requesting_credentials(self):
        intake = load_module("assess_intake", INTAKE_SCRIPT)
        payload = complete_intake()
        payload["fair"]["source_mode"] = None

        result = intake.assess_intake(payload)

        self.assertEqual(result["state"], "NEED_FAIR_SOURCE")
        self.assertIn("fair.source_mode", result["missing_fields"])
        self.assertIn("Ask for an export, public URL, or user-opened authenticated tab.", result["next_actions"])
        self.assertIn("Request or store passwords", result["forbidden_actions"])

    def test_authenticated_mode_requires_user_login_then_read_only_authorization(self):
        intake = load_module("assess_intake", INTAKE_SCRIPT)
        payload = complete_intake("AUTHENTICATED_READ_ONLY")

        before_login = intake.assess_intake(payload)
        payload["access"]["user_logged_in"] = True
        after_login = intake.assess_intake(payload)

        self.assertEqual(before_login["state"], "NEED_USER_LOGIN")
        self.assertEqual(after_login["state"], "NEED_READ_ONLY_AUTHORIZATION")

    def test_authenticated_mode_becomes_ready_after_read_only_authorization(self):
        intake = load_module("assess_intake", INTAKE_SCRIPT)
        payload = complete_intake("AUTHENTICATED_READ_ONLY")
        payload["access"].update(
            {"user_logged_in": True, "authorization_scope": "read_only"}
        )

        result = intake.assess_intake(payload)

        self.assertEqual(result["state"], "READY_FOR_INGESTION")
        self.assertEqual(result["permitted_actions"], ["Read visible employer, role, and session data"])

    def test_shared_credentials_are_rejected(self):
        intake = load_module("assess_intake", INTAKE_SCRIPT)
        payload = complete_intake("AUTHENTICATED_READ_ONLY")
        payload["access"]["credentials_shared"] = True

        with self.assertRaisesRegex(ValueError, "credentials"):
            intake.assess_intake(payload)

    def test_incomplete_upload_is_ready_for_ingestion_with_gaps(self):
        intake = load_module("assess_intake", INTAKE_SCRIPT)
        payload = complete_intake("UPLOAD")
        payload["fair"]["role_data_present"] = False
        payload["fair"]["session_data_present"] = False

        result = intake.assess_intake(payload)

        self.assertEqual(result["state"], "READY_FOR_INGESTION")
        self.assertIn("fair.role_data_present", result["missing_fields"])
        self.assertIn("fair.session_data_present", result["missing_fields"])

    def test_handshake_live_fetch_requires_login_even_when_marked_public(self):
        intake = load_module("assess_intake", INTAKE_SCRIPT)
        payload = complete_intake("PUBLIC_WEB")
        payload["fair"]["platform"] = "handshake"
        payload["access"]["user_logged_in"] = False

        before_login = intake.assess_intake(payload)
        payload["access"]["user_logged_in"] = True
        after_login = intake.assess_intake(payload)

        self.assertEqual(before_login["state"], "NEED_USER_LOGIN")
        self.assertEqual(after_login["state"], "NEED_READ_ONLY_AUTHORIZATION")

    def test_logged_in_handshake_fetch_is_normalized_to_authenticated_read_only(self):
        intake = load_module("assess_intake", INTAKE_SCRIPT)
        payload = complete_intake("PUBLIC_WEB")
        payload["fair"]["platform"] = "handshake"
        payload["access"].update(
            {"user_logged_in": True, "authorization_scope": "read_only"}
        )

        result = intake.assess_intake(payload)

        self.assertEqual(result["state"], "READY_FOR_INGESTION")
        self.assertEqual(result["source_mode"], "AUTHENTICATED_READ_ONLY")

    def test_uploaded_handshake_export_does_not_require_login(self):
        intake = load_module("assess_intake", INTAKE_SCRIPT)
        payload = complete_intake("UPLOAD")
        payload["fair"]["platform"] = "handshake"
        payload["access"]["user_logged_in"] = False

        result = intake.assess_intake(payload)

        self.assertEqual(result["state"], "READY_FOR_INGESTION")
        self.assertEqual(result["source_mode"], "UPLOAD")


class SponsorHeadcountSalaryPolicyTests(unittest.TestCase):
    def test_exact_role_no_sponsorship_is_hard_disqualifier(self):
        ranker = load_module("rank_policy", RANK_SCRIPT)
        item = opportunity()
        item["evidence"]["sponsorship"] = {
            "status": "no",
            "scope": "exact_role",
            "evidence_id": "sponsor-1",
        }
        payload = rank_document(item, needs_sponsorship=True)
        payload["evidence_records"] = [{"claim_id": "sponsor-1", "claim": "No sponsorship."}]

        result = ranker.build_battle_plan(payload)["opportunities"][0]

        self.assertEqual(result["tier"], "SKIP")
        self.assertIn("exact_role_no_sponsorship", result["reasons"])

    def test_company_history_sponsorship_yes_is_review_not_hard_positive(self):
        ranker = load_module("rank_policy", RANK_SCRIPT)
        item = opportunity()
        item["evidence"]["sponsorship"] = {
            "status": "yes",
            "scope": "company_history",
            "evidence_id": "sponsor-history",
        }
        payload = rank_document(item, needs_sponsorship=True)
        payload["evidence_records"] = [
            {"claim_id": "sponsor-history", "claim": "Historical H-1B activity."}
        ]

        result = ranker.build_battle_plan(payload)["opportunities"][0]

        self.assertNotEqual(result["tier"], "SKIP")
        self.assertNotEqual(result["tier"], "MUST_VISIT")
        self.assertIn("sponsorship_not_exact_role", result["review_flags"])

    def test_official_salary_max_below_hard_floor_skips(self):
        ranker = load_module("rank_policy", RANK_SCRIPT)
        item = opportunity()
        item["evidence"]["salary"] = {
            "min": 70000,
            "max": 90000,
            "currency": "USD",
            "source_type": "official_exact_role",
            "evidence_id": "salary-1",
        }
        payload = rank_document(
            item,
            salary={"minimum": 100000, "currency": "USD", "hard_constraint": True},
        )
        payload["evidence_records"] = [{"claim_id": "salary-1", "claim": "Official range."}]

        result = ranker.build_battle_plan(payload)["opportunities"][0]

        self.assertEqual(result["tier"], "SKIP")
        self.assertIn("salary_below_hard_minimum", result["reasons"])

    def test_unknown_salary_with_hard_floor_requires_review(self):
        ranker = load_module("rank_policy", RANK_SCRIPT)
        item = opportunity()
        item["evidence"]["salary"] = {
            "min": None,
            "max": None,
            "currency": "USD",
            "source_type": "unknown",
            "evidence_id": None,
        }
        payload = rank_document(
            item,
            salary={"minimum": 100000, "currency": "USD", "hard_constraint": True},
        )

        result = ranker.build_battle_plan(payload)["opportunities"][0]

        self.assertEqual(result["tier"], "IF_TIME")
        self.assertIn("salary_unknown_for_hard_minimum", result["review_flags"])

    def test_unknown_headcount_caps_must_visit_when_high_importance(self):
        ranker = load_module("rank_policy", RANK_SCRIPT)
        item = opportunity()
        item["evidence"]["headcount"] = {"status": "unknown", "evidence_id": None}

        result = ranker.build_battle_plan(
            rank_document(item, headcount_importance="high")
        )["opportunities"][0]

        self.assertEqual(result["tier"], "IF_TIME")
        self.assertIn("headcount_unknown", result["review_flags"])

    def test_structured_evidence_ids_must_exist(self):
        ranker = load_module("rank_policy", RANK_SCRIPT)
        item = opportunity()
        item["evidence"]["headcount"] = {"status": "confirmed", "evidence_id": "hc-1"}

        with self.assertRaisesRegex(ValueError, "hc-1"):
            ranker.build_battle_plan(rank_document(item))

    def test_definite_structured_claims_require_an_evidence_id(self):
        ranker = load_module("rank_policy", RANK_SCRIPT)
        claim_shapes = [
            {
                "sponsorship": {
                    "status": "no",
                    "scope": "exact_role",
                    "evidence_id": None,
                }
            },
            {"headcount": {"status": "confirmed", "evidence_id": None}},
            {
                "salary": {
                    "min": 70000,
                    "max": 90000,
                    "currency": "USD",
                    "source_type": "official_exact_role",
                    "evidence_id": None,
                }
            },
        ]

        for evidence_update in claim_shapes:
            with self.subTest(evidence_update=evidence_update):
                item = opportunity()
                item["evidence"].update(evidence_update)
                with self.assertRaisesRegex(ValueError, "evidence_id"):
                    ranker.build_battle_plan(rank_document(item, needs_sponsorship=True))


if __name__ == "__main__":
    unittest.main()
