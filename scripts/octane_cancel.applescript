(*
 * octane_cancel.applescript
 * ------------------------------------------------------------------
 * On-demand control #5: cancel a running script / in-progress render.
 *
 * Octane X has NO "Cancel script" / "Stop" / "Abort" menu item. The only
 * programmatic cancel gesture is the standard Escape keypress, which aborts
 * an in-progress render or current operation in Octane's live viewport.
 *
 * This is BEST-EFFORT: if a Lua script is fully synchronous and blocking the
 * Lua thread, Escape may not take effect until the script yields. If the
 * operation does not stop, escalate to a hard stop:
 *   osascript scripts/octane_shutdown.applescript --force
 *
 * Exit codes:
 *   0  Escape sent (reported as best-effort)
 *   non-zero  Octane X not running
 *
 * RUN:
 *   osascript scripts/octane_cancel.applescript
 *)
set appName to "Octane X"
tell application "System Events"
  if not (exists process appName) then
    error "Octane X not running — nothing to cancel."
  end if
  set frontmost of process appName to true
  -- Escape (key code 53) is the standard Octane cancel gesture for an
  -- in-progress render / current operation.
  key code 53
end tell
return "sent cancel (Escape) to Octane X — best-effort; if a synchronous Lua script is still running, escalate to octane_shutdown.applescript --force"
