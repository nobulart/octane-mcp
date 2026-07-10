#!/usr/bin/env bash
# coord_intent.sh — declare which files we intend to touch this session.
#
# Sends an 'intent' message to the peer so they can avoid editing the same files
# (conflict prevention). Cleared implicitly when a 'done' is sent (the push itself
# signals completion). Re-announce at session start or when scope changes.
#
# Usage: coord_intent.sh "src/foo.py;docs/bar.md;hermes/skills/x/SKILL.md"

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

FILES="${1:-}"
[ -z "$FILES" ] && { echo "usage: coord_intent.sh \"path1;path2;...\""; exit 1; }

TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
MSG="$(python3 -c 'import json,sys; print(json.dumps({"from":"'"$COORD_SELF_ID"'","ts":"'"$TS"'","type":"intent","repo":"octanex-mcp","branch":"main","files":sys.argv[1].split(";"),"session":"'"$$"'"},separators=(",",":")))' "$FILES")"

coord_append_peer "$MSG"
coord_append_local "$MSG"
coord_log "intent: $FILES"
echo "declared intent: $FILES"
