(*
 * relaunch_octane_oneshot.applescript [TIMEOUT_S] [PREVIEW_PATH]
 * ------------------------------------------------------------------
 * COLD CYCLE (control for bridge-patch reloads / wedged sessions):
 *   1. Quit Octane X (if running), wait for the process to actually exit.
 *   2. Relaunch Octane X, wait for its menu bar to become UI-ready.
 *   3. Click Script > hermes_bridge_oneshot.generated (one click drains the
 *      ENTIRE queue; the Lua drain loop re-snapshots until empty).
 *   4. Poll until queue/ is empty AND the preview PNG is freshly written, or
 *      TIMEOUT_S elapses. Print a JSON summary.
 *
 * EXIT: always prints JSON and exits 0; inspect the "ok" field for success.
 * Only exits non-zero on a HARD control failure (TCC -1719, app-down, click
 * not found).
 *
 * NOTE ON "RENDER TARGET": this script does NOT perform a manual "Hermes
 * Render Target" re-select. The Lua bridge now activates the render target
 * programmatically before each render (verified live in bridge.log:
 * "activated render target Hermes Render Target" -> "render start requested"
 * -> PNG saved). Do NOT reintroduce a manual re-select step — it is obsolete.
 *
 * WHEN: ONLY on a cold boot / after editing a bridge template (Octane caches
 * Lua in memory, so a patched bridge needs a relaunch). NEVER relaunch between
 * import_geometry and save_preview — that purges the in-memory scene and
 * yields a uniform gray (243,243,243) frame.
 *
 * RUN:
 *   osascript scripts/relaunch_octane_oneshot.applescript
 *   osascript scripts/relaunch_octane_oneshot.applescript 120 /abs/preview.png
 *)
on run argv
  set appPath to "/Applications/Octane X.app"
  set appName to "Octane X"
  set target to "hermes_bridge_oneshot.generated"
  set wsRoot to (system attribute "HOME") & "/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
  set qDir to wsRoot & "/queue"
  set previewPath to wsRoot & "/renders/preview.png"
  set timeoutS to 90
  if (count of argv) > 0 then
    try
      set timeoutS to (argv's item 1 as number)
    end try
  end if
  if (count of argv) > 1 then
    set previewPath to argv's item 2 as text
  end if

  -- 1) Quit if running, wait for exit.
  tell application "System Events"
    if exists process appName then
      tell application appName to quit
    end if
  end tell
  set quitDeadline to (current date) + 15
  repeat while (current date) < quitDeadline
    tell application "System Events"
      if not (exists process appName) then exit repeat
    end tell
    delay 0.5
  end repeat

  -- 2) Launch + wait for UI-ready.
  do shell script "open -a " & quoted form of appPath
  try
    tell application appName to activate
  on error
  end try
  set launchWait to 15
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
          -- whole wait. (Verified live 2026-07-12.)
          set tccSeen to true
          delay 0.5
        else if errNum is -1728 then
          delay 0.5
        else if errNum is -600 then
          -- app not yet ready during relaunch race; retry within window
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

  -- 3) Click the one-shot bridge.
  set clickedName to ""
  tell application "System Events"
    tell process appName
      set frontmost to true
      set menuCandidates to {"Script", "Scripts", "Lua", "File"}
      repeat with menuTitle in menuCandidates
        try
          set candidateMenu to menu 1 of menu bar item (menuTitle as text) of menu bar 1
          repeat with directItem in menu items of candidateMenu
            set itemName to name of directItem
            if itemName contains target then
              click directItem
              set clickedName to itemName
              exit repeat
            end if
          end repeat
          if clickedName is not "" then exit repeat
          repeat with submenuItem in menu items of candidateMenu
            try
              repeat with nestedItem in menu items of menu 1 of submenuItem
                set nestedName to name of nestedItem
                if nestedName contains target then
                  click nestedItem
                  set clickedName to nestedName
                  exit repeat
                end if
              end repeat
            end try
            if clickedName is not "" then exit repeat
          end repeat
        end try
        if clickedName is not "" then exit repeat
      end repeat
      if clickedName is "" then
        error "Could not find '" & target & "' in Octane X Scripts menu. Confirm Preferences -> Scripts path points to the repo octane_lua directory."
      end if
    end tell
  end tell

  -- 4) Poll queue empty + fresh preview.
  set beforeEpoch to 0
  set pngPreExists to (do shell script "test -f " & quoted form of previewPath & " && echo 1 || echo 0") as number
  if pngPreExists is 1 then
    set beforeEpoch to (do shell script "stat -f %m " & quoted form of previewPath) as number
  end if
  set qRem to 9999
  set fresh to 0
  set waited to 0
  repeat while waited < timeoutS
    set qRem to (do shell script "ls -1 " & quoted form of qDir & "/*.json 2>/dev/null | wc -l | tr -d ' '") as number
    set fresh to 0
    set pngExists to (do shell script "test -f " & quoted form of previewPath & " && echo 1 || echo 0") as number
    if pngExists is 1 then
      set now to (do shell script "stat -f %m " & quoted form of previewPath) as number
      if now > beforeEpoch then set fresh to 1
    end if
    if qRem is 0 and fresh is 1 then exit repeat
    delay 2
    set waited to waited + 2
  end repeat

  set ok to (qRem is 0) and (fresh is 1)
  set out to "{"
  set out to out & "\"clicked\":\"" & clickedName & "\","
  set out to out & "\"queue_remaining\":" & qRem & ","
  set out to out & "\"preview_written\":" & fresh & ","
  set out to out & "\"waited\":" & waited & ","
  set out to out & "\"ok\":" & (ok as text)
  set out to out & "}"
  return out
end run
