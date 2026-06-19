# Model Roles

## Role assignments by mode

| Role | safe-default | qwen-led | dual-builder |
|---|---|---|---|
| Planner | Claude | Qwen | Claude |
| Builder | Codex | Qwen | Codex (A) + Qwen (B) |
| First reviewer | Qwen | None (stage skipped) | Qwen |
| Verifier | Antigravity | Antigravity | Antigravity |
| Final reviewer | Claude | Claude | Claude |
| Approver | Human | Human | Human |

## qwen-led stage contract

The `qwen-led` mode uses this exact sequence:

1. `qwen_plan.sh` writes `PLAN.md`.
2. `check_plan.py` and `check_rsk0.py` validate the plan.
3. `qwen_build.sh` writes `EDIT_QWEN.md` and `CHANGES.diff`.
4. `check_scope.py` validates the changed-file scope.
5. First review and its gate are skipped. `REVIEW_QWEN.json` is not produced or required.
6. `antigravity_verify.sh` writes `VERIFY.json`; `check_verify.py` validates it.
7. `claude_review.sh` writes `REVIEW_CLAUDE.json` without requiring `REVIEW_QWEN.json`.
8. `check_review.py --reviewer claude` and the secret gate run before final reporting.

Claude's final review is the independent review for `qwen-led`. The mode must halt if that review is missing, rejects the change, reports blockers, or reports scope drift.

## Tool capabilities

| Tool | Write to repo | Push to branch | Merge to main | Run terminal |
|---|---|---|---|---|
| Claude Code | Plan/review only (read-only default) | No | No | No |
| Codex CLI | Yes (workspace only) | With approval | Never | Yes (workspace) |
| Qwen Code | Yes (workspace only) | With approval | Never | Restricted |
| Antigravity | No (verify only) | No | No | Read-only |

## Notes

- **qwen-led mode:** Qwen does not review its own build. The Qwen first-review stage and artifact are omitted; Claude provides the independent final review.
- **dual-builder mode:** Two independent builds (Codex on branch-A, Qwen on branch-B) are compared; the winner is selected before verification and review.
- All modes share the same safety gates, RSK enforcement, and human approval requirements.
