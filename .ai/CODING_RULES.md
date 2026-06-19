# Coding Rules

All AI agents follow these rules in this repository.

## General

- Make small, clear changes. Do not rewrite unrelated files.
- Do not remove unused features or code without explicit instruction.
- Prefer simple, maintainable code over clever abstractions.
- Use clear, descriptive variable and function names.
- Add comments only where the WHY is non-obvious.
- Write small functions with a single responsibility.
- Run available tests before handing off.
- Work on a feature branch. Never push to `main`.

## Bash

- Always start scripts with `set -euo pipefail`.
- Quote all variable expansions: `"$VAR"` not `$VAR`.
- Use `[[ ]]` for conditionals, not `[ ]`.
- Run shellcheck before committing.

## Python

- Target Python 3.11+.
- Use type hints on function signatures.
- Format with `ruff` or `black`.
- Use `pathlib.Path` for file paths, not string concatenation.
- Exit with explicit codes: 0 (pass), 1 (fail), 2 (RSK-0 halt).

## JSON artifacts

- Use 2-space indentation.
- Validate against the schema in `schemas/` before writing.
- Gates reject invalid JSON — produce valid JSON or fail explicitly.

## Artifact files

- `TASK.md`, `PLAN.md`, `EDIT_*.md` — Markdown with YAML front matter.
- `VERIFY.json`, `REVIEW_*.json` — strict JSON, no prose outside the schema.
