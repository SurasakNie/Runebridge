from __future__ import annotations

import argparse
from pathlib import Path

from common import GateError, fail


BASE = {"TASK.md", "PLAN.md", "CHANGES.diff", "VERIFY.json", "REVIEW_CLAUDE.json"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_dir", type=Path)
    parser.add_argument("--mode", required=True, choices=("safe-default", "qwen-led", "dual-builder"))
    args = parser.parse_args()
    required = set(BASE)
    required.add("EDIT_QWEN.md" if args.mode == "qwen-led" else "EDIT_CODEX.md")
    if args.mode in {"safe-default", "dual-builder"}:
        required.add("REVIEW_QWEN.json")
    if args.mode == "dual-builder":
        required.add("EDIT_QWEN.md")
    missing = sorted(name for name in required if not (args.task_dir / name).is_file())
    if missing:
        return fail(GateError(f"missing artifacts: {', '.join(missing)}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
