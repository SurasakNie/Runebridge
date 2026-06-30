# Agent Handoff

## Current State

Phases 0.5A through 5 are complete. The Phase 6 plan, isolated runner, Claude planner/reviewer adapter contracts, Codex builder adapter contract, approval-ledger mechanism (P6-LEDGER-001, PR #24), and Qwen reviewer adapter (P6-QWEN-ADAPTER-001, PR #27) are all merged. The public adapter registry remains empty, so no real vendor or live execution is enabled in the shared remote environment. Qwen provider/auth decisions are recorded, the shared remote environment remains blocked by egress-policy `403 Forbidden`, and the approved operating model is `PC-first, VM-later` for Qwen live execution. P6-001D and P6-001F remain gated on explicit per-run human approval.

**P6-001H-EVID is COMPLETE — first live Qwen reviewer evidence merged (PR #33, `2351d91`).** The live-invocation blocker was resolved in PR #31 (`ff4dfad`): Qwen Code CLI `0.19.2` returns the schema-valid review JSON in the result envelope's `result` string field, not in `structured_output`, so the parser falls back through `structured_output` → `structured_result` → JSON-parsed `result` (plus runner hardening: daemon-thread stdout/stderr readers for Windows pipe-inheritance, `use_dedicated_vendor_cwd`, `APPDATA`/`LOCALAPPDATA`/`USERPROFILE` passthrough, `--max-tool-calls 3`, tail-not-head diagnostics). The bounded live run then executed on the approved PC runner with model `qwen3.6-plus`: `execution=live`, `exit_code=0`, all gates passed, `blocked_command_count=0`, `budget_result=not_reported`. Evidence lives at `.bridge/P6-001H-EVID/` (REVIEW_QWEN.json, runner-emitted LIVE_RUN_METADATA.json, BLOCKED_COMMANDS.log) with `REVIEW_CLAUDE.json` verdict **approve** (RSK-1, human_review_required true). The Qwen review *content* is synthetic-fixture output, not a real code review — the value is the proven end-to-end live pipeline. Full suite **140 passing**.

**P6-001F prep is staged in PR #35 (`claude/p6-001f-prep`, open, not merged).** Architect exploration found P6-001F could not run as documented and corrected it (docs + one prompt change + a runner script; no runner/validator changes): (1) the runbook/PLAN.md called `run_isolated_validation(config, spec, workspace=WORKSPACE)` but the function has no `workspace` parameter; (2) the docs described an external `fixture.txt` workspace the runner never uses — it provisions its own empty temp workspace, uses it as Codex's cwd, then requires it to contain exactly `fixture.txt`; (3) because the workspace starts empty Codex must *create* `fixture.txt`, yet `validate_synthetic_diff` requires `--- a/fixture.txt` / `+++ b/fixture.txt` headers, so `build_codex_adapter`'s prompt was hardened to pin the create-one-file behavior, `files_changed=["fixture.txt"]`, and those exact diff headers; (4) `ARTIFACT_ROOT` was `.bridge/P6-001F` (would publish to `.bridge/P6-001F/P6-001F`) and is corrected to `.bridge`. Added a tested convenience runner `run_p6_001f.py`. Validators and the command/flag layout are unchanged; the fake-CLI contract tests still pass. Full suite **140 passing**; `tests/live/test_codex_adapters.py` 11 passing; `check_plan.py` exits 0 on the corrected PLAN.md. **No live call was made.** P6-001F stays **Blocked** on the PC run + per-run approval; real Codex diff/scope behavior is only verifiable on the PC.

## Last Agent

| Field | Value |
|---|---|
| Tool | Claude Code |
| Date | 2026-06-30 |
| Branch | claude/p6-001f-prep (manual maintenance) |
| Task | P6-001F prep: harden Codex prompt, fix runbook/PLAN.md, add PC runner (PR #35) |

## What Was Changed

- Hardened `build_codex_adapter`'s bound prompt in `tools/bridge/live/codex_adapters.py` (create-one-file `fixture.txt`, `files_changed=["fixture.txt"]`, `tool=codex`, `dry_run=false`, exact `a/`…`b/` diff headers). Validators unchanged.
- Corrected `.bridge/P6-001F/PLAN.md` and `docs/PC-Runner-P6-001F-Handoff.md`: removed the non-existent `workspace=` arg and the phantom external workspace, fixed `ARTIFACT_ROOT` to `.bridge`, aligned prompt/sandbox/preflight wording with the real runner.
- Added `run_p6_001f.py` (tested one-command PC runner with preflight checklist).
- Opened PR #35 (`claude/p6-001f-prep` → `main`); merge stays human-controlled.

## Files Modified

- `tools/bridge/live/codex_adapters.py`
- `.bridge/P6-001F/PLAN.md`
- `docs/PC-Runner-P6-001F-Handoff.md`
- `run_p6_001f.py` (new)
- `.ai/TASKS.md`, `.ai/AGENT_HANDOFF.md`, `.ai/CHANGELOG_AI.md` (this status save)

## Tests Run

Full suite **140 passed**; `tests/live/test_codex_adapters.py` 11 passed; `check_plan.py` exits 0 on `.bridge/P6-001F/PLAN.md`; `import run_p6_001f` clean. No live vendor call.

## Known Issues

- No real vendor adapter is registered in ENABLED_ADAPTERS; the public runner refuses live dispatch with exit code 2.
- Codex CLI flags remain contract assumptions; PR #35 hardened the prompt but `codex --help` (`exec`, `--json`, `--sandbox workspace-write`, `--schema`, `--budget-usd`) must still be verified on the PC before the P6-001F run, updating `codex_adapters.py` + re-running the fake-CLI tests if any differ.
- The real Codex builder diff/scope behavior is unverified until the PC run: if Codex emits `--- /dev/null` headers or writes extra files despite the hardened prompt, the run fails closed (no evidence) and the prompt/adapter needs another pass + fresh approval.
- The shared remote environment returns egress-policy `403 Forbidden` to approved Qwen provider hosts; live Qwen depends on the owner's approved PC runner.
- Antigravity remains deferred until a supported headless interface exists.
- The conductor GitHub App must be installed and verified before automated PR operations.
- The Qwen parser `result`-string path assumes bare JSON (the P6-001H-EVID live run confirmed bare JSON, no fences). If a future Qwen build wraps the JSON in markdown fences or prose, `json.loads(result)` fails **closed** (no bad evidence) and `_extract_payload` must be made fence-tolerant before re-running.
- The Qwen free OAuth login tier ended 2026-04-15; live runs now depend on a paid Alibaba coding/Model-Studio plan. The trial quota is ~1,000,000 tokens per model, so a different `--model` (e.g. `qwen3.7-plus`, `qwen3-coder-plus`) is a fresh allotment — but any new live run needs a new single-use ledger entry and produces new evidence.
- P6-QWEN-ADAPTER-001 and P6-LEDGER-001 were built and reviewed by the same model; REVIEW_CLAUDE.json for P6-001H-EVID is `human_review_required: true` — independent human sign-off recommended before integrating live Qwen into the conductor (P6-001J).

## Next Recommended Step

P6-001F prep is in **PR #35** (`claude/p6-001f-prep`, open). First **merge PR #35** (CI: `bridge-gates` + `test`). Then, on the approved PC runner, run **P6-001F — bounded Codex builder validation** per the corrected `docs/PC-Runner-P6-001F-Handoff.md` / `.bridge/P6-001F/PLAN.md`:

1. Verify `codex --help` flags against `tools/bridge/live/codex_adapters.py` (`exec`, `--json`, `--sandbox workspace-write`, `--schema`, `--budget-usd`); update the adapter + re-run `pytest tests/live/test_codex_adapters.py` if they differ. Record the version.
2. Add the single-use approval-ledger entry `P6-001F-RUN-001` (vendor codex, role builder, run-day date, RSK-1) and obtain explicit per-run human approval.
3. Run `python run_p6_001f.py --codex-version <ver>` (emits `.bridge/P6-001F/`), secret-scan the evidence, commit the sanitized artifacts + ledger entry, open the evidence PR; bring the diff back here for `REVIEW_CLAUDE.json` and the P6-001F → Complete reconciliation.

After that: P6-001D (bounded Claude validation), then P6-001G (Claude/Codex hybrid), then P6-001J (conductor integration) and P6-001K (Phase 6 report).

## Warnings

Do not treat the shared remote environment as live-Qwen-capable while provider hosts return egress-policy `403 Forbidden`. Do not register a real adapter, execute live Qwen outside an approved external runner, or enable automated GitHub operations. Keep future merges human-controlled.
