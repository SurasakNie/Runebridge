from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_reserved_scaffold_paths_exist() -> None:
    for relative_path in (
        "schemas/.gitkeep",
        "tools/bridge/adapters/.gitkeep",
        "tools/bridge/gates/.gitkeep",
        ".bridge/README.md",
        "docs/Repository-Directory-Ownership.md",
    ):
        assert (ROOT / relative_path).is_file(), relative_path


def test_conductor_placeholder_fails_closed() -> None:
    script = ROOT / "tools/bridge/orchestrate.sh"

    result = subprocess.run(
        ["bash", str(script)],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert "not implemented" in result.stderr
