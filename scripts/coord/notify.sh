#!/usr/bin/env bash
# coord_notify.sh — instantly inform the peer that we pushed commits to origin/main.
#
# Intended as a git post-push hook (or run manually). Reads the pushed range,
# builds one structured message (SHAs + touched files + summary), and delivers it
# to the peer's inbox DIRECTLY over SSH (sub-second) + our local outbox (redundancy).
#
# Usage: coord_notify.sh [--from <sha>] [--to <sha>] [--summary "..."] [--verified]
#   (no args: auto-detect from origin/main..HEAD on the repo)

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

FROM=""; TO=""; SUMMARY=""; VERIFIED=0
while [ $# -gt 0 ]; do
  case "$1" in
    --from)    FROM="$2"; shift 2 ;;
    --to)      TO="$2"; shift 2 ;;
    --summary) SUMMARY="$2"; shift 2 ;;
    --verified) VERIFIED=1; shift ;;
    *) shift ;;
  esac
done

cd "$(coord_repo_dir)" || { coord_log "notify: cannot cd to repo"; exit 1; }

# Determine the pushed range. If --from/--to given, use them; else origin/main..HEAD.
if [ -z "$FROM" ] || [ -z "$TO" ]; then
  FROM="$(coord_git rev-parse origin/main 2>/dev/null)"
  TO="$(coord_git rev-parse HEAD 2>/dev/null)"
fi
[ -z "$FROM" ] || [ -z "$TO" ] && { coord_log "notify: no range"; exit 0; }

# Touched files across the range (compact, deduped)
FILES="$(coord_git diff --name-only "$FROM" "$TO" 2>/dev/null | sort -u | paste -sd ';' -)"
COMMITS="$(coord_git log --pretty=format:%h "$FROM".."$TO" 2>/dev/null | paste -sd ',' -)"
[ -z "$SUMMARY" ] && SUMMARY="$(coord_git log --pretty=format:'%s' "$FROM".."$TO" 2>/dev/null | head -1)"

TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Build JSON (python for safe escaping)
MSG="$(python3 - "$COORD_SELF_ID" "$TS" "$COMMITS" "$FILES" "$SUMMARY" "$VERIFIED" <<'PY'
import json,sys
self_id,ts,commits,files,summary,verified=sys.argv[1:7]
print(json.dumps({
  "from": self_id,
  "ts": ts,
  "type": "done",
  "repo": "octanex-mcp",
  "branch": "main",
  "commits": commits.split(',') if commits else [],
  "files": files.split(';') if files else [],
  "summary": summary,
  "verified": verified == "1",
  "action": "rebase",
}, separators=(',',':')))
PY
)"

coord_append_peer "$MSG"
coord_append_local "$MSG"
coord_log "notify: pushed $COMMITS (files: ${FILES:-none}) -> peer"
echo "notified peer: $COMMITS"
