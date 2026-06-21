from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_reserved_scaffold_paths_exist() -> None:
    for relative_path in (
        "schemas",
        "tools/bridge/adapters",
        "tools/bridge/gates",
    ):
        assert (ROOT / relative_path).is_dir(), relative_path

    for relative_path in (
        "tools/bridge/adapters/claude_plan.sh",
        "schemas/plan.schema.json",
        "tools/bridge/gates/check_plan.py",
        ".bridge/README.md",
        "docs/Repository-Directory-Ownership.md",
    ):
        assert (ROOT / relative_path).is_file(), relative_path


def test_conductor_requires_explicit_arguments() -> None:
    script = ROOT / "tools/bridge/orchestrate.sh"

    result = subprocess.run(
        ["bash", str(script)],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Usage:" in result.stderr
