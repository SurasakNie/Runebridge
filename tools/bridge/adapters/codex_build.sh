#!/usr/bin/env bash
# shellcheck source=common.sh disable=SC1091
source "$(dirname "$0")/common.sh"
cat >"$TASK_DIR/EDIT_CODEX.md" <<EOF
---
task_id: $TASK_ID
tool: codex
files_changed: []
tests:
  - dry-run contract test
dry_run: true
---
# Implementation Summary

Deterministic mock Codex build for $TASK_ID.
EOF
: >"$TASK_DIR/CHANGES.diff"
