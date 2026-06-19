# AI Bridge — Implementation Plan and Concerns

**Branch:** `claude/latest-drafts-ptdnpq`  
**Date:** 2026-06-18  
**Status:** Approved for implementation with Phase 0.5 prerequisites

---

## Part 1 — Implementation Plan

### What Is Being Built

A full repository scaffold for the Runebridge AI Bridge Pipeline, covering shared `.ai/` context, root instruction files, artifact schemas, deterministic gates, adapter stubs, GitHub workflows, dry-run support, and the Pattern A conductor.

The scaffold is intended to support three operating modes from the start:

- `safe-default` — recommended mode
- `qwen-led`
- `dual-builder`

All modes must use the same artifact contracts, deterministic gates, secret scanning, RSK enforcement, dry-run behavior, and human approval rules.

### Files to Create

#### Group 1 — Root instruction files

| File | Purpose |
|---|---|
| `AGENTS.md` | Universal pre-read for all AI agents; lists `.ai/` read order, work process, and restrictions |
| `CLAUDE.md` | Claude Code-specific: architect + final reviewer role; read-only default for plan/review stages |
| `QWEN.md` | Qwen Code-specific: builder, first reviewer, refactor agent, bug hunter, qwen-led mode |
| `.gitignore` | Excludes secrets, local configs, `.bridge/` runtime subdirs, Python cache, logs, local env files |
| `.env.example` | Safe example of required environment variables without real secrets |
| `.pre-commit-config.yaml` | Local lint/test hooks for Python, Bash, and secrets hygiene |

#### Group 2 — `.ai/` shared context (committed, versioned)

| File | Purpose |
|---|---|
| `.ai/PROJECT_BRIEF.md` | Project purpose, stack, constraints, definition of success, canonical repo layout including `docs/` |
| `.ai/CODING_RULES.md` | Style rules all agents follow |
| `.ai/TASKS.md` | Active task tracking and backlog |
| `.ai/AGENT_HANDOFF.md` | Cross-agent handoff state and decisions log |
| `.ai/CHANGELOG_AI.md` | AI-generated change log; appended by conductor in final report stage |
| `.ai/SECURITY_RULES.md` | Dangerous actions policy; defines RSK-0/RSK-1/RSK-2 and enforcement |
| `.ai/MODEL_ROLES.md` | Role assignments per model for each operating mode |
| `.ai/MCP_POLICY.md` | MCP permission policy: allowed servers, per-tool access map, banned defaults |

#### Group 3 — `schemas/` artifact contracts (JSON Schema draft-07)

| File | Validates |
|---|---|
| `schemas/task.schema.json` | `TASK.md` YAML front matter |
| `schemas/plan.schema.json` | `PLAN.md` YAML front matter; enforces non-empty `files_to_touch` and `acceptance_criteria` |
| `schemas/edit-summary.schema.json` | `EDIT_*.md` build summary |
| `schemas/verify.schema.json` | `VERIFY.json` |
| `schemas/review.schema.json` | `REVIEW_CLAUDE.json` and `REVIEW_QWEN.json` |

#### Group 4 — `prompts/` versioned role prompts

| File | Used by |
|---|---|
| `prompts/plan.md` | `adapters/claude_plan.sh` |
| `prompts/edit-from-plan.md` | `adapters/codex_build.sh`, `adapters/qwen_build.sh` |
| `prompts/qwen-review.md` | `adapters/qwen_review.sh` |
| `prompts/antigravity-verify.md` | `adapters/antigravity_verify.sh` |
| `prompts/final-review.md` | `adapters/claude_review.sh` |

**Language handling (all prompt files):** Task input may be written in English or Thai. Every prompt file must include the following instruction at the top:

```
The task description may be written in English or Thai.
Detect the language of the task input automatically.
If the input is in English, respond and write all pipeline artifacts in English.
If the input is in Thai, respond and write all pipeline artifacts in Thai.
Match the output language to the input language exactly.
```

This means: you write your task in EN → all pipeline output comes back in EN. You write in TH → all pipeline output comes back in TH.

#### Group 5 — `tools/bridge/gates/` deterministic stop/go scripts (Python)

Exit codes: **0** = pass, **1** = fail, **2** = RSK-0 halt.

| File | Checks |
|---|---|
| `check_plan.py` | `files_to_touch` non-empty, `acceptance_criteria` non-empty, schema validates |
| `check_scope.py` | Every file in `CHANGES.diff` is listed in `PLAN.md`'s `files_to_touch` |
| `check_review.py` | `blockers == []`, `scope_drift == false`, verdicts match when both reviewers are required |
| `check_verify.py` | `VERIFY.json` result is `"pass"` |
| `check_rsk0.py` | No RSK-0 triggers in plan; exits 2 on trip |
| `check_artifacts.py` | All required artifacts exist and are non-empty for the given mode |
| `check_no_secrets.py` | Regex scan of `CHANGES.diff` for API keys, tokens, and high-entropy secrets |

`tools/requirements.txt` already exists in the plan with `jsonschema>=4.0` and `PyYAML>=6.0`. This is not absent, but it is incomplete and must be expanded during Phase 0.5.

#### Group 6 — `tools/bridge/adapters/` vendor CLI wrappers (bash)

Each adapter takes `TASK_ID` as an argument, reads `.bridge/$TASK_ID/` inputs, writes `.bridge/$TASK_ID/` outputs, and exits 0/non-zero. All vendor CLI invocations are isolated here; the conductor never calls vendor CLIs directly.

| File | Wraps | I/O |
|---|---|---|
| `claude_plan.sh` | Claude Code (`claude -p`) | In: `TASK.md` → Out: `PLAN.md` |
| `codex_build.sh` | OpenAI Codex CLI (`codex exec`) | In: `PLAN.md` → Out: `EDIT_CODEX.md`, `CHANGES.diff` |
| `qwen_build.sh` | Qwen Code (`qwen`) | In: `PLAN.md` → Out: `EDIT_QWEN.md`, `CHANGES.diff` |
| `qwen_review.sh` | Qwen Code — read-only | In: `PLAN.md`, `CHANGES.diff` → Out: `REVIEW_QWEN.json` |
| `antigravity_verify.sh` | Google Antigravity | In: `PLAN.md`, `CHANGES.diff` → Out: `VERIFY.json` |
| `claude_review.sh` | Claude Code — read-only | In: `PLAN.md`, `CHANGES.diff`, `REVIEW_QWEN.json`, `VERIFY.json` → Out: `REVIEW_CLAUDE.json` |

#### Group 7 — `tools/bridge/orchestrate.sh` (Pattern A conductor)

Accepts: `--task`, `--mode` (`safe-default` | `qwen-led` | `dual-builder`), `--planner`, `--builder`, `--first-reviewer`, `--verifier`, `--final-reviewer`.

Stage sequence:

```text
Stage  0  Init          — create branch bridge/<task-id>, write TASK.md
Stage  1  Plan          — run planner adapter
Stage  2  Gate          — check_plan.py + check_rsk0.py
Stage  3  Build         — run builder adapter
Stage  4  Gate          — check_scope.py
Stage  5  First review  — qwen_review.sh
Stage  6  Gate          — check_review.py --reviewer qwen
Stage  7  Verify        — run verifier adapter
Stage  8  Gate          — check_verify.py
Stage  9  Final review  — claude_review.sh
Stage 10  Gate          — check_review.py --reviewer both + check_no_secrets.py
Stage 11  Final report  — write FINAL_REPORT.md, append CHANGELOG_AI.md
Stage 12  PR            — commit artifacts + gh pr create
```

Key behaviors:

- Any gate exits non-zero → halt with message.
- `check_rsk0.py` exit code 2 → `halt_rsk0()` and print `HUMAN_REQUIRED`.
- Verify retry budget: 2 retries; previous `CHANGES.diff` archived as `CHANGES.diff.attempt-N`.
- Cross-check disagreement → halt and attach both reviews.
- `DRY_RUN_MODE=true` must run the full flow using deterministic mock artifacts.

#### Group 8 — `.bridge/.gitkeep`

Tracks the directory in git. Runtime task subdirectories (`.bridge/<task-id>/`) are gitignored via `.bridge/*/`.

#### Group 9 — `.github/workflows/`

| File | Triggers | Checks |
|---|---|---|
| `test.yml` | push + PR to main | shellcheck on adapters + conductor; `py_compile` on gates; JSON schema syntax validation; gate unit tests |
| `bridge-gates.yml` | PR touching `.bridge/` paths | `check_artifacts.py` + `check_no_secrets.py` on bridge PRs |

### Updated Roadmap

```text
Phase 0    Planning approval
Phase 0.5  Environment, security, permissions, and tooling setup
Phase 0.6  Vendor identity and CLI validation
Phase 1    Repository scaffold
Phase 2    Schemas and deterministic gates
Phase 3    Adapter stubs and dry-run outputs
Phase 4    Pattern A conductor
Phase 5    Full dry-run pipeline validation
Phase 6    Live vendor integration
Phase 7    Mode benchmarking: safe-default, qwen-led, dual-builder
```

---

## Part 2 — Decisions and Concerns

Reviewed against the three planning documents (`aibridgepipelineplan1qwen.md`, `aibridgepipelineplan2qwen.md`, `aibridgepipelineplan3qwen.md`) and `docs/Runebridge-Private-Repository-Architecture.md`.

### Concern 1 — Naming conflict: session recovery files vs. `.ai/` convention (Approved)

**Decision:** Use `.ai/` as the canonical session recovery and shared-context system.

Do not create duplicate root-level files:

- `PROJECT_CONTEXT.md`
- `ARCHITECTURE.md`
- `DECISIONS.md`
- `OPEN_TASKS.md`

Map any unique content from those concepts into:

- `.ai/PROJECT_BRIEF.md`
- `.ai/TASKS.md`
- `.ai/AGENT_HANDOFF.md`
- `AGENTS.md`
- `CLAUDE.md`

### Concern 2 — `docs/` directory not in the planned repo layout (Approved)

**Decision:** Add `docs/` to the canonical repository layout.

Update:

- `README.md`
- `.ai/PROJECT_BRIEF.md`
- repository structure diagrams

### Concern 3 — Operating modes (Approved: keep all for now)

**Decision:** Keep all planned operating modes in the implementation:

- `safe-default`
- `qwen-led`
- `dual-builder`

**Condition:** All modes must use the same safety guarantees:

- artifact contracts
- schema validation
- scope gate
- RSK-0 halt behavior
- verification gate
- independent review gate
- secret scanning
- human approval before merge or irreversible action

No mode may bypass deterministic gates or human approval requirements.

### Concern 4 — Dashboard scope not in Phase 1–3 (Approved: defer)

**Decision:** Defer dashboard development.

Add to `.ai/TASKS.md` backlog only:

- token usage dashboard
- cost dashboard
- pipeline visualization dashboard
- agent activity dashboard

### Concern 5 — AI Replacement Matrix (Approved: no concern)

Appendix A's replacement matrix is consistent with the planned `MODEL_ROLES.md` design. No action needed.

### Concern 6 — GitHub Actions minute budget on private repos (Approved: monitor after implementation)

**Decision:** Proceed with the current GitHub Actions design and monitor usage after implementation.

Potential future options if Actions minutes become a constraint:

- GitHub Pro
- reduced workflow triggers
- self-hosted runners
- public Runebridge repository with private project repositories

### Concern 7 — Dry-run mode before real vendor CLI use (Approved: add)

**Decision:** Add `DRY_RUN_MODE=true` support before real vendor CLI use is enabled.

When dry-run mode is active:

- adapter scripts must skip real Claude/Codex/Qwen/Antigravity CLI calls
- adapter scripts must write deterministic mock artifacts instead
- gates must run normally against the mock artifacts
- branch creation, artifact flow, retry behavior, halt behavior, final report generation, and PR creation logic can be tested safely
- dry-run output must clearly state `DRY_RUN_MODE=true`

This allows validation of:

- artifact flow
- gate logic
- retry loops
- branch creation
- final report generation
- PR creation
- CI workflow behavior

without spending tokens or depending on vendor CLI behavior.

---

## Part 3 — Accepted Phase 0.5 Conditions

These additions are accepted with two corrections:

1. Python environment management is not completely absent. The plan already mentions `tools/requirements.txt` with `jsonschema` and `PyYAML`, but it is incomplete and must be expanded.
2. A PAT is not required immediately. Start with `GITHUB_TOKEN` using explicit least-privilege permissions. Escalate to a GitHub App token or temporary PAT only if required.

### 0.5.1 Environment and Tooling Setup

Add **Phase 0.5 — Environment, Security, Permissions, and Tooling Setup** before scaffold implementation.

Phase 0.5 must define:

- Python version
- virtual environment setup
- dependency installation
- Bash/system dependencies
- GitHub CLI requirement
- local credential handling
- baseline `.gitignore`
- pre-commit tooling
- gate test tooling

Recommended files:

- `tools/requirements.txt`
- optional future `pyproject.toml`
- `.gitignore`
- `.env.example`
- `.pre-commit-config.yaml`
- `tests/gates/`

### 0.5.2 Python Dependency Management

Corrected status: partially covered, but incomplete.

The plan already includes:

- `jsonschema>=4.0`
- `PyYAML>=6.0`

Add required dependencies:

- `pytest`

Recommended optional tooling:

- `ruff`
- `black`
- `pre-commit`
- `requests` only if HTTP API fallback is needed

Local virtual environment rule:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r tools/requirements.txt
```

CI rule:

GitHub Actions must install the same requirements before running gate scripts or tests.

### 0.5.3 Bash and System Dependencies

Required tools:

- `bash`
- `git`
- `gh`
- `jq`
- `shellcheck`

GitHub-hosted Ubuntu runners may include some tools by default, but workflows should explicitly install or verify required tools.

### 0.5.4 Branch Protection Rules

Add branch protection requirements for `main`:

- no direct push to `main`
- pull request required before merge
- required status checks must pass
- required review before merge
- conversation resolution required
- force push disabled
- branch deletion disabled
- optional: require signed commits
- optional: apply rules to administrators

Required checks should include at minimum:

- `test.yml`
- `bridge-gates.yml`

No generated branch may bypass protected `main`.

### 0.5.5 GitHub Permissions and Token Strategy

Corrected strategy: do not require a PAT first.

Preferred order:

1. `GITHUB_TOKEN`
2. GitHub App token
3. temporary PAT only if needed

Default rule:

Use `GITHUB_TOKEN` with explicit least-privilege permissions wherever possible.

For CI-only workflows:

```yaml
permissions:
  contents: read
```

For PR creation and branch automation:

```yaml
permissions:
  contents: write
  pull-requests: write
  actions: read
  checks: read
```

Escalate to a GitHub App token or temporary PAT only if automation must:

- trigger follow-up workflows
- perform actions not supported by `GITHUB_TOKEN`
- create automation-owned PRs without manual workflow approval
- operate across repositories

If a temporary PAT is used, store it as a repository secret:

```text
RUNEBRIDGE_AUTOMATION_TOKEN
```

### 0.5.6 Vendor Secret Management

Potential GitHub Repository Secrets:

```text
ANTHROPIC_API_KEY
OPENAI_API_KEY
QWEN_API_KEY
ANTIGRAVITY_API_KEY
RUNEBRIDGE_AUTOMATION_TOKEN
```

Rules:

- no vendor key may be committed
- no vendor key may be written into `.bridge/` artifacts
- no vendor key may appear in logs
- no vendor key may be passed as a command-line argument
- keys must be injected through environment variables

Example CI injection:

```yaml
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

When `DRY_RUN_MODE=true`, vendor keys are not required.

### 0.5.7 Local Phase 0 Credential Strategy

Before vendor CLI tests, create or verify `.gitignore` includes:

```gitignore
.env
.env.*
!.env.example
.venv/
.bridge/*/
*.log
*.tmp
.cache/
__pycache__/
.pytest_cache/
```

Local credential options:

- `.env` file ignored by git
- `direnv`
- shell session environment variables
- password manager injection

Prohibited:

- pasting API keys directly into terminal commands
- committing local credential files
- storing keys in markdown handoff files

### 0.5.8 Agent Identity and Commit Attribution

Each automated commit and artifact must identify:

- operating mode
- planner
- builder
- verifier
- reviewer
- dry-run vs live mode
- tool adapter used
- timestamp
- task ID

Recommended git author:

```text
Runebridge Bot <runebridge-bot@users.noreply.github.com>
```

Artifact-level attribution example:

```yaml
agent_role: builder
agent_tool: codex
mode: safe-default
dry_run: true
task_id: RB-0001
```

### 0.5.9 Structured Output and Parsing Strategy

Do not rely on free-form AI text for gate inputs.

Required strategy:

- Markdown artifacts with YAML front matter for `TASK.md`, `PLAN.md`, and `EDIT_*.md`
- strict JSON for `VERIFY.json`, `REVIEW_CLAUDE.json`, and `REVIEW_QWEN.json`
- prompts must clearly require the expected artifact format
- gates must reject invalid JSON, missing required fields, and invalid front matter

Gate behavior:

- fail with clear error messages
- reject conversational filler outside expected strict artifact boundaries when strict mode is enabled
- rely on schema validation instead of model trust

Structured-output libraries may be considered later, but Phase 1 should use deterministic parsing and schema validation.

### 0.5.10 Failure, Retry, and Escalation Policy

Default retry budget:

```text
max_retries = 2
```

Retry allowed for:

- verification failure
- build failure caused by implementation error
- schema-format correction

Retry not allowed for:

- RSK-0 trigger
- secret detected
- scope drift
- branch protection failure
- missing credentials
- unknown vendor identity
- repeated invalid model output after retry budget

Human escalation required when:

- retries are exhausted
- reviewers disagree
- RSK-0 action appears
- secret is detected
- vendor tool cannot be verified
- protected branch rule blocks automation unexpectedly

### 0.5.11 Log and Artifact Retention

Logs should include:

- task ID
- stage name
- adapter name
- exit code
- gate result
- timestamp
- dry-run flag

Logs must not include:

- API keys
- tokens
- raw secrets
- sensitive customer data
- full hidden prompts if they contain sensitive information

Recommended storage:

- GitHub Actions logs for CI execution
- `.bridge/<task-id>/FINAL_REPORT.md` for summarized pipeline result
- optional `.bridge/<task-id>/logs/` only if logs are sanitized

Initial retention:

Use GitHub Actions default retention first. Define custom retention later if needed.

### 0.5.12 Gate Test Strategy

Use `pytest` to test Python gates before live model integration.

Required test cases:

- valid plan passes
- missing `files_to_touch` fails
- missing `acceptance_criteria` fails
- RSK-0 deployment request exits 2
- scope drift fails
- secret pattern fails
- valid verification passes
- review blocker fails
- invalid JSON fails

Directory:

```text
tests/gates/
```

### 0.5.13 Local Developer Tooling

Recommended tools:

- `pre-commit`
- `ruff`
- `black`
- `shellcheck`
- `pytest`

Required checks before PR:

- Python syntax check
- gate unit tests
- shellcheck for Bash scripts
- JSON schema syntax validation
- secret scan

### 0.5.14 Antigravity Identity Discovery

The exact Google Antigravity tool identity, installation method, CLI behavior, and invocation method are unconfirmed.

Before live verification mode:

- identify exact tool
- confirm install method
- confirm authentication
- confirm CLI/API invocation
- confirm output format
- confirm exit codes

Blocking rule:

Antigravity uncertainty does not block dry-run scaffold implementation. It blocks live verification mode.

### 0.5.15 Phase 0 Security Checklist

Before any vendor CLI validation:

- `.gitignore` exists
- `.env` is ignored
- no key is pasted into terminal command history
- local logs are excluded
- local cache folders are excluded
- dry-run mode is tested first where possible
- billing/quota is checked for each vendor

---

## Summary of Actions Before Implementation

| # | Action | Owner | Priority | Decision |
|---|---|---|---|---|
| 1 | Use `.ai/` as canonical session recovery/shared context system | Human | Blocking | Approved |
| 2 | Add `docs/` to canonical repo layout | Claude Code | Low | Approved |
| 3 | Keep all operating modes (`safe-default`, `qwen-led`, `dual-builder`) | Claude Code | High | Approved |
| 4 | Defer dashboard to backlog | Agreed | Low | Approved |
| 5 | Proceed with current GitHub Actions design and monitor minutes | Human | High | Approved |
| 6 | Add `DRY_RUN_MODE=true` support for safe pipeline validation | Claude Code | High | Approved |
| 7 | Add Phase 0.5 environment, security, permissions, and tooling setup | Claude Code | High | Approved with corrections |
| 8 | Start with `GITHUB_TOKEN`; escalate to GitHub App/PAT only if needed | Claude Code | High | Approved correction |
| 9 | Expand existing Python requirements instead of treating dependency management as absent | Claude Code | High | Approved correction |

## Updated Readiness Status

Architecture: ready.  
Safety model: ready.  
Dry-run scaffold implementation: ready after Phase 0.5 environment and security setup is added.  
Vendor validation: not ready until Phase 0.6.  
Live model integration: not ready until vendor CLI validation and credential strategy are confirmed.

## Final Decision

**GO — Approved to proceed with Phase 0.5.**

Do not proceed to live vendor integration until:

- environment/tooling setup is complete
- branch protection is configured
- local credential strategy is confirmed
- GitHub secrets strategy is confirmed
- structured output parsing is implemented
- gate tests exist
- Antigravity identity is confirmed

Dry-run scaffold implementation may proceed after Phase 0.5 is completed.
