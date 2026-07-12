(*
 * octane_status.applescript
 * ------------------------------------------------------------------
 * Print a JSON status blob to stdout. Pure reporting — never mutates Octane:
 *   { "running", "ui_ready", "tcc_ok", "scripts_menu": [...], "bridge_status": {...} }
 * Reads the live workspace status.json (written by the Lua bridge) if present.
 * Safe to run at any time.
 *
 * RUN:
 *   osascript scripts/octane_status.applescript
 *)
set appName to "Octane X"
set wsRoot to (system attribute "HOME") & "/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"

set appRunning to false
set uiReady to false
set tccOk to false
set scriptsMenu to {}

tell application "System Events"
  if exists process appName then
    set appRunning to true
    try
      tell process appName
        set frontmost to true
        set _probe to count of menu bar items of menu bar 1
      end tell
      if _probe > 0 then
        set uiReady to true
        set tccOk to true
        repeat with mb in menu bar items of menu bar 1 of process appName
          set t to name of mb
          if t is "Script" or t is "Scripts" or t is "Lua" then
            repeat with itm in menu items of menu 1 of mb
              set end of scriptsMenu to name of itm
            end repeat
          end if
        end repeat
      end if
    on error errMsg number errNum
      if errNum is -1719 then
        -- running but TCC denied: report tcc_ok=false, keep appRunning=true
        set tccOk to false
      end if
    end try
  end if
end tell

-- Build a JSON array string from the scripts menu list.
set arr to ""
repeat with nm in scriptsMenu
  if arr is not "" then set arr to arr & ","
  set arr to arr & "\"" & nm & "\""
end repeat
set scriptsMenuJson to "[" & arr & "]"

-- Read live bridge status.json if present (best-effort, embedded raw JSON).
set bridgeStatusJson to ""
set statusPath to wsRoot & "/status.json"
try
  set j to do shell script "cat " & quoted form of statusPath & " 2>/dev/null"
  if j is not "" then set bridgeStatusJson to "," & "\"bridge_status\":" & j
end try

set out to "{"
set out to out & "\"running\":" & (appRunning as text) & ","
set out to out & "\"ui_ready\":" & (uiReady as text) & ","
set out to out & "\"tcc_ok\":" & (tccOk as text) & ","
set out to out & "\"scripts_menu\":" & scriptsMenuJson
set out to out & bridgeStatusJson
set out to out & "}"
return out
