# QWEN.md — Qwen Code Instructions

Read `AGENTS.md` first, then this file.

## Roles

Qwen Code can serve as:

- **Planner** — produce the implementation plan in `qwen-led` mode
- **Primary builder** — implement the approved plan
- **First reviewer** — independent review before verification
- **Refactor agent** — improve code quality within approved scope
- **Test generator** — write tests for existing code
- **Bug hunter** — find logic errors and edge cases

## When planning (`qwen-led`)

1. Read the task and all required `.ai/` context without modifying source files.
2. Use `prompts/plan.md` and write only `PLAN.md`.
3. Set the planner identity to `qwen` in the artifact front matter.
4. Do not implement the plan during the planning stage.
5. Stop for RSK-0 or ambiguous requirements as directed by the planning prompt.
6. Do not modify shared `.ai/` state or perform Git/PR operations.

## When building

1. Read `PLAN.md` completely before writing any code.
2. Touch only the files listed in `files_to_touch`.
3. Make the smallest safe change that satisfies the acceptance criteria.
4. Run available tests.
5. Write an implementation summary in `EDIT_QWEN.md` matching `schemas/edit-summary.schema.json`.
6. Do not commit or push; the conductor owns Git operations.
7. Do not modify shared `.ai/` state; the conductor owns handoff, changelog, commit, push, and PR operations.

## When reviewing (first review)

1. This is a read-only stage — do not edit code or push.
2. Check the diff against `PLAN.md` and `.ai/CODING_RULES.md`.
3. Flag logic bugs, edge cases, missing tests, scope drift, and security mistakes.
4. Output `REVIEW_QWEN.json` matching `schemas/review.schema.json`.
5. Your review will be compared with Claude's — flag anything it may miss.
6. Do not modify source files or shared `.ai/` state.

**qwen-led mode:** Do not run the Qwen first-review stage after a Qwen build. `REVIEW_QWEN.json` is omitted in this mode; Antigravity verifies the build and Claude performs the independent final review.

## Hard restrictions

- Never commit or push from a role stage; the conductor owns Git operations.
- Never commit secrets or credentials.
- Never run destructive commands (`rm -rf`, `git reset --hard`, `git push --force`, `DROP TABLE`, etc.) without explicit human approval.
