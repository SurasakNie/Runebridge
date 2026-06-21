from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[2]
CONDUCTOR = ROOT / "tools/bridge/orchestrate.sh"
SECRET_GATE = ROOT / "tools/bridge/gates/check_no_secrets.py"
TASK_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
MODES = ("safe-default", "qwen-led", "dual-builder")
BLOCKED_COMMANDS = (
    "claude",
    "claude.cmd",
    "codex",
    "codex.cmd",
    "qwen",
    "qwen.cmd",
    "antigravity-ide",
    "antigravity-ide.cmd",
    "git",
    "gh",
    "curl",
    "wget",
)
SENSITIVE_MARKERS = ("API_KEY", "PASSWORD", "SECRET", "TOKEN", "CREDENTIAL")


def bash_path(path: Path) -> str:
    resolved = path.resolve()
    if os.name != "nt":
        return str(resolved)
    drive = resolved.drive.rstrip(":").lower()
    remainder = resolved.as_posix().split(":", 1)[1]
    return f"/{drive}{remainder}"


def guarded_environment(
    source: Mapping[str, str],
    shim_dir: Path,
    log_path: Path,
    *,
    base_path: str | None = None,
    guard_file: Path | None = None,
) -> dict[str, str]:
    environment = {
        key: value
        for key, value in source.items()
        if not any(marker in key.upper() for marker in SENSITIVE_MARKERS)
    }
    environment["PATH"] = ":".join((bash_path(shim_dir), base_path or source.get("PATH", "")))
    environment["RUNEBRIDGE_EXTERNAL_LOG"] = bash_path(log_path)
    if guard_file:
        environment["BASH_ENV"] = bash_path(guard_file)
    environment["DRY_RUN_MODE"] = "true"
    environment["PYTHON"] = str(Path(sys.executable).resolve())
    return environment


def create_shims(directory: Path) -> None:
    body = (
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"${0##*/}\" >> \"${RUNEBRIDGE_EXTERNAL_LOG:?}\"\n"
        "exit 99\n"
    )
    for command in BLOCKED_COMMANDS:
        path = directory / command
        path.write_text(body, encoding="utf-8", newline="\n")
        path.chmod(0o755)


def create_bash_guard(path: Path) -> None:
    lines = [
        '_runebridge_block() { printf \'%s\\n\' "$1" >> "${RUNEBRIDGE_EXTERNAL_LOG:?}"; return 99; }'
    ]
    for command in BLOCKED_COMMANDS:
        lines.append(f"function {command} {{ _runebridge_block {command}; }}")
        lines.append(f"export -f {command}")
    lines.append("export -f _runebridge_block")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--mode", required=True, choices=MODES)
    parser.add_argument("--date", required=True)
    parser.add_argument("--artifact-root", type=Path, default=ROOT / ".bridge")
    args = parser.parse_args()
    if not TASK_ID_PATTERN.fullmatch(args.task):
        parser.error("--task must contain only letters, digits, dot, underscore, or hyphen")
    try:
        date.fromisoformat(args.date)
    except ValueError:
        parser.error("--date must be an ISO date (YYYY-MM-DD)")
    return args


def write_evidence(task_dir: Path, log_source: Path, args: argparse.Namespace, exit_code: int) -> None:
    log_target = task_dir / "EXTERNAL_COMMANDS.log"
    shutil.copyfile(log_source, log_target)
    metadata = {
        "conductor_exit_code": exit_code,
        "credentials_available": False,
        "mode": args.mode,
        "python_executable": str(Path(sys.executable).resolve()),
        "python_version": ".".join(str(part) for part in sys.version_info[:3]),
        "run_date": args.date,
        "task_id": args.task,
    }
    (task_dir / "RUN_METADATA.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    args = parse_args()
    artifact_root = args.artifact_root.resolve()
    task_dir = artifact_root / args.task
    if task_dir.exists():
        print(f"Task directory already exists: {task_dir}", file=sys.stderr)
        return 1

    bash = shutil.which("bash")
    if not bash:
        print("bash is required", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="runebridge-shims-") as temporary:
        temporary_path = Path(temporary)
        shim_dir = temporary_path / "bin"
        shim_dir.mkdir()
        log_path = temporary_path / "external-commands.log"
        log_path.touch()
        guard_file = temporary_path / "guard.sh"
        create_shims(shim_dir)
        create_bash_guard(guard_file)
        resolved_bash_path = subprocess.check_output(
            [bash, "-c", 'printf "%s" "$PATH"'],
            cwd=ROOT,
            env=os.environ,
            text=True,
        )
        environment = guarded_environment(
            os.environ,
            shim_dir,
            log_path,
            base_path=resolved_bash_path,
            guard_file=guard_file,
        )
        environment["RUNEBRIDGE_DATE"] = args.date

        result = subprocess.run(
            [
                bash,
                str(CONDUCTOR),
                "--task",
                args.task,
                "--mode",
                args.mode,
                "--artifact-root",
                str(artifact_root),
            ],
            cwd=ROOT,
            env=environment,
            check=False,
        )
        if not task_dir.is_dir():
            return result.returncode

        write_evidence(task_dir, log_path, args, result.returncode)
        if log_path.stat().st_size:
            print("Blocked external command invocation detected", file=sys.stderr)
            return 1

        evidence_files = sorted(path for path in task_dir.iterdir() if path.is_file())
        secret_result = subprocess.run(
            [sys.executable, str(SECRET_GATE), *(str(path) for path in evidence_files)],
            cwd=ROOT,
            env=environment,
            check=False,
        )
        if secret_result.returncode:
            return secret_result.returncode
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
