# Vendor CLI Validation

## Scope

Phase 0.6 validates vendor identity, installation, authentication readiness, noninteractive output, bounded execution, and exit behavior before adapter implementation. No credentials or raw session identifiers are recorded here.

## Validation Matrix

| Vendor | Command | Version | Authentication | Structured output | Exit behavior | Status |
|---|---|---:|---|---|---|---|
| Claude Code | `claude` | 2.1.183 | Verified through Claude.ai | JSON result envelope verified | Success `0`; budget halt `1` | Ready for adapter contract work |
| Codex CLI | `codex.cmd` on Windows | 0.141.0 | Verified through ChatGPT | JSONL events verified | Success `0`; invalid argument `2` | Ready for adapter contract work |
| Qwen Code | `qwen.cmd` on Windows | 0.18.4 | Provider selected: Alibaba Cloud Coding Plan; configuration pending | JSON, stream JSON, and JSON Schema advertised | Budget exit `55` advertised; live path not tested | Provider decided; auth configuration and live validation pending |
| Antigravity IDE | `antigravity-ide.cmd` | 1.107.0 | Not verifiable from launcher | No headless structured-output contract exposed | Not tested | Deferred: IDE-only surface rejected; awaiting headless interface |

## Claude Code Evidence

- `claude --version` returned 2.1.183.
- `claude auth status` reported an authenticated first-party Claude.ai session.
- A no-tools, no-persistence JSON call returned `PHASE06_OK` with exit code 0.
- A lower budget cap returned a machine-readable `error_max_budget_usd` result with exit code 1.
- The success call used a USD 0.06 cap and reported approximately USD 0.048 total cost.
- Windows PowerShell JSON Schema quoting needs an adapter-safe wrapper; the CLI rejected the malformed shell argument before inference.

## Codex CLI Evidence

- The official npm package `@openai/codex` 0.141.0 is installed.
- `codex login status` reported an authenticated ChatGPT session.
- An ephemeral, read-only JSONL call from a temporary non-repository directory returned `PHASE06_OK` with exit code 0.
- An invalid sandbox value failed before inference with exit code 2.
- PowerShell execution policy blocks the generated `codex.ps1`; Windows adapters must invoke `codex.cmd` explicitly.
- The CLI emitted non-blocking warnings for unsupported PowerShell shell snapshots and unrelated local plugin manifests. Adapter parsing must keep stderr separate from JSONL stdout.

## Qwen Code Evidence and Blocker

- The official npm package `@qwen-code/qwen-code` 0.18.4 is installed.
- PowerShell execution policy blocks the generated `qwen.ps1`; Windows adapters must invoke `qwen.cmd` explicitly.
- Help output advertises JSON, stream JSON, JSON Schema, wall-time limits, tool-call limits, and exit code 55 for budget termination.
- Official Qwen documentation states that the Qwen OAuth free tier was discontinued on 2026-04-15.
- Provider decision: standardize on the Alibaba Cloud Coding Plan. Live validation is pending plan subscription and credential provisioning.
- Never store a provider key in repository files or `settings.json`; supply Coding Plan credentials only through an approved environment or secret store.

## Antigravity Evidence and Blocker

- Antigravity IDE 1.107.0 is installed and exposes `antigravity-ide.cmd chat`.
- The launcher can open IDE chat in `ask`, `edit`, or `agent` mode.
- The launcher does not advertise headless JSON output, schema validation, bounded execution, or authentication status.
- Interface decision: the IDE-only chat surface is not an acceptable integration point. A supported headless API or CLI with a structured-output and exit-code contract is required.
- Antigravity is deferred until such a headless interface is available; no production adapter will be implemented against the IDE launcher.

## Phase 0.6 Exit Criteria

- [x] Claude installation, authentication, success output, and failure exit verified
- [x] Codex installation, authentication, success output, and failure exit verified
- [x] Qwen provider selected (Alibaba Cloud Coding Plan); authentication configuration outside the repository pending
- [ ] Qwen success JSON and bounded failure exit verified
- [x] Antigravity automation-interface decision made: IDE-only rejected, headless interface required (deferred)
- [ ] Antigravity authentication, structured output, timeout, and failure exit verified
- [ ] Sanitized final validation matrix approved

## Decisions Resolved

1. Qwen provider and credential source: Alibaba Cloud Coding Plan, credentials supplied via an approved environment or secret store.
2. Antigravity integration surface: the IDE-only chat surface is rejected; a supported headless API/CLI is required, so Antigravity is deferred until one is available.
