from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[3]
METADATA_GATE = ROOT / "tools/bridge/gates/check_live_metadata.py"
SECRET_GATE = ROOT / "tools/bridge/gates/check_no_secrets.py"
APPROVAL_LEDGER = ROOT / "tools/bridge/live/approval-ledger.json"
TASK_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
APPROVAL_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,63}$")
ABSOLUTE_PATH_PATTERN = re.compile(r"(?:^|[\s\"'(])(?:[A-Za-z]:[\\/]|\\{1,2}|/)")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
VENDORS = ("claude", "codex", "qwen", "antigravity")
ROLES = ("planner", "builder", "reviewer", "verifier")
RSK_LEVELS = ("RSK-0", "RSK-1", "RSK-2")
LEDGER_ENTRY_KEYS = frozenset(
    {"approval_id", "vendor", "role", "run_date", "approved_by", "rsk_level"}
)
BLOCKED_COMMANDS = ("claude", "codex", "qwen", "antigravity-ide", "git", "gh", "curl", "wget")
BASE_ENVIRONMENT_KEYS = (
    "COMSPEC",
    "LANG",
    "LC_ALL",
    "PATH",
    "PATHEXT",
    "SYSTEMROOT",
    "TERM",
    "WINDIR",
)
FORBIDDEN_RESULT_KEYS = {
    "account_email",
    "chain_of_thought",
    "debug",
    "home_directory",
    "prompt",
    "request_id",
    "session_id",
    "stderr",
    "stdout",
    "transcript",
}


def read_schema(name: str) -> dict[str, object]:
    value = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError("schema must contain a JSON object")
    return value


class ValidationError(RuntimeError):
    pass


class LiveRefusal(ValidationError):
    pass


@dataclass(frozen=True)
class ParsedArtifact:
    name: str
    content: bytes
    normalized: dict[str, object]
    budget_result: str = "not_reported"
    extra_artifacts: tuple[tuple[str, bytes], ...] = ()


ResultParser = Callable[[str, "ValidationConfig"], ParsedArtifact]


@dataclass(frozen=True)
class AdapterSpec:
    command: tuple[str, ...]
    cli_name: str
    cli_version: str
    authentication_class: str
    credentials_available: bool
    model_identifier: str | None = None
    environment_keys: tuple[str, ...] = ()
    result_parser: ResultParser | None = None
    allowed_workspace_files: tuple[str, ...] = ()
    # When True the vendor process runs with a separate cwd (vendor_cwd) rather
    # than workspace. Use for Electron/Node CLIs that spawn background processes
    # (e.g. Qwen's managed-auto-memory-extractor) which would otherwise cause
    # spurious scope failures or WinError 32 cleanup locks.
    use_dedicated_vendor_cwd: bool = False


@dataclass(frozen=True)
class ValidationConfig:
    task_id: str
    vendor: str
    role: str
    approval_id: str
    run_date: str
    artifact_root: Path
    timeout_seconds: int = 30
    budget_ceiling_usd: float = 0.10
    live: bool = False


# P6-001B intentionally enables no real vendor command. Later implementation
# PRs must add reviewed AdapterSpec entries before the CLI can invoke a vendor.
ENABLED_ADAPTERS: dict[tuple[str, str], AdapterSpec] = {}


def bash_path(path: Path) -> str:
    resolved = path.resolve()
    if os.name != "nt":
        return str(resolved)
    drive = resolved.drive.rstrip(":").lower()
    remainder = resolved.as_posix().split(":", 1)[1]
    return f"/{drive}{remainder}"


def validate_config(config: ValidationConfig) -> None:
    if not config.live:
        raise LiveRefusal("live execution requires the explicit --live flag")
    if not TASK_ID_PATTERN.fullmatch(config.task_id):
        raise ValidationError("task ID must contain only letters, digits, dot, underscore, or hyphen")
    if not APPROVAL_ID_PATTERN.fullmatch(config.approval_id):
        raise ValidationError("approval ID must be 3-64 safe identifier characters")
    if config.vendor not in VENDORS:
        raise ValidationError(f"unsupported vendor: {config.vendor}")
    if config.role not in ROLES:
        raise ValidationError(f"unsupported role: {config.role}")
    try:
        date.fromisoformat(config.run_date)
    except ValueError as exc:
        raise ValidationError("run date must use YYYY-MM-DD") from exc
    if not 1 <= config.timeout_seconds <= 300:
        raise ValidationError("timeout must be between 1 and 300 seconds")
    if not math.isfinite(config.budget_ceiling_usd) or not 0 < config.budget_ceiling_usd <= 10:
        raise ValidationError("budget ceiling must be greater than 0 and no more than USD 10")
    if (config.artifact_root.resolve() / config.task_id).exists():
        raise ValidationError("task directory already exists")


def validate_adapter(spec: AdapterSpec) -> None:
    if not spec.command:
        raise ValidationError("adapter command is empty")
    executable = Path(spec.command[0])
    if not executable.is_absolute() or not executable.is_file():
        raise ValidationError("adapter command must start with an existing absolute executable path")
    if not spec.cli_name or not spec.cli_version:
        raise ValidationError("adapter CLI name and version are required")
    if spec.authentication_class not in {"interactive_session", "environment_secret", "test_fixture"}:
        raise ValidationError("unsupported authentication class")
    if spec.authentication_class == "test_fixture" and spec.credentials_available:
        raise ValidationError("test fixtures must not claim credentials")
    if spec.authentication_class != "test_fixture" and not spec.credentials_available:
        raise ValidationError("live authentication must be available")


def validate_ledger_entry(entry: object) -> dict[str, str]:
    if not isinstance(entry, dict) or set(entry) != set(LEDGER_ENTRY_KEYS):
        raise ValidationError("approval ledger entry has unexpected or missing keys")
    if any(not isinstance(value, str) for value in entry.values()):
        raise ValidationError("approval ledger entry fields must be strings")
    if not APPROVAL_ID_PATTERN.fullmatch(entry["approval_id"]):
        raise ValidationError("approval ledger entry has an invalid approval_id")
    if entry["vendor"] not in VENDORS:
        raise ValidationError("approval ledger entry has an unsupported vendor")
    if entry["role"] not in ROLES:
        raise ValidationError("approval ledger entry has an unsupported role")
    try:
        date.fromisoformat(entry["run_date"])
    except ValueError as exc:
        raise ValidationError("approval ledger entry run_date must use YYYY-MM-DD") from exc
    if not entry["approved_by"]:
        raise ValidationError("approval ledger entry approved_by must be non-empty")
    if entry["rsk_level"] not in RSK_LEVELS:
        raise ValidationError("approval ledger entry has an invalid rsk_level")
    return entry


def load_approval_ledger(path: Path) -> list[dict[str, str]]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValidationError("approval ledger is missing or unreadable") from exc
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError("approval ledger is not valid JSON") from exc
    if not isinstance(document, dict) or set(document) != {"entries"}:
        raise ValidationError("approval ledger must be an object with only an entries key")
    if not isinstance(document["entries"], list):
        raise ValidationError("approval ledger entries must be a list")
    return [validate_ledger_entry(entry) for entry in document["entries"]]


def assert_approved(config: ValidationConfig, ledger: Sequence[Mapping[str, str]]) -> None:
    for entry in ledger:
        if (
            entry["approval_id"] == config.approval_id
            and entry["vendor"] == config.vendor
            and entry["role"] == config.role
            and entry["run_date"] == config.run_date
        ):
            return
    raise ValidationError(
        "approval_id is not approved in the ledger for this vendor, role, and date"
    )


def create_bash_guard(path: Path) -> None:
    lines = [
        '_runebridge_block() { printf \'%s\\n\' "$1" >> "${RUNEBRIDGE_EXTERNAL_LOG:?}"; return 99; }'
    ]
    for command in BLOCKED_COMMANDS:
        lines.append(f"function {command} {{ _runebridge_block {command}; }}")
        lines.append(f"export -f {command}")
    lines.append("export -f _runebridge_block")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def create_command_shims(directory: Path) -> None:
    for command in BLOCKED_COMMANDS:
        if os.name == "nt":
            path = directory / f"{command}.cmd"
            path.write_text(
                "@echo off\r\n"
                f'>>"%RUNEBRIDGE_EXTERNAL_LOG_NATIVE%" echo {command}\r\n'
                "exit /b 99\r\n",
                encoding="utf-8",
                newline="",
            )
        else:
            path = directory / command
            path.write_text(
                "#!/usr/bin/env bash\n"
                f'printf \'%s\\n\' "{command}" >> "${{RUNEBRIDGE_EXTERNAL_LOG:?}}"\n'
                "exit 99\n",
                encoding="utf-8",
                newline="\n",
            )
            path.chmod(0o755)


def build_environment(
    source: Mapping[str, str],
    spec: AdapterSpec,
    shim_dir: Path,
    log_path: Path,
    guard_file: Path,
    temporary_path: Path,
) -> dict[str, str]:
    allowed = set(BASE_ENVIRONMENT_KEYS) | {key.upper() for key in spec.environment_keys}
    environment = {key: value for key, value in source.items() if key.upper() in allowed}
    environment["PATH"] = os.pathsep.join((str(shim_dir.resolve()), source.get("PATH", "")))
    environment["BASH_ENV"] = bash_path(guard_file)
    environment["RUNEBRIDGE_EXTERNAL_LOG"] = bash_path(log_path)
    environment["RUNEBRIDGE_EXTERNAL_LOG_NATIVE"] = str(log_path.resolve())
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONUTF8"] = "1"
    for key in ("TEMP", "TMP", "TMPDIR"):
        environment[key] = str(temporary_path.resolve())
    return environment


def terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            check=False,
            text=True,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def _drain_pipe(pipe: object, chunks: list[bytes]) -> None:
    """Read a binary pipe to EOF, tolerating closure from another thread."""
    try:
        while True:
            chunk = pipe.read(65536)  # type: ignore[attr-defined]
            if not chunk:
                break
            chunks.append(chunk)
    except OSError:
        pass


def invoke(
    command: Sequence[str],
    workspace: Path,
    environment: Mapping[str, str],
    timeout_seconds: int,
) -> tuple[int, str, str]:
    process_options: dict[str, object] = {}
    if os.name == "nt":
        process_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        process_options["start_new_session"] = True
    process = subprocess.Popen(
        list(command),
        cwd=workspace,
        env=dict(environment),
        stdout=subprocess.PIPE,
        # stderr is captured for diagnostics only; it is never written as durable
        # evidence. A daemon reader (like stdout) prevents child processes that
        # inherit the pipe handle on Windows from blocking the main thread.
        stderr=subprocess.PIPE,
        text=False,
        **process_options,
    )
    # Read stdout/stderr in daemon threads so that child processes which inherit
    # the pipe handles (e.g. Qwen's managed-auto-memory-extractor on Windows)
    # cannot block the main thread indefinitely after the vendor process exits.
    stdout_chunks: list[bytes] = []
    stderr_chunks: list[bytes] = []
    out_reader = threading.Thread(target=_drain_pipe, args=(process.stdout, stdout_chunks), daemon=True)
    err_reader = threading.Thread(target=_drain_pipe, args=(process.stderr, stderr_chunks), daemon=True)
    out_reader.start()
    err_reader.start()
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        terminate_process_tree(process)
        raise ValidationError("vendor command exceeded the approved timeout") from exc
    finally:
        # Close the read ends so the reader threads unblock even if child
        # processes still hold the write ends open.
        for stream in (process.stdout, process.stderr):
            try:
                if stream is not None:
                    stream.close()
            except OSError:
                pass
    out_reader.join(timeout=5)
    err_reader.join(timeout=5)
    stdout = b"".join(stdout_chunks).decode("utf-8", errors="replace")
    stderr = b"".join(stderr_chunks).decode("utf-8", errors="replace")
    return process.returncode, stdout, stderr


def parse_result(stdout: str) -> dict[str, object]:
    try:
        value = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ValidationError("vendor stdout is not one JSON document") from exc
    if not isinstance(value, dict):
        raise ValidationError("vendor stdout must contain a JSON object")
    validate_normalized_result(value)
    return value


def parse_generic_artifact(stdout: str, _config: ValidationConfig) -> ParsedArtifact:
    normalized = parse_result(stdout)
    content = (json.dumps(normalized, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return ParsedArtifact("NORMALIZED_RESULT.json", content, normalized)


def validate_normalized_result(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = key.lower().replace("-", "_")
            if normalized_key in FORBIDDEN_RESULT_KEYS:
                raise ValidationError("normalized result contains a forbidden sensitive field")
            if ABSOLUTE_PATH_PATTERN.search(key) or EMAIL_PATTERN.search(key):
                raise ValidationError("normalized result contains sensitive content in a field name")
            validate_normalized_result(item)
    elif isinstance(value, list):
        for item in value:
            validate_normalized_result(item)
    elif isinstance(value, str):
        if ABSOLUTE_PATH_PATTERN.search(value):
            raise ValidationError("normalized result contains an absolute path")
        if EMAIL_PATTERN.search(value):
            raise ValidationError("normalized result contains an email address")


def workspace_files(workspace: Path) -> list[str]:
    return [path.relative_to(workspace).as_posix() for path in sorted(workspace.rglob("*")) if path.is_file()]


def validate_workspace_scope(workspace: Path, allowed_files: Sequence[str]) -> None:
    actual = set(workspace_files(workspace))
    allowed = set(allowed_files)
    if not allowed:
        if actual:
            raise ValidationError("vendor command wrote outside the approved no-write scope")
        return
    invalid_allowed = [
        path
        for path in allowed
        if Path(path).is_absolute() or ".." in Path(path).parts or Path(path).as_posix() != path
    ]
    if invalid_allowed:
        raise ValidationError("adapter declared an invalid workspace scope")
    drift = sorted(actual - allowed)
    missing = sorted(allowed - actual)
    if drift:
        raise ValidationError("vendor command wrote outside the approved workspace scope")
    if missing:
        raise ValidationError("vendor command did not produce the approved workspace file")


def write_json(path: Path, value: object) -> bytes:
    content = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(content)
    return content


def run_gate(gate: Path, paths: Sequence[Path], environment: Mapping[str, str]) -> None:
    result = subprocess.run(
        [sys.executable, str(gate), *(str(path) for path in paths)],
        cwd=ROOT,
        env=dict(environment),
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode:
        raise ValidationError(f"{gate.name} rejected candidate evidence")


def publish_candidate(candidate: Path, artifact_root: Path, task_id: str) -> Path:
    artifact_root.mkdir(parents=True, exist_ok=True)
    task_dir = artifact_root / task_id
    if task_dir.exists():
        raise ValidationError("task directory already exists")
    staging_dir = Path(tempfile.mkdtemp(prefix=f".{task_id}.staging-", dir=artifact_root))
    try:
        shutil.copytree(candidate, staging_dir, dirs_exist_ok=True)
        if task_dir.exists():
            raise ValidationError("task directory appeared during publication")
        staging_dir.replace(task_dir)
    except (OSError, ValidationError) as exc:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        raise ValidationError("could not publish candidate evidence") from exc
    return task_dir


def run_isolated_validation(
    config: ValidationConfig,
    spec: AdapterSpec,
    *,
    source_environment: Mapping[str, str] | None = None,
    ledger_path: Path | None = None,
) -> Path:
    validate_config(config)
    validate_adapter(spec)
    # Real credentialed runs must be bound to an approved ledger entry before any
    # vendor invocation. Test fixtures declare no credentials and are exempt.
    if spec.authentication_class != "test_fixture":
        ledger = load_approval_ledger(APPROVAL_LEDGER if ledger_path is None else ledger_path)
        assert_approved(config, ledger)
    artifact_root = config.artifact_root.resolve()
    temporary_base = Path(tempfile.gettempdir()).resolve()
    if temporary_base == ROOT or ROOT in temporary_base.parents:
        raise ValidationError("raw temporary storage must be outside the repository")
    with tempfile.TemporaryDirectory(prefix="runebridge-live-", dir=temporary_base) as temporary:
        temporary_path = Path(temporary)
        workspace = temporary_path / "workspace"
        shim_dir = temporary_path / "guards"
        candidate = temporary_path / "candidate"
        workspace.mkdir()
        shim_dir.mkdir()
        candidate.mkdir()
        # For adapters that opt in, use a separate vendor_cwd so that background
        # processes (e.g. Qwen's managed-auto-memory-extractor) can write temp
        # files to their cwd without causing spurious workspace scope failures or
        # WinError 32 cleanup locks.  Other adapters (e.g. Codex builder) keep
        # workspace as their cwd so file output goes to the scope-checked area.
        if spec.use_dedicated_vendor_cwd:
            vendor_cwd = temporary_path / "vendor_cwd"
            vendor_cwd.mkdir()
        else:
            vendor_cwd = workspace
        log_path = temporary_path / "blocked-commands.log"
        log_path.touch()
        guard_file = temporary_path / "bash-guard.sh"
        create_command_shims(shim_dir)
        create_bash_guard(guard_file)
        environment = build_environment(
            os.environ if source_environment is None else source_environment,
            spec,
            shim_dir,
            log_path,
            guard_file,
            temporary_path,
        )
        exit_code, stdout, stderr = invoke(spec.command, vendor_cwd, environment, config.timeout_seconds)
        if exit_code:
            # stderr/stdout are transient diagnostics for the operator console
            # only; they are never persisted as durable evidence. Surface the
            # tail so large init events do not hide the final result event.
            detail = " ".join((stderr or stdout).split())[-800:]
            raise ValidationError(
                f"vendor command failed with exit code {exit_code}: {detail}"
                if detail
                else f"vendor command failed with exit code {exit_code}"
            )
        blocked_commands = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line]
        if blocked_commands:
            raise ValidationError("blocked command invocation detected")
        validate_workspace_scope(workspace, spec.allowed_workspace_files)
        parsed = (spec.result_parser or parse_generic_artifact)(stdout, config)
        validate_normalized_result(parsed.normalized)
        artifacts = ((parsed.name, parsed.content), *parsed.extra_artifacts)
        artifact_names: set[str] = set()
        artifact_sha256s: dict[str, str] = {}
        for name, content in artifacts:
            if Path(name).name != name or not name:
                raise ValidationError("adapter returned an invalid artifact name")
            if not isinstance(content, bytes):
                raise ValidationError("adapter returned non-byte artifact content")
            if name in artifact_names:
                raise ValidationError("adapter returned a duplicate artifact name")
            artifact_names.add(name)
            artifact_sha256s[name] = hashlib.sha256(content).hexdigest()
            (candidate / name).write_bytes(content)
        shutil.copyfile(log_path, candidate / "BLOCKED_COMMANDS.log")
        # P6-001B measures generic JSON/privacy parsing and a no-write workspace.
        # Role-specific adapters must measure their artifact schema before registration.
        metadata = {
            "approval_id_sha256": hashlib.sha256(config.approval_id.encode("utf-8")).hexdigest(),
            "artifact_sha256s": artifact_sha256s,
            "attempt_count": 1,
            "authentication_class": spec.authentication_class,
            "blocked_command_count": 0,
            "budget_ceiling_usd": config.budget_ceiling_usd,
            # Fixtures record the approved ceiling only; vendor adapters must enforce it.
            "budget_result": parsed.budget_result,
            "cli_name": spec.cli_name,
            "cli_version": spec.cli_version,
            "credentials_available": spec.credentials_available,
            "execution": "live",
            "exit_code": 0,
            "model_identifier": spec.model_identifier,
            "result_sha256": hashlib.sha256(parsed.content).hexdigest(),
            "role": config.role,
            "run_date": config.run_date,
            "schema_valid": True,
            "scope_valid": True,
            "secret_scan_passed": False,
            "task_id": config.task_id,
            "timeout_seconds": config.timeout_seconds,
            "vendor": config.vendor,
        }
        metadata_path = candidate / "LIVE_RUN_METADATA.json"
        write_json(metadata_path, metadata)
        evidence_paths = sorted(path for path in candidate.iterdir() if path.is_file())
        run_gate(SECRET_GATE, evidence_paths, environment)
        metadata["secret_scan_passed"] = True
        write_json(metadata_path, metadata)
        run_gate(METADATA_GATE, [metadata_path], environment)
        run_gate(SECRET_GATE, evidence_paths, environment)
        return publish_candidate(candidate, artifact_root, config.task_id)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--vendor", required=True, choices=VENDORS)
    parser.add_argument("--role", required=True, choices=ROLES)
    parser.add_argument("--approval-id", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--artifact-root", type=Path, default=ROOT / ".bridge")
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--budget-ceiling-usd", type=float, default=0.10)
    parser.add_argument("--live", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = ValidationConfig(
        task_id=args.task,
        vendor=args.vendor,
        role=args.role,
        approval_id=args.approval_id,
        run_date=args.date,
        artifact_root=args.artifact_root,
        timeout_seconds=args.timeout_seconds,
        budget_ceiling_usd=args.budget_ceiling_usd,
        live=args.live,
    )
    try:
        validate_config(config)
        spec = ENABLED_ADAPTERS.get((config.vendor, config.role))
        if spec is None:
            raise LiveRefusal("no live vendor adapter is enabled in P6-001B")
        run_isolated_validation(config, spec)
    except LiveRefusal as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
