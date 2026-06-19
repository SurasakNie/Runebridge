# Tasks

## Active Task

| Field | Value |
|---|---|
| Task ID | P05B-001 |
| Goal | Establish environment, security, permissions, and tooling setup |
| Owner | Human + Codex |
| Status | In progress; baseline and host tools verified, public visibility decided, active `main` ruleset verified; remaining GitHub controls pending |
| Branch | claude/latest-drafts-ptdnpq |
| Related files | `.env.example`, `tools/requirements.txt`, `.pre-commit-config.yaml`, `tests/gates/`, setup documentation |
| Risk level | RSK-1 for files; RSK-0 for visibility, protection, or permission changes |
| Required mode | Manual repository maintenance |

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

