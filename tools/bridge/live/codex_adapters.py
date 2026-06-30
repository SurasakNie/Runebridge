from __future__ import annotations

import json
import math
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

from tools.bridge.live.run_isolated_validation import (
    AdapterSpec,
    ParsedArtifact,
    ValidationConfig,
    ValidationError,
    read_schema,
)


SYNTHETIC_WORKSPACE_FILE = "fixture.txt"


def validate_edit_summary(payload: dict[str, object], task_id: str) -> None:
    errors = sorted(
        Draft7Validator(read_schema("edit-summary.schema.json")).iter_errors(payload),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise ValidationError("Codex structured output failed the edit summary schema")
    if payload.get("task_id") != task_id:
        raise ValidationError("Codex structured output has the wrong task ID")
    if payload.get("tool") != "codex":
        raise ValidationError("Codex structured output has the wrong tool")
    if payload.get("dry_run") is not False:
        raise ValidationError("Codex live contract output must not claim dry-run execution")
    if payload.get("files_changed") != [SYNTHETIC_WORKSPACE_FILE]:
        raise ValidationError("Codex structured output does not match the approved synthetic scope")


def validate_synthetic_diff(diff_text: str) -> None:
    if not diff_text.strip():
        raise ValidationError("Codex builder contract requires a non-empty diff")
    has_before = False
    has_after = False
    for line in diff_text.splitlines():
        if line.startswith(f"--- a/{SYNTHETIC_WORKSPACE_FILE}") and (
            len(line) == len(f"--- a/{SYNTHETIC_WORKSPACE_FILE}")
            or line[len(f"--- a/{SYNTHETIC_WORKSPACE_FILE}")] in {"\t", " "}
        ):
            has_before = True
        if line.startswith(f"+++ b/{SYNTHETIC_WORKSPACE_FILE}") and (
            len(line) == len(f"+++ b/{SYNTHETIC_WORKSPACE_FILE}")
            or line[len(f"+++ b/{SYNTHETIC_WORKSPACE_FILE}")] in {"\t", " "}
        ):
            has_after = True
    if not has_before or not has_after:
        raise ValidationError("Codex diff does not match the approved synthetic scope")


def render_edit_summary(payload: dict[str, object]) -> bytes:
    front_matter = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).strip()
    body = (
        "\n\n# Implementation Summary\n\n"
        "Synthetic Codex builder contract validated a bounded workspace edit.\n"
    )
    return f"---\n{front_matter}\n---{body}".encode("utf-8")


def parse_codex_result(stdout: str, config: ValidationConfig) -> ParsedArtifact:
    try:
        envelope = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ValidationError("Codex stdout is not one JSON result envelope") from exc
    if not isinstance(envelope, dict) or envelope.get("type") != "result" or envelope.get("is_error") is not False:
        raise ValidationError("Codex did not return a successful result envelope")
    payload = envelope.get("structured_output")
    if not isinstance(payload, dict):
        raise ValidationError("Codex result envelope lacks structured output")
    cost = envelope.get("total_cost_usd")
    if isinstance(cost, bool) or not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0:
        raise ValidationError("Codex result envelope lacks a valid reported cost")
    if cost > config.budget_ceiling_usd:
        raise ValidationError("Codex reported cost exceeds the approved budget")
    diff_text = envelope.get("changes_diff")
    if not isinstance(diff_text, str):
        raise ValidationError("Codex result envelope lacks a diff")
    validate_edit_summary(payload, config.task_id)
    validate_synthetic_diff(diff_text)
    return ParsedArtifact(
        "EDIT_CODEX.md",
        render_edit_summary(payload),
        payload,
        budget_result="within_ceiling",
        extra_artifacts=(("CHANGES.diff", diff_text.encode("utf-8")),),
    )


def build_codex_adapter(
    executable: Path,
    *,
    cli_version: str,
    task_id: str,
    budget_ceiling_usd: float,
    prompt: str,
    model_identifier: str | None = None,
) -> AdapterSpec:
    schema = read_schema("edit-summary.schema.json")
    bound_prompt = (
        f"Runebridge synthetic builder contract for task {task_id}. "
        f"The working directory is empty; create exactly one file named "
        f"{SYNTHETIC_WORKSPACE_FILE} in it and write no other file. "
        "Return exactly one JSON result envelope (type=result, is_error=false) whose "
        f"structured_output matches the supplied schema with task_id exactly {task_id}, "
        f'tool=codex, dry_run=false, and files_changed exactly ["{SYNTHETIC_WORKSPACE_FILE}"]. '
        "Put the unified diff in changes_diff and write its headers as exactly "
        f"'--- a/{SYNTHETIC_WORKSPACE_FILE}' and '+++ b/{SYNTHETIC_WORKSPACE_FILE}' "
        "(use these a/ and b/ headers even though the file is newly created). "
        f"Fixture: {prompt}"
    )
    command = (
        str(executable.resolve()),
        "exec",
        "--json",
        "--sandbox",
        "workspace-write",
        "--schema",
        json.dumps(schema, separators=(",", ":"), sort_keys=True),
        "--budget-usd",
        format(budget_ceiling_usd, ".2f"),
        bound_prompt,
    )
    return AdapterSpec(
        command=command,
        cli_name="codex",
        cli_version=cli_version,
        authentication_class="interactive_session",
        credentials_available=True,
        model_identifier=model_identifier,
        result_parser=parse_codex_result,
        allowed_workspace_files=(SYNTHETIC_WORKSPACE_FILE,),
    )
