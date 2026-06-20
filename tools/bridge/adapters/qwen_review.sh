#!/usr/bin/env bash
# shellcheck source=common.sh disable=SC1091
source "$(dirname "$0")/common.sh"
cat >"$TASK_DIR/REVIEW_QWEN.json" <<EOF
{"task_id":"$TASK_ID","reviewer":"qwen","verdict":"approve","blockers":[],"bugs_found":[],"missing_tests":[],"scope_drift":false,"security_concerns":[],"suggestions":[]}
EOF
