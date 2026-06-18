# Runebridge
# AI Bridge
Vendor-neutral AI development pipeline coordinating Claude Code, Codex, Qwen Code, and Antigravity through Git branches, explicit artifacts, deterministic safety gates, independent reviews, and human-approved pull requests.

AI Bridge is a planned, vendor-neutral workflow for coordinating multiple AI coding tools through a Git repository. It uses explicit files and Git branches as the shared context between Claude Code, OpenAI Codex CLI, Qwen Code, Google Antigravity, and a human reviewer.

> **Project status:** Design phase. The repository currently contains planning documents; the conductor, adapters, gates, and CI workflows have not yet been implemented.

## Goal

Turn one task specification into a reviewed pull request through a controlled pipeline.

## Design Principles

- **Git is the source of truth.**
- **Artifacts are the shared memory.**
- **Humans control irreversible actions.**
- **Gates are deterministic.**
- **Permissions follow least privilege.**
- **Retries are bounded.**

## Supported Operating Modes

The repository supports three operating modes:

- `safe-default` (recommended)
- `qwen-led`
- `dual-builder`

All modes use the same:

- artifact contracts
- schema validation
- scope gates
- verification gates
- secret scanning
- RSK enforcement
- human approval requirements
- dry-run support

No operating mode may bypass safety controls.

## Planned Repository Layout

```text
.
|-- .ai/
|-- .bridge/
|-- docs/                        # Architecture, planning, and design documents
|-- prompts/
|-- schemas/
|-- tools/bridge/
|   |-- adapters/
|   |-- gates/
|   `-- orchestrate.sh
|-- AGENTS.md
|-- CLAUDE.md
|-- QWEN.md
`-- README.md
```

## Safety Model

RSK-0 actions require human approval.

The conductor must halt when:

- plan or acceptance criteria are missing
- implementation changes files outside approved scope
- verification fails after retry budget
- reviewers report blockers or scope drift
- secrets are detected
- RSK-0 actions are requested

## Dry Run Requirement

Before real vendor CLI execution is enabled, the system must support:

`DRY_RUN_MODE=true`

When enabled:

- Claude, Codex, Qwen, and Antigravity adapters generate deterministic mock artifacts
- Gates execute normally
- Branch creation and PR logic can be validated
- Retry loops and halt behavior can be tested
- No vendor tokens are consumed

## Rollout

- Phase 0: Manual validation and vendor CLI verification
- Phase 1: Shared `.ai/` context and repository scaffold
- Phase 2: CI and deterministic gates
- Phase 3: Pattern A conductor
- Phase 4: Dry-run validation
- Phase 5: Optimize and benchmark supported operating modes (`safe-default`, `qwen-led`, `dual-builder`)
- Phase 6: Evaluate advanced orchestration options

## Current Documentation

- `docs/Runebridge-Private-Repository-Architecture.md`
- `docs/AI-Bridge-Implementation-Plan-and-Concerns.md`
- Pipeline planning documents

## License

MIT License
