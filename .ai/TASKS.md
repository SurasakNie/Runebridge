# Tasks

## Active Task

| Field | Value |
|---|---|
| Task ID | P6-001F |
| Goal | Execute bounded Codex builder validation only after explicit per-run approval |
| Owner | Human + Codex |
| Status | **Complete.** Evidence merged (PR #37, `4398a80`); adapter/sandbox fixes merged (PR #36, `2408c82`); reviewed approve (RSK-1, human_review_required true) |
| Branch | merged to `main` |
| Related files | `tools/bridge/live/`, `tools/bridge/gates/`, `schemas/`, `tests/live/`, Phase 6 plan |
| Risk level | RSK-1 paid live execution; each run requires explicit approval |
| Required mode | Manual repository maintenance |

### Ratified P6-001F execution parameters (historical record — the run these gated is Complete)

The owner confirmed these parameters on 2026-06-28, then re-ratified the model and
timeout on 2026-07-01 after live PC probes against the real codex-cli 0.141.0. The
bounded run executed successfully under these final values; kept here as the
record of what was actually approved and used.

The **model was re-ratified to `gpt-5.4` on 2026-07-01**: preflight probes against
a real codex-cli 0.141.0 install proved the originally ratified `codex-mini-latest`
is rejected with a ChatGPT-account Codex auth (`"The 'codex-mini-latest' model is
not supported when using Codex with a ChatGPT account"`, HTTP 400). `gpt-5.4` is the
account's configured default and ran the synthetic builder contract end-to-end in
the probes. The **budget ceiling is now advisory, not mechanically enforced**:
codex-cli 0.141.0 has no `--budget-usd` flag and reports token usage, not a dollar
cost, so `budget_result` is recorded as `not_reported` (same precedent as the Qwen
adapter). **`git` is a tolerated (neutralized) blocked command (owner-ratified
2026-07-01)**: Codex calls `git` internally for diff-tracking; a live probe showed
the PATH shim turns each call into a no-op (git never runs, workspace stays scoped
to `fixture.txt`, Codex still produces correct output), so those attempts are
recorded in `BLOCKED_COMMANDS.log` and the metadata `neutralized_commands` field
rather than failing the run. `gh`/`curl`/`wget`/foreign vendors remain fatal.
**The timeout was re-ratified `30 s` → `60 s` on 2026-07-01**: a live run timed
out mid-turn at `30 s` (`ValidationError: vendor command exceeded the approved
timeout`) — Codex's turn involves several self-verification round-trips (each
its own model turn plus a `powershell.exe` call), and wall-clock varies enough
that `30 s` is not a reliable margin. `60 s` matches the ad hoc probe timeouts
that completed reliably in preflight diagnostics.

| Parameter | Value |
|---|---|
| Approval ID | `P6-001F-RUN-001` |
| Model | `gpt-5.4` (re-ratified 2026-07-01; was `codex-mini-latest`, unusable with ChatGPT-account auth) |
| Timeout | `60 s` (re-ratified 2026-07-01; was `30 s` — a live run timed out mid-turn, since Codex's turn takes several self-verification round-trips) |
| Budget ceiling | `$0.06` (advisory; not enforced by codex-cli 0.141.0) |
| Approach | Direct runner (`build_codex_adapter` + `run_isolated_validation`); no conductor |
| Environment | Local-only execution on an approved runner |

## Phase 6 Work Items

| ID | Task | Status | Dependency / approval |
|---|---|---|---|
| P6-001A | Approve the Phase 6 live-vendor validation plan | Complete | PR #12 merged manually |
| P6-001B | Implement isolated runner, provenance format, and negative tests | Complete | PR #13 merged at `124efe0`; no real adapters enabled; 88 tests pass |
| P6-001C | Implement Claude live adapters behind refusal-by-default controls | Complete | PR #15 merged at `16ae812`; public registry remains empty; 96 tests pass |
| P6-001D | Execute bounded Claude validation | Blocked | P6-001C merged; awaiting explicit per-run human approval and the P6-001D execution preflight in the Phase 6 plan |
| P6-001E | Implement Codex live adapter and scope-sandbox tests | Complete | PR #18 merged at `c724769`; fake-CLI contracts pass; public registry remains empty |
| P6-001F | Execute bounded Codex validation | **Complete** | Prep PR #35 merged (`6f4d48a`). The Codex adapter was corrected against a real codex-cli 0.141.0 install via live preflight probes on the approved PC (PR #36, `2408c82`): (1) model re-ratified `codex-mini-latest` → `gpt-5.4` (the former is rejected with ChatGPT-account auth); (2) `--schema` → `--output-schema <file>` written without a BOM, with a relaxed schema (strips `uniqueItems`/`pattern`/`minLength`, which OpenAI structured-output rejects); (3) `--budget-usd` dropped (nonexistent; no dollar cost reported) → `budget_result=not_reported`; (4) JSONL event parsing + runner-side diff synthesis replace the old single-envelope/`changes_diff` assumptions; (5) a process-tree monitor added to close an absolute-path command-blocking bypass initially killed Codex's own child process, fixed by excluding the vendor's own name from its watch set; (6) `git` (Codex's internal diff-tracking) is a tolerated, neutralized blocked command, owner-ratified; (7) timeout re-ratified `30s` → `60s` after a live run timed out mid-turn; (8) a Windows `WinError 32` temp-cleanup race was made non-fatal. The bounded live run then executed successfully on the approved PC runner with the single-use ledger entry `P6-001F-RUN-001`: `execution=live`, `exit_code=0`, model `gpt-5.4`, `cli_version=0.141.0`, all gates passed, `blocked_command_count=0`, `neutralized_commands=[git]`, `budget_result=not_reported`. Evidence merged in PR #37 (`4398a80`); `REVIEW_CLAUDE.json` verdict **approve** (RSK-1, `human_review_required=true`, flags the git-tolerance policy and the monitor's vendor-self-exclusion fix for independent human sign-off before P6-001J). Full suite 155 passing. |
| P6-001G | Validate one explicit Claude/Codex hybrid pipeline | Blocked | P6-001F complete; awaiting P6-001D (bounded Claude validation) |
| P6-001H | Decide Qwen provider and authentication path | Complete | Provider/auth path recorded; shared remote environment returns egress-policy `403 Forbidden` to approved Qwen provider hosts, so live Qwen uses the approved `PC-first, VM-later` runner model. Live evidence produced under P6-001H-EVID. |
| P6-001H-EVID | Capture approval-bound Qwen live evidence (promote staged synthetic reviewer artifact) | Complete | Bounded live Qwen reviewer run executed on the approved PC runner; evidence merged in PR #33 at `2351d91` (`.bridge/P6-001H-EVID/`: REVIEW_QWEN.json, runner-emitted LIVE_RUN_METADATA.json, BLOCKED_COMMANDS.log). Run was `execution=live`, `exit_code=0`, all gates passed, `blocked_command_count=0`, model `qwen3.6-plus`, `budget_result=not_reported`. REVIEW_CLAUDE.json verdict approve, RSK-1, human_review_required true (REVIEW_QWEN.json content is synthetic-fixture output, not a real code review). Single-use approval-ledger entry `P6-001H-EVID-RUN-001` committed; full suite 140 passing. |
| P6-LEDGER-001 | Implement the approval-ledger mechanism (schema, fail-closed ledger, runner binding, fake-CLI tests) | Complete | PR #24 merged at `3c39a53`; 128 tests pass (+19); REVIEW_CLAUDE.json verdict approve, RSK-1, human_review_required true (same model built and reviewed — independent Qwen/human review recommended before the first live credentialed run) |
| P6-QWEN-ADAPTER-001 | Implement the Qwen reviewer adapter module and fake-CLI contract tests | Complete | PR #27 merged at `3a368df`; 136 tests pass (+8); REVIEW_CLAUDE.json verdict approve, RSK-1, human_review_required true; CLI flags must be verified with `qwen --help` during PC preflight before the live run |
| P6-001I | Reassess Antigravity headless interface | Deferred | Supported headless contract required |
| P6-001J | Integrate approved live roles into the conductor | Blocked | Individual and hybrid evidence approved |
| P6-001K | Publish Phase 6 validation report and reconcile status | Blocked | Prior Phase 6 gates complete or formally deferred |

## Phase 5 Work Items

| ID | Task | Status | Dependency / approval |
|---|---|---|---|
| P5-001A | Run `safe-default` full dry run | Complete | Guarded run exited 0 |
| P5-001B | Run `qwen-led` full dry run | Complete | Guarded run exited 0 |
| P5-001C | Run `dual-builder` full dry run | Complete | Guarded run exited 0 |
| P5-001D | Verify artifacts, halt behavior, and no external calls | Complete | 67 tests, empty logs, and protected checks passed |
| P5-001E | Publish sanitized Phase 5 evidence | Complete | Report and GitHub check evidence recorded |

## Phase 4 Work Items

| ID | Task | Status | Dependency / approval |
|---|---|---|---|
| P4-001A | Implement explicit stage maps for three modes | Complete | Phase 2 gates and Phase 3 adapters |
| P4-001B | Implement halt, report, and bounded retry behavior | Complete | P4-001A |
| P4-001C | Preserve RSK-0 and dry-run-only controls | Complete | Exit 2 tests pass |
| P4-001D | Add all-stage fault-injection tests | Complete | 24 conductor tests pass |
| P4-001E | Run local and protected verification | Complete | PR #8 merged with protected checks passing |

## Phase 3 Work Items

| ID | Task | Status | Dependency / approval |
|---|---|---|---|
| P3-001A | Implement seven deterministic adapter stubs | Complete | Phase 2 schemas and gates |
| P3-001B | Enforce dry-run-only fail-closed behavior | Complete | Live mode exits 2 before writing |
| P3-001C | Add schema-valid and byte-stability tests | Complete | Twenty-seven total tests pass |
| P3-001D | Run local and protected verification | Complete | PR #7 merged with protected checks passing |

## Phase 2 Work Items

| ID | Task | Status | Dependency / approval |
|---|---|---|---|
| P2-001A | Define five draft-07 artifact schemas | Complete | JSON parse and schema tests passed |
| P2-001B | Implement seven deterministic gate CLIs | Complete | Exit behavior tests passed |
| P2-001C | Add pass/fail/RSK-0 gate tests | Complete | Fifteen total gate tests passed |
| P2-001D | Run local and protected CI verification | Complete | PR #6 merged with protected checks passing |
| P2-001E | Review repository Actions restrictions | Deferred | Explicit human approval required for settings changes |

## Phase 1 Work Items

| ID | Task | Status | Dependency / approval |
|---|---|---|---|
| P1-001A | Reserve `schemas/` | Complete | Local verification passed |
| P1-001B | Reserve `tools/bridge/adapters/` | Complete | Local verification passed |
| P1-001C | Reserve `tools/bridge/gates/` | Complete | Local verification passed |
| P1-001D | Add fail-closed `tools/bridge/orchestrate.sh` placeholder | Complete | Exit 2, Bash syntax, and ShellCheck passed |
| P1-001E | Document `.bridge/` runtime-artifact layout | Complete | Policy consistency passed |
| P1-001F | Document directory ownership | Complete | Policy consistency passed |
| P1-001G | Add scaffold verification and run protected checks | Complete | PR #5 merged with protected checks passing |

## Phase 0.6 Work Items

| ID | Task | Status | Dependency / approval |
|---|---|---|---|
| P06-001A | Validate Claude Code CLI | Complete | Authenticated first-party session |
| P06-001B | Validate Codex CLI | Complete | Authenticated ChatGPT session |
| P06-001C | Validate Qwen Code CLI | Deferred to Phase 6 | Mock adapter approved; live provider not selected |
| P06-001D | Validate Antigravity automation interface | Deferred | IDE-only surface rejected; awaiting supported headless structured interface |
| P06-001E | Approve sanitized Phase 0.6 matrix | Complete | Owner approved both deferrals on 2026-06-20 |

## Phase 0.5B Work Items

| ID | Task | Status | Dependency / approval |
|---|---|---|---|
| P05B-001A | Repository baseline and host tools | Complete | None |
| P05B-001B | Public visibility and active `main` ruleset | Complete | Human decision recorded |
| P05B-001C | Least-privilege GitHub Actions permission contract | Complete | Reversible documentation |
| P05B-001D | Minimum GitHub App permission contract | Complete | Reversible documentation |
| P05B-001E | Verify secret scanning and push protection | Complete; both enabled | Human approval recorded 2026-06-20 |
| P05B-001F | Require resolved review conversations | Complete; enabled | Human approval recorded 2026-06-20 |
| P05B-001G | Define and require CI status checks | Complete; three passing checks required | Human approval recorded 2026-06-20 |
| P05B-001H | Final Phase 0.5B audit | Complete | Actions restrictions deferred to Phase 2; conductor App required before automation |

## Backlog

| ID | Goal | Priority | Notes |
|---|---|---|---|
| DASH-001 | Token usage and cost dashboard | Low | Defer to Phase 7+ |
| DASH-002 | Pipeline visualization dashboard | Low | Defer to Phase 7+ |
| DASH-003 | Agent activity log dashboard | Low | Defer to Phase 7+ |

## Done

| ID | Goal | Completed | Notes |
|---|---|---|---|
| P05A-001 | Resolve `qwen-led` workflow contract | 2026-06-19 | Planner, review, artifact, adapter, and final-gate flow aligned |
| P05A-002 | Define pipeline write ownership | 2026-06-19 | Role artifacts separated from conductor-owned shared state and Git operations |
| P05A-003 | Standardize artifact and EN/TH contracts | 2026-06-19 | YAML/JSON formats and canonical machine-readable values aligned |
| P05A-004 | Align documentation and pre-read chains | 2026-06-19 | README, project state, agent pre-read, verifier pre-read, and audit status aligned |
| P05B-001 | Establish environment, security, permissions, and tooling setup | 2026-06-20 | Baseline, host tools, security controls, CI checks, and final audit complete |
| P1-001 | Implement approved repository scaffold | 2026-06-20 | PR #5 merged with seven tests and protected checks passing |
| P2-001 | Implement schemas and deterministic gates | 2026-06-21 | PR #6 merged with fifteen tests and protected checks passing |
| P3-001 | Implement deterministic dry-run adapters | 2026-06-21 | PR #7 merged with 27 tests and protected checks passing |
| P4-001 | Implement Pattern A conductor | 2026-06-21 | PR #8 merged with 59 tests and protected checks passing |
| P5-001 | Validate the full dry-run pipeline | 2026-06-21 | PR #10 merged with 67 tests, guarded evidence, and protected checks passing |
