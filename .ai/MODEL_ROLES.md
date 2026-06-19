# Model Roles

## Role assignments by mode

| Role | safe-default | qwen-led | dual-builder |
|---|---|---|---|
| Planner | Claude | Qwen | Claude |
| Builder | Codex | Qwen | Codex (A) + Qwen (B) |
| First reviewer | Qwen | — (self-review skipped) | Qwen |
| Verifier | Antigravity | Antigravity | Antigravity |
| Final reviewer | Claude | Claude | Claude |
| Approver | Human | Human | Human |

## Tool capabilities

| Tool | Write to repo | Push to branch | Merge to main | Run terminal |
|---|---|---|---|---|
| Claude Code | Plan/review only (read-only default) | No | No | No |
| Codex CLI | Yes (workspace only) | With approval | Never | Yes (workspace) |
| Qwen Code | Yes (workspace only) | With approval | Never | Restricted |
| Antigravity | No (verify only) | No | No | Read-only |

## Notes

- **qwen-led mode:** No independent first reviewer. Qwen produces code and reviews it in Stage 9. Apply extra scrutiny when using this mode.
- **dual-builder mode:** Two independent builds (Codex on branch-A, Qwen on branch-B) are compared; the winner is selected before verification and review.
- All modes share the same safety gates, RSK enforcement, and human approval requirements.
