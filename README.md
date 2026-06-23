# Runebridge AI Bridge
Vendor-neutral AI development pipeline coordinating Claude Code, Codex, Qwen Code, and Antigravity through Git branches, explicit artifacts, deterministic safety gates, independent reviews, and human-approved pull requests.

AI Bridge is a planned, vendor-neutral workflow for coordinating multiple AI coding tools through a Git repository. It uses explicit files and Git branches as the shared context between Claude Code, OpenAI Codex CLI, Qwen Code, Google Antigravity, and a human reviewer.

> **Project status:** Phases 0.5A through 5 are complete; the Phase 6 plan, isolated runner, Claude planner/reviewer adapter contracts, and Codex builder adapter contract are merged through P6-001E. The public adapter registry remains empty and live execution is still disabled; P6-001F Codex validation remains blocked on explicit per-run approval. Public visibility is intentional; `main` requires a pull request, resolved conversations, and three passing baseline checks. The solo-project policy requires no GitHub approval, but merge remains a manual owner action. Secret scanning and push protection are enabled.

## Goal

Turn one task specification into a reviewed pull request through a controlled pipeline.

## Design Principles

- **Git is the source of truth.**
- **Artifacts are the shared memory.**
- **Humans control irreversible actions.**
- **Gates are deterministic.**
- **Permissions follow least privilege.**
- **Retries are bounded.**

## Planned Operating Modes

The pipeline contract defines three operating modes:

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
|-- .github/workflows/
|-- docs/                        # Architecture, planning, and design documents
|-- prompts/
|-- schemas/
|-- tests/gates/
|-- tests/live/
|-- tools/requirements.txt
|-- tools/bridge/
|   |-- adapters/
|   |-- gates/
|   |-- live/
|   `-- orchestrate.sh
|-- .env.example
|-- .pre-commit-config.yaml
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

- Phase 0: Planning approval
- Phase 0.5A: Contract and documentation alignment - merged into `main`
- Phase 0.5B: Environment, security, permissions, and tooling setup - merged into `main`
- Phase 0.6: Vendor identity and CLI validation - complete; Qwen and Antigravity live paths deferred
- Phase 1: Repository scaffold - complete
- Phase 2: Schemas and deterministic gates - complete
- Phase 3: Adapter stubs and deterministic dry-run outputs - complete
- Phase 4: Pattern A conductor - complete
- Phase 5: Full dry-run pipeline validation - complete
- Phase 6: Live vendor integration - Codex builder contract merged; bounded live validation awaits explicit approval
- Phase 7: Mode benchmarking and deferred dashboard evaluation

## Current Documentation

- `docs/Runebridge-Private-Repository-Architecture.md`
- `docs/AI-Bridge-Implementation-Plan-and-Concerns.md`
- `docs/Environment-and-Security-Setup.md`
- `docs/Vendor-CLI-Validation.md`
- `docs/Phase-1-Repository-Scaffold-Plan.md`
- `docs/Repository-Directory-Ownership.md`
- `docs/Phase-2-Schemas-and-Gates-Plan.md`
- `docs/Phase-3-Deterministic-Adapters-Plan.md`
- `docs/Phase-4-Pattern-A-Conductor-Plan.md`
- `docs/Phase-5-Full-Dry-Run-Plan.md`
- `docs/Phase-5-Full-Dry-Run-Validation.md`
- `docs/Phase-6-Live-Vendor-Validation-Plan.md`
- Pipeline planning documents

## License

MIT License
