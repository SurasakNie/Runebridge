---
task_id: P6-QWEN-ADAPTER-001
planner: claude
risk_level: RSK-1
files_to_touch:
  - tools/bridge/live/qwen_adapters.py
  - tests/live/test_qwen_adapters.py
acceptance_criteria:
  - "gate check_plan.py exits 0 on this PLAN.md"
  - "tools/bridge/live/qwen_adapters.py exports build_qwen_adapter and parse_qwen_result; it does not import from or modify run_isolated_validation.ENABLED_ADAPTERS"
  - "parse_qwen_result validates the structured output against review.schema.json, checks reviewer == 'qwen' and task_id match, and raises ValidationError on any violation"
  - "build_qwen_adapter returns an AdapterSpec with authentication_class='environment_secret', environment_keys containing the QWEN_API_KEY key name, and result_parser bound to parse_qwen_result"
  - "fake-CLI tests cover: valid reviewer output accepted; wrong reviewer rejected; wrong task_id rejected; schema-invalid payload rejected; cost-exceeded rejected; missing structured_output rejected; invalid envelope rejected"
  - "check_no_secrets.py exits 0 over tools/bridge/live/qwen_adapters.py"
  - "full pytest suite passes with no regressions; run_isolated_validation.ENABLED_ADAPTERS remains empty after import"
requires_human_approval: false
---
# Plan — P6-QWEN-ADAPTER-001 Qwen Reviewer Adapter

## Goal

Give the isolated validation runner a Qwen reviewer adapter module so the
approved PC runner can build and pass a real `AdapterSpec` to
`run_isolated_validation` for a bounded live Qwen reviewer run. The adapter
is never registered in `ENABLED_ADAPTERS` and is never imported by the shared
remote environment's runner; activation is always explicit and PC-local.

## Approach

### 1. `tools/bridge/live/qwen_adapters.py`

Mirror the structure of `claude_adapters.py` for the reviewer role only.

**`parse_qwen_result(stdout, config) -> ParsedArtifact`**

Parse the Qwen CLI stdout as a JSON result envelope. Assumed envelope shape
(to be confirmed during the PC preflight):

```json
{
  "type": "result",
  "is_error": false,
  "structured_output": { ...review.schema fields... },
  "total_cost_usd": 0.04
}
```

Steps:
1. `json.loads(stdout)` — raise `ValidationError` on decode failure.
2. Check `envelope["type"] == "result"` and `envelope["is_error"] is False`.
3. Extract `envelope["structured_output"]` — must be a dict.
4. Extract `envelope["total_cost_usd"]` — must be a finite non-negative float;
   raise `ValidationError` if it exceeds `config.budget_ceiling_usd`.
5. Validate `structured_output` against `review.schema.json` using
   `Draft7Validator(read_schema("review.schema.json"))`.
6. Check `structured_output["reviewer"] == "qwen"` and
   `structured_output["task_id"] == config.task_id`.
7. Return `ParsedArtifact("REVIEW_QWEN.json", content, normalized,
   budget_result="within_ceiling")` where `content` is the canonical
   JSON serialisation of `structured_output`.

**PC preflight note:** If the real Qwen CLI stdout differs from the assumed
envelope (e.g., uses a different key for cost, or wraps output differently),
the builder must update `parse_qwen_result` to match and record the exact
deviation in the PR description. The fake-CLI tests define the contract the
real CLI must match; if they cannot, update the adapter and tests together.

**`build_qwen_adapter(executable, *, cli_version, task_id, budget_ceiling_usd, prompt, model_identifier=None) -> AdapterSpec`**

Constructs the `AdapterSpec` for the Qwen reviewer. Key properties:

- `authentication_class = "environment_secret"` — the Qwen API key is
  injected as `QWEN_API_KEY` in the approved PC environment; it is never
  committed.
- `credentials_available = True` for a live run.
- `environment_keys = ("QWEN_API_KEY",)` — allows the runner to pass the
  key into the sandboxed environment.
- `allowed_workspace_files = ()` — reviewer role writes nothing to the
  workspace.
- `result_parser` — bound to `parse_qwen_result`.
- `model_identifier` — nullable; set to the pinned model (e.g.
  `"qwen-turbo"`) when known.

Assumed CLI command structure (to be confirmed during PC preflight):

```python
command = (
    str(executable.resolve()),
    "--output-format", "json",
    "--json-schema", json.dumps(schema, ...),
    "--no-session-persistence",
    "--max-budget-usd", format(budget_ceiling_usd, ".2f"),
    bound_prompt,
)
```

where `bound_prompt` follows the same pattern as `build_claude_adapter`:

```
"Runebridge synthetic reviewer contract for task {task_id}. "
"Return only the structured output required by the supplied JSON Schema. "
"The task_id must be exactly {task_id}. The reviewer must be 'qwen'. "
"Fixture: {prompt}"
```

The builder **must** run `qwen --help` (or equivalent) on the PC and replace
the assumed flags with the actual flags before using the adapter. Document
the verified flags in the PR description.

### 2. `tests/live/test_qwen_adapters.py`

Use the same fake-CLI pattern as `test_codex_adapters.py` and
`test_isolated_runner.py`. Each fake script is a small Python file that
prints a specific JSON envelope to stdout and exits 0.

Required test cases (all using `authentication_class="test_fixture"` so
ledger checks are bypassed for unit testing):

| Test | Fake stdout | Expected outcome |
|---|---|---|
| `test_valid_reviewer_output_accepted` | Valid `REVIEW_QWEN.json` envelope | Run succeeds; artifact written |
| `test_wrong_reviewer_rejected` | `reviewer: "claude"` | `ValidationError` |
| `test_wrong_task_id_rejected` | `task_id: "WRONG"` | `ValidationError` |
| `test_schema_invalid_payload_rejected` | Missing required `verdict` | `ValidationError` |
| `test_cost_exceeded_rejected` | `total_cost_usd` > ceiling | `ValidationError` |
| `test_missing_structured_output_rejected` | No `structured_output` key | `ValidationError` |
| `test_invalid_envelope_rejected` | Not JSON / wrong envelope shape | `ValidationError` |
| `test_enabled_adapters_stays_empty` | Import `run_isolated_validation` | `ENABLED_ADAPTERS == {}` |

The last test asserts that importing `run_isolated_validation` after importing
`qwen_adapters` does not populate `ENABLED_ADAPTERS` — this is the key guard
against accidental registration.

## Risks

RSK-1. The module makes no live call, registers no adapter in the shared
runner, and touches only two new files. The main risk is an incorrect CLI
flag assumption: mitigated by (a) explicitly marking all CLI flags as PC
preflight items and (b) requiring the builder to record verified flags in the
PR before merge.

A secondary risk is that the Qwen envelope differs structurally from the
assumed shape. Mitigated by the fake-CLI contract tests — they define the
shape the real CLI must match and will catch a wrong-format adapter at the PR
review stage if the builder updates only the adapter but not the tests.

## Stop conditions

- Stop and re-plan if the Qwen CLI output cannot be made to match any
  parseable JSON envelope without modifying `run_isolated_validation.py`
  shared infrastructure — that is a separate plan change.
- Stop if any flag, credential, host name, or environment value would need
  to be committed to the repository.
- Stop if registering the adapter in `ENABLED_ADAPTERS` appears necessary —
  it is not; the PC runner constructs the spec directly.
- Stop if the scope gate halts on files outside `files_to_touch`.

## Out of scope

- Live Qwen run (Step 3 in `docs/PC-Runner-Session-Handoff.md`).
- Adding a ledger entry for the live run (owner action, PC only).
- Promoting the staged Qwen evidence to official status (P6-001H-EVID).
- Conductor integration (P6-001J) and Phase 6 report (P6-001K).
