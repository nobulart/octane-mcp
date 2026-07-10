#!/usr/bin/env bash
# coord_watch.sh — poll the peer's outbox, auto-absorb their pushes, ack back.
#
# Run by a Hermes cron every ~2 min. On each run:
#   1. pull peer outbox -> our inbox (coord_pull_peer)
#   2. for any NEW peer message of type done/note/intent, react:
#        - type done/intent touching our repo: git fetch; if tree CLEAN, rebase
#          origin/main; send an 'ack' back over SSH fast-path.
#        - if tree DIRTY: send a 'blocked' message (do NOT rebase, never lose work).
#   3. type ack/blocked from peer: just log (non-reactive, prevents loops).
#
# Idempotent: dedup via peer-line membership; watermark only used for logging.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

cd "$(coord_repo_dir)" || { coord_log "watch: cannot cd to repo"; exit 1; }

NEW="$(coord_pull_peer)"
coord_log "watch: pulled $NEW new peer message(s)"

[ "$NEW" -eq 0 ] && exit 0

# Read only the NEW lines (tail -n NEW of inbox, but dedup-safe: reprocess all inbox
# lines, react once per unseen type=done/intent from peer using a seen-file).
SEEN="$COORD_DIR/.coord_seen"
touch "$SEEN"

react_to() {
  # $1 = whole JSON line
  local reacted=0
  if echo "$1" | python3 -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get("from")=="'"$COORD_PEER_ID"'" and d.get("type") in ("done","intent","note") else 1)' 2>/dev/null; then
    reacted=1
    local dtype action
    dtype="$(echo "$1" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("type"))')"
    coord_log "watch: reacting to peer $dtype"

    # fetch first
    coord_git fetch origin 2>&1 | tail -1
    local behind; behind="$(coord_git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)"

    if [ "$behind" -eq 0 ]; then
      coord_log "watch: already up to date"
      action="noop"
    elif coord_is_dirty; then
      coord_log "watch: tree DIRTY (behind $behind) -> BLOCKED, no rebase"
      action="blocked"
      local blk; blk="$(python3 -c 'import json; print(json.dumps({"from":"'"$COORD_SELF_ID"'","ts":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","type":"blocked","repo":"octanex-mcp","reason":"local dirty tree; rebase skipped","behind":'"$behind"'},separators=(",",":")))')"
      coord_append_peer "$blk"
      coord_append_local "$blk"
    else
      if coord_git rebase origin/main 2>&1 | tail -3; then
        coord_log "watch: rebased onto origin/main (was behind $behind)"
        action="rebased"
      else
        coord_git rebase --abort 2>/dev/null || true
        coord_log "watch: rebase FAILED -> aborted; manual resolution needed"
        action="rebase_failed"
        local fail; fail="$(python3 -c 'import json; print(json.dumps({"from":"'"$COORD_SELF_ID"'","ts":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","type":"blocked","repo":"octanex-mcp","reason":"rebase conflict; needs manual resolution","behind":'"$behind"'},separators=(",",":")))')"
        coord_append_peer "$fail"
        coord_append_local "$fail"
      fi
    fi

    # acknowledge (only for done/intent that required action)
    if [ "$action" != "noop" ]; then
      local ack; ack="$(python3 -c 'import json; print(json.dumps({"from":"'"$COORD_SELF_ID"'","ts":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","type":"ack","repo":"octanex-mcp","for_type":"'"$dtype"'","action":"'"$action"'"},separators=(",",":")))')"
      coord_append_peer "$ack"
      coord_append_local "$ack"
    fi
  fi
  echo "$1" >> "$SEEN"
}

# process inbox lines not yet in seen-file
while IFS= read -r line; do
  [ -z "$line" ] && continue
  grep -qxF "$line" "$SEEN" 2>/dev/null && continue
  react_to "$line"
done < "$COORD_INBOX"
