from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tools.bridge.run_guarded_dry_run import create_bash_guard, create_shims, guarded_environment


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/bridge/run_guarded_dry_run.py"
CONDUCTOR = ROOT / "tools/bridge/orchestrate.sh"
GATE = ROOT / "tools/bridge/gates/check_artifacts.py"
RUN_DATE = "2026-06-21"


def run_guarded(root: Path, task: str, mode: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--task",
            task,
            "--mode",
            mode,
            "--date",
            RUN_DATE,
            "--artifact-root",
            str(root),
        ],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )


def hashes(directory: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.iterdir())
        if path.is_file()
    }


@pytest.mark.parametrize(
    ("task", "mode", "required", "forbidden"),
    (
        ("P5-SAFE-001", "safe-default", {"EDIT_CODEX.md", "REVIEW_QWEN.json"}, {"EDIT_QWEN.md"}),
        ("P5-QWEN-001", "qwen-led", {"EDIT_QWEN.md"}, {"EDIT_CODEX.md", "REVIEW_QWEN.json"}),
        ("P5-DUAL-001", "dual-builder", {"EDIT_CODEX.md", "EDIT_QWEN.md", "REVIEW_QWEN.json"}, set()),
    ),
)
def test_guarded_modes_are_valid_and_reproducible(
    tmp_path: Path,
    task: str,
    mode: str,
    required: set[str],
    forbidden: set[str],
) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first = run_guarded(first_root, task, mode)
    second = run_guarded(second_root, task, mode)
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    first_task = first_root / task
    second_task = second_root / task
    names = {path.name for path in first_task.iterdir()}
    assert required <= names
    assert not (forbidden & names)
    assert (first_task / "EXTERNAL_COMMANDS.log").read_bytes() == b""
    metadata = json.loads((first_task / "RUN_METADATA.json").read_text(encoding="utf-8"))
    assert metadata["python_executable"] == str(Path(sys.executable).resolve())
    assert metadata["python_version"] == ".".join(str(part) for part in sys.version_info[:3])
    assert hashes(first_task) == hashes(second_task)
    gate = subprocess.run(
        [sys.executable, str(GATE), str(first_task), "--mode", mode],
        cwd=ROOT,
        check=False,
    )
    assert gate.returncode == 0


def test_guard_removes_credentials_and_blocks_commands(tmp_path: Path) -> None:
    shim_dir = tmp_path / "bin"
    shim_dir.mkdir()
    log = tmp_path / "commands.log"
    log.touch()
    guard_file = tmp_path / "guard.sh"
    create_shims(shim_dir)
    create_bash_guard(guard_file)
    bash = shutil.which("bash")
    assert bash
    base_path = subprocess.check_output([bash, "-c", 'printf "%s" "$PATH"'], text=True)
    environment = guarded_environment(
        {**os.environ, "OPENAI_API_KEY": "not-a-real-secret", "GITHUB_TOKEN": "not-a-real-token"},
        shim_dir,
        log,
        base_path=base_path,
        guard_file=guard_file,
    )
    assert "OPENAI_API_KEY" not in environment
    assert "GITHUB_TOKEN" not in environment
    result = subprocess.run([bash, "-c", "git --version"], env=environment, check=False)
    assert result.returncode == 99
    assert log.read_text(encoding="utf-8").strip() == "git"


def test_live_mode_refusal_creates_no_directory(tmp_path: Path) -> None:
    result = subprocess.run(
        ["bash", str(CONDUCTOR), "--task", "P5-LIVE-001", "--mode", "safe-default", "--artifact-root", str(tmp_path)],
        cwd=ROOT,
        env={**os.environ, "DRY_RUN_MODE": "false"},
        check=False,
    )
    assert result.returncode == 2
    assert not (tmp_path / "P5-LIVE-001").exists()


@pytest.mark.parametrize(
    ("stage", "code", "expected"),
    (("verify", "1", 1), ("rsk0_gate", "2", 2)),
)
def test_injected_failures_bind_exit_to_stage(tmp_path: Path, stage: str, code: str, expected: int) -> None:
    task = f"P5-{stage.upper().replace('_', '-')}-001"
    environment = {
        **os.environ,
        "DRY_RUN_MODE": "true",
        "PYTHON": str(Path(sys.executable).resolve()),
        "RUNEBRIDGE_DATE": RUN_DATE,
        "RUNEBRIDGE_FAIL_STAGE": stage,
        "RUNEBRIDGE_FAIL_CODE": code,
    }
    result = subprocess.run(
        ["bash", str(CONDUCTOR), "--task", task, "--mode", "safe-default", "--artifact-root", str(tmp_path)],
        cwd=ROOT,
        env=environment,
        check=False,
    )
    assert result.returncode == expected
    report = (tmp_path / task / "FINAL_REPORT.md").read_text(encoding="utf-8")
    assert f"failed_stage: {stage}" in report


def test_retry_recovers_and_task_reuse_is_rejected(tmp_path: Path) -> None:
    environment = {
        **os.environ,
        "DRY_RUN_MODE": "true",
        "PYTHON": str(Path(sys.executable).resolve()),
        "RUNEBRIDGE_DATE": RUN_DATE,
        "RUNEBRIDGE_FAIL_ONCE_STAGE": "verify",
        "RUNEBRIDGE_MAX_RETRIES": "1",
    }
    command = [
        "bash",
        str(CONDUCTOR),
        "--task",
        "P5-RETRY-001",
        "--mode",
        "safe-default",
        "--artifact-root",
        str(tmp_path),
    ]
    assert subprocess.run(command, cwd=ROOT, env=environment, check=False).returncode == 0
    before = hashes(tmp_path / "P5-RETRY-001")
    assert subprocess.run(command, cwd=ROOT, env=environment, check=False).returncode == 1
    assert before == hashes(tmp_path / "P5-RETRY-001")
