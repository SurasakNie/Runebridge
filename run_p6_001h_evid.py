#!/usr/bin/env python3
"""PC runner — bounded live Qwen reviewer validation for P6-001H-EVID.

Approval ID:  P6-QWEN-REVIEW-002-RUN-001
Vendor:       qwen
Role:         reviewer
Budget:       $0.10 ceiling
Timeout:      30 s

Prerequisites
-------------
1. Pull the latest claude/resume-tasks-48qvg1 branch (includes the ledger entry).
2. Run ``qwen --help`` and confirm --output-format, --json-schema, --max-tool-calls,
   and --no-chat-recording are present; update qwen_adapters.py if any flag differs.
3. Record the exact CLI version string (e.g. ``0.19.2``).
4. Confirm provider egress works: ``qwen --help`` must not time out.
5. Give explicit per-run verbal or written approval before invoking this script.

Usage
-----
    python run_p6_001h_evid.py --qwen-version VERSION [--qwen-path PATH] [--model MODEL]

    QWEN_CLI_VERSION env var may substitute for --qwen-version.
    QWEN_PATH env var may substitute for --qwen-path.
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

from tools.bridge.live.qwen_adapters import build_qwen_adapter
from tools.bridge.live.run_isolated_validation import ValidationConfig, run_isolated_validation

TASK_ID = "P6-QWEN-REVIEW-002"
APPROVAL_ID = "P6-QWEN-REVIEW-002-RUN-001"
BUDGET_CEILING_USD = 0.10
TIMEOUT_SECONDS = 30
ARTIFACT_ROOT = REPO_ROOT / ".bridge"

# Synthetic fixture — no customer data, no repo source.
FIXTURE_PROMPT = (
    "Review a minimal synthetic diff for the Runebridge pipeline. "
    "The diff adds one blank line to a placeholder file. "
    "There are no bugs, security issues, missing tests, or scope drift. "
    "Verdict: approve."
)


def resolve_qwen(qwen_path_arg: str | None) -> Path:
    candidate = qwen_path_arg or os.environ.get("QWEN_PATH") or shutil.which("qwen")
    if not candidate:
        raise SystemExit(
            "qwen CLI not found. Pass --qwen-path, set QWEN_PATH, or put qwen on PATH."
        )
    resolved = Path(candidate).resolve()
    if not resolved.is_file():
        raise SystemExit(f"qwen executable not found: {resolved}")
    return resolved


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qwen-path", help="Absolute path to qwen executable")
    parser.add_argument(
        "--qwen-version",
        help="Qwen CLI version string, e.g. '0.19.2' (or set QWEN_CLI_VERSION)",
    )
    parser.add_argument("--model", help="Qwen model identifier (optional)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    qwen_path = resolve_qwen(args.qwen_path)
    cli_version = args.qwen_version or os.environ.get("QWEN_CLI_VERSION", "")
    if not cli_version:
        raise SystemExit(
            "Qwen CLI version required. Pass --qwen-version or set QWEN_CLI_VERSION.\n"
            "Obtain it from: qwen --version"
        )

    run_date = datetime.date.today().isoformat()

    print(f"Task:        {TASK_ID}")
    print(f"Approval ID: {APPROVAL_ID}")
    print(f"Run date:    {run_date}")
    print(f"Qwen:        {qwen_path}  (version {cli_version})")
    print(f"Model:       {args.model or '(not specified)'}")
    print(f"Budget:      ${BUDGET_CEILING_USD:.2f} ceiling")
    print(f"Timeout:     {TIMEOUT_SECONDS} s")
    print()

    spec = build_qwen_adapter(
        executable=qwen_path,
        cli_version=cli_version,
        task_id=TASK_ID,
        budget_ceiling_usd=BUDGET_CEILING_USD,
        prompt=FIXTURE_PROMPT,
        model_identifier=args.model or None,
    )

    config = ValidationConfig(
        task_id=TASK_ID,
        vendor="qwen",
        role="reviewer",
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
    print("Next: commit only the new .bridge/P6-QWEN-REVIEW-002/ directory,")
    print("tools/bridge/live/approval-ledger.json, and .ai/ status files,")
    print("then open a review-branch PR for human merge.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
