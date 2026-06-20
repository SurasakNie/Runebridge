#!/usr/bin/env bash
# shellcheck source=common.sh disable=SC1091
source "$(dirname "$0")/common.sh"
cat >"$TASK_DIR/EDIT_QWEN.md" <<EOF
---
task_id: $TASK_ID
tool: qwen
files_changed: []
tests:
  - dry-run contract test
dry_run: true
---
# Implementation Summary

Deterministic mock Qwen build for $TASK_ID.
EOF
: >"$TASK_DIR/CHANGES.diff"
