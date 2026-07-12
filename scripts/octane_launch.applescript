(*
 * octane_launch.applescript
 * ------------------------------------------------------------------
 * Ensure Octane X is running and its menu bar is UI-ready (so the
 * Scripts menu can be UI-scripted). Idempotent: if already running and
 * ready, returns immediately without relaunching.
 *
 * Exit codes:
 *   0  Octane X is running and UI-ready (printed: "ready" / "ready (already running)")
 *   2  Launched but did not become UI-ready within the wait window
 *   -1719 surfaces verbatim if macOS Accessibility (TCC) is denied
 *
 * WHY THIS SHAPE (load-bearing, from octane-viz skill + bridge_control.py):
 *  - Octane X has NO CLI Lua entry point (docs/octane-x-no-cli.md). The only
 *    programmatic surface is UI-scripting the Scripts menu via System Events.
 *  - `exists process "Octane X"` MUST run INSIDE `tell application "System
 *    Events"`; at top level it is a -2741 compile error.
 *  - TCC must be granted to the process that runs osascript (the Hermes
 *    agent-runtime python, or its shell/terminal ancestor), NOT Hermes.app.
 *
 * RUN:
 *   osascript scripts/octane_launch.applescript
 *   osascript scripts/octane_launch.applescript 20      # custom launch wait (s)
 *)
on run argv
  set appPath to "/Applications/Octane X.app"
  set appName to "Octane X"
  set launchWait to 15
  if (count of argv) > 0 then
    try
      set launchWait to (argv's item 1 as number)
    end try
  end if

  -- Fast path: already running + menu bar populated.
  tell application "System Events"
    if exists process appName then
      try
        tell process appName
          set frontmost to true
          set _probe to count of menu bar items of menu bar 1
        end tell
        if _probe > 0 then
          return "ready (already running)"
        end if
      on error errMsg number errNum
        if errNum is -1719 then
          error "assistive access denied (-1719): grant Accessibility to the process running osascript in System Settings -> Privacy & Security -> Accessibility" number errNum
        end if
      end try
    end if
  end tell

  -- Launch (or activate) and wait for the menu bar to populate.
  do shell script "open -a " & quoted form of appPath
  try
    tell application appName to activate
  on error
    -- app may still be launching; the readiness loop below retries
  end try

  set launchDeadline to (current date) + launchWait
  set launched to false
  set tccSeen to false
  repeat while (current date) < launchDeadline
    tell application "System Events"
      try
        if exists process appName then
          tell process appName
            set frontmost to true
            delay 0.4
            set _probe to count of menu bar items of menu bar 1
          end tell
          if _probe > 0 then
            set launched to true
            exit repeat
          end if
        end if
      on error errMsg number errNum
        if errNum is -1719 then
          -- A -1719 right after launching a fresh Octane process is often a
          -- TRANSIENT frontmost/TCC-race (a subsequent System Events call in
          -- the same session typically succeeds). Retry within the launch
          -- window; only surface it as a hard TCC error if it PERSISTS for the
          -- whole wait. (Verified live 2026-07-12: a relaunch returned -1719
          -- on the first probe, then succeeded on the next call.)
          set tccSeen to true
          delay 0.5
        else if errNum is -1728 then
          -- menu bar not ready yet; keep waiting
          delay 0.5
        end if
      end try
    end tell
    if launched then exit repeat
    delay 0.3
  end repeat

  if not launched then
    if tccSeen then
      error "assistive access denied (-1719): grant Accessibility to the process running osascript in System Settings -> Privacy & Security -> Accessibility" number -1719
    end if
    error "Octane X did not become UI-ready within " & launchWait & "s after launch (menus not populated)." number 2
  end if
  return "ready"
end run
