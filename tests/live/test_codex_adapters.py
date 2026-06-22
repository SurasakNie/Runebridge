from __future__ import annotations

import json
import hashlib
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tools.bridge.live.codex_adapters import SYNTHETIC_WORKSPACE_FILE, build_codex_adapter
from tools.bridge.live.run_isolated_validation import (
    AdapterSpec,
    ParsedArtifact,
    ValidationConfig,
    ValidationError,
    run_isolated_validation,
)


RUN_DATE = "2026-06-22"
ROOT = Path(__file__).resolve().parents[2]


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


def builder_payload(task_id: str) -> dict[str, object]:
    return {
        "task_id": task_id,
        "tool": "codex",
        "files_changed": [SYNTHETIC_WORKSPACE_FILE],
        "tests": ["synthetic builder contract passed"],
        "dry_run": False,
    }


def synthetic_diff() -> str:
    return (
        f"--- a/{SYNTHETIC_WORKSPACE_FILE}\t2026-06-22 00:00:00 +0000\n"
        f"+++ b/{SYNTHETIC_WORKSPACE_FILE}\t2026-06-22 00:00:01 +0000\n"
        "@@ -0,0 +1 @@\n"
        "+synthetic bounded edit\n"
    )


def fake_adapter(
    tmp_path: Path,
    task_id: str,
    envelope: dict[str, object],
    *,
    write_fixture: bool = True,
    write_extra: bool = False,
):
    script = tmp_path / "fake-codex.py"
    lines = ["from pathlib import Path", "import json"]
    if write_fixture:
        lines.append(f"Path({SYNTHETIC_WORKSPACE_FILE!r}).write_text('synthetic bounded edit\\n', encoding='utf-8')")
    if write_extra:
        lines.append("Path('unexpected.txt').write_text('scope drift\\n', encoding='utf-8')")
    lines.append(f"print({json.dumps(json.dumps(envelope))})")
    script.write_text("\n".join(lines) + "\n", encoding="utf-8")
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
    envelope = {
        "type": "result",
        "is_error": False,
        "total_cost_usd": 0.04,
        "structured_output": builder_payload(task_id),
        "changes_diff": synthetic_diff(),
    }
    task_dir = run_isolated_validation(
        config(tmp_path / "artifacts", task_id),
        fake_adapter(tmp_path, task_id, envelope),
    )
    assert {path.name for path in task_dir.iterdir()} == {
        "EDIT_CODEX.md",
        "CHANGES.diff",
        "BLOCKED_COMMANDS.log",
        "LIVE_RUN_METADATA.json",
    }
    edit_text = (task_dir / "EDIT_CODEX.md").read_text(encoding="utf-8")
    assert yaml.safe_load(edit_text.split("---", 2)[1]) == builder_payload(task_id)
    assert (task_dir / "CHANGES.diff").read_text(encoding="utf-8") == synthetic_diff()
    metadata = json.loads((task_dir / "LIVE_RUN_METADATA.json").read_text(encoding="utf-8"))
    assert metadata["vendor"] == "codex"
    assert metadata["role"] == "builder"
    assert metadata["budget_result"] == "within_ceiling"
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


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ({"total_cost_usd": 0.07}, "exceeds"),
        ({"total_cost_usd": None}, "reported cost"),
        ({"structured_output": {"task_id": "WRONG"}}, "edit summary schema"),
        ({"changes_diff": ""}, "non-empty diff"),
        ({"is_error": True}, "successful result"),
    ),
)
def test_fake_codex_contract_fails_closed(
    tmp_path: Path, mutation: dict[str, object], message: str
) -> None:
    task_id = "P6-CODEX-FAIL"
    envelope = {
        "type": "result",
        "is_error": False,
        "total_cost_usd": 0.04,
        "structured_output": builder_payload(task_id),
        "changes_diff": synthetic_diff(),
        **mutation,
    }
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match=message):
        run_isolated_validation(
            config(artifact_root, task_id),
            fake_adapter(tmp_path, task_id, envelope),
        )
    assert not artifact_root.exists()


def test_codex_workspace_scope_rejects_extra_write(tmp_path: Path) -> None:
    task_id = "P6-CODEX-DRIFT"
    envelope = {
        "type": "result",
        "is_error": False,
        "total_cost_usd": 0.04,
        "structured_output": builder_payload(task_id),
        "changes_diff": synthetic_diff(),
    }
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match="workspace scope"):
        run_isolated_validation(
            config(artifact_root, task_id),
            fake_adapter(tmp_path, task_id, envelope, write_extra=True),
        )
    assert not artifact_root.exists()


def test_codex_workspace_scope_requires_declared_write(tmp_path: Path) -> None:
    task_id = "P6-CODEX-MISSING"
    envelope = {
        "type": "result",
        "is_error": False,
        "total_cost_usd": 0.04,
        "structured_output": builder_payload(task_id),
        "changes_diff": synthetic_diff(),
    }
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match="approved workspace file"):
        run_isolated_validation(
            config(artifact_root, task_id),
            fake_adapter(tmp_path, task_id, envelope, write_fixture=False),
        )
    assert not artifact_root.exists()


def test_codex_command_uses_workspace_sandbox_and_bounds_budget(tmp_path: Path) -> None:
    spec = build_codex_adapter(
        Path(sys.executable),
        cli_version="fixture",
        task_id="P6-CODEX-COMMAND",
        budget_ceiling_usd=0.06,
        prompt="synthetic fixture",
    )
    assert spec.command[1:3] == ("exec", "--json")
    assert spec.command[spec.command.index("--sandbox") + 1] == "workspace-write"
    assert spec.command[spec.command.index("--budget-usd") + 1] == "0.06"
    assert "P6-CODEX-COMMAND" in spec.command[-1]
    assert spec.allowed_workspace_files == (SYNTHETIC_WORKSPACE_FILE,)


def test_extra_artifact_content_must_be_bytes(tmp_path: Path) -> None:
    script = tmp_path / "fake.py"
    script.write_text("import json\nprint(json.dumps({'status': 'ok'}))\n", encoding="utf-8")

    def parser(_stdout: str, _config: ValidationConfig) -> ParsedArtifact:
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
