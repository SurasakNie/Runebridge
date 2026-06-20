from __future__ import annotations

import argparse
from pathlib import Path

from common import GateError, fail, read_front_matter, validate


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
    if args.mode == "qwen-led" and (args.task_dir / "REVIEW_QWEN.json").exists():
        return fail(GateError("REVIEW_QWEN.json is forbidden in qwen-led mode"))
    try:
        validate(read_front_matter(args.task_dir / "TASK.md"), "task.schema.json")
        for name in sorted(required & {"EDIT_CODEX.md", "EDIT_QWEN.md"}):
            validate(read_front_matter(args.task_dir / name), "edit-summary.schema.json")
    except GateError as exc:
        return fail(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
