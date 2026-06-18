# AI Bridge — Implementation Plan and Concerns

**Branch:** `claude/latest-drafts-ptdnpq`  
**Date:** 2026-06-18  
**Status:** Awaiting approval before implementation begins

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
| `.ai/CODING_RULES.md` | Style rules all agents follow (bash `set -euo pipefail`, Python type hints, JSON 2-space indent, etc.) |
| `.ai/TASKS.md` | Active task tracking — updated by conductor at each stage transition |
| `.ai/AGENT_HANDOFF.md` | Cross-agent handoff state; append-only log of who handed off to whom |
| `.ai/CHANGELOG_AI.md` | AI-generated change log; appended by conductor in Stage 11 |
| `.ai/SECURITY_RULES.md` | Dangerous actions policy; defines RSK-0/RSK-1/RSK-2 and enforcement |
| `.ai/MODEL_ROLES.md` | Role assignments per model for each operating mode |
| `.ai/MCP_POLICY.md` | MCP permission policy: allowed servers, per-tool access map, banned defaults |

#### Group 3 — `schemas/` artifact contracts (JSON Schema draft-07)

| File | Validates |
|---|---|
| `schemas/task.schema.json` | `TASK.md` YAML front-matter |
| `schemas/plan.schema.json` | `PLAN.md` YAML front-matter — enforces `files_to_touch` and `acceptance_criteria` are non-empty |
| `schemas/edit-summary.schema.json` | `EDIT_*.md` build summary |
| `schemas/verify.schema.json` | `VERIFY.json` |
| `schemas/review.schema.json` | `REVIEW_CLAUDE.json` and `REVIEW_QWEN.json` |

#### Group 4 — `prompts/` versioned role prompts

| File | Used by |
|---|---|
| `prompts/plan.md` | `adapters/claude_plan.sh` |
| `prompts/edit-from-plan.md` | `adapters/codex_build.sh`, `adapters/qwen_build.sh` |
| `prompts/qwen-review.md` | `adapters/qwen_review.sh` — read-only review; no edits, no push |
| `prompts/antigravity-verify.md` | `adapters/antigravity_verify.sh` |
| `prompts/final-review.md` | `adapters/claude_review.sh` |

#### Group 5 — `tools/bridge/gates/` deterministic stop/go scripts (Python)

Exit codes: **0** = pass, **1** = fail (retry possible), **2** = RSK-0 halt (stop entire pipeline, wait for human).

| File | Checks |
|---|---|
| `check_plan.py` | `files_to_touch` non-empty, `acceptance_criteria` non-empty, schema validates |
| `check_scope.py` | Every file in `CHANGES.diff` is listed in `PLAN.md`'s `files_to_touch` |
| `check_review.py` | `blockers == []`, `scope_drift == false`, verdicts match (`--reviewer both`) |
| `check_verify.py` | `VERIFY.json` result is `"pass"` |
| `check_rsk0.py` | No RSK-0 triggers in plan (merge, deploy, secret rotation, force-push, schema migration); exits 2 on trip |
| `check_artifacts.py` | All required artifacts exist and are non-empty for the given mode |
| `check_no_secrets.py` | Regex scan of `CHANGES.diff` for API key patterns, tokens, high-entropy secrets |

`tools/requirements.txt` — `jsonschema>=4.0`, `PyYAML>=6.0`

#### Group 6 — `tools/bridge/adapters/` vendor CLI wrappers (bash)

Each adapter: takes `TASK_ID` as arg, reads `.bridge/$TASK_ID/` inputs, writes `.bridge/$TASK_ID/` outputs, exits 0/non-zero. All vendor CLI invocations are isolated here — the conductor never calls vendor CLIs directly.

| File | Wraps | I/O |
|---|---|---|
| `claude_plan.sh` | Claude Code (`claude -p`) | In: `TASK.md` → Out: `PLAN.md` |
| `codex_build.sh` | OpenAI Codex CLI (`codex exec`) | In: `PLAN.md` → Out: `EDIT_CODEX.md`, `CHANGES.diff` |
| `qwen_build.sh` | Qwen Code (`qwen`) | In: `PLAN.md` → Out: `EDIT_QWEN.md`, `CHANGES.diff` |
| `qwen_review.sh` | Qwen Code — read-only | In: `PLAN.md`, `CHANGES.diff` → Out: `REVIEW_QWEN.json` |
| `antigravity_verify.sh` | Google Antigravity | In: `PLAN.md`, `CHANGES.diff` → Out: `VERIFY.json` |
| `claude_review.sh` | Claude Code — read-only | In: `PLAN.md`, `CHANGES.diff`, `REVIEW_QWEN.json`, `VERIFY.json` → Out: `REVIEW_CLAUDE.json` |

#### Group 7 — `tools/bridge/orchestrate.sh` (Pattern A conductor)

Accepts: `--task`, `--mode` (safe-default | qwen-led | dual-builder), `--planner`, `--builder`, `--first-reviewer`, `--verifier`, `--final-reviewer`.

Stage sequence:

```
Stage  0  Init          — create branch bridge/<task-id>, write TASK.md
Stage  1  Plan          — run planner adapter
Stage  2  Gate          — check_plan.py + check_rsk0.py (exit 2 → halt_rsk0)
Stage  3  Build         — run builder adapter
Stage  4  Gate          — check_scope.py
Stage  5  First review  — qwen_review.sh
Stage  6  Gate          — check_review.py --reviewer qwen
Stage  7  Verify        — run verifier adapter  ← retry loop entry
Stage  8  Gate          — check_verify.py (fail → back to Stage 3, max 2 retries, then halt)
Stage  9  Final review  — claude_review.sh
Stage 10  Gate          — check_review.py --reviewer both + check_no_secrets.py
Stage 11  Final report  — write FINAL_REPORT.md, append CHANGELOG_AI.md
Stage 12  PR            — commit artifacts + gh pr create
```

Key behaviors:
- Any gate exits non-zero → halt with message
- `check_rsk0.py` exit code 2 → `halt_rsk0()` — stops entirely, prints `HUMAN_REQUIRED`
- Verify retry budget: 2 retries; previous `CHANGES.diff` archived as `CHANGES.diff.attempt-N`
- Cross-check disagreement (verdicts diverge on `blockers` or `scope_drift`) → halt, attach both reviews

#### Group 8 — `.bridge/.gitkeep`

Tracks the directory in git. Runtime task subdirs (`.bridge/<task-id>/`) are gitignored via `.bridge/*/`.

#### Group 9 — `.github/workflows/`

| File | Triggers | Checks |
|---|---|---|
| `test.yml` | push + PR to main | shellcheck on adapters + conductor; `py_compile` on gates; JSON schema syntax validation |
| `bridge-gates.yml` | PR touching `.bridge/` paths | `check_artifacts.py` + `check_no_secrets.py` on bridge PRs |

### Implementation Order

```
1.  .gitignore
2.  .bridge/.gitkeep
3.  schemas/*.json  (5 files)
4.  .ai/*.md        (8 files)
5.  AGENTS.md, CLAUDE.md, QWEN.md
6.  prompts/*.md    (5 files)
7.  tools/requirements.txt
8.  tools/bridge/gates/*.py   (7 files)
9.  tools/bridge/adapters/*.sh  (6 files)
10. tools/bridge/orchestrate.sh
11. .github/workflows/test.yml
12. .github/workflows/bridge-gates.yml
```

---

## Part 2 — Concerns from `docs/Runebridge-Private-Repository-Architecture.md`

Reviewed against the three planning documents (`aibridgepipelineplan1qwen.md`, `aibridgepipelineplan2qwen.md`, `aibridgepipelineplan3qwen.md`).

### Concern 1 — Naming conflict: session recovery files vs. `.ai/` convention (Action required)

**What the architecture doc says:** Appendix B recommends root-level files `PROJECT_CONTEXT.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `OPEN_TASKS.md` for session recovery.

**What the planning docs say:** The same purpose is served by `.ai/PROJECT_BRIEF.md`, `.ai/TASKS.md`, `.ai/AGENT_HANDOFF.md`, and `CLAUDE.md`/`AGENTS.md`.

**Problem:** Two parallel naming schemes for the same content creates confusion for agents about which file to read.

**Recommended fix:** Adopt the `.ai/` convention (already well-specified). Map unique content from the architecture doc's Appendix B into the `.ai/` files:
- `PROJECT_CONTEXT.md` content → `.ai/PROJECT_BRIEF.md`
- `ARCHITECTURE.md` content → `CLAUDE.md` + `AGENTS.md`
- `DECISIONS.md` content → `.ai/AGENT_HANDOFF.md` (decisions section)
- `OPEN_TASKS.md` content → `.ai/TASKS.md`

### Concern 2 — `docs/` directory not in the planned repo layout

**What the architecture doc says:** Lives at `docs/Runebridge-Private-Repository-Architecture.md` (already on `main`).

**What the planning docs say:** Planned layout includes `docs/` implicitly but doesn't define its contents.

**Problem:** No conflict, but the `docs/` directory should be acknowledged in the canonical repo layout so it isn't accidentally omitted from future structure diagrams.

**Recommended fix:** Add `docs/` to the layout table in `README.md` and in `.ai/PROJECT_BRIEF.md` as part of this implementation pass.

### Concern 3 — GitHub Actions minute budget on private repos (Cost risk)

**What the architecture doc says:** Recommends GitHub Free with private repositories.

**What the planning docs say:** Pipeline assumes GitHub Actions CI running on every PR (lint + gate checks).

**Problem:** GitHub Free allows **2,000 Actions minutes/month** for private repos. With multiple project repos (AirPump, PhoneHolder, MedicalDevice) each running CI on every PR, this budget can run out within a few weeks of active development.

**Recommended fix:**
- Option A: Use GitHub Pro ($4/user/month) for 3,000 minutes/month.
- Option B: Restrict the heavier `bridge-gates.yml` workflow to only run on PRs targeting `main`, not all branches.
- Option C: Keep Runebridge itself public (pipeline config, not project source) and keep project repos private.

No public code risk in option C — the `.ai/` files and pipeline config contain no secrets (per the security rules), and adapter stubs document behavior without exposing credentials.

### Concern 4 — Dashboard scope not in Phase 1–3

**What the architecture doc says:** `dashboard/index.html` as a local token usage dashboard.

**What the planning docs say:** No dashboard mentioned anywhere in Phases 0–6.

**Problem:** Not a conflict — but building a dashboard now adds scope to an already large first implementation.

**Recommended fix:** Defer to Phase 5 or later. Add a placeholder task in `.ai/TASKS.md` backlog.

### Concern 5 — AI Replacement Matrix (no concern)

Appendix A's replacement matrix (Claude → Qwen fallback for planner/reviewer; Codex → Qwen fallback for builder) is fully consistent with the planning docs' `MODEL_ROLES.md` design. No action needed.

---

## Summary of Actions Before Implementation

| # | Action | Owner | Priority |
|---|---|---|---|
| 1 | Decide on `.ai/` vs. root-level session recovery files | Human | **Blocking** |
| 2 | Decide on GitHub Free vs. Pro (CI minutes) | Human | High |
| 3 | Add `docs/` to canonical repo layout | Claude Code (this pass) | Low |
| 4 | Defer dashboard to backlog | Agreed | Low |

Once action item 1 is decided, implementation can begin with all 40 scaffold files on branch `claude/latest-drafts-ptdnpq`.
