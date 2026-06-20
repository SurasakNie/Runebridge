#!/usr/bin/env bash
# shellcheck source=common.sh disable=SC1091
source "$(dirname "$0")/common.sh"
cat >"$TASK_DIR/PLAN.md" <<EOF
---
task_id: $TASK_ID
planner: qwen
risk_level: RSK-2
files_to_touch:
  - src/example.py
acceptance_criteria:
  - deterministic dry-run artifact is valid
requires_human_approval: false
---
# Plan

Deterministic dry-run plan for $TASK_ID.
EOF
