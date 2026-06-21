from __future__ import annotations

from pathlib import Path

from common import GateArgumentParser, GateError, fail, read_json, validate


def main() -> int:
    parser = GateArgumentParser()
    parser.add_argument("metadata", type=Path)
    args = parser.parse_args()
    try:
        value = read_json(args.metadata)
        validate(value, "live-run-metadata.schema.json")
        uses_fixture = value["authentication_class"] == "test_fixture"
        if uses_fixture == value["credentials_available"]:
            raise GateError("test fixtures must not claim credentials; live authentication must be available")
    except GateError as exc:
        return fail(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
