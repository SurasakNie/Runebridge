from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath

from common import GateError, fail, read_front_matter, validate


def normalize(path: str) -> str:
    return str(PurePosixPath(path.replace("\\", "/")))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("changed", nargs="*")
    args = parser.parse_args()
    try:
        plan = read_front_matter(args.plan)
        validate(plan, "plan.schema.json")
    except GateError as exc:
        return fail(exc)
    allowed = {normalize(path) for path in plan["files_to_touch"]}
    drift = sorted({normalize(path) for path in args.changed} - allowed)
    if drift:
        return fail(GateError(f"scope drift: {', '.join(drift)}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
