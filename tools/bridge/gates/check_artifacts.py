from __future__ import annotations

import argparse
from pathlib import Path

from common import GateError, fail, read_front_matter, read_json, validate


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
        task = read_front_matter(args.task_dir / "TASK.md")
        validate(task, "task.schema.json")
        artifacts = [read_front_matter(args.task_dir / "PLAN.md")]
        validate(artifacts[0], "plan.schema.json")
        for name in sorted(required & {"EDIT_CODEX.md", "EDIT_QWEN.md"}):
            edit = read_front_matter(args.task_dir / name)
            validate(edit, "edit-summary.schema.json")
            artifacts.append(edit)
        verify = read_json(args.task_dir / "VERIFY.json")
        validate(verify, "verify.schema.json")
        artifacts.append(verify)
        for name in sorted(required & {"REVIEW_QWEN.json", "REVIEW_CLAUDE.json"}):
            review = read_json(args.task_dir / name)
            validate(review, "review.schema.json")
            artifacts.append(review)
        if any(artifact["task_id"] != task["task_id"] for artifact in artifacts):
            raise GateError("artifact task_id does not match TASK.md")
    except GateError as exc:
        return fail(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
