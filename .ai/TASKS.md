# Tasks

## Active Task

| Field | Value |
|---|---|
| Task ID | P1-001 |
| Goal | Implement the approved repository scaffold |
| Owner | Human + Codex |
| Status | Ready; Phase 0.6 complete |
| Branch | To be created from `main` |
| Related files | Planned repository layout in `README.md` and the implementation plan |
| Risk level | RSK-2 for reversible scaffold files |
| Required mode | Manual repository maintenance |

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

