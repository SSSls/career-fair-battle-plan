import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PLANNER_SCRIPT = ROOT / "career-fair-battle-plan" / "scripts" / "plan_jev_requests.py"


def load_planner():
    spec = importlib.util.spec_from_file_location("plan_jev_requests", PLANNER_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


if __name__ == "__main__":
    unittest.main()
