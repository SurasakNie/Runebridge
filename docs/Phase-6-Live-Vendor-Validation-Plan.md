# Phase 6 Live-Vendor Validation Plan

## Status

Approved through PR #12 as the Phase 6 execution gate. This document does not authorize live inference, credential changes, provider subscriptions, GitHub automation, repository-setting changes, or deployment. P6-001B merged through PR #13; P6-001C Claude adapter contracts are complete pending review with no enabled real vendor adapters.

## Objective

Validate bounded live execution for the already authenticated Claude Code and Codex CLI roles without weakening the deterministic dry-run pipeline. Establish explicit decision gates for Qwen and Antigravity, then integrate only approved live roles into the conductor through reviewed, fail-closed changes.

Phase 6 must distinguish these claims:

1. **Live adapter validated:** one vendor role passed its isolated contract.
2. **Hybrid pipeline validated:** every stage records whether it used a live or mock adapter.
3. **All-live pipeline validated:** every required role used an approved live adapter. This claim is forbidden while any required role remains mocked or deferred.

## Baseline

- Phase 5 validated `safe-default`, `qwen-led`, and `dual-builder` in deterministic dry-run mode.
- The Phase 4 conductor rejects non-dry-run execution with exit code 2.
- Claude Code and Codex CLI previously passed bounded, noninteractive, structured-output checks using existing first-party authenticated sessions.
- Qwen Code is installed, but its live provider and credential source are not selected.
- Antigravity exposes only an IDE launcher; no supported headless structured-output contract is approved.
- Automated Git and GitHub operations remain disabled until the scoped conductor GitHub App is separately approved, installed, and verified.

Tool versions and authentication state are execution-time facts. Every implementation or live-validation PR must re-read and sanitize them rather than relying on the Phase 0.6 snapshot.

## Non-Goals

- Do not enable live calls in this planning PR.
- Do not modify the Phase 4 conductor or existing deterministic adapters in this planning PR.
- Do not install a Qwen provider, start a subscription, or create provider credentials without explicit human approval.
- Do not automate Antigravity through its GUI or IDE launcher.
- Do not install or modify a GitHub App, repository ruleset, Actions permissions, secrets, or environments.
- Do not run live vendors on customer code, private downstream repositories, or sensitive prompts.
- Do not benchmark vendor quality, latency, or cost beyond contract validation; comparative benchmarking belongs to Phase 7.

## Safety Principles

1. **Dry-run remains default.** Existing dry-run commands and byte-stability tests must remain unchanged.
2. **Live execution is explicit.** No environment variable or missing flag may silently select a live adapter.
3. **Validate roles in isolation first.** The conductor remains dry-run-only until individual live contracts pass.
4. **Use synthetic fixtures only.** Live prompts and workspaces contain no repository secrets, customer data, or unrelated source.
5. **Minimize credentials.** Reuse approved interactive sessions or an approved secret store; never copy raw tokens into the repository, command line, artifacts, or logs.
6. **Separate streams.** Parse structured stdout only; capture stderr separately and redact it before any evidence is retained.
7. **Fail closed.** Authentication, timeout, budget, schema, secret, scope, or provenance failures halt the run.
8. **No hidden fallback.** A failed live adapter must not fall back to a mock adapter inside the same task.
9. **No implicit retry.** Only explicitly classified transient failures may retry once.
10. **Human-controlled Git.** Phase 6 validation does not commit, push, open, approve, or merge pull requests automatically.

## Risk and Approval Gates

| Action | Risk | Required approval |
|---|---|---|
| Review or merge this plan | RSK-2 / normal PR | Human review and manual merge |
| Implement runner, contracts, and tests with live calls disabled | RSK-1 | Reviewed PR |
| Revalidate CLI version and sanitized authentication status | RSK-1 | Approved execution checklist |
| Run one bounded Claude or Codex synthetic live call | RSK-1 | Human approval recorded before the run |
| Enable a live role in an isolated hybrid pipeline run | RSK-1 | Prior adapter evidence plus human approval |
| Select or purchase a Qwen provider; create or rotate credentials | RSK-0 | Stop and obtain explicit human decision |
| Install or change the conductor GitHub App or repository permissions | RSK-0 | Stop and obtain explicit human decision |
| Automate an unsupported Antigravity interface | Prohibited | No approval path in Phase 6 |
| Merge any Phase 6 PR | RSK-0 | Explicit manual merge approval |

Approval for one run does not authorize later runs, another vendor, a higher budget, a different workspace, or a different model.

## Architecture

### Stage A: Isolated live runner

Add a separate runner for individual role validation. It must not call `tools/bridge/orchestrate.sh` and must not modify the existing dry-run adapters.

The runner must:

- accept one vendor, one role, one synthetic fixture, one output directory, a timeout, and a budget ceiling;
- require an explicit `--live` flag plus a per-run approval identifier supplied by the human operator;
- refuse unknown vendors, roles, models, paths, or approval identifiers before invoking a vendor;
- build a minimal allowlisted environment instead of inheriting the full parent environment;
- block `git`, `gh`, `curl`, `wget`, and non-selected vendor commands through the Phase 5 guard approach;
- invoke the selected vendor exactly once per attempt;
- keep raw stdout, stderr, and temporary workspaces outside the repository;
- parse and normalize structured output before writing candidate evidence;
- run schema, provenance, scope, and secret gates after normalization;
- delete transient raw output only after sanitized pass/fail evidence is produced locally;
- never overwrite an existing task directory.

### Stage B: Live adapter contracts

Each live role adapter must satisfy the same artifact ownership rules as its deterministic counterpart:

| Vendor role | Allowed durable artifact | Source writes |
|---|---|---|
| Claude planner | `PLAN.md` | None |
| Claude final reviewer | `REVIEW_CLAUDE.json` | None |
| Codex builder | `EDIT_CODEX.md`, `CHANGES.diff` | Synthetic fixture workspace only |
| Qwen planner | `PLAN.md` | None |
| Qwen builder | `EDIT_QWEN.md`, `CHANGES.diff` | Synthetic fixture workspace only |
| Qwen reviewer | `REVIEW_QWEN.json` | None |

Existing schemas remain authoritative. Any required schema extension must be backward-compatible and land in a separate reviewed PR before live evidence uses it.

### Stage C: Conductor integration

Only after isolated Claude and Codex contracts pass may a later PR propose conductor integration.

That PR must:

- preserve the current dry-run invocation and output byte-for-byte;
- add an explicit execution selector whose default is dry-run;
- reject mixed live/mock execution unless the requested mode is explicitly `hybrid`;
- record `execution: live|mock` and vendor identity for every role;
- perform a preflight before creating the task directory;
- halt before downstream stages when a live adapter fails;
- retain exit code 2 exclusively for RSK-0 or explicit live-refusal outcomes;
- keep all Git and GitHub operations disabled.

## Credential and Environment Contract

The live runner must use an allowlist, not a denylist, for inherited environment variables.

Allowed categories:

- operating-system variables required to start the selected CLI;
- temporary-directory variables pointing outside the repository;
- locale and terminal variables required for stable encoding;
- a vendor-specific authentication handle already approved for that run;
- runner-owned timeout, budget, and evidence-path variables.

Forbidden categories:

- unrelated `API_KEY`, `PASSWORD`, `SECRET`, `TOKEN`, or `CREDENTIAL` variables;
- GitHub tokens, Git credential helpers, SSH agent sockets, cloud credentials, and package-registry tokens;
- repository-local `.env` files or vendor settings files;
- raw session identifiers in stdout, stderr, metadata, or error messages.

The runner must record only `credentials_available: true|false`, the authentication mechanism class (for example `interactive_session`), and the vendor name. It must never record the credential value, account email, session identifier, or home-directory path.

## Network and Tool Boundary

- Only the selected vendor CLI may make its normal vendor API connection.
- Git, GitHub CLI, generic network clients, package managers, shells spawned for arbitrary commands, and all other vendor CLIs remain blocked and logged.
- Tool use must be disabled for planner and reviewer validation.
- Codex builder validation runs in a disposable synthetic workspace with the narrowest supported write sandbox and no Git repository.
- Any attempted blocked command, unexpected child process, or network helper fails the run even if the vendor returns success.

## Vendor Sequence

| Order | Vendor / role | Entry condition | Live validation | Exit condition |
|---:|---|---|---|---|
| 1 | Claude planner | Runner contract and negative tests pass | One synthetic plan with tools disabled and strict structured output | Schema-valid `PLAN.md`; bounded cost/time; no blocked command or secret |
| 2 | Claude reviewer | Claude planner contract passes | Review fixed synthetic artifacts without source writes | Schema-valid `REVIEW_CLAUDE.json`; no scope or secret violation |
| 3 | Codex builder | Disposable workspace and scope checks pass | Apply one trivial synthetic edit under write sandbox | Valid `EDIT_CODEX.md` and non-empty `CHANGES.diff`; writes match plan scope |
| 4 | Claude + Codex hybrid | Individual contracts pass | Planner and reviewer live, builder live, unvalidated roles explicitly mocked or omitted | Full provenance; all deterministic gates pass; no all-live claim |
| 5 | Qwen decision gate | Human selects provider, credential source, model, and budget | No call until RSK-0 decision is recorded | Approved contract or formal continued deferral |
| 6 | Qwen roles | Decision gate passes | Planner, builder, then reviewer validated separately | Same contract quality as Claude/Codex; no self-review in `qwen-led` |
| 7 | Antigravity interface review | Supported headless interface is documented by vendor | Contract inspection before any inference | Structured output, bounded execution, auth status, and exit-code contract, or continued deferral |
| 8 | Mode integration | Every required role for a mode has passed | Validate one mode at a time | Mode-specific live/hybrid claim accurately recorded |

Claude and Codex order may be swapped only if the implementation PR documents why and preserves the same gates.

## Work Breakdown

| ID | Deliverable | Calls allowed | Completion gate |
|---|---|---|---|
| P6-001A | Approve this Phase 6 plan | None | Plan PR merged manually |
| P6-001B | Implement isolated runner, provenance format, and negative tests | None | Full suite and protected checks pass |
| P6-001C | Implement Claude planner/reviewer live adapters behind refusal-by-default controls | None | Unit and contract tests pass with fake CLI fixtures |
| P6-001D | Execute bounded Claude validation | Approved Claude calls only | Sanitized evidence reviewed and merged |
| P6-001E | Implement Codex builder live adapter and scope sandbox tests | None | Unit and contract tests pass with fake CLI fixtures |
| P6-001F | Execute bounded Codex validation | Approved Codex calls only | Sanitized evidence reviewed and merged |
| P6-001G | Validate one explicitly hybrid Claude/Codex pipeline | Approved Claude/Codex calls only | Provenance and all deterministic gates pass |
| P6-001H | Decide Qwen provider and authentication path | None until human decision | Approved selection or explicit continued deferral |
| P6-001I | Reassess Antigravity headless interface | Help/docs inspection only | Approved contract or explicit continued deferral |
| P6-001J | Integrate approved live roles into conductor | None during implementation PR | Default dry-run preserved; protected checks pass |
| P6-001K | Publish Phase 6 validation report and reconcile status | No new calls | Evidence, limitations, and claims reviewed |

Implementation and execution must remain separate PRs. A PR that adds live-call capability must contain no official live evidence; an execution PR must use code already merged and protected on `main`.

## Live Evidence Contract

Official live evidence uses single-use task IDs and a new reviewed metadata schema. Candidate fields:

- `task_id`
- `vendor`
- `role`
- `execution` (`live` or `mock`)
- `cli_name`
- `cli_version`
- `model_identifier` when returned by the vendor
- `authentication_class`
- `credentials_available`
- `exit_code`
- `attempt_count`
- `timeout_seconds`
- `budget_ceiling_usd` when supported
- `budget_result` when reported
- `blocked_command_count`
- `schema_valid`
- `scope_valid`
- `secret_scan_passed`
- `run_date`

Do not commit:

- raw prompts, raw transcripts, chain-of-thought, or vendor debug dumps;
- account names, emails, home paths, session IDs, request IDs, or tokens;
- complete environment snapshots;
- raw stderr or unreviewed stdout;
- timestamps or random identifiers that add no audit value;
- absolute executable or workspace paths.

Unlike Phase 5, live inference is not expected to be byte-identical. Phase 6 reproducibility means the same fixture repeatedly passes the schema, scope, provenance, timeout, budget, and secret gates. Content hashes may document a particular accepted result but must not be presented as deterministic vendor output.

## Test Matrix

Every live runner or adapter implementation must test these cases with fake CLIs before any real call:

| Case | Expected result |
|---|---|
| Missing explicit live flag | Refuse before task-directory creation |
| Missing or malformed approval identifier | Refuse before vendor invocation |
| Missing authentication | Fail without retry; no durable raw output |
| Selected CLI missing | Fail preflight |
| Wrong CLI version policy | Fail preflight or require reviewed compatibility update |
| Timeout | Kill process tree, fail, and record sanitized timeout evidence |
| Budget halt | Fail without retry; preserve reported bounded-cost metadata |
| Invalid structured output | Fail schema gate |
| Valid stdout plus noisy stderr | Parse stdout only; redact/discard stderr |
| Secret-like output | Fail secret gate and prohibit commit |
| Blocked command attempt | Log command name, return failure, prohibit success claim |
| Write outside synthetic scope | Fail scope gate |
| Non-empty in-scope diff | Validate against `files_to_touch` |
| Transient vendor error | At most one explicitly approved retry |
| Existing task ID | Refuse without modifying evidence |
| Live adapter failure in hybrid run | Halt; do not fall back to mock |
| Dry-run regression | Existing Phase 5 byte-identity tests remain unchanged and pass |

## Timeout, Budget, and Retry Policy

- Every call has a wall-time limit enforced outside the vendor process.
- Planner and reviewer calls default to no tools and the smallest reviewed budget that can satisfy the fixture.
- Builder validation permits only the synthetic edit and uses the narrowest available write sandbox.
- The implementation PR must set numeric timeout and budget defaults before execution; execution approval records any override.
- Maximum attempts are one by default and two only for a classified transient vendor failure.
- Never retry authentication failure, invalid arguments, budget halt, timeout, schema failure, scope drift, secret detection, blocked-command detection, or RSK-0.
- The total approved budget covers all attempts; a retry does not reset it.

## Validation Gates

Each official run must pass, in order:

1. Human approval and single-use task ID.
2. CLI identity, supported version policy, and sanitized authentication preflight.
3. Synthetic fixture hash and allowed-path check.
4. Minimal environment and blocked-command guard installation.
5. Bounded vendor invocation.
6. Process-tree termination confirmation.
7. Structured-output parsing and normalization.
8. Artifact schema validation.
9. Source-scope validation where writes are allowed.
10. Provenance validation with explicit live/mock identity.
11. Secret scan over every candidate committed artifact.
12. Human review of sanitized evidence.
13. Complete local tests and protected pull-request checks.

Failure at any gate stops the task. Later gates must not run against partially trusted output unless needed to create a sanitized local failure report.

## CI and Manual Execution Boundary

- GitHub Actions must not perform live vendor calls in Phase 6.
- Pull-request CI continues to use deterministic mocks and fake CLI fixtures only.
- Official live calls run manually from an approved local environment.
- No vendor credential is added to GitHub Actions secrets during Phase 6 without a separate RSK-0 decision.
- Protected checks validate code, schemas, fixtures, sanitization, and committed evidence; they do not repeat inference.

## Rollback

At every Phase 6 step:

- the deterministic adapters and dry-run conductor remain available;
- live selection remains disabled by default;
- removing the new live runner or adapter selection restores the Phase 5 behavior;
- failed official evidence stays uncommitted unless a sanitized failure report is explicitly approved;
- no rollback requires credential rotation because credentials are never copied or modified by the runner;
- any suspected credential exposure halts work and escalates to an RSK-0 incident decision before repository activity continues.

## Phase 6 Exit Criteria

Phase 6 may be marked complete only when:

- the plan and all implementation PRs are manually reviewed and merged;
- Claude planner and reviewer live contracts pass, or are explicitly deferred with rationale;
- Codex builder live contract passes, or is explicitly deferred with rationale;
- Qwen has either an approved live provider with passing role contracts or a recorded continued deferral;
- Antigravity has either an approved headless contract with passing validation or a recorded continued deferral;
- every tested pipeline identifies each role as live or mock;
- no hybrid run is described as all-live;
- dry-run byte identity and all existing tests still pass;
- no secret, raw credential, personal path, or unreviewed transcript is committed;
- a sanitized validation report states exactly which vendors, roles, and modes were validated;
- all protected checks pass and the owner manually approves the final merge.

If Qwen remains deferred, `qwen-led`, `safe-default`, and `dual-builder` cannot receive an all-live claim because each requires a Qwen role. If Antigravity remains deferred, the deterministic mock verifier remains the only approved verifier.

## Decisions Required Before Execution

1. Approve the isolated-runner architecture and separation from the dry-run conductor.
2. Approve numeric timeout and budget ceilings for Claude and Codex fixtures.
3. Approve the exact synthetic fixture content and permitted workspace paths.
4. Decide whether existing interactive Claude/Codex sessions are acceptable for official evidence or whether a separate credential mechanism is required.
5. Select or continue to defer the Qwen provider and credential source.
6. Confirm Antigravity remains deferred unless a supported headless contract appears.
7. Decide whether conductor live integration is in Phase 6 after individual validation or deferred to a follow-on phase.

No decision above is implied by merging this planning document.
