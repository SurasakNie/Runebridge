# Phase 4 Pattern A Conductor Plan

## Objective

Implement a deterministic, dry-run-only conductor that sequences Phase 3 adapters and Phase 2 gates for `safe-default`, `qwen-led`, and `dual-builder` modes.

## Controls

- Live mode exits `2` before creating a task directory.
- RSK-0 gate exit `2` is never retried and is propagated unchanged.
- Gate usage and validation errors exit `1`; exit `2` is reserved for explicit RSK-0 escalation.
- Ordinary stage failures may retry from zero to three times through `RUNEBRIDGE_MAX_RETRIES`.
- Every failed stage halts the pipeline before any later stage.
- Task identifiers are single-use; an existing task directory is rejected without modification.
- `FINAL_REPORT.md` records pass/fail, the failed stage, and completed stages.
- The conductor performs no Git, GitHub, merge, secret, deployment, or vendor operation.

## Mode Maps

- `safe-default`: Claude plan, Codex build, Qwen review, mock verify, Claude final review.
- `qwen-led`: Qwen plan/build, no Qwen review, mock verify, Claude final review.
- `dual-builder`: Claude plan, Codex and Qwen builds, Qwen review, mock verify, Claude final review.

Every adapter transition is followed by the relevant deterministic gate. The final secret and mode-aware artifact gates run before a passing report.
The scope gate parses `CHANGES.diff` and rejects paths outside the plan's `files_to_touch` list; an empty dry-run diff is valid.

## Exit Gate

Tests prove all three mode maps, every reachable stage failure, fail-closed live behavior, bounded retry validation, RSK-0 propagation, single-use task directories, and halt-before-later-stage behavior. All protected CI checks pass before manual merge.
