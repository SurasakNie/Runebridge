# PC Runner Session Handoff — Live Qwen Evidence

This note hands off the Phase 6 live-Qwen work to a **local Claude Code session
running on the owner's PC** (the approved live Qwen runner under the
`PC-first, VM-later` model). The shared remote environment cannot perform live
Qwen calls (egress-policy `403 Forbidden` to provider hosts), so the live steps
below must run on the PC.

## Before you start (local session)

1. Pull `main` (Steps 1 and 2 below are already merged).
2. Read, in order: `AGENTS.md`, `.ai/PROJECT_BRIEF.md`, `.ai/CODING_RULES.md`,
   `.ai/SECURITY_RULES.md`, `.ai/MODEL_ROLES.md`, `.ai/TASKS.md`, then
   `docs/Phase-6-Qwen-Live-Evidence-Plan.md`.
3. Confirm Qwen provider egress works from the PC before any live step.

## Recommended ordering

### Step 1 — Build `P6-LEDGER-001` ✅ Complete (PR #24 merged)

The approval-ledger mechanism is implemented and merged. No action needed.

### Step 2 — Qwen reviewer adapter ✅ Complete (PR #27 merged)

`tools/bridge/live/qwen_adapters.py` is implemented and merged. The adapter
is **not** registered in `ENABLED_ADAPTERS`; the PC runner constructs
`AdapterSpec` directly via `build_qwen_adapter` and passes it to
`run_isolated_validation`. Note: `qwen --help` flag verification is still a
PC preflight item — confirm every flag in `build_qwen_adapter`'s command tuple
before the live run.

### Step 3 — Bounded live Qwen reviewer run (PC only, per-run approval)

1. Add an approval-ledger entry (from Step 1) for a fresh single-use `task_id`
   and `approval_id`, `vendor: qwen`, `role: reviewer`, today's date.
2. Pin and record the `qwen` CLI version; verify the adapter's flags.
3. Run `tools/bridge/live/run_isolated_validation.py --live` with the approved
   `--approval-id`, `--vendor qwen --role reviewer`, the synthetic reviewer
   fixture, `--timeout-seconds 30`, and an approved `--budget-ceiling-usd`.
4. Let the runner emit `LIVE_RUN_METADATA.json` and run the metadata + secret
   gates. **Never hand-edit the metadata** — it must be runner-generated.
5. Confirm no out-of-scope writes and an empty `BLOCKED_COMMANDS.log`.

### Step 4 — Promote and reconcile

- Move the run's `FINAL_REPORT.md` from `provisional-pass` to a status that
  reflects official, approval-bound live evidence.
- Reconcile `.ai/TASKS.md`, `.ai/AGENT_HANDOFF.md`, `.ai/CHANGELOG_AI.md`.
- Claude reviews the diff (`REVIEW_CLAUDE.json`); keep the merge human-controlled.

## Non-negotiable rails (restate from the plans)

- Synthetic fixtures only; no customer/repo source in live prompts.
- Commit no secret, API key, account email, host name, session id, or absolute
  path. The secret gate runs over every committed file.
- The ledger is fail-closed: an empty or non-matching ledger refuses the run.
- Single-use `task_id` and `approval_id` per run; approval for one run does not
  authorize another.
- Official metadata is runner-emitted only.
- One reviewer run is one role; it is not an all-live pipeline claim.
- Keep all Git/GitHub merges human-controlled.

## What stays here (remote session)

This remote session keeps the architect and reviewer roles: refining plans and
running the Claude review stage on diffs you bring back. It cannot run live Qwen.
