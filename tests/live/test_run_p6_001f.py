from __future__ import annotations

from pathlib import Path

import pytest

import run_p6_001f


RUNNER_OUTPUTS = ("EDIT_CODEX.md", "CHANGES.diff", "LIVE_RUN_METADATA.json", "BLOCKED_COMMANDS.log")


def _staging_with_outputs(root: Path) -> Path:
    produced = root / "staging" / "P6-001F"
    produced.mkdir(parents=True)
    for name in RUNNER_OUTPUTS:
        (produced / name).write_text(f"content-of-{name}", encoding="utf-8")
    return produced


def test_publish_evidence_copies_outputs_beside_plan(tmp_path: Path) -> None:
    produced = _staging_with_outputs(tmp_path)
    evidence_dir = tmp_path / "bridge" / "P6-001F"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "PLAN.md").write_text("plan", encoding="utf-8")
    (evidence_dir / "TASK.md").write_text("task", encoding="utf-8")

    copied = run_p6_001f.publish_evidence(produced, evidence_dir)

    assert set(copied) == set(RUNNER_OUTPUTS)
    # Planning artifacts are left untouched.
    assert (evidence_dir / "PLAN.md").read_text(encoding="utf-8") == "plan"
    assert (evidence_dir / "TASK.md").read_text(encoding="utf-8") == "task"
    # Evidence files land byte-for-byte beside them.
    for name in RUNNER_OUTPUTS:
        assert (evidence_dir / name).read_text(encoding="utf-8") == f"content-of-{name}"


def test_publish_evidence_creates_dir_when_absent(tmp_path: Path) -> None:
    produced = _staging_with_outputs(tmp_path)
    evidence_dir = tmp_path / "bridge" / "P6-001F"  # does not exist yet

    copied = run_p6_001f.publish_evidence(produced, evidence_dir)

    assert set(copied) == set(RUNNER_OUTPUTS)
    assert (evidence_dir / "EDIT_CODEX.md").is_file()


def test_publish_evidence_refuses_to_overwrite_existing_file(tmp_path: Path) -> None:
    produced = _staging_with_outputs(tmp_path)
    evidence_dir = tmp_path / "bridge" / "P6-001F"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "EDIT_CODEX.md").write_text("prior-evidence", encoding="utf-8")

    with pytest.raises(SystemExit, match="Refusing to overwrite"):
        run_p6_001f.publish_evidence(produced, evidence_dir)

    # The pre-existing file is left exactly as it was.
    assert (evidence_dir / "EDIT_CODEX.md").read_text(encoding="utf-8") == "prior-evidence"
