from __future__ import annotations

import argparse

from common import GateError, fail, read_front_matter, validate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=str)
    args = parser.parse_args()
    try:
        validate(read_front_matter(__import__("pathlib").Path(args.plan)), "plan.schema.json")
    except GateError as exc:
        return fail(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
