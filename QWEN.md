# QWEN.md — Qwen Code Instructions

Read `AGENTS.md` first, then this file.

## Roles

Qwen Code can serve as:

- **Primary builder** — implement the approved plan
- **First reviewer** — independent review before verification
- **Refactor agent** — improve code quality within approved scope
- **Test generator** — write tests for existing code
- **Bug hunter** — find logic errors and edge cases

## When building

1. Read `PLAN.md` completely before writing any code.
2. Touch only the files listed in `files_to_touch`.
3. Make the smallest safe change that satisfies the acceptance criteria.
4. Run available tests.
5. Write an implementation summary in `EDIT_QWEN.md` matching `schemas/edit-summary.schema.json`.
6. Do not push to `main`.

## When reviewing (first review)

1. This is a read-only stage — do not edit code or push.
2. Check the diff against `PLAN.md` and `.ai/CODING_RULES.md`.
3. Flag logic bugs, edge cases, missing tests, scope drift, and security mistakes.
4. Output `REVIEW_QWEN.json` matching `schemas/review.schema.json`.
5. Your review will be compared with Claude's — flag anything it may miss.

**Note (qwen-led mode):** If you built the code in this task, your first review is self-review. Apply extra rigor and flag your own uncertainties explicitly.

## Hard restrictions

- Never push directly to `main`.
- Never commit secrets or credentials.
- Never run destructive commands (`rm -rf`, `git reset --hard`, `git push --force`, `DROP TABLE`, etc.) without explicit human approval.
