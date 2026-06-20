#!/usr/bin/env bash
# shellcheck source=common.sh disable=SC1091
source "$(dirname "$0")/common.sh"
cat >"$TASK_DIR/VERIFY.json" <<EOF
{"task_id":"$TASK_ID","verifier":"mock","result":"pass","checks":[{"name":"dry-run","status":"pass","detail":"deterministic mock verification"}],"failing_tests":[],"artifacts":[],"dry_run":true}
EOF
