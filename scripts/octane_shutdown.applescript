(*
 * octane_shutdown.applescript [--force]
 * ------------------------------------------------------------------
 * On-demand control #6: shut down Octane X.
 *
 * Default (no arg): graceful `Quit Octane X` (the app's Quit menu item), then
 * poll until the process actually exits. If the quit is blocked (e.g. a busy
 * Lua script / unsaved-document sheet), it times out and reports a hint to
 * use --force.
 *
 * --force: if graceful quit is unavailable or blocked, `kill -9` the Octane X
 * process(es). Use only when a script/render will not yield to graceful quit.
 *
 * Exit codes:
 *   0  Octane X not running, or shut down successfully
 *   non-zero  graceful quit timed out (use --force) / TCC on initial probe
 *
 * RUN:
 *   osascript scripts/octane_shutdown.applescript          # graceful
 *   osascript scripts/octane_shutdown.applescript --force  # hard kill
 *)
on run argv
  set appName to "Octane X"
  set force to false
  if (count of argv) > 0 then
    if argv's item 1 is "force" or argv's item 1 is "--force" then set force to true
  end if

  tell application "System Events"
    if not (exists process appName) then
      return "not running"
    end if
  end tell

  if force then
    do shell script "pkill -9 -x 'Octane X'"
    set deadline to (current date) + 10
    repeat while (current date) < deadline
      tell application "System Events"
        if not (exists process appName) then return "force-quit Octane X"
      end tell
      delay 0.3
    end repeat
    return "force-quit signaled; process may still be terminating"
  end if

  -- Graceful quit.
  tell application appName to quit
  set quitWait to 15
  set deadline to (current date) + quitWait
  repeat while (current date) < deadline
    tell application "System Events"
      if not (exists process appName) then return "shut down (graceful)"
    end tell
    delay 0.5
  end repeat
  error "graceful quit timed out after " & quitWait & "s (Octane X busy / modal). Use: octane_shutdown.applescript --force" number 1
end run
