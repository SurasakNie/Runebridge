from __future__ import annotations

import sys
from pathlib import Path

from common import GateArgumentParser, GateError, fail, read_json, validate


def main() -> int:
    parser = GateArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--reviewer", required=True, choices=("qwen", "claude"))
    args = parser.parse_args()
    try:
        review = read_json(args.artifact)
        validate(review, "review.schema.json")
        if review["reviewer"] != args.reviewer:
            raise GateError("unexpected reviewer")
        # RSK-0 is the pipeline escalation signal and intentionally takes precedence over rejection details.
        if review.get("risk_assessment") == "RSK-0":
            print("review reports RSK-0", file=sys.stderr)
            return 2
        if review["verdict"] != "approve" or review["blockers"] or review["scope_drift"] or review.get("security_concerns"):
            raise GateError("review did not approve cleanly")
    except GateError as exc:
        return fail(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
