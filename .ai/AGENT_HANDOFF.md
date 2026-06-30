# Agent Handoff

## Current State

Phases 0.5A through 5 are complete. The Phase 6 plan, isolated runner, Claude planner/reviewer adapter contracts, Codex builder adapter contract, approval-ledger mechanism (P6-LEDGER-001, PR #24), and Qwen reviewer adapter (P6-QWEN-ADAPTER-001, PR #27) are all merged. The public adapter registry remains empty, so no real vendor or live execution is enabled in the shared remote environment. Qwen provider/auth decisions are recorded, the shared remote environment remains blocked by egress-policy `403 Forbidden`, and the approved operating model is `PC-first, VM-later` for Qwen live execution. P6-001D and P6-001F remain gated on explicit per-run human approval.

**P6-001H-EVID is COMPLETE — first live Qwen reviewer evidence merged (PR #33, `2351d91`).** The live-invocation blocker was resolved in PR #31 (`ff4dfad`): Qwen Code CLI `0.19.2` returns the schema-valid review JSON in the result envelope's `result` string field, not in `structured_output`, so the parser falls back through `structured_output` → `structured_result` → JSON-parsed `result` (plus runner hardening: daemon-thread stdout/stderr readers for Windows pipe-inheritance, `use_dedicated_vendor_cwd`, `APPDATA`/`LOCALAPPDATA`/`USERPROFILE` passthrough, `--max-tool-calls 3`, tail-not-head diagnostics). The bounded live run then executed on the approved PC runner with model `qwen3.6-plus`: `execution=live`, `exit_code=0`, all gates passed, `blocked_command_count=0`, `budget_result=not_reported`. Evidence lives at `.bridge/P6-001H-EVID/` (REVIEW_QWEN.json, runner-emitted LIVE_RUN_METADATA.json, BLOCKED_COMMANDS.log) with `REVIEW_CLAUDE.json` verdict **approve** (RSK-1, human_review_required true). The Qwen review *content* is synthetic-fixture output, not a real code review — the value is the proven end-to-end live pipeline. Full suite **140 passing**.

## Last Agent

| Field | Value |
|---|---|
| Tool | Claude Code |
| Date | 2026-06-30 |
| Branch | claude/p6-001h-evid-complete (manual maintenance) |
| Task | Post-PR #33 reconciliation: mark P6-001H-EVID Complete |

## What Was Changed

- Reconciled status after PR #33 (`2351d91`), the merged P6-001H-EVID live evidence bundle.
- Marked P6-001H-EVID and its parent P6-001H **Complete** in `.ai/TASKS.md`.
- Updated `.ai/AGENT_HANDOFF.md` and `.ai/CHANGELOG_AI.md`.

## Files Modified

- `.ai/TASKS.md`
- `.ai/AGENT_HANDOFF.md`
- `.ai/CHANGELOG_AI.md`

## Tests Run

140 passed (full suite, verified against `origin/main`). No code changes in this reconciliation commit.

## Known Issues

- No real vendor adapter is registered in ENABLED_ADAPTERS; the public runner refuses live dispatch with exit code 2.
- Codex CLI flags are contract assumptions only; `codex --help` must be verified before P6-001F.
- The shared remote environment returns egress-policy `403 Forbidden` to approved Qwen provider hosts; live Qwen depends on the owner's approved PC runner.
- Codex CLI flags are contract assumptions only; `codex --help` must be verified before P6-001F.
- Antigravity remains deferred until a supported headless interface exists.
- The conductor GitHub App must be installed and verified before automated PR operations.
- The Qwen parser `result`-string path assumes bare JSON (the P6-001H-EVID live run confirmed bare JSON, no fences). If a future Qwen build wraps the JSON in markdown fences or prose, `json.loads(result)` fails **closed** (no bad evidence) and `_extract_payload` must be made fence-tolerant before re-running.
- The Qwen free OAuth login tier ended 2026-04-15; live runs now depend on a paid Alibaba coding/Model-Studio plan. The trial quota is ~1,000,000 tokens per model, so a different `--model` (e.g. `qwen3.7-plus`, `qwen3-coder-plus`) is a fresh allotment — but any new live run needs a new single-use ledger entry and produces new evidence.
- P6-QWEN-ADAPTER-001 and P6-LEDGER-001 were built and reviewed by the same model; REVIEW_CLAUDE.json for P6-001H-EVID is `human_review_required: true` — independent human sign-off recommended before integrating live Qwen into the conductor (P6-001J).

## Next Recommended Step

P6-001H-EVID is complete (PR #33 merged). The next live-validation target is **P6-001F — bounded Codex builder validation**, which follows the same pattern as the Qwen run and already has a runbook at `docs/PC-Runner-P6-001F-Handoff.md`. On the approved PC runner:

1. Verify `codex --help` flags against `tools/bridge/live/codex_adapters.py` (`exec`, `--json`, `--sandbox workspace-write`, `--schema`, `--budget-usd`); update the adapter + re-run `pytest tests/live/test_codex_adapters.py` if they differ.
2. Add a single-use approval-ledger entry for the Codex run (run-day date) and obtain per-run human approval.
3. Run the bounded validation, secret-scan the evidence, commit the sanitized artifacts + ledger entry, open the PR; produce `REVIEW_CLAUDE.json` here.

After that: P6-001D (bounded Claude validation), then P6-001G (Claude/Codex hybrid), then P6-001J (conductor integration) and P6-001K (Phase 6 report).

## Warnings

Do not treat the shared remote environment as live-Qwen-capable while provider hosts return egress-policy `403 Forbidden`. Do not register a real adapter, execute live Qwen outside an approved external runner, or enable automated GitHub operations. Keep future merges human-controlled.
