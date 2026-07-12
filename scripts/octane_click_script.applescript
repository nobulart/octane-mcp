(*
 * octane_click_script.applescript <NAME>
 * ------------------------------------------------------------------
 * Click a named item in Octane X's Scripts menu (singular "Script").
 * NAME may be a full filename (hermes_bridge_oneshot.generated) or any
 * substring. Searches the "Script"/"Scripts"/"Lua" menu items and their
 * first-level submenus. Returns the matched item name + menu.
 *
 * Exit codes:
 *   0  clicked
 *   non-zero  not found, or TCC (-1719) / app-not-running (-600)
 *
 * NOTE: Octane X must already be running + UI-ready. Launch it first with
 * octane_launch.applescript, or use octane_drain.applescript /
 * octane_relaunch_drain.applescript which launch internally.
 *
 * WHY THIS SHAPE: never use `run script file` on the .lua bridge — AppleScript
 * tries to compile Lua as AppleScript and dies with -2741. The Scripts-menu
 * CLICK path runs it as Lua.
 *
 * RUN:
 *   osascript scripts/octane_click_script.applescript hermes_bridge_oneshot.generated
 *   osascript scripts/octane_click_script.applescript "export_api_docs_v3"
 *)
on run argv
  if (count of argv) is 0 then
    error "usage: osascript octane_click_script.applescript <SCRIPT_NAME>"
  end if
  set target to argv's item 1 as text
  set appName to "Octane X"
  set menuCandidates to {"Script", "Scripts", "Lua", "File"}

  tell application "System Events"
    if not (exists process appName) then
      error "Octane X not running — launch it first (octane_launch.applescript)."
    end if
    tell process appName
      set frontmost to true
      repeat with menuTitle in menuCandidates
        try
          set candidateMenu to menu 1 of menu bar item (menuTitle as text) of menu bar 1
          -- direct items
          repeat with directItem in menu items of candidateMenu
            set itemName to name of directItem
            if itemName contains target then
              click directItem
              return "clicked " & itemName & " via " & (menuTitle as text)
            end if
          end repeat
          -- nested submenu items (first level)
          repeat with submenuItem in menu items of candidateMenu
            try
              repeat with nestedItem in menu items of menu 1 of submenuItem
                set nestedName to name of nestedItem
                if nestedName contains target then
                  click nestedItem
                  return "clicked " & nestedName & " via " & (menuTitle as text) & " submenu"
                end if
              end repeat
            end try
          end repeat
        end try
      end repeat
      error "Could not find '" & target & "' in Octane X Scripts menu. Confirm Preferences -> Scripts path points to the repo octane_lua directory."
    end tell
  end tell
end run
