---
task_id: P6-QWEN-REVIEW-001
requester: human
created_at: 2026-06-27
risk_level: RSK-1
mode: safe-default
branch: codex/qwen-pc-runner-evidence
---
# Task

Validate that the approved PC-first Qwen runner can perform the Runebridge Qwen review role against a synthetic fixture and return strict JSON only.

## Constraints

- Use the approved external PC runner only.
- Use synthetic review input only.
- Do not include credentials, raw provider configuration, or unrelated local paths in committed artifacts.
- Treat this directory as staging for formal Phase 6 evidence; approval-bound live metadata is still pending.
