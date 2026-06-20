# Repository Directory Ownership

## Purpose

This document assigns responsibility for reserved pipeline paths. It does not authorize implementation before the owning phase begins.

| Path | Owner | Population phase | Phase 1 state |
|---|---|---|---|
| `schemas/` | Schema and gate implementation | Phase 2 | Empty placeholder |
| `tools/bridge/gates/` | Deterministic gate implementation | Phase 2 | Empty placeholder |
| `tools/bridge/adapters/` | Vendor adapter implementation | Phase 3 | Deterministic dry-run stubs |
| `tools/bridge/orchestrate.sh` | Pattern A conductor | Phase 4 | Fail-closed placeholder |
| `.bridge/<task-id>/` | Stage owners through conductor-controlled writes | Phases 3-4 | Layout documented only |
| `tests/gates/` | Gate and scaffold verification | Phases 1-2 | Environment and scaffold tests |

Only the conductor may update shared AI state or perform Git and pull-request operations during automated runs. Manual repository maintenance may change these paths only when they are explicitly in task scope.
