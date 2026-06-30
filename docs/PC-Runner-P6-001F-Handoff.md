# PC Runner Session Handoff — P6-001F Bounded Codex Validation

This note hands off the P6-001F Codex builder validation to a **local session
on an approved runner**. The shared remote environment cannot invoke a real
`codex` CLI, so the execution steps below must run locally.

## Prerequisites (confirm before starting)

- `P6-LEDGER-001` is complete (approval-ledger mechanism merged — PR #24).
- `P6-001E` is complete (Codex adapter contract merged — PR #18).
- Codex CLI is installed and accessible on the runner.
- An authenticated Codex/ChatGPT session is active.
- You have read: `AGENTS.md`, `.ai/PROJECT_BRIEF.md`, `.ai/CODING_RULES.md`,
  `.ai/SECURITY_RULES.md`, `.ai/MODEL_ROLES.md`, `.ai/TASKS.md`,
  `docs/Phase-6-Live-Vendor-Validation-Plan.md`, and `.bridge/P6-001F/PLAN.md`.

## Step 1 — Preflight

Complete every item in the `.bridge/P6-001F/PLAN.md` preflight checklist before
invoking the runner:

1. **CLI flag verification.** Run `codex --help`. Confirm `exec`, `--json`,
   `--sandbox workspace-write`, `--schema`, and `--budget-usd` all exist.
   If any flag is missing or renamed, update `tools/bridge/live/codex_adapters.py`
   and re-run `pytest tests/live/test_codex_adapters.py` before continuing.

2. **CLI version.** Record the exact version string; you will pass it as
   `cli_version` to `build_codex_adapter`.

3. **Approval-ledger entry.** Add to `tools/bridge/live/approval-ledger.json`:
   ```json
   {
     "approval_id": "P6-001F-RUN-001",
     "vendor": "codex",
     "role": "builder",
     "run_date": "<today's date YYYY-MM-DD>",
     "approved_by": "human",
     "rsk_level": "RSK-1"
   }
   ```
   Validate: `python3 -c "import json,jsonschema; from pathlib import Path; jsonschema.validate(json.loads(Path('tools/bridge/live/approval-ledger.json').read_text()), json.loads(Path('schemas/approval-ledger.schema.json').read_text())); print('OK')"`

4. **Synthetic fixture text.** Decide the benign one-line fixture text to pass via
   the `prompt` argument (e.g. `# Codex builder contract validated.`). There is **no
   external workspace directory to create**: the runner provisions its own empty,
   isolated temporary workspace and Codex creates `fixture.txt` inside it. The runner
   isolates the run internally — it blocks `git`, `gh`, `curl`, `wget`, and the vendor
   CLIs via PATH shims and fails the run if `BLOCKED_COMMANDS.log` is non-empty.

5. **Per-run human approval.** Give explicit verbal or written approval for run
   `P6-001F-RUN-001` immediately before invoking the runner. Ratification of
   parameters on 2026-06-28 does **not** constitute per-run approval.

## Step 2 — Execute

Run the following in a Python session at the repository root:

```python
from pathlib import Path
from tools.bridge.live.codex_adapters import build_codex_adapter
from tools.bridge.live.run_isolated_validation import ValidationConfig, run_isolated_validation
import datetime

ARTIFACT_ROOT = Path(".bridge")   # runner publishes to ARTIFACT_ROOT / task_id → .bridge/P6-001F
TODAY = datetime.date.today().isoformat()
CODEX_PATH = Path("/path/to/codex")          # resolved on the runner
CODEX_VERSION = "<verified version string>"

spec = build_codex_adapter(
    executable=CODEX_PATH,
    cli_version=CODEX_VERSION,
    task_id="P6-001F",
    budget_ceiling_usd=0.06,
    prompt="Create fixture.txt containing the single line '# Codex builder contract validated.'",
    model_identifier="codex-mini-latest",
)

config = ValidationConfig(
    task_id="P6-001F",
    vendor="codex",
    role="builder",
    approval_id="P6-001F-RUN-001",
    run_date=TODAY,
    artifact_root=ARTIFACT_ROOT,
    timeout_seconds=30,
    budget_ceiling_usd=0.06,
    live=True,
)

task_dir = run_isolated_validation(config, spec)
print("Evidence written to:", task_dir)
```

## Step 3 — Post-run verification

```bash
# Secret scan over evidence files
python3 tools/bridge/gates/check_no_secrets.py .bridge/P6-001F/EDIT_CODEX.md
python3 tools/bridge/gates/check_no_secrets.py .bridge/P6-001F/CHANGES.diff
python3 tools/bridge/gates/check_no_secrets.py .bridge/P6-001F/LIVE_RUN_METADATA.json

# Confirm CHANGES.diff is scoped to fixture.txt only (no other paths)
grep "^--- \|^+++ " .bridge/P6-001F/CHANGES.diff

# Confirm cost did not exceed $0.06
python3 -c "
import json, yaml
from pathlib import Path
md = Path('.bridge/P6-001F/EDIT_CODEX.md').read_text()
fm = md.split('---')[1]
data = yaml.safe_load(fm)
print('cost_usd:', data.get('total_cost_usd', 'missing'))
"
```

All three secret scans must exit 0. The diff must reference only `fixture.txt`.

## Step 4 — Commit evidence and reconcile

Commit only:
- `.bridge/P6-001F/EDIT_CODEX.md`
- `.bridge/P6-001F/CHANGES.diff`
- `.bridge/P6-001F/LIVE_RUN_METADATA.json`
- `tools/bridge/live/approval-ledger.json` (with the P6-001F-RUN-001 entry)
- `.ai/TASKS.md` (P6-001F → Complete)
- `.ai/AGENT_HANDOFF.md` and `.ai/CHANGELOG_AI.md`

Commit message must not include absolute paths, session IDs, API tokens, or
email addresses.

Open a PR targeting `main`. Keep the merge human-controlled.

## Non-negotiable rails

- Synthetic fixture only; no customer/repo source in live prompts.
- Commit no secret, API key, host name, session ID, or absolute path.
- The ledger is fail-closed: an empty or non-matching ledger refuses the run.
- `P6-001F-RUN-001` is single-use; approval for this run does not authorize
  another run, another model, a higher budget, or a different workspace.
- Official metadata is runner-emitted only — never hand-authored.
- If preflight fails at any step, stop and do not invoke the runner.

## What stays in the remote session

The remote session keeps the architect and reviewer roles. After you bring back
the committed evidence diff, open a review request here and Claude will produce
`REVIEW_CLAUDE.json` for the evidence files.
