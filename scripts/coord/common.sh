#!/usr/bin/env bash
# coord/common.sh — shared functions for the octanex-mcp coordination loop.
#
# Provides: host identity, peer resolution, message append (local + SSH fast-path),
# message read, and watermark tracking. Sourced by coord_notify.sh / coord_watch.sh.
#
# Requires: bash, ssh (keyless to peer), python3, git (in the repo dir).
# No external packages (fswatch/launchd/airdrop) — polling + SSH only.

set -uo pipefail

# ---- host identity (auto-detected) ------------------------------------------
COORD_HOST="$(scutil --get LocalHostName 2>/dev/null || hostname -s 2>/dev/null || echo unknown)"
# canonical id used in messages: "macbook-pro" or "mac-studio"
case "$(echo "$COORD_HOST" | tr '[:upper:]' '[:lower:]')" in
  *studio*)  COORD_SELF_ID="mac-studio"      ;;
  *macbook*) COORD_SELF_ID="macbook-pro"     ;;
  *)         COORD_SELF_ID="$COORD_HOST"     ;;
esac

# ---- peer resolution --------------------------------------------------------
# Peer is the OTHER instance. Hostname follows <id>.local; SSH user is "craig".
case "$COORD_SELF_ID" in
  macbook-pro) COORD_PEER_ID="mac-studio";     COORD_PEER_HOST="mac-studio.local";;
  mac-studio)  COORD_PEER_ID="macbook-pro";    COORD_PEER_HOST="macbook-pro.local";;
  *)           COORD_PEER_ID="peer";           COORD_PEER_HOST="peer.local";;
esac
COORD_PEER_USER="${COORD_PEER_USER:-craig}"

# ---- paths ------------------------------------------------------------------
COORD_DIR="${COORD_DIR:-$HOME/hermes-bridge}"
COORD_OUTBOX="$COORD_DIR/outbox.jsonl"
COORD_INBOX="$COORD_DIR/inbox.jsonl"
COORD_WATERMARK="$COORD_DIR/.coord_watermark"   # last seen peer message ts+linehash
COORD_LOG="$COORD_DIR/coord.log"

mkdir -p "$COORD_DIR"

# ---- logging -----------------------------------------------------------------
coord_log() {
  local ts; ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf '[%s %s] %s\n' "$ts" "$COORD_SELF_ID" "$*" >> "$COORD_LOG" 2>/dev/null || true
}

# ---- message append ----------------------------------------------------------
# coord_append_local <json-line>   -> append to OUR outbox (redundancy + cron dedup)
coord_append_local() {
  printf '%s\n' "$1" >> "$COORD_OUTBOX"
}

# coord_append_peer <json-line>  -> append DIRECTLY to peer inbox over SSH (fast-path)
#   Falls back to local outbox if SSH fails (the cron sync will deliver later).
coord_append_peer() {
  local line="$1"
  if printf '%s\n' "$line" | ssh -o BatchMode=yes -o ConnectTimeout=10 \
       "$COORD_PEER_USER@$COORD_PEER_HOST" 'cat >> ~/hermes-bridge/inbox.jsonl' 2>/dev/null; then
    coord_log "notify fast-path OK -> $COORD_PEER_ID"
    return 0
  else
    coord_log "notify fast-path SSH FAILED -> fell back to local outbox"
    coord_append_local "$line"   # peer's sync.sh will pull this on next cron
    return 1
  fi
}

# ---- watermark (last ingested peer line) ------------------------------------
coord_watermark_get() { cat "$COORD_WATERMARK" 2>/dev/null || echo ""; }
coord_watermark_set() { printf '%s' "$1" > "$COORD_WATERMARK"; }

# ---- pull peer outbox -> our inbox (one-shot, dedup) -------------------------
# Returns: number of NEW lines ingested (0 if none).
coord_pull_peer() {
  local tmp; tmp="$(mktemp -t peer-out.XXXXXX)"
  if ! ssh -o BatchMode=yes -o ConnectTimeout=10 \
       "$COORD_PEER_USER@$COORD_PEER_HOST" \
       'cat ~/hermes-bridge/outbox.jsonl 2>/dev/null || true' > "$tmp" 2>/dev/null; then
    rm -f "$tmp"; echo 0; return
  fi
  local new=0 line
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    if ! grep -qxF "$line" "$COORD_INBOX" 2>/dev/null; then
      printf '%s\n' "$line" >> "$COORD_INBOX"
      new=$((new+1))
    fi
  done < "$tmp"
  rm -f "$tmp"
  echo "$new"
}

# ---- repo helpers (must be run from the repo dir) ---------------------------
coord_repo_dir() { echo "${COORD_REPO:-$HOME/octanex-mcp}"; }

coord_git() { git -C "$(coord_repo_dir)" "$@"; }

# detect dirty tree (uncommitted changes), robust
coord_is_dirty() {
  [ -n "$(coord_git status --porcelain 2>/dev/null)" ]
}
