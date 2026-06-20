#!/usr/bin/env bash

set -euo pipefail

require_dry_run() {
  if [[ "${DRY_RUN_MODE:-}" != "true" ]]; then
    echo "Live adapter execution is disabled until Phase 6." >&2
    exit 2
  fi
}

require_task_dir() {
  if [[ "$#" -ne 1 || ! -d "$1" ]]; then
    echo "Usage: ${0##*/} <task-directory>" >&2
    exit 1
  fi
  TASK_DIR="$1"
  TASK_ID="$(basename "$TASK_DIR")"
  if [[ ! "$TASK_ID" =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "Invalid task identifier: $TASK_ID" >&2
    exit 1
  fi
}

require_dry_run
require_task_dir "$@"
