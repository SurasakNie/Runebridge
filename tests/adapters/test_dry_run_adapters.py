from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
ADAPTERS = ROOT / "tools/bridge/adapters"
GATES = ROOT / "tools/bridge/gates"


def run_adapter(name: str, task_dir: Path, *, dry_run: str = "true") -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "DRY_RUN_MODE": dry_run}
    return subprocess.run(
        ["bash", str(ADAPTERS / name), str(task_dir)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        check=False,
        text=True,
    )


def run_gate(name: str, *args: object) -> int:
    return subprocess.run(
        [sys.executable, str(GATES / name), *(str(arg) for arg in args)],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    ).returncode


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_task(path: Path, mode: str) -> None:
    path.write_text(
        "---\n"
        "task_id: T003\nrequester: human\ncreated_at: 2026-06-21\n"
        f"risk_level: RSK-2\nmode: {mode}\nbranch: bridge/T003-dry-run\n"
        "---\n# Task\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("adapter", "outputs"),
    (
        ("claude_plan.sh", ("PLAN.md",)),
        ("qwen_plan.sh", ("PLAN.md",)),
        ("codex_build.sh", ("EDIT_CODEX.md", "CHANGES.diff")),
        ("qwen_build.sh", ("EDIT_QWEN.md", "CHANGES.diff")),
        ("qwen_review.sh", ("REVIEW_QWEN.json",)),
        ("mock_verify.sh", ("VERIFY.json",)),
        ("claude_review.sh", ("REVIEW_CLAUDE.json",)),
    ),
)
def test_adapter_outputs_are_byte_stable(tmp_path: Path, adapter: str, outputs: tuple[str, ...]) -> None:
    task_dir = tmp_path / "T003"
    task_dir.mkdir()
    assert run_adapter(adapter, task_dir).returncode == 0
    first = {name: digest(task_dir / name) for name in outputs}
    assert run_adapter(adapter, task_dir).returncode == 0
    assert first == {name: digest(task_dir / name) for name in outputs}


def test_generated_artifacts_pass_schema_gates(tmp_path: Path) -> None:
    task_dir = tmp_path / "T003"
    task_dir.mkdir()
    write_task(task_dir / "TASK.md", "safe-default")
    for adapter in (
        "claude_plan.sh",
        "codex_build.sh",
        "qwen_review.sh",
        "mock_verify.sh",
        "claude_review.sh",
    ):
        assert run_adapter(adapter, task_dir).returncode == 0
    assert run_gate("check_plan.py", task_dir / "PLAN.md") == 0
    assert run_gate("check_verify.py", task_dir / "VERIFY.json") == 0
    assert run_gate("check_review.py", task_dir / "REVIEW_QWEN.json", "--reviewer", "qwen") == 0
    assert run_gate("check_review.py", task_dir / "REVIEW_CLAUDE.json", "--reviewer", "claude") == 0
    assert run_gate("check_artifacts.py", task_dir, "--mode", "safe-default") == 0


def test_live_mode_fails_closed_without_output(tmp_path: Path) -> None:
    task_dir = tmp_path / "T003"
    task_dir.mkdir()
    result = run_adapter("claude_plan.sh", task_dir, dry_run="false")
    assert result.returncode == 2
    assert not (task_dir / "PLAN.md").exists()


def test_qwen_led_does_not_create_qwen_review(tmp_path: Path) -> None:
    task_dir = tmp_path / "T003"
    task_dir.mkdir()
    write_task(task_dir / "TASK.md", "qwen-led")
    for adapter in ("qwen_plan.sh", "qwen_build.sh", "mock_verify.sh", "claude_review.sh"):
        assert run_adapter(adapter, task_dir).returncode == 0
    assert not (task_dir / "REVIEW_QWEN.json").exists()
    assert run_gate("check_artifacts.py", task_dir, "--mode", "qwen-led") == 0


def test_dual_builder_artifact_matrix(tmp_path: Path) -> None:
    task_dir = tmp_path / "T003"
    task_dir.mkdir()
    write_task(task_dir / "TASK.md", "dual-builder")
    for adapter in (
        "claude_plan.sh",
        "codex_build.sh",
        "qwen_build.sh",
        "qwen_review.sh",
        "mock_verify.sh",
        "claude_review.sh",
    ):
        assert run_adapter(adapter, task_dir).returncode == 0
    assert run_gate("check_artifacts.py", task_dir, "--mode", "dual-builder") == 0


def test_artifact_gate_rejects_task_id_mismatch(tmp_path: Path) -> None:
    task_dir = tmp_path / "T003"
    task_dir.mkdir()
    write_task(task_dir / "TASK.md", "safe-default")
    for adapter in (
        "claude_plan.sh",
        "codex_build.sh",
        "qwen_review.sh",
        "mock_verify.sh",
        "claude_review.sh",
    ):
        assert run_adapter(adapter, task_dir).returncode == 0
    task = (task_dir / "TASK.md").read_text(encoding="utf-8").replace("task_id: T003", "task_id: OTHER")
    (task_dir / "TASK.md").write_text(task, encoding="utf-8")
    assert run_gate("check_artifacts.py", task_dir, "--mode", "safe-default") == 1
