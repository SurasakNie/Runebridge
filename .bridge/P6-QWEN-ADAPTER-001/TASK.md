---
task_id: P6-QWEN-ADAPTER-001
requester: human
created_at: "2026-06-29"
risk_level: RSK-1
mode: safe-default
branch: bridge/P6-QWEN-ADAPTER-001-qwen-reviewer-adapter
---
# Task

Implement the Qwen reviewer adapter module so the isolated validation runner
can execute a bounded live Qwen reviewer run on the approved PC runner.

## Scope

- Add `tools/bridge/live/qwen_adapters.py` with a `build_qwen_adapter` factory
  and a `parse_qwen_result` parser that validates the reviewer artifact against
  `review.schema.json`.
- Add `tests/live/test_qwen_adapters.py` with fake-CLI contract tests covering
  the valid and invalid output cases.
- Do **not** register the adapter in `ENABLED_ADAPTERS` in
  `run_isolated_validation.py`; the PC runner constructs the spec directly and
  passes it to `run_isolated_validation`. The shared remote environment must
  never activate a real Qwen adapter.

## Constraints

- No live vendor call in this task. All tests use fake-CLI scripts.
- `ENABLED_ADAPTERS` stays empty. No import of `qwen_adapters` from
  `run_isolated_validation.py`.
- The Qwen CLI executable path, flags, and JSON output envelope format must be
  confirmed during the PC preflight before the live run. Record any deviations
  from the assumed envelope in the PR description.
- No credential, API key, host name, email, or absolute path may be committed.
- Architecture is fixed by `docs/Phase-6-Qwen-Live-Evidence-Plan.md` and
  `docs/PC-Runner-Session-Handoff.md`.
