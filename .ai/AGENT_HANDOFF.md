# Agent Handoff

## Current State

Phases 0.5A through 5 are complete. The Phase 6 plan, isolated runner, Claude planner/reviewer adapter contracts, Codex builder adapter contract, approval-ledger mechanism (P6-LEDGER-001, PR #24), and Qwen reviewer adapter (P6-QWEN-ADAPTER-001, PR #27) are all merged. The public adapter registry remains empty, so no real vendor or live execution is enabled in the shared remote environment. Qwen provider/auth decisions are recorded, the shared remote environment remains blocked by egress-policy `403 Forbidden`, and the approved operating model is `PC-first, VM-later` for Qwen live execution. P6-001D and P6-001F remain gated on explicit per-run human approval.

**P6-001H-EVID live-invocation blocker is resolved and merged (PR #31, `ff4dfad`).** A live debugging session on the approved PC runner found that **Qwen Code CLI `0.19.2` returns the schema-valid review JSON in the result envelope's `result` string field, not in `structured_output`** (`--json-schema` does not populate a `structured_output` object in this build). The parser now extracts the payload from `structured_output` → `structured_result` → JSON-parsed `result` (Codex authored the fallback; the same session also hardened the runner: daemon-thread stdout/stderr readers to avoid Windows pipe-inheritance hangs, `use_dedicated_vendor_cwd` to isolate Qwen's background processes, `APPDATA`/`LOCALAPPDATA`/`USERPROFILE` passthrough for stored OAuth, `--max-tool-calls 3`, and tail-not-head error diagnostics). All existing checks — review schema, `reviewer == "qwen"`, `task_id`, budget ceiling, and the fail-closed posture — are preserved. Full suite is **140 passing**. The bounded live evidence run has **not** been re-executed after the fix, so no official `.bridge/P6-001H-EVID/` artifacts exist yet.

## Last Agent

| Field | Value |
|---|---|
| Tool | Claude Code |
| Date | 2026-06-30 |
| Branch | claude/resume-tasks-lvxf5c (manual maintenance) |
| Task | Post-PR #31 reconciliation: record the Qwen `result`-string finding; mark P6-001H-EVID In progress |

## What Was Changed

- Reconciled status after PR #31 (`ff4dfad`, "fix qwen result payload parsing"), which was a code/tests-only merge.
- Marked P6-001H-EVID **In progress** in `.ai/TASKS.md` and recorded the `result`-string finding and the merged parser fallback.
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
- No official full live-run metadata or `.bridge/P6-001H-EVID/` evidence exists yet; the post-fix live run is still pending on the PC runner.
- The shared remote environment returns egress-policy `403 Forbidden` to approved Qwen provider hosts.
- Live Qwen depends on the owner's approved PC runner.
- Antigravity remains deferred until a supported headless interface exists.
- The conductor GitHub App must be installed and verified before automated PR operations.
- Qwen reviewer adapter flags are now verified against Qwen Code CLI `0.19.2` (`--output-format json`, `--json-schema`, `--max-tool-calls 3`, `--no-chat-recording`); structured output arrives in the result envelope's `result` string, handled by the merged parser fallback.
- The parser `result`-string path assumes bare JSON. If a future Qwen build wraps the JSON in markdown fences or surrounding prose, `json.loads(result)` fails **closed** (no bad evidence is published) but the run will not produce evidence until extraction tolerates fences. The first live run will confirm the actual format.
- P6-QWEN-ADAPTER-001 and P6-LEDGER-001 were both built and reviewed by the same model; independent Qwen/human review recommended before the first live credentialed run.

## Next Recommended Step

The P6-001H-EVID code blocker is fixed and merged (PR #31). The remaining steps are PC-runner-only:

1. On the approved PC runner, add the approval-ledger entry `P6-001H-EVID-RUN-001` (vendor `qwen`, role `reviewer`, RSK-1) to `tools/bridge/live/approval-ledger.json`, set the run date to the actual run day, and obtain fresh per-run human approval immediately before invoking.
2. Run the bounded live Qwen reviewer validation once to emit `.bridge/P6-001H-EVID/` (`REVIEW_QWEN.json`, runner-generated `LIVE_RUN_METADATA.json`, `BLOCKED_COMMANDS.log`).
3. Secret-scan every evidence file, then commit only the sanitized artifacts **plus** the `approval-ledger.json` entry in a single evidence PR (do not commit PC scratch files). Open the PR; keep the merge human-controlled.
4. Bring the evidence diff back to the remote session for `REVIEW_CLAUDE.json`, then mark P6-001H-EVID Complete.

After that, P6-001F (bounded Codex validation) may proceed once CLI flags, authentication, and per-run approval are confirmed.

## Warnings

Do not treat the shared remote environment as live-Qwen-capable while provider hosts return egress-policy `403 Forbidden`. Do not register a real adapter, execute live Qwen outside an approved external runner, or enable automated GitHub operations. Keep future merges human-controlled.
