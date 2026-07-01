---
task_id: P6-001F
planner: claude
risk_level: RSK-1
files_to_touch:
  - .bridge/P6-001F/EDIT_CODEX.md
  - .bridge/P6-001F/CHANGES.diff
  - .bridge/P6-001F/LIVE_RUN_METADATA.json
  - tools/bridge/live/approval-ledger.json
  - .ai/TASKS.md
acceptance_criteria:
  - "gate check_plan.py exits 0 on this PLAN.md"
  - "approval-ledger.json contains an entry with approval_id P6-001F-RUN-001, vendor codex, role builder, run_date matching the execution date, and rsk_level RSK-1"
  - "EDIT_CODEX.md is runner-emitted and validates against schemas/edit-summary.schema.json with task_id matching the run config, tool == codex, dry_run == false"
  - "CHANGES.diff is runner-emitted, non-empty, and scoped only to fixture.txt"
  - "LIVE_RUN_METADATA.json is runner-emitted (not hand-authored) and contains approval_id P6-001F-RUN-001"
  - "check_no_secrets.py exits 0 over all three committed evidence files"
  - "LIVE_RUN_METADATA.json records a budget_result value (not_reported is acceptable: Codex CLI 0.141.0 reports token usage, not a dollar cost, and has no --budget-usd flag; $0.06 is the approved ceiling, not a mechanically enforced one)"
  - "no raw stdout, stderr, workspace paths, session identifiers, or absolute paths are committed"
requires_human_approval: true
---
# Plan — P6-001F Bounded Codex Builder Validation

## Goal

Execute one bounded live Codex builder call on the approved runner, produce
schema-valid sanitized evidence, and commit it as official Phase 6 Codex builder
validation.

## Preflight checklist (must pass before invoking the runner)

1. **CLI flag verification.** Run `codex exec --help` and confirm every flag in
   `build_codex_adapter`'s `command` tuple (`--json`, `--sandbox workspace-write`,
   `--skip-git-repo-check`, `--output-schema <file>`, `--model`) exists and
   behaves as assumed. Verified against a real codex-cli 0.141.0 install on
   2026-07-01: `--schema` (inline JSON) and `--budget-usd` do not exist; the
   real event stream is JSONL with no reported dollar cost. If any flag differs
   on your install, update `tools/bridge/live/codex_adapters.py` and re-run the
   fake-CLI test suite before proceeding.

2. **CLI version policy.** Record the installed `codex` version; supply it as
   `cli_version` to `build_codex_adapter`. Reject any version that lacks the
   `--json` or `--sandbox` flags.

3. **Approval-ledger entry.** Add to `tools/bridge/live/approval-ledger.json`:
   ```json
   {
     "approval_id": "P6-001F-RUN-001",
     "vendor": "codex",
     "role": "builder",
     "run_date": "<YYYY-MM-DD of actual execution>",
     "approved_by": "human",
     "rsk_level": "RSK-1"
   }
   ```
   Validate the updated file against `schemas/approval-ledger.schema.json`.
   The runner refuses if no matching entry is found.

4. **Synthetic fixture text.** Decide the benign one-line fixture text to pass via
   the `prompt` argument (for example `# Codex builder contract validated.`). There
   is **no external workspace directory to create**: the runner provisions its own
   empty, isolated temporary workspace and Codex creates `fixture.txt` inside it. No
   repository source, customer data, or secrets may appear in the fixture text.

5. **Sandbox confirmation.** The runner isolates the run internally — it blocks
   `git`, `gh`, `curl`, `wget`, and the vendor CLIs via PATH shims and fails the run
   if `BLOCKED_COMMANDS.log` is non-empty. Confirm the prompt drives only the single
   `codex exec` call with no other tool or network helper.

6. **Per-run human approval.** The owner must give explicit verbal or written
   approval for `P6-001F-RUN-001` immediately before the runner is invoked.
   Ratification of parameters does not constitute per-run approval.

## Execution

```python
from pathlib import Path
from tools.bridge.live.codex_adapters import build_codex_adapter
from tools.bridge.live.run_isolated_validation import ValidationConfig, run_isolated_validation

ARTIFACT_ROOT = Path(".bridge")   # runner publishes to ARTIFACT_ROOT / task_id → .bridge/P6-001F

spec = build_codex_adapter(
    executable=Path("/path/to/codex"),  # resolved on the runner
    cli_version="<verified version>",
    task_id="P6-001F",
    budget_ceiling_usd=0.06,
    prompt="Create fixture.txt containing the single line '# Codex builder contract validated.'",
    model_identifier="gpt-5.4",  # codex-mini-latest is unsupported with ChatGPT-account auth
)

config = ValidationConfig(
    task_id="P6-001F",
    vendor="codex",
    role="builder",
    approval_id="P6-001F-RUN-001",
    run_date="<YYYY-MM-DD>",
    artifact_root=ARTIFACT_ROOT,
    timeout_seconds=30,
    budget_ceiling_usd=0.06,
    live=True,
)

task_dir = run_isolated_validation(config, spec)
```

## Post-run verification

1. `tools/bridge/gates/check_no_secrets.py` over `.bridge/P6-001F/EDIT_CODEX.md`,
   `.bridge/P6-001F/CHANGES.diff`, and `.bridge/P6-001F/LIVE_RUN_METADATA.json`.
2. Confirm `CHANGES.diff` references only `fixture.txt` (no other paths).
3. Confirm `LIVE_RUN_METADATA.json` is runner-emitted (creation timestamp matches
   the run, no hand-authored fields).
4. Review `budget_result` in `LIVE_RUN_METADATA.json` and the console token-usage
   output at run time. `not_reported` is expected and acceptable; Codex CLI
   0.141.0 has no mechanism to enforce or report a dollar-cost ceiling.

## Evidence commit

Commit only the three sanitized files listed in `files_to_touch`, the updated
`approval-ledger.json`, and the `.ai/TASKS.md` status update. The commit message
must not include absolute paths, API tokens, session identifiers, or email addresses.

## Stop conditions

- Any preflight step fails → do not invoke the runner.
- Runner exits non-zero → do not commit partial output; diagnose and retry with
  updated flags only after re-confirming per-run approval.
- `check_no_secrets.py` exits non-zero over evidence files → do not commit;
  scrub or regenerate before proceeding.
- Codex reports a failed turn, writes outside the approved workspace scope, or
  returns structured output that fails schema/task-ID validation →
  `ValidationError` halts the run; no evidence committed.
