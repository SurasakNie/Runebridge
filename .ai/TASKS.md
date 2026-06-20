# Tasks

## Active Task

| Field | Value |
|---|---|
| Task ID | P05B-001 |
| Goal | Establish environment, security, permissions, and tooling setup |
| Owner | Human + Codex |
| Status | In progress; baseline and host tools verified, public visibility decided, active `main` ruleset verified; remaining GitHub controls pending |
| Branch | claude/latest-drafts-ptdnpq |
| Related files | `.env.example`, `tools/requirements.txt`, `.pre-commit-config.yaml`, `tests/gates/`, `.ai/SECURITY_RULES.md`, `.ai/MCP_POLICY.md`, setup documentation |
| Risk level | RSK-1 for files; RSK-0 for visibility, protection, or permission changes |
| Required mode | Manual repository maintenance |

## Phase 0.5B Work Items

| ID | Task | Status | Dependency / approval |
|---|---|---|---|
| P05B-001A | Repository baseline and host tools | Complete | None |
| P05B-001B | Public visibility and active `main` ruleset | Complete | Human decision recorded |
| P05B-001C | Least-privilege GitHub Actions permission contract | Complete | Reversible documentation |
| P05B-001D | Minimum GitHub App permission contract | Complete | Reversible documentation |
| P05B-001E | Verify secret scanning and push protection | Audited; both disabled | RSK-0 human approval required before enabling |
| P05B-001F | Require resolved review conversations | Audited; disabled | RSK-0 human approval required before ruleset change |
| P05B-001G | Define required CI checks and Actions restrictions | Deferred to Phase 2 | Named workflows and action dependencies must exist first |
| P05B-001H | Final Phase 0.5B audit | Pending | P05B-001C through P05B-001F complete; P05B-001G explicitly deferred |

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

