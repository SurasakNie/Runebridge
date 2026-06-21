from __future__ import annotations

from pathlib import Path

from common import GateArgumentParser, GateError, fail, read_front_matter, validate


def main() -> int:
    parser = GateArgumentParser()
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    try:
        validate(read_front_matter(args.plan), "plan.schema.json")
    except GateError as exc:
        return fail(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
