from __future__ import annotations

import argparse
from pathlib import Path

from common import GateError, fail, read_front_matter, validate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    try:
        plan = read_front_matter(args.plan)
        validate(plan, "plan.schema.json")
    except GateError as exc:
        return fail(exc)
    if plan["risk_level"] == "RSK-0" or plan["requires_human_approval"]:
        print("RSK-0 or human approval required", file=__import__("sys").stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
