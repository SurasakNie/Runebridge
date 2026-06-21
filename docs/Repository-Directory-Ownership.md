# Repository Directory Ownership

## Purpose

This document assigns responsibility for reserved pipeline paths. It does not authorize implementation before the owning phase begins.

| Path | Owner | Population phase | Current state |
|---|---|---|---|
| `schemas/` | Schema and gate implementation | Phases 2 and 6 | Artifact and live-provenance schemas |
| `tools/bridge/gates/` | Deterministic gate implementation | Phases 2 and 6 | Artifact, safety, and live-provenance gates |
| `tools/bridge/adapters/` | Vendor adapter implementation | Phase 3 | Deterministic dry-run stubs |
| `tools/bridge/live/` | Isolated live-validation runner | Phase 6 | Refusal-by-default runner; no real adapters enabled |
| `tools/bridge/orchestrate.sh` | Pattern A conductor | Phase 4 | Dry-run-only implementation |
| `.bridge/<task-id>/` | Stage owners through conductor-controlled writes | Phases 3-6 | Dry-run evidence; live evidence requires Phase 6 gates |
| `tests/gates/` | Gate and scaffold verification | Phases 1-6 | Deterministic gate and scaffold tests |
| `tests/live/` | Isolated runner verification | Phase 6 | Fake-CLI success and negative-path tests only |

Only the conductor may update shared AI state or perform Git and pull-request operations during automated runs. Manual repository maintenance may change these paths only when they are explicitly in task scope.
