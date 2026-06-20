from __future__ import annotations

import argparse
from pathlib import Path

from common import GateError, fail, read_json, validate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    try:
        artifact = read_json(args.artifact)
        validate(artifact, "verify.schema.json")
        if artifact["result"] != "pass" or any(check["status"] != "pass" for check in artifact["checks"]):
            raise GateError("verification did not pass")
    except GateError as exc:
        return fail(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
