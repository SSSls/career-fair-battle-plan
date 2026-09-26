import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "career-fair-battle-plan" / "scripts" / "normalize_source.py"
READINESS_SCRIPT = ROOT / "career-fair-battle-plan" / "scripts" / "decision_readiness.py"


def load_normalizer():
    spec = importlib.util.spec_from_file_location("normalize_source", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_readiness():
    spec = importlib.util.spec_from_file_location("decision_readiness", READINESS_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SourceNormalizationTests(unittest.TestCase):
    def test_public_preview_preserves_partial_coverage_and_unknown_session(self):
        payload = {
            "adapter": "handshake_public_preview",
            "accessed_at": "2026-09-25",
            "source_url": "https://fixtures.invalid/fair-preview",
            "advertised_employer_count": 11,
            "employers": [
                {
                    "name": "Example Trading",
                    "job_titles": ["Software Intern"],
                    "work_authorization_text": "Employer is willing to sponsor candidates",
                    "session_count": 1,
                }
            ],
        }

        result = load_normalizer().normalize_source(payload)

        lead = result["leads"][0]
        sponsor = next(
            record
            for record in result["evidence_records"]
            if record["field"] == "sponsorship"
        )
        self.assertEqual(
            result["coverage"], {"visible": 1, "advertised": 11, "complete": False}
        )
        self.assertEqual(lead["evidence_level"], "TITLE_ONLY")
        self.assertEqual(lead["visit_access"], "unknown")
        self.assertEqual(lead["session_status"], "unknown")
        self.assertEqual(sponsor["scope"], "employer_event_card")
        self.assertEqual(sponsor["status"], "yes")

    def test_official_public_partial_page_keeps_featured_employers_incomplete(self):
        payload = {
            "adapter": "official_school",
            "accessed_at": "2026-09-25",
            "source_url": "https://fixtures.invalid/university/fair",
            "fair": {"name": "Engineering Fair", "date": "2026-10-02"},
            "advertised_employer_count": 30,
            "employers": [{"name": "Featured Employer"}, {"name": "Featured Lab"}],
            "employer_list_kind": "featured_only",
        }

        result = load_normalizer().normalize_source(payload)

        self.assertEqual(result["coverage"]["visible"], 2)
        self.assertFalse(result["coverage"]["complete"])
        self.assertTrue(all(lead["evidence_level"] == "EMPLOYER_NAME" for lead in result["leads"]))

    def test_official_login_wall_reports_requirement_without_inventing_leads(self):
        result = load_normalizer().normalize_source(
            {
                "adapter": "official_school",
                "accessed_at": "2026-09-25",
                "source_url": "https://fixtures.invalid/university/login-wall",
                "fair": {"name": "Technical Fair", "date": "2026-10-10"},
                "login_required_for_employer_list": True,
                "employers": [],
            }
        )

        self.assertEqual(result["leads"], [])
        self.assertEqual(result["access_requirements"], ["login_required_for_employer_list"])
        self.assertFalse(result["coverage"]["complete"])

    def test_historical_directory_stays_company_history_and_stale(self):
        result = load_normalizer().normalize_source(
            {
                "adapter": "external_role_research",
                "accessed_at": "2026-09-25",
                "source_url": "https://fixtures.invalid/historical-directory",
                "roles": [
                    {
                        "source_id": "history-1",
                        "company": "Historical Employer",
                        "role": None,
                        "sponsorship": "yes",
                        "scope": "company_history",
                        "published_at": "2024-09-01",
                        "freshness": "stale",
                    }
                ],
            }
        )

        sponsor = next(r for r in result["evidence_records"] if r["field"] == "sponsorship")
        self.assertEqual(sponsor["scope"], "company_history")
        self.assertEqual(sponsor["freshness"], "stale")
        self.assertEqual(result["leads"][0]["evidence_level"], "EMPLOYER_NAME")

    def test_authenticated_exact_session_is_the_only_verified_visit_path(self):
        result = load_normalizer().normalize_source(
            {
                "adapter": "handshake_authenticated_read_only",
                "accessed_at": "2026-09-25",
                "source_url": "https://fixtures.invalid/authenticated-fair",
                "employers": [
                    {
                        "name": "Verified Employer",
                        "roles": [{"title": "Software Intern", "source_id": "role-1"}],
                        "sessions": [
                            {
                                "source_id": "session-1",
                                "status": "available",
                                "start_minute": 30,
                                "end_minute": 45,
                                "channel": "video",
                            }
                        ],
                    }
                ],
            }
        )

        lead = result["leads"][0]
        self.assertEqual(lead["evidence_level"], "SESSION_VERIFIED")
        self.assertEqual(lead["visit_access"], "verified")
        self.assertEqual(lead["session_status"], "available")

    def test_duplicate_source_ids_are_rejected(self):
        payload = {
            "adapter": "external_role_research",
            "accessed_at": "2026-09-25",
            "source_url": "https://fixtures.invalid/jobs",
            "roles": [
                {"source_id": "dup", "company": "A", "role": "Intern"},
                {"source_id": "dup", "company": "B", "role": "Engineer"},
            ],
        }

        with self.assertRaisesRegex(ValueError, "duplicate evidence"):
            load_normalizer().normalize_source(payload)

    def test_invalid_accessed_date_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "accessed_at"):
            load_normalizer().normalize_source(
                {
                    "adapter": "official_school",
                    "accessed_at": "09/25/2026",
                    "source_url": "https://fixtures.invalid/fair",
                    "fair": {"name": "Fair"},
                    "employers": [],
                }
            )

    def test_unsupported_adapter_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsupported source adapter"):
            load_normalizer().normalize_source(
                {"adapter": "private_scraper", "accessed_at": "2026-09-25"}
            )

    def test_strongest_evidence_level_uses_declared_scope(self):
        normalizer = load_normalizer()
        records = [
            {"scope": "employer_event_card", "field": "role"},
            {"scope": "exact_role", "field": "role"},
            {"scope": "exact_session", "field": "session", "status": "yes"},
        ]

        self.assertEqual(normalizer.strongest_evidence_level(records), "SESSION_VERIFIED")


class DecisionReadinessTests(unittest.TestCase):
    def test_title_only_cannot_be_full_or_high_confidence(self):
        readiness = load_readiness().build_decision_readiness(
            {
                "evidence_level": "TITLE_ONLY",
                "visit_access": "unknown",
                "evidence_records": [],
                "judgments": {
                    "role_fit": {"type": "score", "score": 4, "confidence": 0.99}
                },
            },
            {"approved": True, "needs_sponsorship": False},
        )

        self.assertEqual(readiness["decision_state"], "PARTIAL")
        self.assertLessEqual(readiness["match_confidence"], 0.59)
        self.assertIn("title_only_cap", readiness["confidence_caps"])

    def test_employer_name_caps_match_confidence_at_point_three_five(self):
        readiness = load_readiness().build_decision_readiness(
            {
                "evidence_level": "EMPLOYER_NAME",
                "visit_access": "unknown",
                "judgments": {
                    "role_fit": {"type": "score", "score": 4, "confidence": 1.0}
                },
            },
            {"approved": True, "needs_sponsorship": False},
        )

        self.assertEqual(readiness["match_confidence"], 0.35)
        self.assertIn("employer_name_cap", readiness["confidence_caps"])

    def test_exact_role_unresolved_hard_fact_caps_decision_at_point_seven_nine(self):
        readiness = load_readiness().build_decision_readiness(
            {
                "evidence_level": "EXACT_ROLE",
                "visit_access": "verified",
                "unresolved_hard_facts": ["sponsorship"],
                "judgments": {
                    "role_fit": {"type": "score", "score": 4, "confidence": 0.95}
                },
            },
            {"approved": True, "needs_sponsorship": True},
        )

        self.assertEqual(readiness["decision_state"], "FULL")
        self.assertLessEqual(readiness["decision_confidence"], 0.79)
        self.assertIn("unresolved_hard_facts_cap", readiness["confidence_caps"])

    def test_verified_route_requires_point_eight_access_confidence(self):
        readiness = load_readiness().build_decision_readiness(
            {
                "evidence_level": "SESSION_VERIFIED",
                "visit_access": "verified",
                "visit_access_confidence": 0.79,
                "judgments": {
                    "role_fit": {"type": "score", "score": 4, "confidence": 0.95}
                },
            },
            {"approved": True, "needs_sponsorship": False},
        )

        self.assertFalse(readiness["route_ready"])
        self.assertIn("visit_access_below_verified_threshold", readiness["review_flags"])

    def test_score_range_crossing_priority_threshold_is_flagged(self):
        readiness = load_readiness().build_decision_readiness(
            {
                "evidence_level": "EXACT_ROLE",
                "visit_access": "unknown",
                "judgments": {
                    "role_fit": {
                        "type": "score",
                        "score": 3.1,
                        "confidence": 0.9,
                        "score_range": [2.5, 3.5],
                    }
                },
            },
            {"approved": True, "needs_sponsorship": False},
        )

        self.assertIn("range_crosses_priority_threshold:role_fit", readiness["review_flags"])

    def test_unapproved_profile_returns_complete_stop_result(self):
        readiness = load_readiness().build_decision_readiness(
            {"evidence_level": "EXACT_ROLE", "visit_access": "verified"},
            {"approved": False, "needs_sponsorship": False},
        )

        self.assertEqual(readiness["decision_state"], "STOP")
        self.assertEqual(readiness["decision_confidence"], 0.0)
        self.assertEqual(readiness["review_flags"], ["candidate_profile_not_approved"])

    def test_unresolved_sponsorship_need_returns_stop(self):
        readiness = load_readiness().build_decision_readiness(
            {"evidence_level": "TITLE_ONLY", "visit_access": "unknown"},
            {"approved": True, "needs_sponsorship": None},
        )

        self.assertEqual(readiness["decision_state"], "STOP")
        self.assertIn("needs_sponsorship_unresolved", readiness["review_flags"])


if __name__ == "__main__":
    unittest.main()
