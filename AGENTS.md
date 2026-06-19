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
5. Update `.ai/AGENT_HANDOFF.md` and `.ai/CHANGELOG_AI.md` after completing work.

## Hard restrictions

- Never commit API keys, passwords, access tokens, SSH keys, private certificates, or customer data.
- Never push directly to `main`. All changes go on a feature branch.
- Never delete files unless explicitly instructed to do so.
- Never make formatting-only changes to files not in scope.
- Never pass secrets as command-line arguments or write them into artifact files.
- If you encounter an RSK-0 action (merge, deploy, secret rotation, force-push, schema migration, production change), stop and wait for human approval.
