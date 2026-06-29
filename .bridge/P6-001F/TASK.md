---
task_id: P6-001F
requester: human
created_at: "2026-06-29"
risk_level: RSK-1
mode: safe-default
branch: P6-001F-execution
---
# Task

Execute the bounded Codex builder validation run under explicit per-run human approval.

## Ratified parameters

| Parameter | Value |
|---|---|
| Approval ID | `P6-001F-RUN-001` |
| Model | `codex-mini-latest` |
| Timeout | `30 s` |
| Budget ceiling | `$0.06` |
| Approach | Direct runner (`build_codex_adapter` + `run_isolated_validation`); no conductor |
| Environment | Local-only execution on an approved runner |

## Scope

- Invoke `build_codex_adapter` with the ratified parameters and a synthetic
  `fixture.txt` workspace.
- Run `run_isolated_validation` (live mode) and let it emit
  `LIVE_RUN_METADATA.json`, `EDIT_CODEX.md`, and `CHANGES.diff`.
- Commit only the sanitized evidence files; never commit raw stdout, stderr,
  workspace paths, session identifiers, or API tokens.
- Update `.ai/TASKS.md` to mark P6-001F Complete after evidence review.

## Constraints

- Per-run human approval (`P6-001F-RUN-001`) must be recorded in
  `tools/bridge/live/approval-ledger.json` before the runner is invoked.
- The run must pass the P6-001F execution preflight in
  `docs/Phase-6-Live-Vendor-Validation-Plan.md` before execution.
- The `codex` CLI flags in `build_codex_adapter` are contract assumptions only;
  verify with `codex --help` and update `codex_adapters.py` if they differ.
- Synthetic fixture only — no repository source, customer data, or secrets.
- Runner-emitted `LIVE_RUN_METADATA.json` only; do not hand-author it.
- No credential, API key, host name, email, or absolute path may be committed.
- Write sandbox: disposable workspace, narrowest supported scope, no Git repo.
