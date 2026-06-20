from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft7Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[3]


class GateError(ValueError):
    pass


def normalize_yaml(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: normalize_yaml(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_yaml(item) for item in value]
    return value


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GateError(f"{path} must contain a JSON object")
    return normalize_yaml(value)


def read_front_matter(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise GateError(f"cannot read {path}: {exc}") from exc
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise GateError(f"{path} must start with YAML front matter")
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as exc:
        raise GateError(f"{path} has unterminated YAML front matter") from exc
    try:
        value = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as exc:
        raise GateError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GateError(f"{path} front matter must be a mapping")
    return normalize_yaml(value)


def validate(value: dict[str, Any], schema_name: str) -> None:
    schema = read_json(ROOT / "schemas" / schema_name)
    errors = sorted(
        Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        details = "; ".join(error.message for error in errors)
        raise GateError(f"schema validation failed: {details}")


def fail(exc: Exception) -> int:
    print(str(exc), file=sys.stderr)
    return 1
