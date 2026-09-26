import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReadmeInstallationTests(unittest.TestCase):
    COMMON_COMMANDS = (
        "python3 --version",
        "python3 -m unittest discover -s tests -v",
        "python3 career-fair-battle-plan/scripts/assess_intake.py career-fair-battle-plan/examples/sample_input.json",
        "python3 career-fair-battle-plan/scripts/run_scenario_matrix.py career-fair-battle-plan/examples/scenario_matrix.json",
        "python3 /Users/sunchunxuan/.codex/skills/.system/skill-creator/scripts/quick_validate.py career-fair-battle-plan",
    )

    def test_english_readme_covers_complete_onboarding(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        required_sections = (
            "## Requirements",
            "## Installation",
            "### Option A — Install as a Codex skill",
            "### Option B — Run the deterministic tools without installing the skill",
            "## Prepare your inputs",
            "## First run",
            "## Updating",
            "## Uninstalling",
            "## Troubleshooting",
        )
        for section in required_sections:
            with self.subTest(section=section):
                self.assertIn(section, readme)

        self.assertIn(
            "git clone https://github.com/SSSls/career-fair-battle-plan.git",
            readme,
        )
        self.assertIn("$career-fair-battle-plan", readme)
        for command in self.COMMON_COMMANDS:
            with self.subTest(command=command):
                self.assertIn(command, readme)
        for phrase in (
            "Python 3.10",
            "PUBLIC_PREVIEW",
            "STOP / PARTIAL / FULL",
            "AUTHENTICATED_READ_ONLY",
            "read-only",
            "provenance",
            "cache",
            "Download ZIP",
            "does not register",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, readme)

    def test_chinese_readme_covers_matching_onboarding(self):
        readme = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        required_sections = (
            "## 环境要求",
            "## 安装",
            "### 方式 A——安装为 Codex Skill",
            "### 方式 B——不安装 Skill，直接运行确定性工具",
            "## 准备输入",
            "## 第一次运行",
            "## 更新",
            "## 卸载",
            "## 常见问题",
        )
        for section in required_sections:
            with self.subTest(section=section):
                self.assertIn(section, readme)

        self.assertIn(
            "git clone https://github.com/SSSls/career-fair-battle-plan.git",
            readme,
        )
        self.assertIn("$career-fair-battle-plan", readme)
        for command in self.COMMON_COMMANDS:
            with self.subTest(command=command):
                self.assertIn(command, readme)
        for phrase in (
            "Python 3.10",
            "PUBLIC_PREVIEW",
            "STOP / PARTIAL / FULL",
            "AUTHENTICATED_READ_ONLY",
            "只读",
            "provenance",
            "cache",
            "Download ZIP",
            "不会注册",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, readme)


if __name__ == "__main__":
    unittest.main()
