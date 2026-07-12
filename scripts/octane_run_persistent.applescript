(*
 * octane_run_persistent.applescript
 * ------------------------------------------------------------------
 * On-demand control #4: click Octane X > Script > hermes_bridge_persistent.generated
 * Opens the persistent bridge window (manual "Process next" / "Drain queue"
 * UI). NOTE: the persistent bridge's auto-poll timer is BROKEN (timer create
 * attempt 1 failed), so it will NOT auto-drain — use the one-shot bridge for
 * automated batch drains. This control just OPENS the persistent window.
 *
 * Exit codes:
 *   0  clicked (window opened)
 *   non-zero  not found / TCC (-1719) / app not running (-600)
 *
 * RUN:
 *   osascript scripts/octane_run_persistent.applescript
 *)
set appName to "Octane X"
set target to "hermes_bridge_persistent.generated"
set clickedName to ""

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
      error "Could not find '" & target & "' in Octane X Scripts menu. Confirm Preferences -> Scripts path points to the repo octane_lua directory."
    end if
  end tell
end tell
return "clicked " & clickedName
