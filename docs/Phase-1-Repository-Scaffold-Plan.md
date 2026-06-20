# Phase 1 Repository Scaffold Plan

## Objective

Create the approved repository directory and placeholder structure required for later schema, gate, adapter, and conductor work. Phase 1 establishes ownership boundaries only; it does not implement pipeline behavior.

## Entry Criteria

- Phases 0.5A, 0.5B, and 0.6 are complete.
- The Phase 0.6 validation matrix and vendor deferrals are approved.
- Work starts from an updated `main` on a feature branch.
- Existing baseline CI, secret scanning, and branch protection remain enabled.

## Deliverables

| ID | Deliverable | Purpose |
|---|---|---|
| P1-001A | `schemas/` | Reserve the location for Phase 2 JSON Schemas |
| P1-001B | `tools/bridge/adapters/` | Reserve the location for Phase 3 vendor adapters |
| P1-001C | `tools/bridge/gates/` | Reserve the location for Phase 2 deterministic gates |
| P1-001D | `tools/bridge/orchestrate.sh` | Add a non-operational placeholder for the Phase 4 conductor |
| P1-001E | `.bridge/` layout documentation | Define generated runtime-artifact boundaries and retention expectations |
| P1-001F | Directory ownership documentation | Identify which later phase may populate each reserved location |
| P1-001G | Scaffold verification | Prove layout, permissions, CI, and secret scanning remain clean |

Empty directories must contain a minimal `.gitkeep` file. The conductor placeholder must exit nonzero with a clear `not implemented` message so it cannot be mistaken for a working pipeline.

## Execution Sequence

1. Synchronize `main` and create a Phase 1 feature branch.
2. Inventory the existing tree and reconcile it with the planned layout in `README.md`.
3. Create only the directories and placeholders listed above.
4. Document ownership, generated-file boundaries, and the non-operational conductor contract.
5. Add focused tests that assert the scaffold exists and the conductor placeholder fails closed.
6. Run local compilation, smoke tests, pre-commit, ShellCheck, and secret scanning.
7. Open a pull request and require all protected checks to pass before manual merge.

## Acceptance Criteria

- Every planned Phase 1 path exists with no unapproved executable behavior.
- `tools/bridge/orchestrate.sh` is syntactically valid and always fails closed.
- No JSON Schema, gate logic, vendor invocation, retry loop, GitHub mutation, or credential handling is implemented.
- Generated `.bridge/` artifacts remain ignored except for approved documentation or placeholders.
- Tests verify the scaffold paths and fail-closed placeholder behavior.
- The full pre-commit suite and all required GitHub checks pass.
- The pull-request diff contains only Phase 1 scaffold, documentation, tests, and shared-state updates.

## Explicitly Out of Scope

- Phase 2 schemas and deterministic gate implementations
- Phase 3 mock or live vendor adapters
- Phase 4 conductor sequencing, retries, or artifact archival
- Automated branch, issue, pull-request, or merge operations
- Qwen provider subscription or credentials
- Antigravity IDE automation

## Risks and Rollback

This work is RSK-2. The blast radius is limited to reserved paths, documentation, and fail-closed placeholders. Roll back by reverting the Phase 1 pull request; no external resources, credentials, repository settings, or vendor accounts are changed.

## Exit Gate

Phase 1 is complete when the protected pull request is manually merged with all acceptance criteria and required checks satisfied. Phase 2 may then implement schemas and deterministic gates in a new feature branch.
