#!/usr/bin/env python3
"""PC runner — bounded live Codex builder validation for P6-001F.

Approval ID:  P6-001F-RUN-001
Vendor:       codex
Role:         builder
Model:        gpt-5.4 (override with --model; codex-mini-latest is NOT usable
              with a ChatGPT-account Codex auth — see DEFAULT_MODEL note)
Budget:       $0.06 ceiling (approved and recorded, not mechanically enforced —
              Codex CLI 0.141.0 has no --budget-usd flag and reports token
              usage, not a dollar cost; budget_result is recorded as
              "not_reported", matching the existing Qwen adapter precedent)
Timeout:      30 s

Prerequisites (see .bridge/P6-001F/PLAN.md for the full preflight)
------------------------------------------------------------------
1. Pull this branch (includes the hardened adapter prompt and corrected runbook).
2. Run ``codex exec --help`` and confirm ``--json``, ``--sandbox`` with
   ``workspace-write``, ``--output-schema <file>``, and ``--model`` are present and
   behave as assumed; update tools/bridge/live/codex_adapters.py and re-run
   ``pytest tests/live/test_codex_adapters.py`` if any flag differs. (Verified
   against a real codex-cli 0.141.0 install on 2026-07-01: --schema and
   --budget-usd do not exist; --output-schema takes a file path, not inline
   JSON, and the file must be written without a UTF-8 BOM or Codex rejects it.)
3. Record the exact CLI version string and pass it as --codex-version.
4. Confirm an authenticated Codex/ChatGPT session is active.
5. Add the single-use approval-ledger entry P6-001F-RUN-001
   (vendor codex, role builder, run_date = today, rsk_level RSK-1) to
   tools/bridge/live/approval-ledger.json and validate it against the schema.
6. Give explicit per-run approval before invoking this script (ratification of the
   2026-06-28 parameters does not constitute per-run approval).

The runner provisions its own empty, isolated temporary workspace; Codex creates
fixture.txt inside it. There is no external workspace directory to prepare.

Usage
-----
    python run_p6_001f.py --codex-version VERSION [--codex-path PATH] [--model MODEL]

    CODEX_CLI_VERSION env var may substitute for --codex-version.
    CODEX_PATH env var may substitute for --codex-path.
"""
from __future__ import annotations

import argparse
import datetime
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from tools.bridge.live.codex_adapters import build_codex_adapter
from tools.bridge.live.run_isolated_validation import ValidationConfig, run_isolated_validation

TASK_ID = "P6-001F"
APPROVAL_ID = "P6-001F-RUN-001"
# codex-mini-latest (the 2026-06-28 ratified model) is REJECTED with a
# ChatGPT-account Codex auth: "The 'codex-mini-latest' model is not supported
# when using Codex with a ChatGPT account" (HTTP 400, confirmed on codex-cli
# 0.141.0, 2026-07-01). gpt-5.4 is the account's configured default and was
# proven to run the synthetic contract end-to-end in preflight probes. If a
# runner uses an API-key Codex auth instead, override with --model.
DEFAULT_MODEL = "gpt-5.4"
BUDGET_CEILING_USD = 0.06
TIMEOUT_SECONDS = 30
ARTIFACT_ROOT = REPO_ROOT / ".bridge"   # runner publishes to ARTIFACT_ROOT / task_id

# Synthetic fixture — no customer data, no repo source. Codex creates fixture.txt
# in the empty isolated workspace and reports a unified diff with a/ b/ headers.
FIXTURE_PROMPT = "Create fixture.txt containing the single line '# Codex builder contract validated.'"


def resolve_codex(codex_path_arg: str | None) -> Path:
    candidate = codex_path_arg or os.environ.get("CODEX_PATH") or shutil.which("codex")
    if not candidate:
        raise SystemExit(
            "codex CLI not found. Pass --codex-path, set CODEX_PATH, or put codex on PATH."
        )
    resolved = Path(candidate).resolve()
    if not resolved.is_file():
        raise SystemExit(f"codex executable not found: {resolved}")
    return resolved


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-path", help="Absolute path to codex executable")
    parser.add_argument(
        "--codex-version",
        help="Codex CLI version string (or set CODEX_CLI_VERSION)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Codex model identifier (default {DEFAULT_MODEL})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    codex_path = resolve_codex(args.codex_path)
    cli_version = args.codex_version or os.environ.get("CODEX_CLI_VERSION", "")
    if not cli_version:
        raise SystemExit(
            "Codex CLI version required. Pass --codex-version or set CODEX_CLI_VERSION.\n"
            "Obtain it from: codex --version"
        )

    run_date = datetime.date.today().isoformat()

    print(f"Task:        {TASK_ID}")
    print(f"Approval ID: {APPROVAL_ID}")
    print(f"Run date:    {run_date}")
    print(f"Codex:       {codex_path}  (version {cli_version})")
    print(f"Model:       {args.model}")
    print(f"Budget:      ${BUDGET_CEILING_USD:.2f} ceiling")
    print(f"Timeout:     {TIMEOUT_SECONDS} s")
    print()

    spec = build_codex_adapter(
        executable=codex_path,
        cli_version=cli_version,
        task_id=TASK_ID,
        budget_ceiling_usd=BUDGET_CEILING_USD,
        prompt=FIXTURE_PROMPT,
        model_identifier=args.model,
    )

    config = ValidationConfig(
        task_id=TASK_ID,
        vendor="codex",
        role="builder",
        approval_id=APPROVAL_ID,
        run_date=run_date,
        artifact_root=ARTIFACT_ROOT,
        timeout_seconds=TIMEOUT_SECONDS,
        budget_ceiling_usd=BUDGET_CEILING_USD,
        live=True,
    )

    print("Running isolated validation …")
    try:
        task_dir = run_isolated_validation(config, spec)
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"Evidence written to: {task_dir}")
    print()
    print("Next: secret-scan the evidence, then commit only the new .bridge/P6-001F/")
    print("directory, tools/bridge/live/approval-ledger.json, and .ai/ status files,")
    print("then open a review-branch PR for human merge.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
