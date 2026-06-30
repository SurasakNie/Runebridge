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


def _extract_payload(envelope: dict) -> dict | None:
    payload = envelope.get("structured_output")
    if isinstance(payload, dict):
        return payload
    payload = envelope.get("structured_result")
    if isinstance(payload, dict):
        return payload
    result = envelope.get("result")
    if isinstance(result, str):
        try:
            payload = json.loads(result)
        except json.JSONDecodeError as exc:
            raise ValidationError("Qwen result field is not valid JSON") from exc
        if isinstance(payload, dict):
            return payload
    return None


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
    payload = _extract_payload(envelope)
    if payload is None:
        # Transient console diagnostic only (never durable evidence): surface the
        # result event's keys and a truncated snippet so the operator can see
        # where the model actually placed its answer. The prompt is synthetic
        # and secret-free.
        diag = json.dumps(envelope, default=str, sort_keys=True)[:1500]
        raise ValidationError(
            "Qwen result envelope lacks structured output. "
            f"Result event keys: {sorted(k for k in envelope if isinstance(k, str))}. "
            f"Envelope snippet: {diag}"
        )
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
        "Do NOT read files, search, fetch web content, or call any other tool. "
        "Immediately emit ONLY the structured output required by the supplied "
        "JSON Schema, using exactly one structured-output tool call. "
        f"The task_id must be exactly {task_id}. The reviewer must be 'qwen'. "
        f"Fixture: {prompt}"
    )
    # Flags verified against Qwen Code CLI 0.19.2 on 2026-06-29.
    # --print absent; positional prompt is one-shot by default.
    # --max-tool-calls 3: Qwen emits structured output VIA a tool call, so a
    #   budget of 0 aborts with FatalBudgetExceededError (exit code 55). With a
    #   budget of 1 the run is flaky: the model occasionally spends its single
    #   call on a preliminary tool_search/read_file, then cannot emit structured
    #   output. A small budget of 3 absorbs that variance while staying tightly
    #   bounded. The prompt explicitly forbids non-structured tool use, so the
    #   model should go straight to the structured-output call. Defense in depth:
    #   the workspace scope check (empty), the secret gate over every artifact,
    #   the synthetic secret-free prompt, the 60s timeout, and the process-tree
    #   kill on timeout bound the blast radius. If the model misbehaves and emits
    #   no structured output, the run fails closed (is_error).
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
        "3",
        "--no-chat-recording",
    ]
    if model_identifier is not None:
        command_parts += ["--model", model_identifier]
    command_parts.append(bound_prompt)
    command = tuple(command_parts)
    # On Windows, Qwen stores OAuth credentials under %APPDATA%\qwen (Electron).
    # APPDATA, LOCALAPPDATA, and USERPROFILE are path pointers, not secrets; the
    # secret gate blocks absolute paths in artifacts so they cannot leak.
    # use_dedicated_vendor_cwd isolates Qwen's background processes (e.g.
    # managed-auto-memory-extractor) from the scope-checked workspace so their
    # transient temp files do not cause spurious scope failures or WinError 32.
    return AdapterSpec(
        command=command,
        cli_name="qwen",
        cli_version=cli_version,
        authentication_class="interactive_session",
        credentials_available=True,
        model_identifier=model_identifier,
        environment_keys=("APPDATA", "LOCALAPPDATA", "USERPROFILE"),
        use_dedicated_vendor_cwd=True,
        result_parser=parse_qwen_result,
    )
