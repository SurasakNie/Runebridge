"""Check the local tools required by the Runebridge dry-run pipeline."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import shutil
import sys


MINIMUM_PYTHON = (3, 11)


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def _find_first(
    candidates: Sequence[str], finder: Callable[[str], str | None]
) -> str | None:
    for candidate in candidates:
        path = finder(candidate)
        if path:
            return path
    return None


def collect_checks(
    finder: Callable[[str], str | None] = shutil.which,
    python_version: tuple[int, int] | None = None,
) -> list[Check]:
    """Return deterministic environment checks for required local tools."""
    version = python_version or (sys.version_info.major, sys.version_info.minor)
    checks = [
        Check(
            "python",
            version >= MINIMUM_PYTHON,
            f"{version[0]}.{version[1]} (required >= 3.11)",
        )
    ]

    for name in ("git", "gh", "bash", "jq", "shellcheck"):
        path = _find_first((name,), finder)
        checks.append(Check(name, path is not None, path or "not found on PATH"))

    scanner = _find_first(("gitleaks", "trufflehog"), finder)
    checks.append(
        Check(
            "secret-scanner",
            scanner is not None,
            scanner or "install gitleaks or trufflehog",
        )
    )
    return checks


def main() -> int:
    checks = collect_checks()
    width = max(len(check.name) for check in checks)
    for check in checks:
        result = "PASS" if check.passed else "FAIL"
        print(f"{check.name:<{width}}  {result}  {check.detail}")
    return 0 if all(check.passed for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())

