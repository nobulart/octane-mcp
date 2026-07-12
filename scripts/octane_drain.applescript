(*
 * octane_drain.applescript [TIMEOUT_S] [PREVIEW_PATH]
 * ------------------------------------------------------------------
 * Click Octane X > Script > hermes_bridge_oneshot.generated (ONE click drains
 * the WHOLE queue) and then poll until the workspace queue/ is empty AND the
 * preview PNG is freshly written (newer than the click), or TIMEOUT_S elapses.
 * Prints a JSON summary:
 *   { "clicked", "queue_remaining", "preview_written", "waited", "ok" }
 *
 * Exit codes:
 *   0  always returns JSON (inspect the "ok" field for drain success)
 *   non-zero  only on a HARD control failure (click not found / TCC / app down)
 *
 * The persistent bridge's auto-poll timer is BROKEN (timer create attempt 1
 * failed), so prefer this one-shot drain. After clicking, do NOT re-click
 * while the queue is empty — a second click while save_preview is rendering is
 * ignored and would kill that render.
 *
 * RUN:
 *   osascript scripts/octane_drain.applescript
 *   osascript scripts/octane_drain.applescript 120 /abs/path/preview.png
 *
 * NOTE: Octane X must already be running + UI-ready (launch with
 * octane_launch.applescript first), OR use octane_relaunch_drain.applescript
 * which launches + drains in one shot.
 *)
on run argv
  set wsRoot to (system attribute "HOME") & "/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
  set qDir to wsRoot & "/queue"
  set timeoutS to 90
  set previewPath to wsRoot & "/renders/preview.png"
  if (count of argv) > 0 then
    try
      set timeoutS to (argv's item 1 as number)
    end try
  end if
  if (count of argv) > 1 then
    set previewPath to argv's item 2 as text
  end if

  set appName to "Octane X"
  set target to "hermes_bridge_oneshot.generated"
  set clickedName to ""

  -- 1) Click the one-shot bridge from the Scripts menu.
  tell application "System Events"
    if not (exists process appName) then
      error "Octane X not running — launch it first (octane_launch.applescript)."
    end if
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
        error "Could not find '" & target & "' in Octane X Scripts menu."
      end if
    end tell
  end tell

  -- 2) Snapshot the preview mtime BEFORE the drain so we can detect a fresh save.
  set beforeEpoch to 0
  set pngPreExists to (do shell script "test -f " & quoted form of previewPath & " && echo 1 || echo 0") as number
  if pngPreExists is 1 then
    set beforeEpoch to (do shell script "stat -f %m " & quoted form of previewPath) as number
  end if

  -- 3) Poll: queue empty + preview freshly written.
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
