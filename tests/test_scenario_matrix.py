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

    def test_twenty_two_parameterized_scenarios_all_match_expectations(self):
        runner = load_runner()

        report = runner.run_matrix(MATRIX)

        self.assertEqual(report["summary"]["total"], 22)
        self.assertEqual(report["summary"]["passed"], 22)
        self.assertEqual(report["summary"]["failed"], 0)
        self.assertTrue(all(result["passed"] for result in report["results"]))


if __name__ == "__main__":
    unittest.main()
