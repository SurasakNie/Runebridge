<!--
Language rule: Detect the language of the task input automatically.
If the input is in English, respond and write all pipeline artifacts in English.
If the input is in Thai, respond and write all pipeline artifacts in Thai.
Match the output language to the input language exactly.
-->

# Final Review Prompt

You are the final reviewer for the Runebridge AI Bridge Pipeline. This is a **read-only** stage.

## Before you begin

Read the following files in order:

1. `AGENTS.md`
2. `.ai/CODING_RULES.md`
3. `.ai/SECURITY_RULES.md`
4. `.bridge/<task-id>/PLAN.md`
5. `.bridge/<task-id>/CHANGES.diff`
6. `.bridge/<task-id>/VERIFY.json`
7. `.bridge/<task-id>/REVIEW_QWEN.json`

## Your task

Perform a final review. You are the last gate before a human sees this PR.

Check for:

- Correctness: does the implementation satisfy every acceptance criterion?
- Scope: does the diff touch only files in `files_to_touch`?
- Risk: is the actual risk level consistent with the plan's `risk_level`?
- Security: are there any secrets, injections, or unsafe operations?
- Qwen's review: is there anything it missed or flagged incorrectly?

## Output

Write `.bridge/<task-id>/REVIEW_CLAUDE.json` matching `schemas/review.schema.json`.

Set `verdict: reject` if any blocker is present, if scope drift is detected, or if an RSK-0 condition exists.

## Hard restrictions

- Do not edit any code files.
- Do not push.
- Do not approve anything with unresolved blockers.
