# Agent Handoff

## Current State

Phases 0.5A through 5 are complete. The Phase 6 plan, isolated runner, Claude planner/reviewer adapter contracts, Codex builder adapter contract, approval-ledger mechanism (P6-LEDGER-001, PR #24), and Qwen reviewer adapter (P6-QWEN-ADAPTER-001, PR #27) are all merged. The public adapter registry remains empty, so no real vendor or live execution is enabled in the shared remote environment. Qwen and Codex provider/auth decisions are recorded; both live vendors follow the approved `PC-first, VM-later` external-runner model. **P6-001D remains the only Phase 6 execution task still gated on explicit per-run human approval** — P6-001F, described below, is now Complete.

**P6-001F is COMPLETE — first live Codex builder evidence merged (PR #37, `4398a80`), Codex adapter/sandbox fixes merged (PR #36, `2408c82`).** Getting one successful bounded live Codex run required five real corrections to the adapter, all discovered only by running against the real `codex-cli 0.141.0` via live PC probes — none were guessable from documentation, and the fake-CLI contract tests could not have caught them:

1. `--schema` does not exist; the real flag is `--output-schema <file>`, which takes a file path (not inline JSON) and must be written **without a UTF-8 BOM** or Codex rejects it. OpenAI's structured-output schema validation also rejects `uniqueItems`/`pattern`/`minLength`, so the schema sent to `--output-schema` is now a relaxed copy with those keywords stripped, while the full strict schema still validates the real response locally.
2. `--budget-usd` does not exist and the CLI never reports a dollar cost — only token usage. Budget enforcement was dropped in favor of `budget_result=not_reported`, matching the existing Qwen precedent.
3. The CLI never emits a diff, only `{"path", "kind": "add"}` file-change metadata. `CHANGES.diff` is now synthesized by the runner from the actual post-run workspace file (`render_synthetic_diff` in `codex_adapters.py`), not extracted from stdout.
4. `--json` means a JSONL event stream, not one result envelope. The parser scans for a terminal `turn.completed` event and the last `agent_message` item, whose `text` field holds the schema-constrained JSON.
5. `--model` was accepted by `build_codex_adapter` but never actually passed to the command — the ratified model was silently not enforced. Now wired through.

Two more defects were found and fixed specifically because a *live* run was attempted, not just the fake-CLI suite: (a) the process-tree monitor added to close a PATH-shim absolute-path bypass (see below) initially watched the vendor's own executable name too, killing Codex's own child process (`codex.cmd` → `codex.exe`) and aborting the run with exit 15 and no diagnostic output — fixed by excluding the running vendor's own name from the monitor's watch set; (b) a Windows `WinError 32` on temp-directory cleanup (a lingering Codex background helper briefly holds a workspace file handle) masked an otherwise-successful run — fixed with `TemporaryDirectory(ignore_cleanup_errors=True)`.

Two ratified parameters were corrected after live probes contradicted them: the model `codex-mini-latest` is rejected outright with a ChatGPT-account Codex auth (HTTP 400: "not supported when using Codex with a ChatGPT account") and was re-ratified to `gpt-5.4`; the `30s` timeout was too tight for Codex's multi-round-trip self-verification turns and was re-ratified to `60s` after a live run timed out mid-turn.

One deliberate, owner-ratified policy decision: **`git` is a tolerated (neutralized) blocked command.** Codex calls `git` internally for diff-tracking; a live probe confirmed the PATH shim still turns every call into a no-op (git never executes, never touches the network, never writes the workspace — the post-run workspace contained only `fixture.txt`), so those attempts are recorded (`BLOCKED_COMMANDS.log`, new `neutralized_command_count`/`neutralized_commands` metadata fields) rather than failing the run. `gh`/`curl`/`wget`/foreign vendors remain fatal, including by absolute path.

This also closed a real sandbox gap unrelated to P6-001F specifically: PATH shims only intercept bare-name command lookups, and a live Codex run was observed invoking `powershell.exe` by absolute path as ordinary agent behavior — a bypass that would apply equally to Claude and Qwen live runs. A `psutil`-based process-tree monitor now catches blocked commands by resolved executable name regardless of invocation style.

The run itself: `execution=live`, `exit_code=0`, model `gpt-5.4`, `cli_version=0.141.0`, all gates passed, `blocked_command_count=0`, `neutralized_commands=[git]`, `budget_result=not_reported`. Evidence lives at `.bridge/P6-001F/` (`EDIT_CODEX.md`, `CHANGES.diff`, `LIVE_RUN_METADATA.json`, `BLOCKED_COMMANDS.log`) with `REVIEW_CLAUDE.json` verdict **approve** (RSK-1, `human_review_required: true`). The review independently re-verified every `PLAN.md` acceptance criterion against the committed bytes (schema validation, hash checks, secret scans, gate re-runs), not just re-reading what the PC runner already checked. Full suite **155 passing**.

**P6-001H-EVID is COMPLETE — first live Qwen reviewer evidence merged (PR #33, `2351d91`).** The live-invocation blocker was resolved in PR #31 (`ff4dfad`): Qwen Code CLI `0.19.2` returns the schema-valid review JSON in the result envelope's `result` string field, not in `structured_output`, so the parser falls back through `structured_output` → `structured_result` → JSON-parsed `result` (plus runner hardening: daemon-thread stdout/stderr readers for Windows pipe-inheritance, `use_dedicated_vendor_cwd`, `APPDATA`/`LOCALAPPDATA`/`USERPROFILE` passthrough, `--max-tool-calls 3`, tail-not-head diagnostics). The bounded live run then executed on the approved PC runner with model `qwen3.6-plus`: `execution=live`, `exit_code=0`, all gates passed, `blocked_command_count=0`, `budget_result=not_reported`. Evidence lives at `.bridge/P6-001H-EVID/` (REVIEW_QWEN.json, runner-emitted LIVE_RUN_METADATA.json, BLOCKED_COMMANDS.log) with `REVIEW_CLAUDE.json` verdict **approve** (RSK-1, human_review_required true). The Qwen review *content* is synthetic-fixture output, not a real code review — the value is the proven end-to-end live pipeline.

## Last Agent

| Field | Value |
|---|---|
| Tool | Claude Code |
| Date | 2026-07-01 |
| Branch | claude/continuation-38tlb0, claude/p6-001f-evidence (both merged to main via PR #36 and PR #37) |
| Task | P6-001F: corrected the Codex adapter against real codex-cli 0.141.0, closed a sandbox command-blocking gap, executed and reviewed the first live P6-001F run, reconciled status docs |

## What Was Changed

- `tools/bridge/live/run_isolated_validation.py`: added a `psutil`-based process-tree monitor (`poll_blocked_descendants`) that catches blocked commands by resolved executable name regardless of invocation style, closing an absolute-path bypass in the PATH-shim mechanism; the monitor excludes the running vendor's own name from its watch set; added `TOLERATED_BLOCKED_COMMANDS = {"git"}` with `neutralized_command_count`/`neutralized_commands` split from the fatal `blocked_command_count`; `ResultParser` now receives the workspace path; `TemporaryDirectory(ignore_cleanup_errors=True)`.
- `tools/bridge/live/codex_adapters.py`: rewrote for the real CLI — `--output-schema <file>` (relaxed, BOM-free) instead of inline `--schema`; dropped `--budget-usd`; JSONL event parsing instead of single-envelope parsing; `render_synthetic_diff` synthesizes the diff from the actual workspace file; `--model` now wired into the command.
- `tools/bridge/live/claude_adapters.py`, `qwen_adapters.py`: updated to the new three-argument `ResultParser` signature (workspace param added, unused by both).
- `schemas/live-run-metadata.schema.json`: added optional `neutralized_command_count`/`neutralized_commands` fields.
- `run_p6_001f.py`: re-ratified `DEFAULT_MODEL` → `gpt-5.4`, `TIMEOUT_SECONDS` → `60`; publishes to a fresh staging dir then relocates evidence into `.bridge/P6-001F/` (the runner refuses to publish into an existing directory, and that directory already holds `PLAN.md`/`TASK.md`).
- `tests/live/test_isolated_runner.py`, `test_codex_adapters.py`, `test_run_p6_001f.py` (new): full coverage of the above — absolute-path monitor detection, vendor-self-exclusion regression, git-tolerance, real JSONL fake-CLI contract, evidence-staging relocation.
- `tools/requirements.txt`, `.pre-commit-config.yaml`: added `psutil`.
- `.bridge/P6-001F/EDIT_CODEX.md`, `CHANGES.diff`, `LIVE_RUN_METADATA.json`, `BLOCKED_COMMANDS.log`, `REVIEW_CLAUDE.json`: the live evidence and review.
- `.ai/TASKS.md`, `.ai/PROJECT_BRIEF.md`, `README.md`, `docs/Phase-6-Live-Vendor-Validation-Plan.md`, `docs/AI-Bridge-Implementation-Plan-and-Concerns.md`, `docs/PC-Runner-P6-001F-Handoff.md`, `.bridge/P6-001F/PLAN.md`: status reconciliation (this update).
- Merged via PR #36 (`2408c82`, code/adapter/sandbox fixes) and PR #37 (`4398a80`, evidence + review), both with green CI (Security baseline, Pre-commit baseline, Python baseline).

## Files Modified

See the PR diffs for the full list: [PR #36](https://github.com/SurasakNie/Runebridge/pull/36), [PR #37](https://github.com/SurasakNie/Runebridge/pull/37).

## Tests Run

Full suite **155 passed** on `main` post-merge. `check_plan.py` exits 0 on `.bridge/P6-001F/PLAN.md`. `check_live_metadata.py`, `check_review.py --reviewer claude`, and `check_no_secrets.py` all exit 0 on the committed evidence and review. Live vendor call: **yes** — the first real P6-001F run, executed on the owner's approved PC runner.

## Known Issues

- No real vendor adapter is registered in `ENABLED_ADAPTERS`; the public runner refuses live dispatch with exit code 2. This is by design — the public registry stays empty in every environment.
- The shared remote environment cannot invoke real Codex or Qwen CLIs at all (no CLI installed, and Qwen's provider hosts return egress-policy `403 Forbidden`); both vendors depend on the owner's approved PC runner for any live execution.
- **The git-tolerance policy and the process-tree monitor's vendor-self-exclusion fix both bear directly on the sandbox's security properties and were authored and reviewed within the same model lineage** — `REVIEW_CLAUDE.json` for P6-001F flags both for independent human sign-off before P6-001J conductor integration.
- Antigravity remains deferred until a supported headless interface exists.
- The conductor GitHub App must be installed and verified before automated PR operations.
- The Qwen parser `result`-string path assumes bare JSON (the P6-001H-EVID live run confirmed bare JSON, no fences). If a future Qwen build wraps the JSON in markdown fences or prose, `json.loads(result)` fails **closed** (no bad evidence) and `_extract_payload` must be made fence-tolerant before re-running.
- The Qwen free OAuth login tier ended 2026-04-15; live runs now depend on a paid Alibaba coding/Model-Studio plan. A different `--model` is a fresh token allotment, but any new live run needs a new single-use ledger entry and produces new evidence.
- Codex's model/timeout ratifications (`gpt-5.4`, `60s`) and the git-tolerance policy were validated against **one PC's** Codex install and ChatGPT-account auth on 2026-07-01; a different account type (API-key auth) or CLI version may need re-verification before reuse.
- The approval-ledger now carries two consumed single-use entries (`P6-001H-EVID-RUN-001`, `P6-001F-RUN-001`); each new live run needs its own fresh entry matched on vendor, role, and run_date.
- Two branches exist (`claude/next-steps-t0vai9`, `claude/resume-tasks-48qvg1`) that were flagged during this session's branch review as stale/superseded or containing unreviewed content (an approval-ledger entry for an unrelated task, `P6-QWEN-REVIEW-002-RUN-001`, from 14 commits behind `main`); neither was merged pending explicit owner direction — see the session transcript for detail.

## Next Recommended Step

P6-001F is Complete. The next Phase 6 execution task is **P6-001D — bounded Claude planner/reviewer validation**, gated the same way P6-001F was: per-run human approval via the approval ledger, executed on the approved PC runner. Given how many real-CLI surprises P6-001F's live run surfaced, expect the same pattern — verify `claude --help`/CLI flags against `tools/bridge/live/claude_adapters.py`'s assumptions via live PC probes *before* spending the single-use approval on the gated run itself.

After P6-001D: P6-001G (Claude/Codex hybrid), then P6-001J (conductor integration — do not proceed without the independent human sign-off flagged above on the git-tolerance and monitor-exclusion changes) and P6-001K (Phase 6 report).

Separately: resolve the two flagged stale/questionable branches (delete `claude/p6-001f-prep`, already merged; decide `claude/next-steps-t0vai9` and `claude/resume-tasks-48qvg1` — see Known Issues).

## Warnings

Do not treat the shared remote environment as live-vendor-capable for Codex or Qwen; both depend on the owner's approved PC runner. Do not register a real adapter, execute live vendor calls outside an approved external runner, or enable automated GitHub operations. Keep future merges human-controlled. Do not integrate live Codex into the conductor (P6-001J) without independent human review of the git-tolerance policy and the monitor's vendor-self-exclusion fix.
