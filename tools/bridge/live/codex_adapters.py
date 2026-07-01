from __future__ import annotations

import json
import tempfile
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

# Codex CLI 0.141.0's --output-schema is enforced via OpenAI structured
# outputs, which rejects several ordinary JSON Schema validation keywords
# (confirmed empirically: uniqueItems is rejected outright with
# invalid_json_schema; pattern/minLength/maxItems/minItems are undocumented
# for strict mode and are stripped defensively too). The full schema is still
# enforced locally afterward against the real structured output.
UNSUPPORTED_OUTPUT_SCHEMA_KEYWORDS = frozenset(
    {"uniqueItems", "pattern", "minLength", "maxLength", "minItems", "maxItems", "format"}
)


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


def render_synthetic_diff(content: str) -> str:
    """Codex CLI 0.141.0 reports file writes only as {"path", "kind": "add"}
    metadata; it never emits diff text. The runner must synthesize the diff
    itself from the actual workspace file it already validated was written."""
    lines = content.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    hunk_header = f"@@ -0,0 +1,{len(lines)} @@\n" if lines else "@@ -0,0 +0,0 @@\n"
    hunk_body = "".join(f"+{line}" for line in lines)
    return f"--- a/{SYNTHETIC_WORKSPACE_FILE}\n+++ b/{SYNTHETIC_WORKSPACE_FILE}\n{hunk_header}{hunk_body}"


def _relax_schema_for_output(node: object) -> object:
    if isinstance(node, dict):
        return {
            key: _relax_schema_for_output(value)
            for key, value in node.items()
            if key not in UNSUPPORTED_OUTPUT_SCHEMA_KEYWORDS
        }
    if isinstance(node, list):
        return [_relax_schema_for_output(item) for item in node]
    return node


def write_relaxed_output_schema(schema: dict[str, object]) -> Path:
    relaxed = _relax_schema_for_output(schema)
    handle = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", prefix="runebridge-codex-schema-", delete=False, encoding="utf-8"
    )
    try:
        json.dump(relaxed, handle, separators=(",", ":"), sort_keys=True)
    finally:
        handle.close()
    return Path(handle.name)


def _parse_jsonl_events(stdout: str) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValidationError("Codex stdout is not one JSON event per line") from exc
        if isinstance(event, dict):
            events.append(event)
    return events


def parse_codex_result(stdout: str, config: ValidationConfig, workspace: Path) -> ParsedArtifact:
    events = _parse_jsonl_events(stdout)
    for event in events:
        if event.get("type") in {"error", "turn.failed"}:
            error_field = event.get("error")
            detail = event.get("message") or (error_field.get("message", "") if isinstance(error_field, dict) else "")
            raise ValidationError(
                f"Codex reported a failed turn: {detail}" if detail else "Codex reported a failed turn"
            )
    if not any(event.get("type") == "turn.completed" for event in events):
        raise ValidationError("Codex did not report a completed turn")
    agent_messages = [
        event["item"]
        for event in events
        if event.get("type") == "item.completed"
        and isinstance(event.get("item"), dict)
        and event["item"].get("type") == "agent_message"
    ]
    if not agent_messages:
        raise ValidationError("Codex did not return a final agent message")
    text = agent_messages[-1].get("text")
    if not isinstance(text, str):
        raise ValidationError("Codex final agent message has no text")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValidationError("Codex final agent message is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValidationError("Codex structured output is not a JSON object")
    validate_edit_summary(payload, config.task_id)
    fixture_path = workspace / SYNTHETIC_WORKSPACE_FILE
    try:
        fixture_content = fixture_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValidationError("Codex did not create the approved workspace file") from exc
    diff_text = render_synthetic_diff(fixture_content)
    validate_synthetic_diff(diff_text)
    return ParsedArtifact(
        "EDIT_CODEX.md",
        render_edit_summary(payload),
        payload,
        # Codex CLI 0.141.0 reports token usage, not a dollar cost, and has no
        # --budget-usd flag; "not_reported" is the schema-valid value already
        # established by the Qwen adapter for the same situation.
        budget_result="not_reported",
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
    schema_path = write_relaxed_output_schema(schema)
    bound_prompt = (
        f"Runebridge synthetic builder contract for task {task_id}. "
        f"The working directory is empty; create exactly one file named "
        f"{SYNTHETIC_WORKSPACE_FILE} in it and write no other file. "
        "Return exactly one structured JSON response matching the supplied schema, "
        f"with task_id exactly {task_id}, tool=codex, dry_run=false, "
        f'files_changed exactly ["{SYNTHETIC_WORKSPACE_FILE}"], and tests=[]. '
        f"Fixture: {prompt}"
    )
    command_parts: list[str] = [
        str(executable.resolve()),
        "exec",
        "--json",
        "--sandbox",
        "workspace-write",
        "--skip-git-repo-check",
        "--output-schema",
        str(schema_path),
    ]
    if model_identifier is not None:
        command_parts += ["--model", model_identifier]
    command_parts.append(bound_prompt)
    return AdapterSpec(
        command=tuple(command_parts),
        cli_name="codex",
        cli_version=cli_version,
        authentication_class="interactive_session",
        credentials_available=True,
        model_identifier=model_identifier,
        result_parser=parse_codex_result,
        allowed_workspace_files=(SYNTHETIC_WORKSPACE_FILE,),
    )
