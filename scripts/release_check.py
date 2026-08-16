"""Repository release gate for M10 production releases."""

from __future__ import annotations

import argparse
import compileall
import subprocess
import sys
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "pyproject.toml",
    "README.md",
    "CHANGELOG.md",
    "SECURITY.md",
    "docs/PRODUCTION_DEPLOYMENT.md",
    "docs/RELEASE_CHECKLIST.md",
    "docs/M10_COMPLETION.md",
)
EXPECTED_SCRIPTS = {
    "disk-io-analyzer": "main:main",
    "disk-io-alerts": "reporting.alert_report:main",
    "disk-io-analytics": "reporting.analytics_report:main",
    "disk-io-optimize": "reporting.optimization_report:main",
    "disk-io-recommendations": "reporting.recommendation_report:main",
}


def _load_project() -> dict:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def validate_metadata() -> list[str]:
    errors: list[str] = []
    project = _load_project().get("project", {})
    version = str(project.get("version", ""))
    namespace: dict[str, object] = {}
    exec((ROOT / "config/version.py").read_text(encoding="utf-8"), namespace)
    code_version = str(namespace.get("__version__", ""))

    if version != code_version:
        errors.append(f"version mismatch: pyproject={version!r}, code={code_version!r}")
    if version != "1.0.0":
        errors.append(f"expected stable version 1.0.0, found {version!r}")
    if str(project.get("requires-python", "")) != ">=3.10":
        errors.append("requires-python must remain >=3.10 for v1.0.0")
    if "psutil>=5.9" not in project.get("dependencies", []):
        errors.append("psutil>=5.9 runtime dependency is missing")

    scripts = project.get("scripts", {})
    for name, target in EXPECTED_SCRIPTS.items():
        if scripts.get(name) != target:
            errors.append(f"console script {name!r} must target {target!r}")
    return errors


def validate_files() -> list[str]:
    errors = [f"missing required file: {path}" for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    for milestone in range(1, 11):
        path = ROOT / "docs" / f"M{milestone}_COMPLETION.md"
        if not path.is_file():
            errors.append(f"missing milestone completion document: {path.relative_to(ROOT)}")
    return errors


def run_compile() -> bool:
    targets = [
        "alerts", "analytics", "analysis", "config", "monitoring",
        "optimizer", "reporting", "utils", "main.py", "scripts",
    ]
    results: list[bool] = []
    for item in targets:
        path = ROOT / item
        if not path.exists():
            continue
        if path.is_dir():
            results.append(compileall.compile_dir(str(path), quiet=1))
        else:
            results.append(compileall.compile_file(str(path), quiet=1))
    return all(results)


def run_tests() -> int:
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run M10 production release gates.")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()

    errors = validate_files() + validate_metadata()
    if not run_compile():
        errors.append("Python compilation failed")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    if not args.skip_tests and run_tests() != 0:
        print("FAIL: unittest suite failed")
        return 1

    print("RELEASE_CHECK_OK version=1.0.0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
