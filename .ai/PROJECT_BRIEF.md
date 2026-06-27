# Project Brief

**Project:** Runebridge
**Purpose:** Vendor-neutral AI development pipeline coordinating Claude Code, OpenAI Codex CLI, Qwen Code, and Google Antigravity through Git branches, explicit artifacts, deterministic safety gates, independent reviews, and human-approved pull requests.
**Stack:** Bash, Python 3.11+, GitHub Actions
**Status:** Phases 0.5A through 5 complete; P6-001E Codex builder adapter contract merged through PR #18, with the public adapter registry empty and P6-001F live execution blocked pending explicit approval. Qwen provider/auth decisions are recorded, the shared remote environment remains blocked by egress-policy `403 Forbidden`, and live Qwen follows the approved `PC-first, VM-later` external-runner model

## Constraints

- Safety gates are required at every stage transition.
- No AI tool may merge to `main` directly.
- Secrets are never committed to any file or artifact.
- All pipeline artifacts are committed to the feature branch for audit trail.
- Role adapters write only their designated artifacts; the conductor owns shared `.ai/` state and Git/PR operations.
- Narrative text may be English or Thai, but machine-readable keys, enums, identifiers, paths, commands, code, and artifact names remain canonical.
- Live Qwen credentials remain outside the repository and outside committed artifacts.
- The shared remote environment is not an approved live Qwen runner while provider hosts return egress-policy `403 Forbidden`.
- The approved fallback is to run live Qwen from an external environment, starting with the owner's PC, while the repository and artifact contracts remain unchanged.

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
