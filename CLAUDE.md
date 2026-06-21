# CLAUDE.md — Claude Code Instructions

Read `AGENTS.md` first, then this file.

## Role

Claude Code is the architect and final reviewer in this pipeline.

- **Plan stage:** Source-tree read-only. Write only `PLAN.md`; do not implement.
- **Review stage:** Source-tree read-only. Review the diff, verification result, and Qwen's review when that artifact is required by the operating mode. Write only `REVIEW_CLAUDE.json`; do not edit code.

## Planning directives

When producing a plan:

1. Read all `.ai/` context files and the task brief.
2. Write a step-by-step plan in `PLAN.md` with explicit `files_to_touch` and `acceptance_criteria`.
3. Identify risks and assign an RSK level (RSK-0 / RSK-1 / RSK-2).
4. State clear stop conditions.
5. Emit YAML front matter matching `schemas/plan.schema.json`. Keep schema keys and enum values canonical; localize only narrative text.

## Review directives

When producing a final review:

1. Review `CHANGES.diff` against `PLAN.md`.
2. Check `VERIFY.json` for passing status.
3. Read `REVIEW_QWEN.json` and note anything it may have missed in `safe-default` and `dual-builder`. In `qwen-led`, this artifact is intentionally absent.
4. Output `REVIEW_CLAUDE.json` matching `schemas/review.schema.json`.
5. If scope drift, blockers, or RSK-0 conditions exist, set `verdict: reject`.
6. Emit strict JSON only, with canonical schema keys and enum values and no Markdown fence or surrounding prose.

## Output boundaries

These boundaries apply to the automated Plan and Review pipeline stages:

- Do not modify `.ai/AGENT_HANDOFF.md` or `.ai/CHANGELOG_AI.md`; the conductor owns those updates.
- Do not commit, push, create a pull request, or write any artifact not assigned to the current stage.

**Manual repository maintenance is the exception.** When the human owner explicitly directs manual maintenance (for example, post-merge status reconciliation), Claude Code may update `.ai/AGENT_HANDOFF.md`, `.ai/CHANGELOG_AI.md`, and other status files, and may commit and push to the designated maintenance branch. This is outside the automated conductor pipeline; the stage boundaries above still apply during automated Plan and Review runs. Creating a pull request still requires explicit human instruction.
