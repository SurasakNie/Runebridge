from __future__ import annotations

import json
import math
from pathlib import Path

from jsonschema import Draft7Validator

from tools.bridge.live.run_isolated_validation import (
    AdapterSpec,
    ParsedArtifact,
    ValidationConfig,
    ValidationError,
    read_schema,
)


def _extract_result_envelope(output: object) -> dict:
    """Return the result-type event dict from a Qwen CLI JSON output."""
    if isinstance(output, dict):
        return output
    if isinstance(output, list):
        events = [e for e in output if isinstance(e, dict) and e.get("type") == "result"]
        if not events:
            raise ValidationError("Qwen output array contains no result event")
        return events[-1]
    raise ValidationError("Qwen stdout is not a JSON object or array")


def parse_qwen_result(stdout: str, config: ValidationConfig) -> ParsedArtifact:
    try:
        output = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ValidationError("Qwen stdout is not valid JSON") from exc
    envelope = _extract_result_envelope(output)
    if envelope.get("is_error") is not False:
        err = envelope.get("error")
        detail = err.get("message", "") if isinstance(err, dict) else ""
        raise ValidationError(
            f"Qwen did not return a successful result envelope: {detail}"
            if detail
            else "Qwen did not return a successful result envelope"
        )
    payload = envelope.get("structured_output")
    if not isinstance(payload, dict):
        raise ValidationError("Qwen result envelope lacks structured output")
    # Qwen CLI 0.19.2 omits total_cost_usd; budget_result="not_reported" is the
    # schema-valid value when no USD figure is available.
    raw_cost = envelope.get("total_cost_usd")
    if raw_cost is None:
        budget_result = "not_reported"
    else:
        if (
            isinstance(raw_cost, bool)
            or not isinstance(raw_cost, (int, float))
            or not math.isfinite(raw_cost)
            or raw_cost < 0
        ):
            raise ValidationError("Qwen result envelope has an invalid total_cost_usd")
        if raw_cost > config.budget_ceiling_usd:
            raise ValidationError("Qwen reported cost exceeds the approved budget")
        budget_result = "within_ceiling"
    errors = sorted(
        Draft7Validator(read_schema("review.schema.json")).iter_errors(payload),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise ValidationError("Qwen structured output failed the review schema")
    if payload.get("reviewer") != "qwen":
        raise ValidationError("Qwen reviewer output has the wrong reviewer")
    if payload.get("task_id") != config.task_id:
        raise ValidationError("Qwen reviewer output has the wrong task ID")
    content = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return ParsedArtifact("REVIEW_QWEN.json", content, payload, budget_result=budget_result)


def build_qwen_adapter(
    executable: Path,
    *,
    cli_version: str,
    task_id: str,
    budget_ceiling_usd: float,
    prompt: str,
    model_identifier: str | None = None,
) -> AdapterSpec:
    schema = read_schema("review.schema.json")
    bound_prompt = (
        f"Runebridge synthetic reviewer contract for task {task_id}. "
        "Return only the structured output required by the supplied JSON Schema. "
        f"The task_id must be exactly {task_id}. The reviewer must be 'qwen'. "
        f"Fixture: {prompt}"
    )
    # Flags verified against Qwen Code CLI 0.19.2 on 2026-06-29.
    # --print absent; positional prompt is one-shot by default.
    # --tools absent; --max-tool-calls 0 blocks non-structured tools (structured_output exempt).
    # --no-session-persistence absent; --no-chat-recording is the equivalent.
    # --disable-slash-commands absent; not needed in headless mode.
    # --max-budget-usd absent; runner validates total_cost_usd from envelope post-run.
    # Auth is stored browser OAuth; no API key env var required (interactive_session).
    command_parts: list[str] = [
        str(executable.resolve()),
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(schema, separators=(",", ":"), sort_keys=True),
        "--max-tool-calls",
        "0",
        "--no-chat-recording",
    ]
    if model_identifier is not None:
        command_parts += ["--model", model_identifier]
    command_parts.append(bound_prompt)
    command = tuple(command_parts)
    return AdapterSpec(
        command=command,
        cli_name="qwen",
        cli_version=cli_version,
        authentication_class="interactive_session",
        credentials_available=True,
        model_identifier=model_identifier,
        result_parser=parse_qwen_result,
    )
