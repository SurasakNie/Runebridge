# Tasks

## Active Task

| Field | Value |
|---|---|
| Task ID | P2-001 |
| Goal | Implement five artifact schemas and seven deterministic gates |
| Owner | Human + Codex |
| Status | In progress; implementation and local verification complete, protected PR checks pending |
| Branch | codex/phase-2-schemas-gates |
| Related files | `schemas/`, `tools/bridge/gates/`, `tests/gates/`, `docs/Phase-2-Schemas-and-Gates-Plan.md` |
| Risk level | RSK-1 for shared artifact and gate contracts |
| Required mode | Manual repository maintenance |

## Phase 2 Work Items

| ID | Task | Status | Dependency / approval |
|---|---|---|---|
| P2-001A | Define five draft-07 artifact schemas | Complete | JSON parse and schema tests passed |
| P2-001B | Implement seven deterministic gate CLIs | Complete | Exit behavior tests passed |
| P2-001C | Add pass/fail/RSK-0 gate tests | Complete | Fifteen total gate tests passed |
| P2-001D | Run local and protected CI verification | In progress | Local suite passed; PR checks pending |
| P2-001E | Review repository Actions restrictions | Pending | Human approval required for settings changes |

## Phase 1 Work Items

| ID | Task | Status | Dependency / approval |
|---|---|---|---|
| P1-001A | Reserve `schemas/` | Complete | Local verification passed |
| P1-001B | Reserve `tools/bridge/adapters/` | Complete | Local verification passed |
| P1-001C | Reserve `tools/bridge/gates/` | Complete | Local verification passed |
| P1-001D | Add fail-closed `tools/bridge/orchestrate.sh` placeholder | Complete | Exit 2, Bash syntax, and ShellCheck passed |
| P1-001E | Document `.bridge/` runtime-artifact layout | Complete | Policy consistency passed |
| P1-001F | Document directory ownership | Complete | Policy consistency passed |
| P1-001G | Add scaffold verification and run protected checks | In progress | Seven local tests passed; protected checks pending |

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

