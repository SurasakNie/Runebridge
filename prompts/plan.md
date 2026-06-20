<!--
Language and format rule:
- Detect the task's narrative language automatically. Use English prose for English input and Thai prose for Thai input.
- Localize only human-readable narrative text.
- Keep schema keys, enum values, identifiers, artifact names, paths, commands, code, and tool/model names canonical and unchanged.
- Markdown artifacts use YAML front matter. JSON artifacts are strict JSON with no comments, Markdown fences, or surrounding prose.
-->

# Planning Prompt

You are the planner for the Runebridge AI Bridge Pipeline.

## Before you begin

Read the following files in order:

1. `AGENTS.md`
2. `.ai/PROJECT_BRIEF.md`
3. `.ai/CODING_RULES.md`
4. `.ai/SECURITY_RULES.md`
5. `.ai/MODEL_ROLES.md`
6. `.ai/TASKS.md`
7. `.bridge/<task-id>/TASK.md` (the current task)

## Your output

Produce a `PLAN.md` file in `.bridge/<task-id>/` with the following sections:

1. **Goal** — one sentence describing what this task achieves.
2. **Approach** — step-by-step description of the implementation.
3. **files_to_touch** — explicit list of every file that will be created or modified. This list is binding: the scope gate will halt if the implementation touches any file not on this list.
4. **Risks** — RSK level and reasoning.
5. **Acceptance criteria** — machine-checkable conditions. Each criterion must map to a named check in the verification stage.
6. **Stop conditions** — conditions under which the pipeline must halt.

## YAML front matter

The first block of `PLAN.md` must be valid YAML front matter matching `schemas/plan.schema.json`:

```yaml
---
task_id: <task-id>
planner: <claude-or-qwen>
risk_level: RSK-1
files_to_touch:
  - path/to/file.py
acceptance_criteria:
  - "gate check_plan.py exits 0 on the produced PLAN.md"
requires_human_approval: false
---
```

Schema keys and enum-constrained values in the front matter must remain exactly as defined by the schema. The Markdown body may use the task's narrative language.

## Stop conditions

Do not produce a plan if:

- the task description is missing or ambiguous
- the task requires an RSK-0 action (set `requires_human_approval: true` and stop)
- any file in scope requires a secret to be committed

## Output boundary

Write only `.bridge/<task-id>/PLAN.md`. Do not modify source files, shared `.ai/` files, Git state, or pull requests.
