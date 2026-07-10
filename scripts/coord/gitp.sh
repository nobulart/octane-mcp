#!/usr/bin/env bash
# scripts/coord/gitp.sh — canonical push for the octanex-mcp coordination loop.
#
# Usage: bash scripts/coord/gitp.sh ["commit message"]   (stages nothing; expects
#        a clean commit ready, OR pass a message to commit all tracked changes)
#
# Does: git push origin main, then notifies the peer instance instantly via
# coord/notify.sh (SSH fast-path + local outbox). Deterministic alternative to
# relying on git's post-receive hook (which does not fire through some git paths).
#
# GUARD: before pushing, checks the peer's recent 'intent' messages (files they
# declared they'd touch). If we're about to push a file the peer intends to edit,
# it PAUSES and warns — so we coordinate instead of creating a rebase conflict.
#
# Non-fatal: a notify failure never breaks the push.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/../.." && pwd)"
COORD_DIR="${COORD_DIR:-$HOME/hermes-bridge}"

cd "$REPO" || { echo "gitp: cannot cd to repo"; exit 1; }

# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

MSG="${1:-}"
if [ -n "$MSG" ]; then
  # commit all currently-staged + tracked-modified; leave untracked scratch alone
  git add -u
  git commit -q -m "$MSG" || { echo "gitp: commit failed (nothing to commit?)"; exit 1; }
fi

# range we are about to push
OLD="$(git rev-parse origin/main 2>/dev/null)"
NEW="$(git rev-parse HEAD 2>/dev/null)"

if [ "$OLD" = "$NEW" ]; then
  echo "gitp: already up to date (nothing to push)"
  exit 0
fi

# ---- peer-intent overlap guard --------------------------------------------
# Pull peer's recent intents from our inbox (they arrive via SSH fast-path or the
# 15-min sync). Compare against the files in OLD..NEW. On overlap, pause.
MY_FILES="$(git diff --name-only "$OLD" "$NEW" 2>/dev/null | sort -u)"
if [ -n "$MY_FILES" ] && [ -f "$COORD_DIR/inbox.jsonl" ]; then
  PEER="$COORD_PEER_ID"
  OVERLAP="$(python3 - "$COORD_DIR/inbox.jsonl" "$PEER" "$MY_FILES" <<'PY'
import json,sys,time
from datetime import datetime,timezone
def parse_ts(ts):
    try:
        return datetime.strptime(ts,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    except: return 0.0
path,peer,myfiles=sys.argv[1],sys.argv[2],set(sys.argv[3].split("\n"))
hits=[]
cutoff=time.time()-1800  # last 30 min
try:
    lines=open(path).read().splitlines()
except FileNotFoundError:
    lines=[]
for ln in lines:
    ln=ln.strip()
    if not ln: continue
    try: d=json.loads(ln)
    except: continue
    if d.get("from")!=peer or d.get("type")!="intent": continue
    t=parse_ts(d.get("ts",""))
    if t<cutoff: continue
    for f in d.get("files",[]):
        if f in myfiles: hits.append((f,d.get("ts","")))
if hits:
    for f,ts in sorted(set(hits)):
        print(f"  - {f}  (peer intent @ {ts})")
PY
)"
  if [ -n "$OVERLAP" ]; then
    echo "gitp: PEER-INTENT OVERLAP — the peer declared they intend to edit:"
    echo "$OVERLAP"
    echo "gitp: aborting push. Coordinate first (split the file, or wait for peer's 'done')."
    exit 2
  fi
fi
# ---------------------------------------------------------------------------

git push origin main 2>&1 | tail -4 || { echo "gitp: push failed"; exit 1; }

# notify peer with the real range
bash "$SCRIPT_DIR/notify.sh" --from "$OLD" --to "$NEW" --verified || true
echo "gitp: pushed + notified peer ($OLD..$NEW)"
