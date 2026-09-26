import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER = ROOT / "career-fair-battle-plan" / "scripts" / "run_scenario_matrix.py"
MATRIX = ROOT / "career-fair-battle-plan" / "examples" / "scenario_matrix.json"
FIXTURES = ROOT / "tests" / "fixtures"
REGRESSION_FIXTURES = (
    "regression-domestic-public-preview.json",
    "regression-sponsor-public-preview.json",
    "regression-high-evidence.json",
    "regression-transition-sponsor.json",
    "regression-sparse-ambiguous.json",
    "regression-jev-baseline.json",
)


def load_runner():
    spec = importlib.util.spec_from_file_location("run_scenario_matrix", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ScenarioMatrixTests(unittest.TestCase):
    def test_prior_regression_fixtures_are_synthetic_and_private_free(self):
        for name in REGRESSION_FIXTURES:
            payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
            metadata = payload["fixture_metadata"]
            self.assertTrue(metadata["synthetic_candidate"])
            self.assertFalse(metadata["contains_private_account_data"])
            self.assertFalse(metadata["real_jev_called"])
            self.assertTrue(metadata["derived_from_prior_local_test"])

    def test_at_least_thirty_six_unique_scenarios_cover_required_dimensions(self):
        runner = load_runner()

        report = runner.run_matrix(MATRIX)
        matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        ids = [scenario["id"] for scenario in matrix["scenarios"]]
        dimensions = {
            dimension
            for scenario in matrix["scenarios"]
            for dimension in scenario.get("dimensions", [])
        }
        required_dimensions = {
            "candidate:conventional-cs",
            "candidate:adjacent-transition",
            "candidate:major-transition",
            "candidate:nontechnical-hybrid",
            "candidate:sparse",
            "candidate:user-pivot",
            "policy:domestic",
            "policy:temporary-authorization",
            "policy:future-sponsorship",
            "policy:unresolved-sponsorship",
            "policy:salary-hard",
            "policy:salary-soft",
            "policy:location",
            "policy:clearance-citizenship",
            "policy:experience-gap",
            "policy:explicit-avoid",
            "source:upload",
            "source:public-web",
            "source:public-preview",
            "source:authenticated-not-registered",
            "source:registered-read-only",
            "source:official-incomplete",
            "source:login-wall",
            "source:none",
            "source:partial-6-of-11",
            "source:stale",
            "source:conflicting",
            "session:fixed",
            "session:flexible",
            "session:full",
            "session:unavailable",
            "session:unknown",
            "session:conflict",
            "session:low-confidence",
            "jev:not-needed",
            "jev:ready-no-client",
            "jev:fixture",
            "jev:malformed",
            "jev:stale-cache",
            "jev:hash-mismatch",
            "jev:cache-hit",
            "jev:retry-telemetry",
        }

        self.assertGreaterEqual(report["summary"]["total"], 36)
        self.assertEqual(report["summary"]["failed"], 0)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(required_dimensions.issubset(dimensions))
        self.assertTrue(all(result["passed"] for result in report["results"]))

    def test_six_prior_inputs_are_replayed_with_safe_outcomes(self):
        report = load_runner().run_matrix(MATRIX)
        regression_results = {
            result["id"]: result for result in report["results"] if result["kind"] == "regression"
        }

        self.assertEqual(len(regression_results), 6)
        self.assertTrue(all(result["passed"] for result in regression_results.values()))


if __name__ == "__main__":
    unittest.main()
