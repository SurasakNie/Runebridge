from __future__ import annotations

import json
import hashlib
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tools.bridge.live.codex_adapters import (
    SYNTHETIC_WORKSPACE_FILE,
    build_codex_adapter,
    render_synthetic_diff,
)
from tools.bridge.live.run_isolated_validation import (
    AdapterSpec,
    ParsedArtifact,
    ValidationConfig,
    ValidationError,
    run_isolated_validation,
)


RUN_DATE = "2026-06-22"
ROOT = Path(__file__).resolve().parents[2]
FIXTURE_CONTENT = "synthetic bounded edit\n"


def config(root: Path, task_id: str) -> ValidationConfig:
    return ValidationConfig(
        task_id=task_id,
        vendor="codex",
        role="builder",
        approval_id="P6-CODEX-CONTRACT",
        run_date=RUN_DATE,
        artifact_root=root,
        timeout_seconds=5,
        budget_ceiling_usd=0.06,
        live=True,
    )


def builder_payload(task_id: str, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "task_id": task_id,
        "tool": "codex",
        "files_changed": [SYNTHETIC_WORKSPACE_FILE],
        "tests": ["synthetic builder contract passed"],
        "dry_run": False,
    }
    payload.update(overrides)
    return payload


def jsonl_lines(
    *,
    agent_text: str | None = None,
    include_agent_message: bool = True,
    include_turn_completed: bool = True,
    include_error: bool = False,
) -> list[str]:
    """Build a realistic Codex CLI 0.141.0 --json event stream, matching what
    manual PC probes against the real CLI actually produced (thread.started,
    turn.started, item.completed file_change/agent_message, turn.completed
    with token usage; error+turn.failed on failure, no total_cost_usd ever)."""
    lines = [
        json.dumps({"type": "thread.started", "thread_id": "fake-thread"}),
        json.dumps({"type": "turn.started"}),
    ]
    if include_error:
        lines.append(json.dumps({"type": "error", "message": "synthetic failure"}))
        lines.append(json.dumps({"type": "turn.failed", "error": {"message": "synthetic failure"}}))
        return lines
    lines.append(
        json.dumps(
            {
                "type": "item.completed",
                "item": {"id": "item_0", "type": "file_change", "changes": [{"path": SYNTHETIC_WORKSPACE_FILE, "kind": "add"}]},
            }
        )
    )
    if include_agent_message:
        lines.append(
            json.dumps({"type": "item.completed", "item": {"id": "item_1", "type": "agent_message", "text": agent_text}})
        )
    if include_turn_completed:
        lines.append(
            json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1000, "cached_input_tokens": 0, "output_tokens": 50, "reasoning_output_tokens": 10}})
        )
    return lines


def fake_adapter(
    tmp_path: Path,
    task_id: str,
    lines: list[str],
    *,
    write_fixture: bool = True,
    write_extra: bool = False,
):
    script = tmp_path / "fake-codex.py"
    body_lines = ["from pathlib import Path"]
    if write_fixture:
        body_lines.append(f"Path({SYNTHETIC_WORKSPACE_FILE!r}).write_text({FIXTURE_CONTENT!r}, encoding='utf-8')")
    if write_extra:
        body_lines.append("Path('unexpected.txt').write_text('scope drift\\n', encoding='utf-8')")
    for line in lines:
        body_lines.append(f"print({line!r})")
    script.write_text("\n".join(body_lines) + "\n", encoding="utf-8")
    spec = build_codex_adapter(
        Path(sys.executable),
        cli_version="fixture",
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
        allowed_workspace_files=spec.allowed_workspace_files,
    )


def test_fake_codex_contract_publishes_builder_artifacts(tmp_path: Path) -> None:
    task_id = "P6-CODEX-BUILD"
    payload = builder_payload(task_id)
    lines = jsonl_lines(agent_text=json.dumps(payload))
    task_dir = run_isolated_validation(
        config(tmp_path / "artifacts", task_id),
        fake_adapter(tmp_path, task_id, lines),
    )
    assert {path.name for path in task_dir.iterdir()} == {
        "EDIT_CODEX.md",
        "CHANGES.diff",
        "BLOCKED_COMMANDS.log",
        "LIVE_RUN_METADATA.json",
    }
    edit_text = (task_dir / "EDIT_CODEX.md").read_text(encoding="utf-8")
    assert yaml.safe_load(edit_text.split("---", 2)[1]) == payload
    expected_diff = render_synthetic_diff(FIXTURE_CONTENT)
    assert (task_dir / "CHANGES.diff").read_text(encoding="utf-8") == expected_diff
    metadata = json.loads((task_dir / "LIVE_RUN_METADATA.json").read_text(encoding="utf-8"))
    assert metadata["vendor"] == "codex"
    assert metadata["role"] == "builder"
    # Codex CLI 0.141.0 reports token usage, not a dollar cost, and has no
    # --budget-usd flag; "not_reported" matches the existing Qwen precedent.
    assert metadata["budget_result"] == "not_reported"
    assert metadata["scope_valid"] is True
    edit_bytes = (task_dir / "EDIT_CODEX.md").read_bytes()
    diff_bytes = (task_dir / "CHANGES.diff").read_bytes()
    assert metadata["result_sha256"] == hashlib.sha256(edit_bytes).hexdigest()
    assert metadata["artifact_sha256s"] == {
        "CHANGES.diff": hashlib.sha256(diff_bytes).hexdigest(),
        "EDIT_CODEX.md": hashlib.sha256(edit_bytes).hexdigest(),
    }
    plan = tmp_path / "PLAN.md"
    plan.write_text(
        "---\n"
        f"task_id: {task_id}\n"
        "planner: claude\n"
        "risk_level: RSK-1\n"
        "files_to_touch:\n"
        f"  - {SYNTHETIC_WORKSPACE_FILE}\n"
        "acceptance_criteria:\n"
        "  - synthetic builder contract passed\n"
        "requires_human_approval: false\n"
        "---\n",
        encoding="utf-8",
    )
    gate = subprocess.run(
        [sys.executable, str(ROOT / "tools/bridge/gates/check_scope.py"), str(plan), "--diff", str(task_dir / "CHANGES.diff")],
        cwd=ROOT,
        check=False,
    )
    assert gate.returncode == 0


def test_fake_codex_contract_fails_closed_on_error_event(tmp_path: Path) -> None:
    task_id = "P6-CODEX-ERROR"
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match="failed turn"):
        run_isolated_validation(
            config(artifact_root, task_id),
            fake_adapter(tmp_path, task_id, jsonl_lines(include_error=True)),
        )
    assert not artifact_root.exists()


def test_fake_codex_contract_fails_closed_without_agent_message(tmp_path: Path) -> None:
    task_id = "P6-CODEX-NOMSG"
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match="final agent message"):
        run_isolated_validation(
            config(artifact_root, task_id),
            fake_adapter(tmp_path, task_id, jsonl_lines(include_agent_message=False)),
        )
    assert not artifact_root.exists()


def test_fake_codex_contract_fails_closed_on_malformed_agent_json(tmp_path: Path) -> None:
    task_id = "P6-CODEX-BADJSON"
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match="not valid JSON"):
        run_isolated_validation(
            config(artifact_root, task_id),
            fake_adapter(tmp_path, task_id, jsonl_lines(agent_text="not json")),
        )
    assert not artifact_root.exists()


def test_fake_codex_contract_fails_closed_on_wrong_task_id(tmp_path: Path) -> None:
    task_id = "P6-CODEX-WRONGID"
    payload = builder_payload("SOME-OTHER-TASK")
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match="wrong task ID"):
        run_isolated_validation(
            config(artifact_root, task_id),
            fake_adapter(tmp_path, task_id, jsonl_lines(agent_text=json.dumps(payload))),
        )
    assert not artifact_root.exists()


def test_fake_codex_contract_fails_closed_without_turn_completed(tmp_path: Path) -> None:
    task_id = "P6-CODEX-NOTURN"
    payload = builder_payload(task_id)
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match="completed turn"):
        run_isolated_validation(
            config(artifact_root, task_id),
            fake_adapter(tmp_path, task_id, jsonl_lines(agent_text=json.dumps(payload), include_turn_completed=False)),
        )
    assert not artifact_root.exists()


def test_codex_workspace_scope_rejects_extra_write(tmp_path: Path) -> None:
    task_id = "P6-CODEX-DRIFT"
    payload = builder_payload(task_id)
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match="workspace scope"):
        run_isolated_validation(
            config(artifact_root, task_id),
            fake_adapter(tmp_path, task_id, jsonl_lines(agent_text=json.dumps(payload)), write_extra=True),
        )
    assert not artifact_root.exists()


def test_codex_workspace_scope_requires_declared_write(tmp_path: Path) -> None:
    task_id = "P6-CODEX-MISSING"
    payload = builder_payload(task_id)
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match="approved workspace file"):
        run_isolated_validation(
            config(artifact_root, task_id),
            fake_adapter(tmp_path, task_id, jsonl_lines(agent_text=json.dumps(payload)), write_fixture=False),
        )
    assert not artifact_root.exists()


def test_render_synthetic_diff_matches_approved_headers() -> None:
    diff_text = render_synthetic_diff("one line\n")
    assert diff_text.splitlines()[0] == f"--- a/{SYNTHETIC_WORKSPACE_FILE}"
    assert diff_text.splitlines()[1] == f"+++ b/{SYNTHETIC_WORKSPACE_FILE}"
    assert "+one line" in diff_text


def test_codex_command_uses_real_flags_and_relaxed_schema(tmp_path: Path) -> None:
    spec = build_codex_adapter(
        Path(sys.executable),
        cli_version="fixture",
        task_id="P6-CODEX-COMMAND",
        budget_ceiling_usd=0.06,
        prompt="synthetic fixture",
        model_identifier="codex-mini-latest",
    )
    assert spec.command[1:3] == ("exec", "--json")
    assert spec.command[spec.command.index("--sandbox") + 1] == "workspace-write"
    assert "--skip-git-repo-check" in spec.command
    assert "--budget-usd" not in spec.command
    assert spec.command[spec.command.index("--model") + 1] == "codex-mini-latest"
    assert "P6-CODEX-COMMAND" in spec.command[-1]
    assert spec.allowed_workspace_files == (SYNTHETIC_WORKSPACE_FILE,)

    schema_path = Path(spec.command[spec.command.index("--output-schema") + 1])
    schema_text = schema_path.read_text(encoding="utf-8")
    assert not schema_text.startswith("﻿")
    schema = json.loads(schema_text)
    assert "uniqueItems" not in json.dumps(schema)
    assert "pattern" not in json.dumps(schema)
    assert "minLength" not in json.dumps(schema)


def test_codex_command_omits_model_flag_when_unset() -> None:
    spec = build_codex_adapter(
        Path(sys.executable),
        cli_version="fixture",
        task_id="P6-CODEX-NOMODEL",
        budget_ceiling_usd=0.06,
        prompt="synthetic fixture",
    )
    assert "--model" not in spec.command


def test_extra_artifact_content_must_be_bytes(tmp_path: Path) -> None:
    script = tmp_path / "fake.py"
    script.write_text("import json\nprint(json.dumps({'status': 'ok'}))\n", encoding="utf-8")

    def parser(_stdout: str, _config: ValidationConfig, _workspace: Path) -> ParsedArtifact:
        return ParsedArtifact(
            "RESULT.json",
            b'{"status": "ok"}\n',
            {"status": "ok"},
            extra_artifacts=(("CHANGES.diff", "not bytes"),),  # type: ignore[arg-type]
        )

    spec = AdapterSpec(
        command=(str(Path(sys.executable).resolve()), str(script)),
        cli_name="fake-cli",
        cli_version="fixture",
        authentication_class="test_fixture",
        credentials_available=False,
        result_parser=parser,
    )
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match="non-byte artifact"):
        run_isolated_validation(config(artifact_root, "P6-CODEX-BYTES"), spec)
    assert not artifact_root.exists()


def test_public_registry_remains_empty() -> None:
    from tools.bridge.live.run_isolated_validation import ENABLED_ADAPTERS

    assert ENABLED_ADAPTERS == {}
