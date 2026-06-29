from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

import tools.bridge.live.run_isolated_validation as runner_module
from tools.bridge.live.qwen_adapters import parse_qwen_result
from tools.bridge.live.run_isolated_validation import (
    AdapterSpec,
    ValidationConfig,
    ValidationError,
)


RUN_DATE = "2026-06-29"
TASK_ID = "P6-QWEN-ADAPTER-TEST"


def write_fake(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8", newline="\n")
    return path


def fixture_spec(script: Path) -> AdapterSpec:
    return AdapterSpec(
        command=(str(Path(sys.executable).resolve()), str(script)),
        cli_name="fake-qwen",
        cli_version="0.1.0",
        authentication_class="test_fixture",
        credentials_available=False,
        model_identifier="qwen-turbo",
        result_parser=parse_qwen_result,
    )


def config(root: Path) -> ValidationConfig:
    return ValidationConfig(
        task_id=TASK_ID,
        vendor="qwen",
        role="reviewer",
        approval_id="P6-QWEN-TEST-001",
        run_date=RUN_DATE,
        artifact_root=root,
        timeout_seconds=5,
        budget_ceiling_usd=0.10,
        live=True,
    )


def valid_payload(task_id: str = TASK_ID) -> dict:
    return {
        "task_id": task_id,
        "reviewer": "qwen",
        "verdict": "approve",
        "blockers": [],
        "bugs_found": [],
        "missing_tests": [],
        "scope_drift": False,
        "security_concerns": [],
        "suggestions": [],
    }


def valid_envelope(task_id: str = TASK_ID, cost: float = 0.02) -> str:
    return json.dumps({"type": "result", "is_error": False, "structured_output": valid_payload(task_id), "total_cost_usd": cost})


def valid_array_envelope(task_id: str = TASK_ID) -> str:
    """Mirrors the actual Qwen CLI 0.19.2 --output-format json output (array, no total_cost_usd)."""
    return json.dumps([
        {"type": "system", "subtype": "init", "session_id": "test"},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "..."}]}},
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "structured_output": valid_payload(task_id),
            "usage": {"input_tokens": 1000, "output_tokens": 100, "total_tokens": 1100},
        },
    ])


def ok_script(tmp_path: Path) -> Path:
    return write_fake(tmp_path / "ok.py", f"print({valid_envelope()!r})\n")


def test_valid_reviewer_output_accepted(tmp_path: Path) -> None:
    task_dir = runner_module.run_isolated_validation(
        config(tmp_path / "artifacts"),
        fixture_spec(ok_script(tmp_path)),
    )
    artifact = json.loads((task_dir / "REVIEW_QWEN.json").read_text(encoding="utf-8"))
    assert artifact["reviewer"] == "qwen"
    assert artifact["verdict"] == "approve"
    assert artifact["task_id"] == TASK_ID


def test_wrong_reviewer_rejected(tmp_path: Path) -> None:
    env = json.loads(valid_envelope())
    # Use "claude" reviewer; add the allOf-required Claude fields so the payload
    # is schema-valid and the explicit reviewer guard is reached.
    env["structured_output"]["reviewer"] = "claude"
    env["structured_output"]["risk_assessment"] = "RSK-1"
    env["structured_output"]["human_review_required"] = False
    env["structured_output"]["notes"] = []
    script = write_fake(tmp_path / "wrong.py", f"print({json.dumps(env)!r})\n")
    with pytest.raises(ValidationError, match="wrong reviewer"):
        runner_module.run_isolated_validation(config(tmp_path / "artifacts"), fixture_spec(script))


def test_wrong_task_id_rejected(tmp_path: Path) -> None:
    script = write_fake(tmp_path / "wrong.py", f"print({valid_envelope(task_id='WRONG-TASK')!r})\n")
    with pytest.raises(ValidationError, match="wrong task ID"):
        runner_module.run_isolated_validation(config(tmp_path / "artifacts"), fixture_spec(script))


def test_schema_invalid_payload_rejected(tmp_path: Path) -> None:
    env = json.loads(valid_envelope())
    del env["structured_output"]["verdict"]
    script = write_fake(tmp_path / "invalid.py", f"print({json.dumps(env)!r})\n")
    with pytest.raises(ValidationError, match="review schema"):
        runner_module.run_isolated_validation(config(tmp_path / "artifacts"), fixture_spec(script))


def test_cost_exceeded_rejected(tmp_path: Path) -> None:
    script = write_fake(tmp_path / "costly.py", f"print({valid_envelope(cost=99.99)!r})\n")
    with pytest.raises(ValidationError, match="exceeds the approved budget"):
        runner_module.run_isolated_validation(config(tmp_path / "artifacts"), fixture_spec(script))


def test_missing_structured_output_rejected(tmp_path: Path) -> None:
    env = {"type": "result", "is_error": False, "total_cost_usd": 0.01}
    script = write_fake(tmp_path / "missing.py", f"print({json.dumps(env)!r})\n")
    with pytest.raises(ValidationError, match="lacks structured output"):
        runner_module.run_isolated_validation(config(tmp_path / "artifacts"), fixture_spec(script))


def test_invalid_envelope_rejected(tmp_path: Path) -> None:
    script = write_fake(tmp_path / "bad.py", 'print("not json")\n')
    with pytest.raises(ValidationError):
        runner_module.run_isolated_validation(config(tmp_path / "artifacts"), fixture_spec(script))


def test_enabled_adapters_stays_empty(tmp_path: Path) -> None:
    import tools.bridge.live.qwen_adapters  # noqa: F401
    importlib.reload(runner_module)
    assert runner_module.ENABLED_ADAPTERS == {}


def test_array_format_accepted(tmp_path: Path) -> None:
    """Qwen CLI 0.19.2 emits a JSON array; the parser must handle it."""
    script = write_fake(tmp_path / "array.py", f"print({valid_array_envelope()!r})\n")
    task_dir = runner_module.run_isolated_validation(
        config(tmp_path / "artifacts"),
        fixture_spec(script),
    )
    artifact = json.loads((task_dir / "REVIEW_QWEN.json").read_text(encoding="utf-8"))
    assert artifact["reviewer"] == "qwen"
    assert artifact["verdict"] == "approve"


def test_is_error_true_rejected(tmp_path: Path) -> None:
    """Qwen returns is_error: true when the model skips the structured_output tool."""
    error_result = json.dumps([
        {"type": "system", "subtype": "init", "session_id": "test"},
        {
            "type": "result",
            "subtype": "error_during_execution",
            "is_error": True,
            "error": {"message": "Model produced plain text instead of calling the structured_output tool."},
            "usage": {"input_tokens": 500, "output_tokens": 10, "total_tokens": 510},
        },
    ])
    script = write_fake(tmp_path / "err.py", f"print({error_result!r})\n")
    with pytest.raises(ValidationError, match="successful result envelope"):
        runner_module.run_isolated_validation(config(tmp_path / "artifacts"), fixture_spec(script))


def test_missing_cost_accepted_with_token_count(tmp_path: Path) -> None:
    """When total_cost_usd is absent, parse succeeds with budget_result=token_count_only."""
    script = write_fake(tmp_path / "nocost.py", f"print({valid_array_envelope()!r})\n")
    task_dir = runner_module.run_isolated_validation(
        config(tmp_path / "artifacts"),
        fixture_spec(script),
    )
    artifact = json.loads((task_dir / "REVIEW_QWEN.json").read_text(encoding="utf-8"))
    assert artifact["reviewer"] == "qwen"
