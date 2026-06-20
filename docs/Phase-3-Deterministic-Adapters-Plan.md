# Phase 3 Deterministic Adapter Plan

## Objective

Implement role-specific adapter stubs that produce byte-stable, schema-valid dry-run artifacts without vendor credentials, network access, Git writes, or GitHub mutations.

## Adapter Inventory

| Adapter | Output |
|---|---|
| `claude_plan.sh` | `PLAN.md` with `planner: claude` |
| `qwen_plan.sh` | `PLAN.md` with `planner: qwen` |
| `codex_build.sh` | `EDIT_CODEX.md` and `CHANGES.diff` |
| `qwen_build.sh` | `EDIT_QWEN.md` and `CHANGES.diff` |
| `qwen_review.sh` | `REVIEW_QWEN.json` |
| `mock_verify.sh` | `VERIFY.json` |
| `claude_review.sh` | `REVIEW_CLAUDE.json` |

Antigravity remains deferred. No production adapter is implemented until a supported headless interface passes Phase 6 validation.

## Contract

- Each adapter accepts exactly one `.bridge/<task-id>/` directory.
- `DRY_RUN_MODE=true` is mandatory; any other value exits `2` before writing.
- Outputs are overwritten atomically enough for local dry-run use and contain no timestamps, random values, credentials, or host-specific paths.
- Repeated identical runs produce identical bytes.
- Role adapters write only their designated artifacts.
- Phase 2 gates validate every generated artifact.
- Every generated artifact's `task_id` must match `TASK.md`.

## Tests

- Run every adapter in a temporary task directory.
- Validate generated artifacts with the Phase 2 gates.
- Run each adapter twice and compare SHA-256 hashes.
- Verify live mode exits `2` and produces no role artifact.
- Verify Qwen-led flow omits `REVIEW_QWEN.json` by not invoking that adapter.
- Verify safe-default, qwen-led, and dual-builder artifact matrices.

## Exit Gate

All adapter contract tests pass locally and in protected CI without credentials or network access. Live integration remains deferred to Phase 6.
