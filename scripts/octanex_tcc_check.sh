#!/usr/bin/env bash
#
# octanex_tcc_check.sh — diagnose + guide the Octane X / System Events
# Accessibility (TCC) -1719 problem, and survive Hermes' multiple daily updates.
#
# WHY THIS EXISTS
# ---------------
# Octane X has no native "run script" AppleScript verb. The ONLY way to fire
# hermes_bridge_*.lua is to UI-script its Scripts menu via System Events. That
# requires macOS Accessibility permission on the process that spawns osascript.
#
# The osascript is spawned by the octanex-mcp SERVER, whose chain is:
#   osascript <- octanex-mcp/.venv/bin/python3 <- /opt/homebrew/bin/uv
#             <- hermes-agent/venv/bin/python (SYMLINK, relinks on update)
#             <- hermes_cli.main serve <- Hermes.app (child of launchd)
#
# TCC keys the grant on the running binary's CODE-SIGNATURE REQUIREMENT. The
# hermes-agent venv python is a symlink that Hermes updates repoint at a freshly
# downloaded cpython build, so a grant made on it stops matching after an update
# -> -1719 returns. Granting Hermes.app alone fails too, because Hermes is
# launched by launchd and the grant does not propagate down to subprocess
# osascript. The durable targets are the STABLE ancestors:
#   * /opt/homebrew/bin/uv        (covers the whole MCP osascript chain)
#   * Terminal.app / iTerm.app    (covers manual terminal osascript tests)
#
# NOTE: Apple does NOT permit scripted ADDITION of Accessibility grants
# (tccutil can only reset). This script computes the correct stable targets,
# flags zombie instances, and re-verifies -1719 after you grant in System
# Settings. Run it after every Hermes update.
#
set -u

OCTANE="Octane X"
echo "=== octanex TCC diagnostic @ $(date) ==="
echo

# 1) Locate the live octanex-mcp server process and walk its ancestors.
server_pids=$(pgrep -f 'octanex-mcp/.venv/bin/octanex-mcp' 2>/dev/null || true)
if [ -z "$server_pids" ]; then
  # fall back: the run_octanex_mcp.sh launcher
  server_pids=$(pgrep -f 'run_octanex_mcp.sh' 2>/dev/null || true)
fi
echo "octanex-mcp server pid(s): ${server_pids:-NONE}"

walk_chain() {
  local pid="$1"
  local guard=0
  echo "  chain for pid $pid:"
  while [ -n "$pid" ] && [ "$pid" != "1" ]; do
    # Bounded loop: a malformed ps line must never wedge the diagnostic.
    guard=$((guard + 1))
    if [ "$guard" -gt 64 ]; then echo "    ...(chain truncated at 64 frames)"; break; fi
    # Take ONLY the line(s) matching this exact PID to avoid multi-line bleed.
    local line
    line=$(ps -o pid=,ppid=,comm= -p "$pid" 2>/dev/null | awk -v p="$pid" '$1==p {print; exit}' | sed 's/^ *//')
    [ -z "$line" ] && break
    local ppid
    ppid=$(echo "$line" | awk '{print $2}')
    local comm
    comm=$(echo "$line" | awk '{print $3}')
    # classify stability
    local tag="?"
    case "$comm" in
      */uv) tag="STABLE(relink-safe)" ;;
      */Terminal|*/iTerm*|Terminal.app|iTerm.app) tag="STABLE(terminal)" ;;
      */Hermes.app/Contents/MacOS/Hermes) tag="STABLE(app, but launchd-child)" ;;
      */hermes-agent/venv/bin/python*|*.venv/bin/python*|*.local/share/uv/python/*) tag="VOLATILE(relinks on update)" ;;
      /bin/bash|/bin/sh|login|zsh) tag="STABLE(shell)" ;;
      *) tag="?" ;;
    esac
    printf "    %-7s ppid=%-7s %-70s [%s]\n" "$(echo "$line" | awk '{print $1}')" "$ppid" "$comm" "$tag"
    # Safety: if ppid parsed empty or self-referential, stop.
    [ -z "$ppid" ] && break
    [ "$ppid" = "$pid" ] && break
    pid="$ppid"
  done
}

for sp in $server_pids; do
  walk_chain "$sp"
done
echo

# 2) Recommend the stable grant targets.
echo "=== RECOMMENDED ACCESSIBILITY GRANT TARGETS (System Settings > Privacy & Security > Accessibility) ==="
echo "  Grant these STABLE paths (they survive Hermes updates):"
echo "    [1] /usr/bin/osascript   <- THE requesting process for ALL System Events UI-scripting."
echo "        macOS keys the grant on the process that EMITS the accessibility request, which is"
echo "        osascript itself (TCC does NOT walk up to uv/python/Hermes.app ancestors). This is"
echo "        the durable fix: osascript lives at a fixed system path and never relinks on update."
echo "    [2] Terminal.app / iTerm.app  <- covers manual terminal osascript tests (some setups"
echo "        also need the launcher granted, but osascript is the required one)."
echo "    [3] /opt/homebrew/bin/uv   <- optional; does NOT by itself clear -1719 (ancestor grants"
echo "        do not propagate to osascript), but harmless to include."
echo
echo "  Do NOT rely on these (they do not clear -1719 for osascript):"
echo "    - /Users/craig/.hermes/hermes-agent/venv/bin/python   (symlink, repointed on update; AND"
echo "      TCC keys on osascript, not this ancestor)"
echo "    - Hermes.app  (launched by launchd; grant does not reach subprocess osascript)"
echo
echo "  How to add: System Settings > Privacy & Security > Accessibility > '+' > Shift-Cmd-G >"
echo "  paste /usr/bin/osascript > Open. If already listed, remove + re-add to refresh the token."
echo

# 3) Detect TRUE duplicate instances (robust: scan full arg list).
#    NORMAL topology = 1 launchd gateway (ai.hermes.gateway) + 1 Hermes.app GUI.
#    Each spins up its own octanex-mcp server — that is EXPECTED, not a defect.
#    A REAL problem = TWO of the SAME kind (two GUIs, or two launchd gateways).
hermes_app_pids=$(ps -ax -o pid=,args= 2>/dev/null | grep -E 'Hermes.app/Contents/MacOS/Hermes' | grep -v grep | awk '{print $1}' | tr '\n' ' ')
# launchd-managed gateway: registered via ~/Library/LaunchAgents/ai.hermes.gateway.plist
gateway_pids=$(launchctl list 2>/dev/null | awk '$3=="ai.hermes.gateway"{print $1}' | tr '\n' ' ')
# fallback: any standalone `gateway run` not under Hermes.app (e.g. a hand-launched one)
gateway_pids=$(echo "$gateway_pids $(ps -ax -o pid=,args= 2>/dev/null | grep -E 'hermes_cli\.main gateway run' | grep -v grep | awk '{print $1}' | tr '\n' ' ')" | tr ' ' '\n' | grep -v '^$' | sort -u | tr '\n' ' ')
octanex_servers=$(ps -ax -o pid=,args= 2>/dev/null | grep -E 'octanex-mcp/\.venv/bin/octanex-mcp' | grep -v grep | awk '{print $1}' | tr '\n' ' ')
echo "=== INSTANCE HEALTH ==="
echo "  Hermes.app GUI instances : ${hermes_app_pids:-NONE}  (expected: exactly 1)"
echo "  launchd gateway daemons  : ${gateway_pids:-NONE}  (expected: exactly 1 = ai.hermes.gateway)"
echo "  octanex-mcp servers      : ${octanex_servers:-NONE}  (expected: 1 per topology)"
gui_count=$(echo "${hermes_app_pids:-}" | wc -w | tr -d ' ')
gw_count=$(echo "${gateway_pids:-}" | wc -w | tr -d ' ')
if [ "${gui_count:-0}" -gt 1 ]; then
  echo "  !! WARNING: ${gui_count} Hermes.app GUI instances — duplicate desktop app (zombie)."
  echo "     Kill the OLDER one to avoid duplicate MCP tool registration."
fi
if [ "${gw_count:-0}" -gt 1 ]; then
  echo "  !! WARNING: ${gw_count} launchd gateway daemons — duplicate ai.hermes.gateway."
  echo "     One is a stray; unload the duplicate via launchctl, do NOT kill (launchd respawns)."
fi
if [ "${gui_count:-0}" -le 1 ] && [ "${gw_count:-0}" -le 1 ]; then
  echo "  OK: normal topology (1 GUI + 1 launchd gateway). Multiple octanex-mcp servers are expected."
fi
echo

# 4) Probe -1719: does a System Events UI-script that DRIVES Octane X work?
echo "=== -1719 PROBE (System Events -> Octane X menu control) ==="
if ! pgrep -x "$OCTANE" >/dev/null; then
  echo "  SKIP: $OCTANE not running."
else
  out=$(osascript -e '
    try
      tell application "System Events" to tell process "Octane X" to get name of menu bar item 1 of menu bar 1
      return "TCC_OK"
    on error errMsg number errNum
      return "TCC_ERR " & errNum & " :: " & errMsg
    end try' 2>&1)
  rc=$?
  if echo "$out" | grep -q "TCC_OK"; then
    echo "  RESULT: PASS — System Events can drive Octane X. TCC is correctly granted."
  else
    echo "  RESULT: FAIL — $out"
    echo "  ACTION: grant /opt/homebrew/bin/uv (and Terminal.app) in System Settings, then re-run this script."
  fi
fi
echo
echo "=== done ==="
