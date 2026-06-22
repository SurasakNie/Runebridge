from __future__ import annotations

from pathlib import Path, PurePosixPath

from common import GateArgumentParser, GateError, fail, read_front_matter, validate


def normalize(path: str) -> str:
    return str(PurePosixPath(path.replace("\\", "/")))


def changed_paths_from_diff(path: Path) -> set[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise GateError(f"cannot read diff {path}: {exc}") from exc
    changed: set[str] = set()
    for line in lines:
        if line.startswith("--- a/") or line.startswith("+++ b/"):
            changed.add(normalize(line[6:].split("\t", 1)[0].split(" ", 1)[0]))
    return changed


def main() -> int:
    parser = GateArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("changed", nargs="*")
    parser.add_argument("--diff", type=Path)
    args = parser.parse_args()
    try:
        plan = read_front_matter(args.plan)
        validate(plan, "plan.schema.json")
    except GateError as exc:
        return fail(exc)
    allowed = {normalize(path) for path in plan["files_to_touch"]}
    changed = {normalize(path) for path in args.changed}
    if args.diff:
        try:
            changed.update(changed_paths_from_diff(args.diff))
        except GateError as exc:
            return fail(exc)
    drift = sorted(changed - allowed)
    if drift:
        return fail(GateError(f"scope drift: {', '.join(drift)}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
