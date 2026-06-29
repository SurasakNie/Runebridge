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


def parse_qwen_result(stdout: str, config: ValidationConfig) -> ParsedArtifact:
    try:
        envelope = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ValidationError("Qwen stdout is not one JSON document") from exc
    if not isinstance(envelope, dict) or envelope.get("type") != "result" or envelope.get("is_error") is not False:
        raise ValidationError("Qwen did not return a successful result envelope")
    payload = envelope.get("structured_output")
    if not isinstance(payload, dict):
        raise ValidationError("Qwen result envelope lacks structured output")
    cost = envelope.get("total_cost_usd")
    if isinstance(cost, bool) or not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0:
        raise ValidationError("Qwen result envelope lacks a valid reported cost")
    if cost > config.budget_ceiling_usd:
        raise ValidationError("Qwen reported cost exceeds the approved budget")
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
    return ParsedArtifact("REVIEW_QWEN.json", content, payload, budget_result="within_ceiling")


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
        authentication_class="environment_secret",
        credentials_available=True,
        model_identifier=model_identifier,
        environment_keys=("QWEN_API_KEY",),
        result_parser=parse_qwen_result,
    )
