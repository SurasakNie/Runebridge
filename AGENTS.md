# AGENTS.md — Universal Pre-Read for All AI Agents

Read this file before taking any action in this repository.

## Read order

1. `AGENTS.md` (this file)
2. `.ai/PROJECT_BRIEF.md`
3. `.ai/CODING_RULES.md`
4. `.ai/SECURITY_RULES.md`
5. `.ai/MODEL_ROLES.md`
6. `.ai/TASKS.md`
7. `.ai/AGENT_HANDOFF.md`

Then read the task-specific files in `.bridge/<task-id>/` if a task ID is given.

## Work process

1. Understand the task completely before making any changes.
2. Inspect all files in scope before editing any of them.
3. Make the smallest safe change that satisfies the task.
4. Run available tests before handing off.
5. Write only the files allowed for the current role and stage.

## Pipeline write ownership

During an orchestrated pipeline run:

| Owner | Allowed writes |
|---|---|
| Planner adapter | `.bridge/<task-id>/PLAN.md` only |
| Builder adapter | Approved source paths, `.bridge/<task-id>/EDIT_<tool>.md`, and `.bridge/<task-id>/CHANGES.diff` |
| Qwen review adapter | `.bridge/<task-id>/REVIEW_QWEN.json` only |
| Verifier adapter | `.bridge/<task-id>/VERIFY.json` only |
| Claude final-review adapter | `.bridge/<task-id>/REVIEW_CLAUDE.json` only |
| Conductor | `TASK.md`, `FINAL_REPORT.md`, shared handoff/changelog state, and Git/PR operations |

- Planning, verification, and review stages are read-only for source files. Writing the designated stage artifact is allowed.
- Role adapters must not modify `.ai/AGENT_HANDOFF.md` or `.ai/CHANGELOG_AI.md`.
- The conductor updates those shared files once during final reporting, using validated task artifacts.
- Manual repository-maintenance tasks may modify `.ai/` files only when those paths are explicitly in task scope.

## Hard restrictions

- Never commit API keys, passwords, access tokens, SSH keys, private certificates, or customer data.
- Never push directly to `main`. All changes go on a feature branch.
- Never delete files unless explicitly instructed to do so.
- Never make formatting-only changes to files not in scope.
- Never pass secrets as command-line arguments or write them into artifact files.
- Never commit, push, create a PR, or update shared `.ai/` state from a role adapter; those actions belong to the conductor.
- If you encounter an RSK-0 action (merge, deploy, secret rotation, force-push, schema migration, production change), stop and wait for human approval.
