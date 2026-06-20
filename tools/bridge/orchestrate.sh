#!/usr/bin/env bash

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ADAPTERS="$ROOT/tools/bridge/adapters"
GATES="$ROOT/tools/bridge/gates"
PYTHON="${PYTHON:-python}"
ARTIFACT_ROOT="$ROOT/.bridge"
TASK_ID=""
MODE=""
MAX_RETRIES="${RUNEBRIDGE_MAX_RETRIES:-0}"
COMPLETED=()
FAIL_ONCE_USED=false

usage() {
  echo "Usage: orchestrate.sh --task <id> --mode <safe-default|qwen-led|dual-builder> [--artifact-root <path>]" >&2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --task) TASK_ID="${2:-}"; shift 2 ;;
    --mode) MODE="${2:-}"; shift 2 ;;
    --artifact-root) ARTIFACT_ROOT="${2:-}"; shift 2 ;;
    *) usage; exit 1 ;;
  esac
done

if [[ ! "$TASK_ID" =~ ^[A-Za-z0-9._-]+$ ]] || [[ ! "$MODE" =~ ^(safe-default|qwen-led|dual-builder)$ ]]; then
  usage
  exit 1
fi
if [[ "${DRY_RUN_MODE:-}" != "true" ]]; then
  echo "The Phase 4 conductor is dry-run-only." >&2
  exit 2
fi
if [[ ! "$MAX_RETRIES" =~ ^[0-3]$ ]]; then
  echo "RUNEBRIDGE_MAX_RETRIES must be between 0 and 3." >&2
  exit 1
fi
if [[ -n "${RUNEBRIDGE_FAIL_CODE:-}" && ! "${RUNEBRIDGE_FAIL_CODE}" =~ ^[12]$ ]]; then
  echo "RUNEBRIDGE_FAIL_CODE must be 1 or 2." >&2
  exit 1
fi

TASK_DIR="$ARTIFACT_ROOT/$TASK_ID"
if [[ -e "$TASK_DIR" ]]; then
  echo "Task directory already exists: $TASK_DIR" >&2
  exit 1
fi
mkdir -p "$TASK_DIR"

write_task() {
  local run_date="${RUNEBRIDGE_DATE:-$(date -u +%F)}"
  cat >"$TASK_DIR/TASK.md" <<EOF
---
task_id: $TASK_ID
requester: human
created_at: $run_date
risk_level: RSK-2
mode: $MODE
branch: bridge/$TASK_ID-dry-run
---
# Task

Deterministic Phase 4 dry-run task.
EOF
}

write_report() {
  local status="$1"
  local failed_stage="${2:-none}"
  {
    echo "# Final Report"
    echo
    echo "- task_id: $TASK_ID"
    echo "- mode: $MODE"
    echo "- status: $status"
    echo "- failed_stage: $failed_stage"
    echo "- completed_stages:"
    if [[ ${#COMPLETED[@]} -eq 0 ]]; then
      echo "  - none"
    else
      printf '  - %s\n' "${COMPLETED[@]}"
    fi
  } >"$TASK_DIR/FINAL_REPORT.md"
}

run_stage() {
  local name="$1"
  shift
  local attempt=0
  local code
  while true; do
    if [[ "${RUNEBRIDGE_FAIL_STAGE:-}" == "$name" ]]; then
      code="${RUNEBRIDGE_FAIL_CODE:-1}"
    elif [[ "${RUNEBRIDGE_FAIL_ONCE_STAGE:-}" == "$name" && "$FAIL_ONCE_USED" == "false" ]]; then
      FAIL_ONCE_USED=true
      code=1
    else
      "$@"
      code=$?
    fi
    if [[ $code -eq 0 ]]; then
      COMPLETED+=("$name")
      return 0
    fi
    if [[ $code -eq 2 || $attempt -ge $MAX_RETRIES ]]; then
      return "$code"
    fi
    attempt=$((attempt + 1))
  done
}

halt_after() {
  local code="$1"
  local stage="$2"
  write_report "fail" "$stage"
  echo "Pipeline halted at $stage with exit $code." >&2
  exit "$code"
}

stage() {
  local name="$1"
  shift
  run_stage "$name" "$@" || halt_after $? "$name"
}

write_task
COMPLETED+=("task")

if [[ "$MODE" == "qwen-led" ]]; then
  stage plan "$ADAPTERS/qwen_plan.sh" "$TASK_DIR"
else
  stage plan "$ADAPTERS/claude_plan.sh" "$TASK_DIR"
fi
stage plan_gate "$PYTHON" "$GATES/check_plan.py" "$TASK_DIR/PLAN.md"
stage rsk0_gate "$PYTHON" "$GATES/check_rsk0.py" "$TASK_DIR/PLAN.md"

if [[ "$MODE" == "qwen-led" ]]; then
  stage build_qwen "$ADAPTERS/qwen_build.sh" "$TASK_DIR"
elif [[ "$MODE" == "dual-builder" ]]; then
  stage build_codex "$ADAPTERS/codex_build.sh" "$TASK_DIR"
  stage build_qwen "$ADAPTERS/qwen_build.sh" "$TASK_DIR"
else
  stage build_codex "$ADAPTERS/codex_build.sh" "$TASK_DIR"
fi
stage scope_gate "$PYTHON" "$GATES/check_scope.py" "$TASK_DIR/PLAN.md"

if [[ "$MODE" != "qwen-led" ]]; then
  stage qwen_review "$ADAPTERS/qwen_review.sh" "$TASK_DIR"
  stage qwen_review_gate "$PYTHON" "$GATES/check_review.py" "$TASK_DIR/REVIEW_QWEN.json" --reviewer qwen
fi

stage verify "$ADAPTERS/mock_verify.sh" "$TASK_DIR"
stage verify_gate "$PYTHON" "$GATES/check_verify.py" "$TASK_DIR/VERIFY.json"
stage claude_review "$ADAPTERS/claude_review.sh" "$TASK_DIR"
stage claude_review_gate "$PYTHON" "$GATES/check_review.py" "$TASK_DIR/REVIEW_CLAUDE.json" --reviewer claude
stage secret_gate "$PYTHON" "$GATES/check_no_secrets.py" "$TASK_DIR"/*
stage artifact_gate "$PYTHON" "$GATES/check_artifacts.py" "$TASK_DIR" --mode "$MODE"

write_report "pass"
exit 0
