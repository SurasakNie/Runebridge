from __future__ import annotations

import re
from pathlib import Path

from common import GateArgumentParser, GateError, fail


PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|password)['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{12,}"),
)


def main() -> int:
    parser = GateArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    findings: list[str] = []
    for path in args.paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if any(pattern.search(text) for pattern in PATTERNS):
            findings.append(str(path))
    if findings:
        return fail(GateError(f"possible secret detected: {', '.join(findings)}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
