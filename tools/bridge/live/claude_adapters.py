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


ROLE_ARTIFACTS = {"planner": "PLAN.md", "reviewer": "REVIEW_CLAUDE.json"}
ROLE_SCHEMAS = {"planner": "plan.schema.json", "reviewer": "review.schema.json"}


def validate_role_payload(role: str, payload: dict[str, object], task_id: str) -> None:
    if role not in ROLE_SCHEMAS:
        raise ValidationError("Claude adapter supports only planner and reviewer roles")
    errors = sorted(
        Draft7Validator(read_schema(ROLE_SCHEMAS[role])).iter_errors(payload),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise ValidationError("Claude structured output failed the role schema")
    if payload.get("task_id") != task_id:
        raise ValidationError("Claude structured output has the wrong task ID")
    if role == "planner" and payload.get("planner") != "claude":
        raise ValidationError("Claude planner output has the wrong planner")
    if role == "reviewer" and payload.get("reviewer") != "claude":
        raise ValidationError("Claude reviewer output has the wrong reviewer")


def render_plan(payload: dict[str, object]) -> bytes:
    front_matter = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).strip()
    body = (
        "\n\n# Live Adapter Contract Plan\n\n"
        "This synthetic artifact validates the Claude planner structured-output contract.\n"
    )
    return f"---\n{front_matter}\n---{body}".encode("utf-8")


def parse_claude_result(role: str, stdout: str, config: ValidationConfig, _workspace: Path) -> ParsedArtifact:
    try:
        envelope = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ValidationError("Claude stdout is not one JSON result envelope") from exc
    if not isinstance(envelope, dict) or envelope.get("type") != "result" or envelope.get("is_error") is not False:
        raise ValidationError("Claude did not return a successful result envelope")
    payload = envelope.get("structured_output")
    if not isinstance(payload, dict):
        raise ValidationError("Claude result envelope lacks structured output")
    cost = envelope.get("total_cost_usd")
    if isinstance(cost, bool) or not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0:
        raise ValidationError("Claude result envelope lacks a valid reported cost")
    if cost > config.budget_ceiling_usd:
        raise ValidationError("Claude reported cost exceeds the approved budget")
    validate_role_payload(role, payload, config.task_id)
    if role == "planner":
        content = render_plan(payload)
    else:
        content = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return ParsedArtifact(
        ROLE_ARTIFACTS[role],
        content,
        payload,
        budget_result="within_ceiling",
    )


def build_claude_adapter(
    executable: Path,
    *,
    cli_version: str,
    role: str,
    task_id: str,
    budget_ceiling_usd: float,
    prompt: str,
    model_identifier: str | None = None,
) -> AdapterSpec:
    if role not in ROLE_SCHEMAS:
        raise ValidationError("Claude adapter supports only planner and reviewer roles")
    schema = read_schema(ROLE_SCHEMAS[role])
    bound_prompt = (
        f"Runebridge synthetic {role} contract for task {task_id}. "
        "Return only the structured output required by the supplied JSON Schema. "
        f"The task_id must be exactly {task_id}. "
        f"Fixture: {prompt}"
    )
    command = (
        str(executable.resolve()),
        "--print",
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(schema, separators=(",", ":"), sort_keys=True),
        "--tools",
        "",
        "--no-session-persistence",
        "--disable-slash-commands",
        "--max-budget-usd",
        format(budget_ceiling_usd, ".2f"),
        bound_prompt,
    )
    return AdapterSpec(
        command=command,
        cli_name="claude",
        cli_version=cli_version,
        authentication_class="interactive_session",
        credentials_available=True,
        model_identifier=model_identifier,
        result_parser=lambda stdout, config, workspace: parse_claude_result(role, stdout, config, workspace),
    )
