from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, FormatChecker

from tools.bridge.live.run_isolated_validation import (
    APPROVAL_LEDGER,
    AdapterSpec,
    ValidationConfig,
    ValidationError,
    assert_approved,
    load_approval_ledger,
    run_isolated_validation,
)


ROOT = Path(__file__).resolve().parents[2]
LEDGER_SCHEMA = ROOT / "schemas/approval-ledger.schema.json"
RUN_DATE = "2026-06-28"
APPROVAL_ID = "P6-QWEN-REVIEW-APPROVAL"


def write_fake(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8", newline="\n")
    return path


def live_spec(script: Path) -> AdapterSpec:
    # An approved credentialed run (not a test fixture), so the ledger applies.
    return AdapterSpec(
        command=(str(Path(sys.executable).resolve()), str(script)),
        cli_name="fake-qwen",
        cli_version="0.19.2",
        authentication_class="interactive_session",
        credentials_available=True,
        model_identifier="qwen-turbo",
    )


def config(root: Path, **overrides: object) -> ValidationConfig:
    values: dict[str, object] = {
        "task_id": "P6-LEDGER-RUN-001",
        "vendor": "qwen",
        "role": "reviewer",
        "approval_id": APPROVAL_ID,
        "run_date": RUN_DATE,
        "artifact_root": root,
        "timeout_seconds": 5,
        "budget_ceiling_usd": 0.06,
        "live": True,
    }
    values.update(overrides)
    return ValidationConfig(**values)  # type: ignore[arg-type]


def entry(**overrides: str) -> dict[str, str]:
    base = {
        "approval_id": APPROVAL_ID,
        "vendor": "qwen",
        "role": "reviewer",
        "run_date": RUN_DATE,
        "approved_by": "owner",
        "rsk_level": "RSK-1",
    }
    base.update(overrides)
    return base


def write_ledger(path: Path, entries: list[dict[str, str]]) -> Path:
    path.write_text(json.dumps({"entries": entries}), encoding="utf-8", newline="\n")
    return path


def ok_script(tmp_path: Path) -> Path:
    return write_fake(tmp_path / "ok.py", "import json\nprint(json.dumps({'status': 'ok'}))\n")


def marker_script(tmp_path: Path, marker: Path) -> Path:
    return write_fake(
        tmp_path / "marker.py",
        f"from pathlib import Path\nPath({str(marker)!r}).touch()\n"
        "import json\nprint(json.dumps({'status': 'ok'}))\n",
    )


def test_matching_entry_allows_run(tmp_path: Path) -> None:
    ledger = write_ledger(tmp_path / "ledger.json", [entry()])
    task_dir = run_isolated_validation(
        config(tmp_path / "artifacts"),
        live_spec(ok_script(tmp_path)),
        ledger_path=ledger,
    )
    metadata = json.loads((task_dir / "LIVE_RUN_METADATA.json").read_text(encoding="utf-8"))
    assert metadata["vendor"] == "qwen"
    assert metadata["role"] == "reviewer"
    assert metadata["model_identifier"] == "qwen-turbo"
    assert metadata["credentials_available"] is True


def test_absent_entry_refuses_before_invocation(tmp_path: Path) -> None:
    marker = tmp_path / "invoked"
    ledger = write_ledger(tmp_path / "ledger.json", [])
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match="not approved in the ledger"):
        run_isolated_validation(
            config(artifact_root),
            live_spec(marker_script(tmp_path, marker)),
            ledger_path=ledger,
        )
    assert not marker.exists()
    assert not artifact_root.exists()


@pytest.mark.parametrize(
    "mismatch",
    (
        {"vendor": "claude"},
        {"role": "planner"},
        {"run_date": "2026-06-27"},
        {"approval_id": "P6-OTHER-APPROVAL"},
    ),
)
def test_vendor_role_date_or_id_mismatch_refuses(tmp_path: Path, mismatch: dict[str, str]) -> None:
    marker = tmp_path / "invoked"
    ledger = write_ledger(tmp_path / "ledger.json", [entry(**mismatch)])
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match="not approved in the ledger"):
        run_isolated_validation(
            config(artifact_root),
            live_spec(marker_script(tmp_path, marker)),
            ledger_path=ledger,
        )
    assert not marker.exists()
    assert not artifact_root.exists()


@pytest.mark.parametrize(
    "body",
    (
        "not json at all",
        json.dumps({"entries": "not-a-list"}),
        json.dumps({"items": []}),
        json.dumps({"entries": [{"approval_id": APPROVAL_ID}]}),
        json.dumps({"entries": [dict(entry(), vendor="unknown")]}),
        json.dumps({"entries": [dict(entry(), run_date="not-a-date")]}),
        json.dumps({"entries": [dict(entry(), rsk_level="RSK-9")]}),
        json.dumps({"entries": [dict(entry(), approval_id="ab")]}),
    ),
)
def test_malformed_ledger_refuses(tmp_path: Path, body: str) -> None:
    marker = tmp_path / "invoked"
    ledger = write_fake(tmp_path / "ledger.json", body)
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError):
        run_isolated_validation(
            config(artifact_root),
            live_spec(marker_script(tmp_path, marker)),
            ledger_path=ledger,
        )
    assert not marker.exists()
    assert not artifact_root.exists()


def test_missing_ledger_file_refuses(tmp_path: Path) -> None:
    marker = tmp_path / "invoked"
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match="missing or unreadable"):
        run_isolated_validation(
            config(artifact_root),
            live_spec(marker_script(tmp_path, marker)),
            ledger_path=tmp_path / "absent.json",
        )
    assert not marker.exists()
    assert not artifact_root.exists()


def test_test_fixture_run_skips_ledger(tmp_path: Path) -> None:
    # A test fixture declares no credentials and must not require a ledger entry,
    # even when the (default committed) ledger is empty.
    fixture = AdapterSpec(
        command=(str(Path(sys.executable).resolve()), str(ok_script(tmp_path))),
        cli_name="fake-cli",
        cli_version="1.0.0",
        authentication_class="test_fixture",
        credentials_available=False,
    )
    task_dir = run_isolated_validation(config(tmp_path / "artifacts"), fixture)
    assert (task_dir / "LIVE_RUN_METADATA.json").exists()


def test_assert_approved_matches_only_on_all_four_fields() -> None:
    ledger = [entry()]
    assert_approved(config(Path(".")), ledger)
    with pytest.raises(ValidationError):
        assert_approved(config(Path("."), role="planner"), ledger)


def test_committed_ledger_is_empty_and_loads() -> None:
    assert load_approval_ledger(APPROVAL_LEDGER) == []


def test_committed_ledger_validates_against_schema() -> None:
    schema = json.loads(LEDGER_SCHEMA.read_text(encoding="utf-8"))
    document = json.loads(APPROVAL_LEDGER.read_text(encoding="utf-8"))
    errors = list(Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(document))
    assert errors == []
