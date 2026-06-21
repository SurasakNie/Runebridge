from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/bridge/orchestrate.sh"


def run_conductor(
    artifact_root: Path,
    *,
    mode: str = "safe-default",
    dry_run: str = "true",
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "DRY_RUN_MODE": dry_run,
        "PYTHON": Path(sys.executable).as_posix(),
        "RUNEBRIDGE_DATE": "2026-06-21",
        **(extra_env or {}),
    }
    return subprocess.run(
        [
            "bash",
            str(SCRIPT),
            "--task",
            "T004",
            "--mode",
            mode,
            "--artifact-root",
            str(artifact_root),
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        check=False,
        text=True,
    )


@pytest.mark.parametrize("mode", ("safe-default", "qwen-led", "dual-builder"))
def test_all_mode_maps_complete(mode: str, tmp_path: Path) -> None:
    result = run_conductor(tmp_path, mode=mode)
    task_dir = tmp_path / "T004"
    assert result.returncode == 0, result.stderr
    report = (task_dir / "FINAL_REPORT.md").read_text(encoding="utf-8")
    assert "status: pass" in report
    assert (task_dir / "REVIEW_QWEN.json").exists() is (mode != "qwen-led")
    assert (task_dir / "EDIT_QWEN.md").exists() is (mode in {"qwen-led", "dual-builder"})
    assert (task_dir / "EDIT_CODEX.md").exists() is (mode in {"safe-default", "dual-builder"})


def test_live_mode_fails_before_task_directory(tmp_path: Path) -> None:
    result = run_conductor(tmp_path, dry_run="false")
    assert result.returncode == 2
    assert not (tmp_path / "T004").exists()


@pytest.mark.parametrize(
    ("mode", "stage"),
    (
        ("safe-default", "plan"),
        ("safe-default", "plan_gate"),
        ("safe-default", "rsk0_gate"),
        ("safe-default", "build_codex"),
        ("safe-default", "scope_gate"),
        ("safe-default", "qwen_review"),
        ("safe-default", "qwen_review_gate"),
        ("safe-default", "verify"),
        ("safe-default", "verify_gate"),
        ("safe-default", "claude_review"),
        ("safe-default", "claude_review_gate"),
        ("safe-default", "secret_gate"),
        ("safe-default", "artifact_gate"),
        ("qwen-led", "build_qwen"),
        ("dual-builder", "build_qwen"),
    ),
)
def test_each_stage_failure_halts(mode: str, stage: str, tmp_path: Path) -> None:
    result = run_conductor(tmp_path, mode=mode, extra_env={"RUNEBRIDGE_FAIL_STAGE": stage})
    task_dir = tmp_path / "T004"
    assert result.returncode == 1
    report = (task_dir / "FINAL_REPORT.md").read_text(encoding="utf-8")
    assert f"failed_stage: {stage}" in report


def test_failure_prevents_later_stage_artifacts(tmp_path: Path) -> None:
    result = run_conductor(tmp_path, extra_env={"RUNEBRIDGE_FAIL_STAGE": "verify"})
    assert result.returncode == 1
    task_dir = tmp_path / "T004"
    assert not (task_dir / "VERIFY.json").exists()
    assert not (task_dir / "REVIEW_CLAUDE.json").exists()


def test_rsk0_exit_is_propagated(tmp_path: Path) -> None:
    result = run_conductor(
        tmp_path,
        extra_env={"RUNEBRIDGE_FAIL_STAGE": "rsk0_gate", "RUNEBRIDGE_FAIL_CODE": "2"},
    )
    assert result.returncode == 2
    report = (tmp_path / "T004/FINAL_REPORT.md").read_text(encoding="utf-8")
    assert "failed_stage: rsk0_gate" in report


def test_bounded_retry_can_recover_once(tmp_path: Path) -> None:
    result = run_conductor(
        tmp_path,
        extra_env={"RUNEBRIDGE_FAIL_ONCE_STAGE": "verify", "RUNEBRIDGE_MAX_RETRIES": "1"},
    )
    assert result.returncode == 0, result.stderr
    report = (tmp_path / "T004/FINAL_REPORT.md").read_text(encoding="utf-8")
    assert "status: pass" in report


def test_retry_budget_is_capped(tmp_path: Path) -> None:
    result = run_conductor(tmp_path, extra_env={"RUNEBRIDGE_MAX_RETRIES": "4"})
    assert result.returncode == 1
    assert not (tmp_path / "T004").exists()


def test_task_id_cannot_reuse_existing_artifacts(tmp_path: Path) -> None:
    task_dir = tmp_path / "T004"
    task_dir.mkdir()
    (task_dir / "stale.txt").write_text("keep", encoding="utf-8")
    result = run_conductor(tmp_path)
    assert result.returncode == 1
    assert (task_dir / "stale.txt").read_text(encoding="utf-8") == "keep"
