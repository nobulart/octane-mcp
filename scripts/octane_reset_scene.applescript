(*
 * octane_reset_scene.applescript
 * ------------------------------------------------------------------
 * Warm-engine reset: Octane X "File" > "New" on the RUNNING process.
 * Clears the in-memory scene graph so the next save_preview does not wedge
 * on stale scene-graph nodes (between recipes). Does NOT relaunch.
 *
 * Exit codes:
 *   0  reset issued (printed: "reset (File > New)")
 *   non-zero  app not running (-600) / TCC (-1719) / menu not ready
 *
 * WHEN: between recipes, before queuing the next scene. Do NOT relaunch
 * Octane X between import_geometry and save_preview — a relaunch purges the
 * in-memory scene and produces a uniform gray (243,243,243) frame.
 *
 * RUN:
 *   osascript scripts/octane_reset_scene.applescript
 *)
set appName to "Octane X"
tell application "System Events"
  if not (exists process appName) then
    error "Octane X not running — launch it first (octane_launch.applescript)."
  end if
  tell process appName
    set frontmost to true
    try
      set _probe to count of menu bar items of menu bar 1
    on error errMsg number errNum
      if errNum is -1719 then
        error "assistive access denied (-1719): grant Accessibility to the process running osascript in System Settings -> Privacy & Security -> Accessibility" number errNum
      end if
      error errMsg number errNum
    end try
    if _probe is 0 then
      error "Octane X menu bar not ready (UI not populated)."
    end if
    click menu item "New" of menu 1 of menu bar item "File" of menu bar 1
  end tell
end tell
return "reset (File > New)"
