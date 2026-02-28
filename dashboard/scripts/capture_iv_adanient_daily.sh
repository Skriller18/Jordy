#!/bin/bash
set -euo pipefail

# Capture near-term ATM IV for ADANIENT from Groww (Python) and store into dashboard DB (Prisma/SQLite).
# Intended to be run after market close.

REPO_ROOT="/Users/admin/Desktop/subhash/Jordy"
DASH="$REPO_ROOT/dashboard"

cd "$REPO_ROOT"

json=$(python scripts/capture_iv_near.py --symbol ADANIENT)

iv=$(python - <<'PY'
import json,sys
obj=json.loads(sys.argv[1])
iv=obj.get('iv')
print('' if iv is None else iv)
PY
"$json")

if [[ -z "$iv" ]]; then
  echo "No IV captured (empty strikes/expiry). Payload: $json" >&2
  exit 0
fi

cd "$DASH"
node scripts/upsert_iv_daily.js --json "$(python - <<'PY'
import json,sys
obj=json.loads(sys.argv[1])
obj['source']='groww_chain'
print(json.dumps(obj))
PY
"$json")"
