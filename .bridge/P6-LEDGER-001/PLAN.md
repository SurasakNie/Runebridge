---
task_id: P6-LEDGER-001
planner: claude
risk_level: RSK-1
files_to_touch:
  - schemas/approval-ledger.schema.json
  - tools/bridge/live/approval-ledger.json
  - tools/bridge/live/run_isolated_validation.py
  - tests/live/test_approval_ledger.py
acceptance_criteria:
  - "gate check_plan.py exits 0 on this PLAN.md"
  - "schemas/approval-ledger.schema.json is valid draft-07 JSON and loads without error"
  - "tools/bridge/live/approval-ledger.json validates against schemas/approval-ledger.schema.json"
  - "the runner refuses (raises ValidationError before vendor invocation) when no ledger entry matches the run approval_id, vendor, role, and run_date"
  - "the runner passes the ledger check when a matching entry exists, demonstrated with a fake-CLI adapter"
  - "tests/live/test_approval_ledger.py covers present, absent, vendor/role/date mismatch, and malformed-ledger cases and all pass"
  - "check_no_secrets.py exits 0 over tools/bridge/live/approval-ledger.json"
  - "the full existing pytest suite still passes and Phase 5 dry-run byte-identity tests are unchanged"
requires_human_approval: false
---
# Plan — P6-LEDGER-001 Approval Ledger

## Goal

Give the isolated validation runner a fail-closed approval-ledger binding so a
live run only proceeds when its `approval_id` was genuinely approved for that
vendor, role, and date.

## Approach

1. **Schema** — add `schemas/approval-ledger.schema.json` (draft-07). The
   document is an object with a single `entries` array; each entry is an object
   with `additionalProperties: false` and required fields:
   - `approval_id` — pattern `^[A-Za-z0-9][A-Za-z0-9._-]{2,63}$` (matches the
     runner's existing `APPROVAL_ID_PATTERN`).
   - `vendor` — enum `["claude", "codex", "qwen", "antigravity"]`.
   - `role` — enum `["planner", "builder", "reviewer", "verifier"]`.
   - `run_date` — `format: date`.
   - `approved_by` — non-empty string (e.g. `owner`).
   - `rsk_level` — enum `["RSK-0", "RSK-1", "RSK-2"]`.
   Forbid any key that could carry a secret by keeping `additionalProperties:
   false` at both levels.

2. **Ledger file** — add `tools/bridge/live/approval-ledger.json` containing
   `{"entries": []}`. An empty ledger is the correct fail-closed default: every
   live run refuses until the owner adds an approved entry. The owner appends one
   entry per approved run on the PC runner; entries are never added in the shared
   remote environment.

3. **Runner binding** — in `tools/bridge/live/run_isolated_validation.py`:
   - Add a module constant `APPROVAL_LEDGER = ROOT / "tools/bridge/live/approval-ledger.json"`.
   - Add `load_approval_ledger(path) -> list[dict]` that reads and schema-checks
     the ledger (reuse the existing schema-validation helper), raising
     `ValidationError` on a missing or malformed file.
   - Add `assert_approved(config, ledger)` that raises `ValidationError` unless
     some entry matches `config.approval_id`, `config.vendor`, `config.role`, and
     `config.run_date` exactly.
   - Call the ledger check inside `validate_config` (or immediately after it in
     `run_isolated_validation`, before `validate_adapter`), so refusal happens
     before any environment build or vendor invocation. Keep the existing
     pattern/structure checks; the ledger check is additive.
   - Add an optional `ledger_path` parameter (default `APPROVAL_LEDGER`) to
     `run_isolated_validation` so tests can inject a temporary ledger without
     touching the committed file.

4. **Tests** — add `tests/live/test_approval_ledger.py` using the existing
   fake-CLI/adapter fixtures from `tests/live/test_isolated_runner.py` so a
   matching entry lets a run proceed to a successful artifact, and the mismatch
   cases refuse before invocation.

## Risks

RSK-1. The change touches live-execution infrastructure but adds only a
fail-closed pre-invocation refusal; it enables no vendor, makes no network call,
and leaves `ENABLED_ADAPTERS` empty. The main risk is a bypassable or
order-wrong check (refusal must occur before any vendor invocation), mitigated by
the absent/mismatch tests asserting no adapter command runs.

## Acceptance criteria

See the front-matter `acceptance_criteria`. Each maps to a verification check:
schema load, ledger validation, the four runner-behaviour tests, the secret gate
over the ledger, and the unchanged full suite plus dry-run byte-identity.

## Stop conditions

- Stop and set `requires_human_approval: true` if the task is reinterpreted to
  register a vendor adapter or make any live call — that is out of scope here and
  RSK-0 in the shared remote environment.
- Stop if any ledger field would require committing a secret, host name, email,
  or path.
- The scope gate must halt if the implementation touches any file outside
  `files_to_touch`.
- Stop if the binding cannot be ordered before vendor invocation without
  restructuring unrelated runner logic; re-plan instead.

## Out of scope

- Qwen reviewer adapter registration (separate reviewed PR, never in the shared
  remote environment).
- The bounded live Qwen run itself, which is PC-runner only and human-approved.
- Conductor integration (P6-001J) and the Phase 6 report (P6-001K).
