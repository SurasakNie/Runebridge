# PC Runner Session Handoff — P6-001H-EVID Live Qwen Reviewer Evidence

This note hands off the **P6-001H-EVID live Qwen reviewer validation** to a
**local session on the approved PC runner**. The shared remote environment
returns egress-policy `403 Forbidden` to approved Qwen provider hosts and cannot
invoke a real `qwen` CLI, so the execution steps below must run locally.

The live-invocation blocker is already resolved: Qwen Code CLI `0.19.2` returns
the schema-valid review JSON in the result envelope's **`result` string field**,
not in `structured_output`. The parser fallback
(`structured_output` → `structured_result` → JSON-parsed `result`) merged in
**PR #31 (`ff4dfad`)**, with all existing schema/reviewer/`task_id`/budget checks
and the fail-closed posture preserved. The full suite is **140 passing**. What
remains is a single bounded live run to produce official evidence.

## Prerequisites (confirm before starting)

- `P6-LEDGER-001` is complete (approval-ledger mechanism merged — PR #24).
- `P6-QWEN-ADAPTER-001` is complete (Qwen reviewer adapter merged — PR #27).
- The PR #31 parser fix is on `main` (`ff4dfad`).
- Qwen Code CLI `0.19.2` is installed and on `PATH`.
- An authenticated browser-OAuth Qwen session is active (the adapter uses
  `interactive_session`; no API-key env var is required).
- You have read: `AGENTS.md`, `.ai/PROJECT_BRIEF.md`, `.ai/SECURITY_RULES.md`,
  `.ai/MODEL_ROLES.md`, `.ai/TASKS.md`, and
  `docs/Phase-6-Qwen-Live-Evidence-Plan.md`.

## Step 1 — Preflight

1. **CLI version.** Run `qwen --version`; confirm `0.19.2`. Record the exact
   string; you will pass it as `cli_version` to `build_qwen_adapter`.

2. **No API keys present.** Confirm no Qwen/OpenAI API-key environment variables
   are set in the shell — authentication is stored browser OAuth only.

3. **Full suite green.** Run the whole test suite and confirm it passes before
   invoking the runner:
   ```powershell
   .venv\Scripts\python.exe -m pytest --basetemp ".tmp\pytest-basetemp"
   ```

4. **Approval-ledger entry.** Add to `tools/bridge/live/approval-ledger.json`,
   using **today's date** as `run_date` (the earlier draft used `2026-06-29`,
   which will be rejected by `assert_approved` if it does not match the run day):
   ```json
   {
     "approval_id": "P6-001H-EVID-RUN-001",
     "vendor": "qwen",
     "role": "reviewer",
     "run_date": "<today's date YYYY-MM-DD>",
     "approved_by": "human",
     "rsk_level": "RSK-1"
   }
   ```
   Validate against the schema:
   ```powershell
   .venv\Scripts\python.exe -c "import json,jsonschema; from pathlib import Path; jsonschema.validate(json.loads(Path('tools/bridge/live/approval-ledger.json').read_text()), json.loads(Path('schemas/approval-ledger.schema.json').read_text())); print('OK')"
   ```

5. **Per-run human approval.** Give explicit approval for run
   `P6-001H-EVID-RUN-001` immediately before invoking the runner. Earlier
   ratification does not constitute per-run approval; the approval is single-use.

## Step 2 — Execute

Run the following in a Python session at the repository root. This uses the
**current** runner API — `run_isolated_validation(config, spec)` takes no
`workspace=` argument (it creates its own isolated temp workspace; the Qwen
adapter sets `use_dedicated_vendor_cwd=True` so background processes write
outside the scope-checked area):

```python
from pathlib import Path
import datetime
from tools.bridge.live.qwen_adapters import build_qwen_adapter
from tools.bridge.live.run_isolated_validation import (
    ValidationConfig,
    run_isolated_validation,
)

TODAY = datetime.date.today().isoformat()           # must match the ledger entry
QWEN_PATH = Path(r"C:\path\to\qwen.exe")            # resolved on the runner
QWEN_VERSION = "0.19.2"                              # verified in Step 1
QWEN_MODEL = None                                    # or the approved model id

spec = build_qwen_adapter(
    executable=QWEN_PATH,
    cli_version=QWEN_VERSION,
    task_id="P6-001H-EVID",
    budget_ceiling_usd=0.10,
    prompt=(
        "Synthetic reviewer fixture: the change is a no-op documentation edit "
        "with no code impact. Return an approving review."
    ),
    model_identifier=QWEN_MODEL,
)

config = ValidationConfig(
    task_id="P6-001H-EVID",
    vendor="qwen",
    role="reviewer",
    approval_id="P6-001H-EVID-RUN-001",
    run_date=TODAY,
    artifact_root=Path(".bridge"),
    timeout_seconds=60,
    budget_ceiling_usd=0.10,
    live=True,
)

task_dir = run_isolated_validation(config, spec)
print("Evidence written to:", task_dir)
```

The runner emits `.bridge/P6-001H-EVID/` containing `REVIEW_QWEN.json`,
`LIVE_RUN_METADATA.json`, and `BLOCKED_COMMANDS.log`. The secret gate
(`check_no_secrets.py`) and metadata gate (`check_live_metadata.py`) run inside
the runner before publication; a failure raises `ValidationError` and writes no
evidence.

## Step 3 — Post-run verification

```powershell
# Secret-scan every evidence file (all must exit 0)
.venv\Scripts\python.exe tools\bridge\gates\check_no_secrets.py .bridge\P6-001H-EVID\REVIEW_QWEN.json
.venv\Scripts\python.exe tools\bridge\gates\check_no_secrets.py .bridge\P6-001H-EVID\LIVE_RUN_METADATA.json
.venv\Scripts\python.exe tools\bridge\gates\check_no_secrets.py .bridge\P6-001H-EVID\BLOCKED_COMMANDS.log
```

- `REVIEW_QWEN.json` must be review-schema valid with `reviewer: "qwen"` and
  `task_id: "P6-001H-EVID"` (the runner already enforced this; re-confirm).
- `LIVE_RUN_METADATA.json` is **runner-emitted** — never hand-edit it.
- `BLOCKED_COMMANDS.log` should be empty (no blocked command was invoked).

## Step 4 — Commit evidence and open the evidence PR

Commit **only**:
- `.bridge/P6-001H-EVID/REVIEW_QWEN.json`
- `.bridge/P6-001H-EVID/LIVE_RUN_METADATA.json`
- `.bridge/P6-001H-EVID/BLOCKED_COMMANDS.log`
- `tools/bridge/live/approval-ledger.json` (with the `P6-001H-EVID-RUN-001` entry)

Do **not** commit PC scratch files (`run_p6_001h_evid.py`, `debug_sandbox.py`,
`debug_output.json`, `out.txt`) or any temp/basetemp directory. Use a clean
publish worktree from `origin/main` if the working folder carries scratch
artifacts.

Commit message must not include absolute paths, session IDs, API tokens, or
email addresses. Open a PR targeting `main`. Keep the merge human-controlled.

## Known risk to watch on the first run

The parser's `result`-string path assumes **bare** JSON. If Qwen `0.19.2` wraps
the JSON in markdown fences (```` ```json … ``` ````) or surrounding prose,
`json.loads(result)` fails **closed** — the run produces no evidence and raises
`Qwen result field is not valid JSON` rather than emitting anything bad. If that
happens, make the extraction fence-tolerant (strip fences / locate the JSON
object) in `tools/bridge/live/qwen_adapters.py::_extract_payload`, add a
regression test, re-run the full suite, and merge that fix before retrying the
live run. The first run reveals the actual format.

## Non-negotiable rails

- Synthetic, secret-free prompt only; no customer/repo source in live prompts.
- The ledger is fail-closed: an empty or non-matching ledger refuses the run.
- `P6-001H-EVID-RUN-001` is single-use; approval for this run does not authorize
  another run, model, budget, or workspace.
- A missing or invalid structured payload must never be coerced into evidence.
- Official `LIVE_RUN_METADATA.json` is runner-emitted only — never hand-authored.
- Commit no secret, API key, host name, session ID, or absolute path.
- If preflight fails at any step, stop and do not invoke the runner.

## What stays in the remote session

The remote session keeps the architect and reviewer roles. After you bring back
the committed evidence diff, open a review request there and Claude will produce
`REVIEW_CLAUDE.json` for the evidence files and reconcile `P6-001H-EVID` to
Complete in `.ai/TASKS.md`.
