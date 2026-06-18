# AI Bridge — Implementation Plan and Concerns

**Branch:** `claude/latest-drafts-ptdnpq`  
**Date:** 2026-06-18  
**Status:** Approved for implementation with conditions

---

## Part 1 — Implementation Plan

### What Is Being Built

A full repository scaffold for the Runebridge AI Bridge Pipeline, covering Phase 1 (shared `.ai/` context + root instruction files) through Phase 3 (Pattern A deterministic conductor). This is the complete working skeleton — every file the pipeline needs to run, with adapter stubs for unconfirmed vendor CLIs.

### Files to Create (~40 files across 9 groups)

#### Group 1 — Root instruction files

| File | Purpose |
|---|---|
| `AGENTS.md` | Universal pre-read for all AI agents; lists `.ai/` read order, work process, and restrictions |
| `CLAUDE.md` | Claude Code-specific: architect + final reviewer role; read-only default for plan/review stages |
| `QWEN.md` | Qwen Code-specific: primary builder, first reviewer, refactor agent, bug hunter |
| `.gitignore` | Excludes secrets, local configs, `.bridge/` runtime subdirs, Python cache |

#### Group 2 — `.ai/` shared context (committed, versioned)

| File | Purpose |
|---|---|
| `.ai/PROJECT_BRIEF.md` | Project purpose, stack, constraints, definition of success |
| `.ai/CODING_RULES.md` | Style rules all agents follow |
| `.ai/TASKS.md` | Active task tracking and backlog |
| `.ai/AGENT_HANDOFF.md` | Cross-agent handoff state and decisions log |
| `.ai/CHANGELOG_AI.md` | AI-generated change log; appended by conductor in Stage 11 |
| `.ai/SECURITY_RULES.md` | Dangerous actions policy; defines RSK-0/RSK-1/RSK-2 and enforcement |
| `.ai/MODEL_ROLES.md` | Role assignments per model for each operating mode |
| `.ai/MCP_POLICY.md` | MCP permission policy: allowed servers, per-tool access map, banned defaults |

#### Group 3 — `schemas/` artifact contracts (JSON Schema draft-07)

| File | Validates |
|---|---|
| `schemas/task.schema.json` | `TASK.md` YAML front-matter |
| `schemas/plan.schema.json` | `PLAN.md` YAML front-matter; enforces non-empty `files_to_touch` and `acceptance_criteria` |
| `schemas/edit-summary.schema.json` | `EDIT_*.md` build summary |
| `schemas/verify.schema.json` | `VERIFY.json` |
| `schemas/review.schema.json` | `REVIEW_CLAUDE.json` and `REVIEW_QWEN.json` |

#### Group 4 — `prompts/` versioned role prompts

| File | Used by |
|---|---|
| `prompts/plan.md` | `adapters/claude_plan.sh` |
| `prompts/edit-from-plan.md` | `adapters/codex_build.sh`, `adapters/qwen_build.sh` |
| `prompts/qwen-review.md` | `adapters/qwen_review.sh` |
| `prompts/antigravity-verify.md` | `adapters/antigravity_verify.sh` |
| `prompts/final-review.md` | `adapters/claude_review.sh` |

#### Group 5 — `tools/bridge/gates/` deterministic stop/go scripts (Python)

Exit codes: **0** = pass, **1** = fail, **2** = RSK-0 halt.

| File | Checks |
|---|---|
| `check_plan.py` | `files_to_touch` non-empty, `acceptance_criteria` non-empty, schema validates |
| `check_scope.py` | Every file in `CHANGES.diff` is listed in `PLAN.md`'s `files_to_touch` |
| `check_review.py` | `blockers == []`, `scope_drift == false`, verdicts match when both reviewers are required |
| `check_verify.py` | `VERIFY.json` result is `"pass"` |
| `check_rsk0.py` | No RSK-0 triggers in plan; exits 2 on trip |
| `check_artifacts.py` | All required artifacts exist and are non-empty for the given mode |
| `check_no_secrets.py` | Regex scan of `CHANGES.diff` for API keys, tokens, and high-entropy secrets |

`tools/requirements.txt` — `jsonschema>=4.0`, `PyYAML>=6.0`

#### Group 6 — `tools/bridge/adapters/` vendor CLI wrappers (bash)

Each adapter takes `TASK_ID` as an argument, reads `.bridge/$TASK_ID/` inputs, writes `.bridge/$TASK_ID/` outputs, and exits 0/non-zero. All vendor CLI invocations are isolated here; the conductor never calls vendor CLIs directly.

| File | Wraps | I/O |
|---|---|---|
| `claude_plan.sh` | Claude Code (`claude -p`) | In: `TASK.md` → Out: `PLAN.md` |
| `codex_build.sh` | OpenAI Codex CLI (`codex exec`) | In: `PLAN.md` → Out: `EDIT_CODEX.md`, `CHANGES.diff` |
| `qwen_build.sh` | Qwen Code (`qwen`) | In: `PLAN.md` → Out: `EDIT_QWEN.md`, `CHANGES.diff` |
| `qwen_review.sh` | Qwen Code — read-only | In: `PLAN.md`, `CHANGES.diff` → Out: `REVIEW_QWEN.json` |
| `antigravity_verify.sh` | Google Antigravity | In: `PLAN.md`, `CHANGES.diff` → Out: `VERIFY.json` |
| `claude_review.sh` | Claude Code — read-only | In: `PLAN.md`, `CHANGES.diff`, `REVIEW_QWEN.json`, `VERIFY.json` → Out: `REVIEW_CLAUDE.json` |

#### Group 7 — `tools/bridge/orchestrate.sh` (Pattern A conductor)

Accepts: `--task`, `--mode` (`safe-default` | `qwen-led` | `dual-builder`), `--planner`, `--builder`, `--first-reviewer`, `--verifier`, `--final-reviewer`.

Stage sequence:

```text
Stage  0  Init          — create branch bridge/<task-id>, write TASK.md
Stage  1  Plan          — run planner adapter
Stage  2  Gate          — check_plan.py + check_rsk0.py
Stage  3  Build         — run builder adapter
Stage  4  Gate          — check_scope.py
Stage  5  First review  — qwen_review.sh
Stage  6  Gate          — check_review.py --reviewer qwen
Stage  7  Verify        — run verifier adapter
Stage  8  Gate          — check_verify.py
Stage  9  Final review  — claude_review.sh
Stage 10  Gate          — check_review.py --reviewer both + check_no_secrets.py
Stage 11  Final report  — write FINAL_REPORT.md, append CHANGELOG_AI.md
Stage 12  PR            — commit artifacts + gh pr create
```

Key behaviors:
- Any gate exits non-zero → halt with message.
- `check_rsk0.py` exit code 2 → `halt_rsk0()` and print `HUMAN_REQUIRED`.
- Verify retry budget: 2 retries; previous `CHANGES.diff` archived as `CHANGES.diff.attempt-N`.
- Cross-check disagreement → halt and attach both reviews.

#### Group 8 — `.bridge/.gitkeep`

Tracks the directory in git. Runtime task subdirectories (`.bridge/<task-id>/`) are gitignored via `.bridge/*/`.

#### Group 9 — `.github/workflows/`

| File | Triggers | Checks |
|---|---|---|
| `test.yml` | push + PR to main | shellcheck on adapters + conductor; `py_compile` on gates; JSON schema syntax validation |
| `bridge-gates.yml` | PR touching `.bridge/` paths | `check_artifacts.py` + `check_no_secrets.py` on bridge PRs |

### Implementation Order

```text
1.  .gitignore
2.  .bridge/.gitkeep
3.  schemas/*.json
4.  .ai/*.md
5.  AGENTS.md, CLAUDE.md, QWEN.md
6.  prompts/*.md
7.  tools/requirements.txt
8.  tools/bridge/gates/*.py
9.  tools/bridge/adapters/*.sh
10. tools/bridge/orchestrate.sh
11. .github/workflows/test.yml
12. .github/workflows/bridge-gates.yml
```

---

## Part 2 — Decisions and Concerns

Reviewed against the three planning documents (`aibridgepipelineplan1qwen.md`, `aibridgepipelineplan2qwen.md`, `aibridgepipelineplan3qwen.md`) and `docs/Runebridge-Private-Repository-Architecture.md`.

### Concern 1 — Naming conflict: session recovery files vs. `.ai/` convention (Approved)

**Decision:** Use `.ai/` as the canonical session recovery and shared-context system.

Do not create duplicate root-level files:
- `PROJECT_CONTEXT.md`
- `ARCHITECTURE.md`
- `DECISIONS.md`
- `OPEN_TASKS.md`

Map any unique content from those concepts into:
- `.ai/PROJECT_BRIEF.md`
- `.ai/TASKS.md`
- `.ai/AGENT_HANDOFF.md`
- `AGENTS.md`
- `CLAUDE.md`

### Concern 2 — `docs/` directory not in the planned repo layout (Approved)

**Decision:** Add `docs/` to the canonical repository layout.

Update:
- `README.md`
- `.ai/PROJECT_BRIEF.md`
- repository structure diagrams

### Concern 3 — Operating modes (Approved: keep all for now)

**Decision:** Keep all planned operating modes in the implementation:
- `safe-default`
- `qwen-led`
- `dual-builder`

**Condition:** All modes must use the same safety guarantees:
- artifact contracts
- schema validation
- scope gate
- RSK-0 halt behavior
- verification gate
- independent review gate
- secret scanning
- human approval before merge or irreversible action

No mode may bypass deterministic gates or human approval requirements.

### Concern 4 — Dashboard scope not in Phase 1–3 (Approved: defer)

**Decision:** Defer dashboard development.

Add to `.ai/TASKS.md` backlog only:
- token usage dashboard
- cost dashboard
- pipeline visualization dashboard
- agent activity dashboard

### Concern 5 — AI Replacement Matrix (Approved: no concern)

Appendix A's replacement matrix is consistent with the planned `MODEL_ROLES.md` design. No action needed.

### Concern 6 — GitHub Actions minute budget on private repos (Approved: monitor after implementation)

**Decision:** Proceed with the current GitHub Actions design and monitor usage after implementation.

Potential future options if Actions minutes become a constraint:
- GitHub Pro
- reduced workflow triggers
- self-hosted runners
- public Runebridge repository with private project repositories

### Concern 7 — Dry-run mode before real vendor CLI use (Approved: add)

**Decision:** Add `DRY_RUN_MODE=true` support before real vendor CLI use is enabled.

When dry-run mode is active:
- adapter scripts must skip real Claude/Codex/Qwen/Antigravity CLI calls
- adapter scripts must write deterministic mock artifacts instead
- gates must run normally against the mock artifacts
- branch creation, artifact flow, retry behavior, halt behavior, final report generation, and PR creation logic can be tested safely
- dry-run output must clearly state `DRY_RUN_MODE=true`

This allows validation of:
- artifact flow
- gate logic
- retry loops
- branch creation
- final report generation
- PR creation
- CI workflow behavior

without spending tokens or depending on vendor CLI behavior.

---

## Summary of Actions Before Implementation

| # | Action | Owner | Priority | Decision |
|---|---|---|---|---|
| 1 | Use `.ai/` as the canonical session recovery/shared context system | Human | Blocking | Approved |
| 2 | Add `docs/` to canonical repo layout | Claude Code | Low | Approved |
| 3 | Keep all operating modes (`safe-default`, `qwen-led`, `dual-builder`) | Claude Code | High | Approved |
| 4 | Defer dashboard to backlog | Agreed | Low | Approved |
| 5 | Proceed with current GitHub Actions design and monitor minutes | Human | High | Approved |
| 6 | Add `DRY_RUN_MODE=true` support for safe pipeline validation | Claude Code | High | Approved |

## Final Decision

**GO — Approved for implementation.**

Proceed with creation of the repository scaffold, schemas, prompts, gates, adapters, workflows, dry-run support, and conductor as described in this document.
