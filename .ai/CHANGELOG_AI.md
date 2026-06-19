# AI Changelog

The conductor appends one entry during final reporting after all gates pass. Role adapters must not edit this file. Manual maintenance may append an entry only when this file is explicitly in task scope. Do not edit previous entries.

## Format

```yaml
date: YYYY-MM-DD
agent: <tool name>
task_id: <task ID or description>
summary: <one sentence>
files_changed:
  - <path>
test_result: pass | fail | skipped
human_review_needed: true | false
```

## Entries

```yaml
date: 2026-06-19
agent: Claude Code
task_id: phase-1-scaffold-md
summary: Created root instruction files, .ai/ context directory, and prompts/ directory.
files_changed:
  - .gitignore
  - AGENTS.md
  - CLAUDE.md
  - QWEN.md
  - .ai/PROJECT_BRIEF.md
  - .ai/CODING_RULES.md
  - .ai/TASKS.md
  - .ai/AGENT_HANDOFF.md
  - .ai/CHANGELOG_AI.md
  - .ai/SECURITY_RULES.md
  - .ai/MODEL_ROLES.md
  - .ai/MCP_POLICY.md
  - prompts/plan.md
  - prompts/edit-from-plan.md
  - prompts/qwen-review.md
  - prompts/antigravity-verify.md
  - prompts/final-review.md
  - .bridge/.gitkeep
test_result: skipped
human_review_needed: false
```

```yaml
date: 2026-06-19
agent: Codex
task_id: phase-0.5a-qwen-led-contract
summary: Resolved the qwen-led planner, review-stage, artifact, adapter, and final-gate contract.
files_changed:
  - .ai/MODEL_ROLES.md
  - .ai/PROJECT_BRIEF.md
  - QWEN.md
  - CLAUDE.md
  - prompts/plan.md
  - prompts/qwen-review.md
  - prompts/final-review.md
  - docs/AI-Bridge-Implementation-Plan-and-Concerns.md
  - .ai/AGENT_HANDOFF.md
  - .ai/CHANGELOG_AI.md
test_result: pass
human_review_needed: true
```

```yaml
date: 2026-06-19
agent: Codex
task_id: phase-0.5a-write-ownership
summary: Assigned role artifact writes, shared AI state, and Git/PR operations to explicit owners.
files_changed:
  - AGENTS.md
  - CLAUDE.md
  - QWEN.md
  - .ai/CODING_RULES.md
  - .ai/PROJECT_BRIEF.md
  - .ai/MODEL_ROLES.md
  - prompts/plan.md
  - prompts/edit-from-plan.md
  - prompts/qwen-review.md
  - prompts/antigravity-verify.md
  - prompts/final-review.md
  - docs/AI-Bridge-Implementation-Plan-and-Concerns.md
  - .ai/AGENT_HANDOFF.md
  - .ai/CHANGELOG_AI.md
test_result: pass
human_review_needed: true
```
