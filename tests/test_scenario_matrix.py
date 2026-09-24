import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER = ROOT / "career-fair-battle-plan" / "scripts" / "run_scenario_matrix.py"
MATRIX = ROOT / "career-fair-battle-plan" / "examples" / "scenario_matrix.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_scenario_matrix", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ScenarioMatrixTests(unittest.TestCase):
    def test_twenty_two_parameterized_scenarios_all_match_expectations(self):
        runner = load_runner()

        report = runner.run_matrix(MATRIX)

        self.assertEqual(report["summary"]["total"], 22)
        self.assertEqual(report["summary"]["passed"], 22)
        self.assertEqual(report["summary"]["failed"], 0)
        self.assertTrue(all(result["passed"] for result in report["results"]))


if __name__ == "__main__":
    unittest.main()
