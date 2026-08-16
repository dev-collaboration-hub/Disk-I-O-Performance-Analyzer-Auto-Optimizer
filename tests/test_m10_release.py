"""M10 production-release metadata tests."""

from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class M10ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with (ROOT / "pyproject.toml").open("rb") as handle:
            cls.config = tomllib.load(handle)

    def test_stable_version_is_consistent(self) -> None:
        namespace: dict[str, object] = {}
        exec((ROOT / "config/version.py").read_text(encoding="utf-8"), namespace)
        self.assertEqual(self.config["project"]["version"], "1.0.0")
        self.assertEqual(namespace["__version__"], "1.0.0")
        self.assertEqual(namespace["RELEASE_CHANNEL"], "stable")

    def test_runtime_contract(self) -> None:
        project = self.config["project"]
        self.assertEqual(project["requires-python"], ">=3.10")
        self.assertIn("psutil>=5.9", project["dependencies"])

    def test_console_entry_points(self) -> None:
        scripts = self.config["project"]["scripts"]
        self.assertEqual(scripts["disk-io-analyzer"], "main:main")
        self.assertEqual(scripts["disk-io-alerts"], "reporting.alert_report:main")
        self.assertEqual(scripts["disk-io-analytics"], "reporting.analytics_report:main")
        self.assertEqual(scripts["disk-io-optimize"], "reporting.optimization_report:main")
        self.assertEqual(scripts["disk-io-recommendations"], "reporting.recommendation_report:main")

    def test_release_documents_exist(self) -> None:
        for path in (
            "CHANGELOG.md", "SECURITY.md", "docs/PRODUCTION_DEPLOYMENT.md",
            "docs/RELEASE_CHECKLIST.md", "docs/M10_COMPLETION.md",
        ):
            self.assertTrue((ROOT / path).is_file(), path)

    def test_all_milestone_completion_documents_exist(self) -> None:
        for milestone in range(1, 11):
            self.assertTrue((ROOT / "docs" / f"M{milestone}_COMPLETION.md").is_file(), f"M{milestone}")

    def test_readme_marks_m10_complete(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("M10 — Production Release: complete", readme)
        self.assertIn("1.0.0", readme)


if __name__ == "__main__":
    unittest.main()
