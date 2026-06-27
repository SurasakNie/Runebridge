# Vendor CLI Validation

## Scope

Phase 0.6 validates vendor identity, installation, authentication readiness, noninteractive output, bounded execution, and exit behavior before adapter implementation. No credentials or raw session identifiers are recorded here.

## Validation Matrix

| Vendor | Command | Version | Authentication | Structured output | Exit behavior | Status |
|---|---|---:|---|---|---|---|
| Claude Code | `claude` | 2.1.183 | Verified through Claude.ai | JSON result envelope verified | Success `0`; budget halt `1` | Ready for adapter contract work |
| Codex CLI | `codex.cmd` on Windows | 0.141.0 | Verified through ChatGPT | JSONL events verified | Success `0`; invalid argument `2` | Ready for adapter contract work |
| Qwen Code | `qwen.cmd` on Windows | 0.19.2 | Provider/auth path selected outside the repository | JSON, stream JSON, and JSON Schema advertised | Shared remote environment blocked by egress-policy `403`; PC runner live sanity checks passed | Live supported only on an approved external runner |
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

## Qwen Code Evidence and Decision

- The official npm package `@qwen-code/qwen-code` was revalidated on the approved PC runner as Qwen Code 0.19.2.
- PowerShell execution policy blocks the generated `qwen.ps1`; Windows adapters must invoke `qwen.cmd` explicitly.
- Help output advertises JSON, stream JSON, JSON Schema, wall-time limits, tool-call limits, and exit code 55 for budget termination.
- Official Qwen documentation states that the Qwen OAuth free tier was discontinued on 2026-04-15.
- Provider/authentication decisions were later recorded outside this repository workflow and are treated as approved operator inputs, not committed secrets.
- The shared remote environment was re-tested against approved provider hosts and received `403 Forbidden` from the organization egress proxy for `dashscope-intl.aliyuncs.com`, `dashscope.aliyuncs.com`, and `openrouter.ai`.
- The approved PC runner successfully initialized the Standard API Key provider against `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` with model `qwen3.6-plus`.
- The approved PC runner returned `PHASE6_QWEN_OK` for a bounded live sanity prompt and produced a schema-valid Qwen reviewer artifact for `P6-QWEN-REVIEW-001`.
- Approved operating model: keep Qwen credentials in an approved external environment or secret store and execute live Qwen from an approved external runner, starting with the owner's PC. Never store provider credentials in repository files or `settings.json`.

## Qwen Network Blocker and Operating Model

- The shared remote environment is not an approved live Qwen runner because provider hosts currently return egress-policy `403 Forbidden`.
- `Runebridge` remains the only repository; live Qwen does not require a second repo.
- The first approved live Qwen runner is the owner's PC, using the same `Runebridge` repository in a local clone.
- If the PC runner is unavailable, other environments must use mock or deferred Qwen behavior rather than claiming live Qwen.
- A VM or server may later replace the PC runner, but that is an infrastructure option rather than a repository change.

## Antigravity Evidence and Blocker

- Antigravity IDE 1.107.0 is installed and exposes `antigravity-ide.cmd chat`.
- The launcher can open IDE chat in `ask`, `edit`, or `agent` mode.
- The launcher does not advertise headless JSON output, schema validation, bounded execution, or authentication status.
- Interface decision: the IDE-only chat surface is not an acceptable integration point. A supported headless API or CLI with a structured-output and exit-code contract is required.
- Antigravity is deferred until such a headless interface is available; no production adapter will be implemented against the IDE launcher.

## Phase 0.6 Exit Criteria

- [x] Claude installation, authentication, success output, and failure exit verified
- [x] Codex installation, authentication, success output, and failure exit verified
- [x] Qwen provider/auth path approved outside the repository
- [x] Shared remote environment tested and confirmed blocked by egress-policy `403 Forbidden`
- [x] Approved interim operating model is `PC-first, VM-later` for live Qwen execution
- [x] Qwen PC runner returned a bounded live sanity response and a schema-valid synthetic review artifact
- [x] Antigravity automation-interface decision made: IDE-only rejected, headless interface required (deferred)
- [x] Antigravity live checks deferred until a supported headless interface exists
- [x] Sanitized final validation matrix approved by the owner on 2026-06-20

## Decisions Resolved

1. Qwen provider and credential source: approved outside the repository, but the shared remote environment is egress-blocked; execute live Qwen only from an approved external runner.
2. Antigravity integration surface: the IDE-only chat surface is rejected; a supported headless API/CLI is required, so Antigravity is deferred until one is available.
