from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GATES = ROOT / "tools/bridge/gates"


def run_gate(name: str, *args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GATES / name), *(str(arg) for arg in args)],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )


def write_plan(path: Path, *, risk: str = "RSK-1", approval: bool = False) -> None:
    path.write_text(
        "---\n"
        "task_id: T001\n"
        "planner: claude\n"
        f"risk_level: {risk}\n"
        "files_to_touch:\n  - src/app.py\n"
        "acceptance_criteria:\n  - tests pass\n"
        f"requires_human_approval: {str(approval).lower()}\n"
        "---\n# Plan\n",
        encoding="utf-8",
    )


def write_task(path: Path) -> None:
    path.write_text(
        "---\n"
        "task_id: T001\nrequester: human\ncreated_at: 2026-06-21\n"
        "risk_level: RSK-1\nmode: qwen-led\nbranch: bridge/T001-test\n"
        "---\n# Task\n",
        encoding="utf-8",
    )


def write_edit(path: Path, tool: str) -> None:
    path.write_text(
        "---\n"
        f"task_id: T001\ntool: {tool}\nfiles_changed: []\ntests: []\ndry_run: true\n"
        "---\n# Edit\n",
        encoding="utf-8",
    )


def valid_verify() -> dict[str, object]:
    return {
        "task_id": "T001",
        "verifier": "mock",
        "result": "pass",
        "checks": [{"name": "tests", "status": "pass", "detail": ""}],
        "failing_tests": [],
        "artifacts": [],
        "dry_run": True,
    }


def valid_review() -> dict[str, object]:
    return {
        "task_id": "T001",
        "reviewer": "claude",
        "verdict": "approve",
        "blockers": [],
        "bugs_found": [],
        "missing_tests": [],
        "scope_drift": False,
        "security_concerns": [],
        "suggestions": [],
        "risk_assessment": "RSK-1",
        "human_review_required": True,
        "notes": [],
    }


def test_plan_gate_accepts_valid_and_rejects_malformed(tmp_path: Path) -> None:
    plan = tmp_path / "PLAN.md"
    write_plan(plan)
    assert run_gate("check_plan.py", plan).returncode == 0
    plan.write_text("not front matter", encoding="utf-8")
    assert run_gate("check_plan.py", plan).returncode == 1


def test_rsk0_gate_uses_reserved_exit(tmp_path: Path) -> None:
    plan = tmp_path / "PLAN.md"
    write_plan(plan, risk="RSK-0", approval=True)
    assert run_gate("check_rsk0.py", plan).returncode == 2


def test_scope_gate_rejects_drift(tmp_path: Path) -> None:
    plan = tmp_path / "PLAN.md"
    write_plan(plan)
    assert run_gate("check_scope.py", plan, "src/app.py").returncode == 0
    assert run_gate("check_scope.py", plan, "src/other.py").returncode == 1


def test_verify_gate_rejects_failed_check(tmp_path: Path) -> None:
    artifact = tmp_path / "VERIFY.json"
    value = valid_verify()
    artifact.write_text(json.dumps(value), encoding="utf-8")
    assert run_gate("check_verify.py", artifact).returncode == 0
    value["checks"][0]["status"] = "fail"  # type: ignore[index]
    artifact.write_text(json.dumps(value), encoding="utf-8")
    assert run_gate("check_verify.py", artifact).returncode == 1


def test_review_gate_rejects_blocker_and_rsk0(tmp_path: Path) -> None:
    artifact = tmp_path / "REVIEW.json"
    value = valid_review()
    artifact.write_text(json.dumps(value), encoding="utf-8")
    assert run_gate("check_review.py", artifact, "--reviewer", "claude").returncode == 0
    value["blockers"] = ["unsafe"]
    artifact.write_text(json.dumps(value), encoding="utf-8")
    assert run_gate("check_review.py", artifact, "--reviewer", "claude").returncode == 1
    value["blockers"] = []
    value["risk_assessment"] = "RSK-0"
    artifact.write_text(json.dumps(value), encoding="utf-8")
    assert run_gate("check_review.py", artifact, "--reviewer", "claude").returncode == 2


def test_artifact_gate_is_mode_aware(tmp_path: Path) -> None:
    common = {"PLAN.md", "CHANGES.diff", "VERIFY.json", "REVIEW_CLAUDE.json"}
    for name in common:
        (tmp_path / name).touch()
    write_task(tmp_path / "TASK.md")
    write_edit(tmp_path / "EDIT_QWEN.md", "qwen")
    assert run_gate("check_artifacts.py", tmp_path, "--mode", "qwen-led").returncode == 0
    assert run_gate("check_artifacts.py", tmp_path, "--mode", "safe-default").returncode == 1
    (tmp_path / "REVIEW_QWEN.json").touch()
    assert run_gate("check_artifacts.py", tmp_path, "--mode", "qwen-led").returncode == 1


def test_artifact_gate_validates_task_and_edit_shapes(tmp_path: Path) -> None:
    for name in {"PLAN.md", "CHANGES.diff", "VERIFY.json", "REVIEW_CLAUDE.json"}:
        (tmp_path / name).touch()
    write_task(tmp_path / "TASK.md")
    write_edit(tmp_path / "EDIT_QWEN.md", "qwen")
    assert run_gate("check_artifacts.py", tmp_path, "--mode", "qwen-led").returncode == 0
    (tmp_path / "EDIT_QWEN.md").write_text("invalid", encoding="utf-8")
    assert run_gate("check_artifacts.py", tmp_path, "--mode", "qwen-led").returncode == 1


def test_secret_gate_rejects_signature(tmp_path: Path) -> None:
    clean = tmp_path / "clean.txt"
    clean.write_text("API_KEY=\n", encoding="utf-8")
    assert run_gate("check_no_secrets.py", clean).returncode == 0
    clean.write_text("password=supersecretvalue123", encoding="utf-8")
    assert run_gate("check_no_secrets.py", clean).returncode == 1
