from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from tools.bridge.live.run_isolated_validation import (
    BLOCKED_COMMANDS_SET,
    AdapterSpec,
    ValidationConfig,
    ValidationError,
    _normalize_command_name,
    poll_blocked_descendants,
    run_isolated_validation,
    validate_normalized_result,
)


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/bridge/live/run_isolated_validation.py"
METADATA_GATE = ROOT / "tools/bridge/gates/check_live_metadata.py"
RUN_DATE = "2026-06-21"


def write_fake(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8", newline="\n")
    return path


def spec(script: Path, *args: str) -> AdapterSpec:
    return AdapterSpec(
        command=(str(Path(sys.executable).resolve()), str(script), *args),
        cli_name="fake-cli",
        cli_version="1.0.0",
        authentication_class="test_fixture",
        credentials_available=False,
    )


def config(root: Path, task: str = "P6-FAKE-001", **overrides: object) -> ValidationConfig:
    values: dict[str, object] = {
        "task_id": task,
        "vendor": "claude",
        "role": "planner",
        "approval_id": "P6-APPROVAL-001",
        "run_date": RUN_DATE,
        "artifact_root": root,
        "timeout_seconds": 5,
        "budget_ceiling_usd": 0.10,
        "live": True,
    }
    values.update(overrides)
    return ValidationConfig(**values)  # type: ignore[arg-type]


def test_fake_success_writes_sanitized_valid_evidence(tmp_path: Path) -> None:
    script = write_fake(
        tmp_path / "success.py",
        "import json, os\n"
        "markers = ('API_KEY', 'PASSWORD', 'SECRET', 'TOKEN', 'CREDENTIAL')\n"
        "present = sorted(key for key in os.environ if any(marker in key.upper() for marker in markers))\n"
        "print(json.dumps({'credential_keys': present, 'status': 'ok'}))\n",
    )
    source = {**os.environ, "OPENAI_API_KEY": "not-a-real-secret", "GITHUB_TOKEN": "not-a-real-token"}
    task_dir = run_isolated_validation(
        config(tmp_path / "artifacts"),
        spec(script),
        source_environment=source,
    )
    assert {path.name for path in task_dir.iterdir()} == {
        "BLOCKED_COMMANDS.log",
        "LIVE_RUN_METADATA.json",
        "NORMALIZED_RESULT.json",
    }
    result_bytes = (task_dir / "NORMALIZED_RESULT.json").read_bytes()
    result = json.loads(result_bytes)
    metadata = json.loads((task_dir / "LIVE_RUN_METADATA.json").read_text(encoding="utf-8"))
    assert result == {"credential_keys": [], "status": "ok"}
    assert metadata["approval_id_sha256"] == hashlib.sha256(b"P6-APPROVAL-001").hexdigest()
    assert metadata["result_sha256"] == hashlib.sha256(result_bytes).hexdigest()
    assert metadata["authentication_class"] == "test_fixture"
    assert metadata["credentials_available"] is False
    assert metadata["secret_scan_passed"] is True
    assert (task_dir / "BLOCKED_COMMANDS.log").read_bytes() == b""
    serialized = (task_dir / "LIVE_RUN_METADATA.json").read_text(encoding="utf-8")
    assert "P6-APPROVAL-001" not in serialized
    assert str(tmp_path) not in serialized


@pytest.mark.parametrize("live", (False, True))
def test_public_cli_refuses_without_enabled_adapter(tmp_path: Path, live: bool) -> None:
    artifact_root = tmp_path / "artifacts"
    command = [
        sys.executable,
        str(RUNNER),
        "--task",
        "P6-REFUSE-001",
        "--vendor",
        "claude",
        "--role",
        "planner",
        "--approval-id",
        "P6-APPROVAL-REFUSE",
        "--date",
        RUN_DATE,
        "--artifact-root",
        str(artifact_root),
    ]
    if live:
        command.append("--live")
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, check=False, text=True)
    assert completed.returncode == 2
    assert not artifact_root.exists()


def test_invalid_approval_refuses_before_invocation(tmp_path: Path) -> None:
    marker = tmp_path / "invoked"
    script = write_fake(tmp_path / "marker.py", f"from pathlib import Path\nPath({str(marker)!r}).touch()\n")
    with pytest.raises(ValidationError, match="approval ID"):
        run_isolated_validation(
            config(tmp_path / "artifacts", approval_id="bad approval"),
            spec(script),
        )
    assert not marker.exists()


def test_blocked_child_command_fails_without_evidence(tmp_path: Path) -> None:
    # curl is a fatal (non-tolerated) blocked command: any invocation aborts the
    # run with no evidence. (git is tolerated — see the neutralized test below.)
    script = write_fake(
        tmp_path / "blocked.py",
        "import json, subprocess\n"
        "subprocess.run(['bash', '-c', 'curl --version'], check=False)\n"
        "print(json.dumps({'status': 'ignored-child-failure'}))\n",
    )
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match="blocked command"):
        run_isolated_validation(config(artifact_root), spec(script))
    assert not artifact_root.exists()


def test_tolerated_git_is_recorded_not_fatal(tmp_path: Path) -> None:
    # git is neutralized by the shim (exits 99, never runs) but is tolerated: the
    # run succeeds, records the attempt in BLOCKED_COMMANDS.log and the metadata
    # neutralized_* fields, and keeps blocked_command_count (fatal count) at 0.
    script = write_fake(
        tmp_path / "git_user.py",
        "import json, subprocess\n"
        "subprocess.run(['bash', '-c', 'git --version'], check=False)\n"
        "print(json.dumps({'status': 'ok'}))\n",
    )
    task_dir = run_isolated_validation(config(tmp_path / "artifacts"), spec(script))
    metadata = json.loads((task_dir / "LIVE_RUN_METADATA.json").read_text(encoding="utf-8"))
    assert metadata["blocked_command_count"] == 0
    assert metadata["neutralized_command_count"] >= 1
    assert metadata["neutralized_commands"] == ["git"]
    blocked_log = (task_dir / "BLOCKED_COMMANDS.log").read_text(encoding="utf-8")
    assert "git" in blocked_log


@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        ("git", "git"),
        ("git.exe", "git"),
        ("GIT.EXE", "git"),
        ("curl.cmd", "curl"),
        ("antigravity-ide", "antigravity-ide"),
        ("antigravity-ide.exe", "antigravity-ide"),
    ),
)
def test_normalize_command_name_strips_extension_and_case(raw: str, expected: str) -> None:
    assert _normalize_command_name(raw) == expected


def test_poll_blocked_descendants_kills_and_logs_absolute_path_invocation(tmp_path: Path) -> None:
    # Reproduces the gap PATH shims cannot cover: a child process exec'd by
    # absolute path never resolves through PATH, so create_command_shims alone
    # would miss it. Live Codex CLI runs were observed spawning subprocesses
    # this way (e.g. an absolute path to powershell.exe) as ordinary agent
    # behavior, so a blocked vendor CLI invoked the same way must still be caught.
    fake_bin_dir = tmp_path / "fake_bin"
    fake_bin_dir.mkdir()
    if os.name == "nt":
        # timeout.exe refuses to run without an attached console; ping.exe has
        # no such quirk and is present on every Windows install, so it is used
        # as a "sleep ~5s" stand-in for the renamed fake binary.
        fake_name = "git.exe"
        source = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "PING.EXE"
        args = ["-n", "6", "127.0.0.1"]
    else:
        fake_name = "git"
        source = Path(shutil.which("sleep") or "/bin/sleep")
        args = ["5"]
    fake_git = fake_bin_dir / fake_name
    shutil.copyfile(source, fake_git)
    fake_git.chmod(0o755)
    child = subprocess.Popen([str(fake_git), *args])
    log_path = tmp_path / "blocked-commands.log"
    log_path.touch()
    stop_event = threading.Event()
    monitor = threading.Thread(
        target=poll_blocked_descendants, args=(os.getpid(), stop_event, log_path, BLOCKED_COMMANDS_SET, 0.05)
    )
    monitor.start()
    try:
        child.wait(timeout=5)
    finally:
        stop_event.set()
        monitor.join(timeout=5)
    assert child.returncode != 0
    logged = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line]
    assert logged == ["git"]


def test_poll_blocked_descendants_leaves_excluded_self_name_alone(tmp_path: Path) -> None:
    # Regression: a vendor CLI legitimately spawns helper children that share
    # its own name (codex.cmd -> codex.exe -> codex helpers). The monitor's
    # watch_set must exclude the vendor's own name, or it kills the real run
    # (the first live Codex run exited 15 for exactly this reason). Here "git"
    # stands in for the vendor's own name and is excluded from watch_set, so the
    # child must survive and nothing must be logged.
    fake_bin_dir = tmp_path / "fake_bin"
    fake_bin_dir.mkdir()
    if os.name == "nt":
        fake_name = "git.exe"
        source = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "PING.EXE"
        args = ["-n", "3", "127.0.0.1"]
    else:
        fake_name = "git"
        source = Path(shutil.which("sleep") or "/bin/sleep")
        args = ["2"]
    fake_git = fake_bin_dir / fake_name
    shutil.copyfile(source, fake_git)
    fake_git.chmod(0o755)
    child = subprocess.Popen([str(fake_git), *args])
    log_path = tmp_path / "blocked-commands.log"
    log_path.touch()
    stop_event = threading.Event()
    watch_set = BLOCKED_COMMANDS_SET - {"git"}  # exclude the "vendor's own" name
    monitor = threading.Thread(
        target=poll_blocked_descendants, args=(os.getpid(), stop_event, log_path, watch_set, 0.05)
    )
    monitor.start()
    try:
        rc = child.wait(timeout=10)
    finally:
        stop_event.set()
        monitor.join(timeout=5)
    assert rc == 0  # not killed
    assert log_path.read_text(encoding="utf-8").strip() == ""


@pytest.mark.skipif(os.name == "nt", reason="renamed-binary trick is POSIX-specific; verify on Windows via manual PC probe")
def test_absolute_path_blocked_command_fails_run_without_evidence(tmp_path: Path) -> None:
    # Uses curl (a fatal, non-tolerated blocked command) invoked by absolute path
    # so the process-tree monitor — not the PATH shim — is what catches it.
    fake_bin_dir = tmp_path / "fake_bin"
    fake_bin_dir.mkdir()
    fake_curl = fake_bin_dir / "curl"
    shutil.copyfile(shutil.which("sleep") or "/bin/sleep", fake_curl)
    fake_curl.chmod(0o755)
    script = write_fake(
        tmp_path / "absolute_blocked.py",
        "import json, subprocess\n"
        f"subprocess.run([{str(fake_curl)!r}, '2'], check=False)\n"
        "print(json.dumps({'status': 'ignored-child-failure'}))\n",
    )
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match="blocked command"):
        run_isolated_validation(config(artifact_root), spec(script))
    assert not artifact_root.exists()


def test_secret_output_is_rejected(tmp_path: Path) -> None:
    script = write_fake(
        tmp_path / "secret.py",
        "import json\nprint(json.dumps({'password': 'supersecretvalue123'}))\n",
    )
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match="check_no_secrets"):
        run_isolated_validation(config(artifact_root), spec(script))
    assert not artifact_root.exists()


def test_timeout_kills_run_without_evidence(tmp_path: Path) -> None:
    script = write_fake(tmp_path / "timeout.py", "import time\ntime.sleep(5)\n")
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match="timeout"):
        run_isolated_validation(
            config(artifact_root, timeout_seconds=1),
            spec(script),
        )
    assert not artifact_root.exists()


def test_invalid_json_is_rejected(tmp_path: Path) -> None:
    script = write_fake(tmp_path / "invalid.py", "print('not json')\n")
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match="not one JSON"):
        run_isolated_validation(config(artifact_root), spec(script))
    assert not artifact_root.exists()


def test_unexpected_workspace_write_is_rejected(tmp_path: Path) -> None:
    script = write_fake(
        tmp_path / "write.py",
        "import json\nfrom pathlib import Path\nPath('unexpected.txt').write_text('x')\n"
        "print(json.dumps({'status': 'ok'}))\n",
    )
    artifact_root = tmp_path / "artifacts"
    with pytest.raises(ValidationError, match="no-write scope"):
        run_isolated_validation(config(artifact_root), spec(script))
    assert not artifact_root.exists()


def test_existing_task_is_not_modified(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts"
    task_dir = artifact_root / "P6-FAKE-001"
    task_dir.mkdir(parents=True)
    marker = task_dir / "marker.txt"
    marker.write_text("original", encoding="utf-8")
    script = write_fake(tmp_path / "success.py", "import json\nprint(json.dumps({'status': 'ok'}))\n")
    with pytest.raises(ValidationError, match="already exists"):
        run_isolated_validation(config(artifact_root), spec(script))
    assert marker.read_text(encoding="utf-8") == "original"


def test_metadata_gate_rejects_fixture_claiming_credentials(tmp_path: Path) -> None:
    script = write_fake(tmp_path / "success.py", "import json\nprint(json.dumps({'status': 'ok'}))\n")
    task_dir = run_isolated_validation(config(tmp_path / "artifacts"), spec(script))
    metadata_path = task_dir / "LIVE_RUN_METADATA.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["credentials_available"] = True
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, str(METADATA_GATE), str(metadata_path)],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )
    assert completed.returncode == 1


@pytest.mark.parametrize(
    "value",
    (
        {"session_id": "abc123"},
        {"detail": "C:\\Users\\Example\\workspace"},
        {"detail": "see C:\\Users\\Example\\workspace"},
        {"detail": "/home/example/workspace"},
        {"detail": "see /home/example/workspace"},
        {"detail": "see \\Users\\Example\\workspace"},
        {"detail": "person@example.com"},
        {"person@example.com": "value"},
        {"transcript": "raw output"},
    ),
)
def test_normalized_result_rejects_sensitive_content(value: object) -> None:
    with pytest.raises(ValidationError):
        validate_normalized_result(value)
