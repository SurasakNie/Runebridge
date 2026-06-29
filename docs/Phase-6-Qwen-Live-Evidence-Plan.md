# Phase 6 Qwen Live-Evidence Capture Plan

## Status

Architect plan for promoting the staged synthetic Qwen reviewer evidence in
`.bridge/P6-QWEN-REVIEW-001/` to official Phase 6 live evidence. This document
plans the work; it does not authorize live inference, register a vendor adapter,
or enable live execution. It is the architect deliverable for the Tier 2 step
recorded in `.ai/AGENT_HANDOFF.md` and the P6-001H follow-through.

## Objective

Capture an approval-bound `LIVE_RUN_METADATA.json` for one bounded live Qwen
reviewer run on the approved PC runner, and bind its `approval_id` to an approval
ledger, so the run can be promoted from `provisional-pass` to official Phase 6
live evidence.

## Current State

The staging directory `.bridge/P6-QWEN-REVIEW-001/` holds:

| File | Role | Note |
|---|---|---|
| `TASK.md` | Task brief | RSK-1, `safe-default`, synthetic fixture only |
| `REVIEW_QWEN.json` | Reviewer artifact | sha256 `7194e0cad2a1eb7032ef382429edf48b15622f20d44d8d464a9b5244a3114594`; passes `check_review.py --reviewer qwen` |
| `FINAL_REPORT.md` | Run report | `status: provisional-pass`; `live_metadata: pending` |

No `LIVE_RUN_METADATA.json` exists, so the directory is staging, not official
evidence. (The recorded artifact hash above is a present fact about the staged
file; a real run regenerates the artifact and its hash on the PC runner, so this
value is a reference for reconciliation, not a value to copy into official
metadata.)

## Gap Analysis

| ID | Gap | Owner | Blocks |
|---|---|---|---|
| G1 | No Qwen reviewer adapter is registered (`ENABLED_ADAPTERS` is empty in `tools/bridge/live/run_isolated_validation.py`); the runner refuses with exit 2. | Pipeline builder | The runner cannot produce metadata until a reviewed adapter is registered. The standing warning forbids registering a real adapter in the shared remote environment. |
| G2 | ~~No approval-ledger mechanism exists~~ Implemented as `P6-LEDGER-001`: a draft-07 schema, a fail-closed committed ledger, and a runner binding that refuses real credentialed runs whose `approval_id`/`vendor`/`role`/`run_date` lack a matching entry. | Done (awaiting independent review) | Preflight item "approval-ledger binding" is now satisfiable; the owner adds an approved entry per live run. |
| G3 | The shared remote environment returns egress-policy `403 Forbidden` to approved Qwen provider hosts. | Owner / environment | The live run cannot execute here; it must run on the approved PC runner. |
| G4 | `cli_version`, `model_identifier`, `budget_result`, and the artifact/result hashes are execution-time facts. | Owner (live run) | Official metadata cannot be authored ahead of the run. |

## Official Metadata Field Sources

`schemas/live-run-metadata.schema.json` requires 22 fields. Each value's origin:

| Field | Source | Constraint |
|---|---|---|
| `task_id` | Run config | Single-use; e.g. a new `P6-QWEN-REVIEW-*` id |
| `vendor` | Run config | `qwen` |
| `role` | Run config | `reviewer` |
| `execution` | Runner | const `live` |
| `cli_name` | Adapter spec | e.g. `qwen` / `qwen-code` |
| `cli_version` | Live preflight | Pinned and recorded from the installed CLI |
| `model_identifier` | Vendor response | e.g. `qwen-turbo`; nullable if unreported |
| `authentication_class` | Adapter spec | `interactive_session` or `environment_secret` (not `test_fixture`) |
| `credentials_available` | Adapter spec | `true` for a live run |
| `approval_id_sha256` | Runner | `sha256(approval_id)`; must match a ledger entry (G2) |
| `artifact_sha256s` | Runner | Computed from emitted artifacts |
| `exit_code` | Runner | const `0` |
| `attempt_count` | Runner | const `1` |
| `timeout_seconds` | Run config | 1–300; reviewer fixture default 30 |
| `budget_ceiling_usd` | Run config | >0 and ≤10 |
| `budget_result` | Vendor/runner | `within_ceiling` or `not_reported` |
| `blocked_command_count` | Runner | const `0` |
| `schema_valid` | Runner | const `true` |
| `scope_valid` | Runner | const `true` (reviewer = no-write scope) |
| `secret_scan_passed` | Runner | const `true` after the secret gate |
| `result_sha256` | Runner | sha256 of the normalized result |
| `run_date` | Run config | `YYYY-MM-DD` |

Conclusion: the runner already emits a schema-shaped `LIVE_RUN_METADATA.json`
(`run_isolated_validation.py`). The missing pieces are a registered Qwen reviewer
adapter (G1) and the approval-ledger binding (G2). No official metadata should be
hand-authored; it must be runner-emitted from the real run.

## Approval-Ledger Design (proposal for the builder)

The ledger gives the runner a fail-closed check that an `approval_id` was
genuinely approved for a specific vendor, role, and date. It is not a vendor
adapter and contains no secrets.

- **Artifact:** a committed, append-only JSON file (proposed
  `tools/bridge/live/approval-ledger.json`) plus a draft-07 schema (proposed
  `schemas/approval-ledger.schema.json`).
- **Entry shape (proposed):**
  ```json
  {
    "approval_id": "P6-QWEN-REVIEW-002",
    "approval_id_sha256": "<sha256 of approval_id>",
    "vendor": "qwen",
    "role": "reviewer",
    "run_date": "YYYY-MM-DD",
    "approved_by": "owner",
    "rsk_level": "RSK-1"
  }
  ```
- **Binding rule:** the runner must refuse before invoking the vendor unless an
  entry matches the run's `approval_id`, `vendor`, `role`, and `run_date`. A
  missing or mismatched entry fails closed (`ValidationError`), consistent with
  the runner's existing pre-invocation checks.
- **Privacy:** `approval_id` is an approval reference, not a credential; it may be
  stored. The ledger must contain no API keys, account emails, host names, or
  paths. The existing `check_no_secrets.py` gate must pass over it.
- **Tests (fake-CLI, no live call):** present-entry approves; absent entry
  refuses; vendor/role/date mismatch refuses; malformed ledger fails preflight.

## Execution Procedure (owner, on the approved PC runner)

These steps cannot run in CI or the shared remote environment. They require the
real `qwen` CLI, an approved session, working provider egress, and explicit
per-run approval.

1. Record an approval-ledger entry for a fresh single-use `task_id` and
   `approval_id` (vendor `qwen`, role `reviewer`, today's date).
2. Verify the installed `qwen` CLI flags and pin `cli_version`; reject versions
   outside the approved policy.
3. Run the isolated validation runner with `--live`, the approved
   `--approval-id`, `--vendor qwen --role reviewer`, the synthetic reviewer
   fixture, `--timeout-seconds 30`, and an approved `--budget-ceiling-usd`.
4. Let the runner emit `LIVE_RUN_METADATA.json` and run the metadata and secret
   gates. Do not hand-edit the metadata.
5. Confirm the run wrote no out-of-scope files and `BLOCKED_COMMANDS.log` is
   empty.
6. Commit only the sanitized evidence (new task directory) to a review branch;
   the owner reviews and merges manually.

## Pipeline Routing

The approval-ledger portion (G2) is routed through the pipeline as task
`P6-LEDGER-001`. Its Plan-stage artifact `.bridge/P6-LEDGER-001/PLAN.md`
(planner: claude) is written and passes `check_plan.py`; a builder (Codex/Qwen)
implements it from that plan, and Claude reviews. It makes no live call and
registers no adapter, so it can be built off the PC runner. The Qwen reviewer
adapter (G1) and the live run (G3/G4) remain separate, PC-gated steps.

## Files To Touch (builder PR, separate from this plan)

- `schemas/approval-ledger.schema.json` (new)
- `tools/bridge/live/approval-ledger.json` (new; initial approved entries)
- `tools/bridge/live/run_isolated_validation.py` (add ledger binding check)
- `tools/bridge/live/` Qwen reviewer adapter registration (separate reviewed PR;
  not in the shared remote environment)
- `tests/live/` ledger-binding and Qwen reviewer adapter tests (fake CLI)
- `.bridge/<new-task-id>/` runner-emitted evidence (execution PR, PC runner only)

## Acceptance Criteria

1. A draft-07 approval-ledger schema and a committed ledger exist, with passing
   fake-CLI tests for present/absent/mismatch/malformed cases.
2. The runner refuses any live run whose `approval_id` is absent from the ledger
   for the run's vendor, role, and date.
3. A bounded live Qwen reviewer run on the approved PC runner emits a
   schema-valid, runner-generated `LIVE_RUN_METADATA.json` with `execution: live`,
   `exit_code: 0`, `attempt_count: 1`, `blocked_command_count: 0`, and an
   `approval_id_sha256` matching a ledger entry.
4. The metadata and secret gates pass over the new evidence; no secret, key,
   email, or path is committed.
5. `FINAL_REPORT.md` for the run moves from `provisional-pass` to a status
   reflecting official, approval-bound live evidence, and `.ai/` status files are
   reconciled.

## Risks and RSK Levels

| Risk | RSK | Mitigation |
|---|---|---|
| Hand-authoring metadata fabricates official evidence | RSK-0 | Metadata must be runner-emitted only; never hand-edited |
| Registering a real adapter in the shared remote environment | RSK-0 | Adapter registration is a separate reviewed PR, never in the shared remote environment |
| Credential or host leakage into the ledger or evidence | RSK-0 | Secret gate over all committed files; ledger stores no secrets |
| Approval reuse across runs | RSK-1 | Single-use `task_id`/`approval_id`; date-scoped ledger entries |
| Provider egress unavailable on the runner | RSK-1 | Run only on an approved PC runner with confirmed egress; otherwise defer |

## Stop Conditions

- Stop if the approval ledger is missing, malformed, or lacks a matching entry.
- Stop if provider egress is unavailable on the chosen runner.
- Stop if any gate fails or any out-of-scope write or blocked command is detected.
- Stop and escalate (RSK-0) on any suspected credential exposure.

## Out of Scope

- Any all-live pipeline claim (a single reviewer run is one role only).
- Conductor integration (P6-001J) and the Phase 6 validation report (P6-001K).
- Authoring adapter or ledger source in the shared remote environment; this plan
  is read-only with respect to live execution.
