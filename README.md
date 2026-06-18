# Runebridge
# AI Bridge
Vendor-neutral AI development pipeline coordinating Claude Code, Codex, Qwen Code, and Antigravity through Git branches, explicit artifacts, deterministic safety gates, independent reviews, and human-approved pull requests.

AI Bridge is a planned, vendor-neutral workflow for coordinating multiple AI coding tools through a Git repository. It uses explicit files and Git branches as the shared context between Claude Code, OpenAI Codex CLI, Qwen Code, Google Antigravity, and a human reviewer.

> **Project status:** Design phase. The repository currently contains planning documents; the conductor, adapters, gates, and CI workflows have not yet been implemented.

## Goal

Turn one task specification into a reviewed pull request through a controlled pipeline:

```text
Human task
    |
    v
Claude Code plans
    |
    v
Codex implements on a feature branch
    |
    v
Antigravity verifies build, tests, and behavior
    |
    v
Claude Code and Qwen Code review independently
    |
    v
Human reviews and merges the pull request
```

The tools do not need a live agent-to-agent protocol. Plans, diffs, verification results, and review verdicts move between stages as committed artifacts.

## Design Principles

- **Git is the source of truth.** All AI-generated changes stay on a feature branch.
- **Artifacts are the shared memory.** Each stage reads and writes explicit files under `.bridge/<task-id>/`.
- **Humans control irreversible actions.** Merge, deployment, secret changes, force pushes, and destructive database operations require approval.
- **Gates are deterministic.** External scripts validate artifacts, scope, verification, and review results.
- **Permissions follow least privilege.** Planning and review are read-only; implementation is limited to the workspace.
- **Retries are bounded.** Failed edit/verify loops stop after a defined retry budget.

## Default Roles

| Role | Tool | Responsibility |
|---|---|---|
| Planner | Claude Code | Define scope, risks, files, tests, and acceptance criteria |
| Builder | OpenAI Codex CLI | Implement the approved plan and run targeted tests |
| Verifier | Google Antigravity | Check build, tests, integration, browser, or UI behavior |
| Primary reviewer | Claude Code | Review correctness, risk, and scope adherence |
| Cross-reviewer | Qwen Code | Provide an independent second review |
| Final approver | Human | Review the pull request and decide whether to merge |

Alternative Qwen-led and dual-builder modes are design options for later phases. The first implementation will use the deterministic default pipeline above.

## Planned Repository Layout

```text
.
|-- .ai/                         # Shared project context and policies
|-- .bridge/
|   `-- <task-id>/               # Per-task handoff artifacts
|       |-- TASK.md
|       |-- PLAN.md
|       |-- CHANGES.diff
|       |-- VERIFY.json
|       |-- REVIEW_CLAUDE.json
|       |-- REVIEW_QWEN.json
|       `-- FINAL_REPORT.md
|-- prompts/                     # Versioned prompts for each role
|-- schemas/                     # Machine-readable artifact schemas
|-- tools/bridge/
|   |-- adapters/                # Vendor CLI wrappers
|   |-- gates/                   # Deterministic stop/go checks
|   `-- orchestrate.sh           # Pattern A conductor
|-- AGENTS.md
|-- CLAUDE.md
|-- QWEN.md
`-- README.md
```

## Safety Model

| Risk | Meaning | Automation policy |
|---|---|---|
| RSK-2 | Easy to reverse, such as documentation changes | AI may proceed on a branch |
| RSK-1 | Normal code changes with meaningful impact | AI may edit and test; pull request required |
| RSK-0 | Irreversible or production-impacting action | Stop and obtain human approval |

The conductor must halt when:

- the plan or acceptance criteria are missing;
- the implementation changes files outside the approved scope;
- verification fails after the retry budget;
- either reviewer reports a blocking issue or scope drift;
- a secret is detected;
- an RSK-0 action is requested; or
- any required stage exits unsuccessfully.

## Planned Workflow

1. Create `bridge/<task-id>` from the protected default branch.
2. Record the original request in `.bridge/<task-id>/TASK.md`.
3. Generate and validate `PLAN.md`.
4. Implement the plan and capture a complete diff, including new files.
5. Run the verification suite and write `VERIFY.json`.
6. Run independent Claude and Qwen reviews against the same final diff.
7. Validate all artifacts and open a pull request.
8. Let a human approve, reject, or request changes.

Any fix made after verification or review invalidates the previous diff and verdicts. The affected checks must run again against the final revision.

## Rollout

- **Phase 0:** Run every stage manually and validate the artifact contracts.
- **Phase 1:** Add shared `.ai/` context, root instruction files, and GitHub protection.
- **Phase 2:** Add CI and deterministic gate scripts.
- **Phase 3:** Build the linear Pattern A conductor.
- **Phase 4:** Add bounded repair loops and independent cross-review.
- **Phase 5:** Evaluate Qwen-led and dual-builder modes.
- **Phase 6:** Consider Antigravity as an optional conductor while retaining external gates.

## Current Documentation

- [Pipeline implementation plan](ai-bridge-pipeline-plan-1-qwen.md) - the canonical pipeline and artifact flow.
- [Repository setup plan](ai-bridge-pipeline-plan-2-qwen.md) - GitHub, MCP, security, and workspace setup.
- [Extended design catalogue](ai-bridge-pipeline-plan-3-qwen.md) - alternative modes, templates, and longer-term options.

Some vendor CLI and SDK details remain intentionally unconfirmed. They will be isolated behind adapters and verified during the manual dry run before automation is enabled.

## Contributing

Keep changes narrow and reviewable:

1. Open an issue or define a task with explicit acceptance criteria.
2. Work on a feature branch; do not push directly to the protected branch.
3. Add or update tests when behavior changes.
4. Do not commit credentials, tokens, private configuration, or customer data.
5. Open a pull request with the plan, verification evidence, and remaining risks.

## License

This project is available under the [MIT License](LICENSE).
