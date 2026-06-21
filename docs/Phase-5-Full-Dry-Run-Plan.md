# Phase 5 Full Dry-Run Validation Plan

## Objective

Validate the three approved happy-path modes through a guarded runner that strips credentials and blocks/logs vendor, network, Git, and GitHub commands.

## Official Runs

| Task | Mode |
|---|---|
| `P5-SAFE-001` | `safe-default` |
| `P5-QWEN-001` | `qwen-led` |
| `P5-DUAL-001` | `dual-builder` |

Each task is rehearsed in two fresh temporary roots with `RUNEBRIDGE_DATE=2026-06-21`, then generated once under `.bridge/`. Official IDs are single-use.

## Controls

- `tools/bridge/run_guarded_dry_run.py` resolves Python, creates command shims and Bash guards, strips credential-like variables, and invokes the conductor.
- Each run writes `EXTERNAL_COMMANDS.log` and `RUN_METADATA.json`, then re-runs the secret gate.
- A non-empty command log fails validation.
- Injected halt, RSK-0, and retry scenarios remain tests and are not committed as official pipeline evidence.
- The Phase 5 pull request is opened manually.

## Exit Gate

All official runs exit 0 with valid mode-specific artifacts, same-host rehearsals are byte-identical, command logs are empty, credentials are unavailable, the complete local suite passes, and all protected checks pass.
