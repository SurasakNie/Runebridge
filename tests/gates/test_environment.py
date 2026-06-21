from __future__ import annotations

from pathlib import Path

from tools.check_environment import collect_checks


ROOT = Path(__file__).resolve().parents[2]


def test_environment_checks_pass_with_all_required_tools() -> None:
    available = {
        name: f"/mock/bin/{name}"
        for name in ("git", "gh", "bash", "jq", "shellcheck", "gitleaks")
    }

    checks = collect_checks(available.get, (3, 11))

    assert checks
    assert all(check.passed for check in checks)


def test_environment_checks_fail_without_secret_scanner() -> None:
    available = {
        name: f"/mock/bin/{name}"
        for name in ("git", "gh", "bash", "jq", "shellcheck")
    }

    checks = collect_checks(available.get, (3, 11))

    scanner = next(check for check in checks if check.name == "secret-scanner")
    assert not scanner.passed


def test_environment_checks_reject_old_python() -> None:
    checks = collect_checks(lambda name: f"/mock/bin/{name}", (3, 10))

    python = next(check for check in checks if check.name == "python")
    assert not python.passed


def test_setup_files_exist() -> None:
    for relative_path in (
        ".env.example",
        ".pre-commit-config.yaml",
        "tools/requirements.txt",
        "docs/Environment-and-Security-Setup.md",
    ):
        assert (ROOT / relative_path).is_file(), relative_path


def test_env_example_contains_no_secret_values() -> None:
    values: dict[str, str] = {}
    for raw_line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        values[key] = value

    assert values["DRY_RUN_MODE"] == "true"
    assert values["RUNEBRIDGE_MODE"] == "safe-default"
    for key, value in values.items():
        if key not in {"DRY_RUN_MODE", "RUNEBRIDGE_MODE"}:
            assert value == "", key

