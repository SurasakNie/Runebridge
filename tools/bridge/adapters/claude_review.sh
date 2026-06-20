#!/usr/bin/env bash
# shellcheck source=common.sh disable=SC1091
source "$(dirname "$0")/common.sh"
cat >"$TASK_DIR/REVIEW_CLAUDE.json" <<EOF
{"task_id":"$TASK_ID","reviewer":"claude","verdict":"approve","blockers":[],"scope_drift":false,"risk_assessment":"RSK-2","human_review_required":true,"notes":[]}
EOF
