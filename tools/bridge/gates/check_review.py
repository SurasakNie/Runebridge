from __future__ import annotations

import argparse
from pathlib import Path

from common import GateError, fail, read_json, validate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--reviewer", choices=("qwen", "claude"))
    args = parser.parse_args()
    try:
        review = read_json(args.artifact)
        validate(review, "review.schema.json")
        if args.reviewer and review["reviewer"] != args.reviewer:
            raise GateError("unexpected reviewer")
        if review.get("risk_assessment") == "RSK-0":
            print("review reports RSK-0", file=__import__("sys").stderr)
            return 2
        if review["verdict"] != "approve" or review["blockers"] or review["scope_drift"] or review.get("security_concerns"):
            raise GateError("review did not approve cleanly")
    except GateError as exc:
        return fail(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
