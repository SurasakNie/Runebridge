from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tools.bridge.live.claude_adapters import build_claude_adapter
from tools.bridge.live.run_isolated_validation import ValidationConfig, ValidationError, run_isolated_validation


RUN_DATE = "2026-06-21"
ROOT = Path(__file__).resolve().parents[2]


def config(root: Path, role: str, task_id: str) -> ValidationConfig:
    return ValidationConfig(
        task_id=task_id,
        vendor="claude",
        role=role,
        approval_id="P6-CLAUDE-CONTRACT",
        run_date=RUN_DATE,
        artifact_root=root,
        timeout_seconds=5,
        budget_ceiling_usd=0.06,
        live=True,
    )


def fake_adapter(tmp_path: Path, role: str, task_id: str, envelope: dict[str, object]):
    script = tmp_path / f"fake-{role}.py"
    script.write_text(f"print({json.dumps(json.dumps(envelope))})\n", encoding="utf-8")
    spec = build_claude_adapter(
        Path(sys.executable),
        cli_version="fixture",
        role=role,
        task_id=task_id,
        budget_ceiling_usd=0.06,
        prompt="synthetic fixture",
    )
    return type(spec)(
        command=(str(Path(sys.executable).resolve()), str(script)),
        cli_name=spec.cli_name,
        cli_version=spec.cli_version,
        authentication_class="test_fixture",
        credentials_available=False,
        result_parser=spec.result_parser,
    )


def planner_payload(task_id: str) -> dict[str, object]:
    return {
        "task_id": task_id,
        "planner": "claude",
        "risk_level": "RSK-1",
        "files_to_touch": ["fixture.txt"],
        "acceptance_criteria": ["synthetic contract passes"],
        "requires_human_approval": False,
    }


def reviewer_payload(task_id: str) -> dict[str, object]:
    return {
        "task_id": task_id,
        "reviewer": "claude",
        "verdict": "approve",
        "blockers": [],
        "scope_drift": False,
        "risk_assessment": "RSK-1",
        "human_review_required": True,
        "notes": [],
    }


@pytest.mark.parametrize(
    ("role", "task_id", "payload", "artifact_name"),
    (
        ("planner", "P6-CLAUDE-PLAN", planner_payload("P6-CLAUDE-PLAN"), "PLAN.md"),
        ("reviewer", "P6-CLAUDE-REVIEW", reviewer_payload("P6-CLAUDE-REVIEW"), "REVIEW_CLAUDE.json"),
    ),
)
def test_fake_claude_contract_publishes_role_artifact(
    tmp_path: Path, role: str, task_id: str, payload: dict[str, object], artifact_name: str
) -> None:
    envelope = {"type": "result", "is_error": False, "total_cost_usd": 0.04, "structured_output": payload}
    task_dir = run_isolated_validation(
        config(tmp_path / "artifacts", role, task_id),
        fake_adapter(tmp_path, role, task_id, envelope),
    )
    assert {path.name for path in task_dir.iterdir()} == {
        artifact_name,
        "BLOCKED_COMMANDS.log",
        "LIVE_RUN_METADATA.json",
    }
    metadata = json.loads((task_dir / "LIVE_RUN_METADATA.json").read_text(encoding="utf-8"))
    assert metadata["budget_result"] == "within_ceiling"
    if role == "planner":
        text = (task_dir / artifact_name).read_text(encoding="utf-8")
        assert yaml.safe_load(text.split("---", 2)[1]) == payload
        gate = subprocess.run(
            [sys.executable, str(ROOT / "tools/bridge/gates/check_plan.py"), str(task_dir / artifact_name)],
            cwd=ROOT,
            check=False,
        )
    else:
        assert json.loads((task_dir / artifact_name).read_text(encoding="utf-8")) == payload
        gate = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools/bridge/gates/check_review.py"),
                str(task_dir / artifact_name),
                "--reviewer",
                "claude",
            ],
            cwd=ROOT,
            check=False,
        )
    assert gate.returncode == 0


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ({"total_cost_usd": 0.07}, "exceeds"),
        ({"total_cost_usd": None}, "reported cost"),
        ({"structured_output": {"task_id": "WRONG"}}, "role schema"),
        ({"is_error": True}, "successful result"),
    ),
)
def test_fake_claude_contract_fails_closed(
    tmp_path: Path, mutation: dict[str, object], message: str
) -> None:
    task_id = "P6-CLAUDE-FAIL"
    envelope = {
        "type": "result",
        "is_error": False,
        "total_cost_usd": 0.04,
        "structured_output": planner_payload(task_id),
        **mutation,
    }
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match=message):
        run_isolated_validation(
            config(artifact_root, "planner", task_id),
            fake_adapter(tmp_path, "planner", task_id, envelope),
        )
    assert not artifact_root.exists()


def test_claude_command_disables_tools_and_bounds_budget(tmp_path: Path) -> None:
    spec = build_claude_adapter(
        Path(sys.executable),
        cli_version="fixture",
        role="planner",
        task_id="P6-CLAUDE-COMMAND",
        budget_ceiling_usd=0.06,
        prompt="synthetic fixture",
    )
    assert spec.command[1:4] == ("--print", "--output-format", "json")
    assert spec.command[spec.command.index("--tools") + 1] == ""
    assert spec.command[spec.command.index("--max-budget-usd") + 1] == "0.06"
    assert "--no-session-persistence" in spec.command
    assert "P6-CLAUDE-COMMAND" in spec.command[-1]


def test_public_registry_remains_empty() -> None:
    from tools.bridge.live.run_isolated_validation import ENABLED_ADAPTERS

    assert ENABLED_ADAPTERS == {}
