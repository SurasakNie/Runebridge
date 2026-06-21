# Tasks

## Active Task

| Field | Value |
|---|---|
| Task ID | P6-001 |
| Goal | Implement the Codex builder live adapter and scope-sandbox tests without executing live calls |
| Owner | Human + Codex |
| Status | Ready for implementation |
| Branch | Not started |
| Related files | `tools/bridge/live/`, `tools/bridge/gates/`, `schemas/`, `tests/live/`, Phase 6 plan |
| Risk level | RSK-1 implementation; adapter registration and live calls prohibited |
| Required mode | Manual repository maintenance |

## Phase 6 Work Items

| ID | Task | Status | Dependency / approval |
|---|---|---|---|
| P6-001A | Approve the Phase 6 live-vendor validation plan | Complete | PR #12 merged manually |
| P6-001B | Implement isolated runner, provenance format, and negative tests | Complete | PR #13 merged at `124efe0`; no real adapters enabled; 88 tests pass |
| P6-001C | Implement Claude live adapters behind refusal-by-default controls | Complete | PR #15 merged at `16ae812`; public registry remains empty; 96 tests pass |
| P6-001D | Execute bounded Claude validation | Blocked | P6-001C merged; awaiting explicit per-run human approval and the P6-001D execution preflight in the Phase 6 plan |
| P6-001E | Implement Codex live adapter and scope-sandbox tests | Ready | P6-001B merged; implementation and fake-CLI tests only |
| P6-001F | Execute bounded Codex validation | Blocked | P6-001E merged; explicit per-run human approval |
| P6-001G | Validate one explicit Claude/Codex hybrid pipeline | Blocked | P6-001D and P6-001F complete |
| P6-001H | Decide Qwen provider and authentication path | Blocked | Explicit RSK-0 human decision; no provider calls before approval |
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

