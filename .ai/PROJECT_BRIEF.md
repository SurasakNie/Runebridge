# Project Brief

**Project:** Runebridge
**Purpose:** Vendor-neutral AI development pipeline coordinating Claude Code, OpenAI Codex CLI, Qwen Code, and Google Antigravity through Git branches, explicit artifacts, deterministic safety gates, independent reviews, and human-approved pull requests.
**Stack:** Bash, Python 3.11+, GitHub Actions
**Status:** Phases 0.5A through 5 complete; Phase 5 merged through PR #10, and Phase 6 live-vendor validation planning is next

## Constraints

- Safety gates are required at every stage transition.
- No AI tool may merge to `main` directly.
- Secrets are never committed to any file or artifact.
- All pipeline artifacts are committed to the feature branch for audit trail.
- Role adapters write only their designated artifacts; the conductor owns shared `.ai/` state and Git/PR operations.
- Narrative text may be English or Thai, but machine-readable keys, enums, identifiers, paths, commands, code, and artifact names remain canonical.

## Canonical repository layout

```text
.
├── .ai/                         # Shared project context (this directory)
├── .bridge/
│   └── <task-id>/               # Per-task handoff artifacts (committed to branch)
│       ├── TASK.md
│       ├── PLAN.md
│       ├── EDIT_*.md
│       ├── CHANGES.diff
│       ├── VERIFY.json
│       ├── REVIEW_CLAUDE.json
│       ├── REVIEW_QWEN.json        # safe-default and dual-builder only
│       └── FINAL_REPORT.md
├── docs/                        # Human-authored documentation
├── prompts/                     # Versioned prompts for each role
├── schemas/                     # JSON Schema artifact contracts
├── tests/
│   └── gates/                   # pytest tests for gate scripts
├── tools/
│   └── bridge/
│       ├── adapters/            # Vendor CLI wrappers
│       ├── gates/               # Deterministic stop/go scripts
│       └── orchestrate.sh       # Pattern A conductor
├── AGENTS.md
├── CLAUDE.md
├── QWEN.md
└── README.md
```

## Definition of success for MVP

- `DRY_RUN_MODE=true bash tools/bridge/orchestrate.sh --task T001 --mode safe-default` runs all 12 stages, produces all artifacts, and exits 0.
- All gate unit tests pass.
- A PR opened by the conductor triggers `test.yml` and `bridge-gates.yml` CI checks.

