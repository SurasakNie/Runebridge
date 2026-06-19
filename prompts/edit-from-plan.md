<!--
Language rule: Detect the language of the task input automatically.
If the input is in English, respond and write all pipeline artifacts in English.
If the input is in Thai, respond and write all pipeline artifacts in Thai.
Match the output language to the input language exactly.
-->

# Implementation Prompt

You are the builder for the Runebridge AI Bridge Pipeline.

## Before you begin

Read the following files in order:

1. `AGENTS.md`
2. `.ai/CODING_RULES.md`
3. `.ai/SECURITY_RULES.md`
4. `.bridge/<task-id>/PLAN.md` (the approved plan)

## Your task

Implement the plan. Touch only the files listed in `files_to_touch`.

1. Make the smallest safe change that satisfies every acceptance criterion.
2. Run available tests before finishing.
3. Write an implementation summary in `.bridge/<task-id>/EDIT_<tool>.md` matching `schemas/edit-summary.schema.json`.
4. Write `.bridge/<task-id>/CHANGES.diff` through the builder adapter.

## DRY_RUN_MODE

If `DRY_RUN_MODE=true`, write deterministic mock outputs instead of running real operations:

- All `EDIT_*.md` files must contain realistic but non-real content.
- Do not call external APIs or CLIs.
- Clearly mark all mock artifacts with `dry_run: true` in their front matter.

## Hard restrictions

- Do not commit secrets or credentials.
- Do not touch files not listed in `files_to_touch`.
- Apart from approved source paths, write only `EDIT_<tool>.md` and `CHANGES.diff`.
- Do not modify `.ai/AGENT_HANDOFF.md` or `.ai/CHANGELOG_AI.md`.
- Do not commit, push, or create a pull request; the conductor owns Git and PR operations.
- Do not run destructive commands without explicit human approval.
