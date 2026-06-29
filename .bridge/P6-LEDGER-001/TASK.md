---
task_id: P6-LEDGER-001
requester: human
created_at: 2026-06-28
risk_level: RSK-1
mode: safe-default
branch: bridge/P6-LEDGER-001-approval-ledger
---
# Task

Implement the approval-ledger mechanism required by the Phase 6 live-run
preflight so the isolated validation runner can bind a per-run `approval_id` to
an approved ledger entry and fail closed when no entry matches.

## Scope

- Add a draft-07 schema and a committed, fail-closed-by-default approval ledger.
- Add a runner check that refuses, before any vendor invocation, unless an entry
  matches the run's `approval_id`, `vendor`, `role`, and `run_date`.
- Add fake-CLI tests for present, absent, mismatched, and malformed cases.

## Constraints

- No live vendor call, and no vendor adapter registration. `ENABLED_ADAPTERS`
  stays empty in the shared remote environment.
- The ledger contains no credentials, host names, emails, or paths.
- Architecture is fixed by `docs/Phase-6-Qwen-Live-Evidence-Plan.md`; this task
  builds only the approval-ledger portion of that plan.
