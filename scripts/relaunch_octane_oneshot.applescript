(*
 * relaunch_octane_oneshot.applescript
 * ------------------------------------------------------------------
 * Quits Octane X, relaunches it, and clicks
 *   Script > hermes_bridge_oneshot.generated
 * in Octane's menu bar Ñ i.e. drains the whole command queue via the
 * one-shot bridge (one click drains the entire queue).
 *
 * WHY THIS SHAPE (load-bearing, from the octane-viz skill):
 *  - The Scripts menu is singular "Script" on this Octane build, not "Scripts".
 *  - `exists process "Octane X"` MUST be evaluated INSIDE
 *    `tell application "System Events"`; at top level it is a -2741
 *    compile error.
 *  - macOS UI-scripting (Accessibility/TCC) must be granted to the process
 *    that runs osascript Ñ for Hermes that is the agent-runtime python
 *    (/Users/craig/.hermes/hermes-agent/venv/bin/python), NOT Hermes.app.
 *    If TCC is missing you get -1719 (surfaced verbatim below).
 *  - After the bridge runs, the "Hermes Render Target" node must be
 *    manually re-selected in the Octane UI or the engine stays idle and
 *    save_preview captures an empty buffer. This script cannot do that.
 *
 * RUN:
 *   osascript scripts/relaunch_octane_oneshot.applescript
 *   (or open it in Script Editor and hit Run)
 * ------------------------------------------------------------------
 *)

set appPath to "/Applications/Octane X.app"
set appName to "Octane X"
set bridgeScriptName to "hermes_bridge_oneshot.generated.lua"
set bridgeScriptStem to "hermes_bridge_oneshot.generated"
set quitWait to 15
set launchWait to 15

-- 1) Gracefully quit Octane X (wait for the process to actually exit).
try
	tell application appName to quit
on error
	-- not running; nothing to quit
end try
set quitDeadline to (current date) + quitWait
repeat while (current date) < quitDeadline
	tell application "System Events"
		if not (exists process appName) then exit repeat
	end tell
	delay 0.5
end repeat

-- 2) Launch (or activate) Octane X, then wait until its menu bar is UI-ready.
do shell script "open -a " & quoted form of appPath
try
	tell application appName to activate
on error
	-- app may still be launching; the readiness loop below retries
end try
set launchDeadline to (current date) + launchWait
set launched to false
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
				error "assistive access denied (-1719): grant Accessibility to the process running osascript in System Settings -> Privacy & Security -> Accessibility" number errNum
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
	error "Octane X did not become UI-ready within " & launchWait & "s after launch (menus not populated)."
end if

-- 3) Click Script > hermes_bridge_oneshot.generated
tell application "System Events"
	tell process appName
		set frontmost to true
		set menuCandidates to {"Script", "Scripts", "Lua", "File"}
		repeat with menuTitle in menuCandidates
			try
				set candidateMenu to menu 1 of menu bar item (menuTitle as text) of menu bar 1
				-- direct items
				repeat with directItem in menu items of candidateMenu
					set itemName to name of directItem
					if itemName is bridgeScriptName or itemName is bridgeScriptStem or itemName contains bridgeScriptName or itemName contains bridgeScriptStem then
						click directItem
						return "clicked " & itemName & " via " & (menuTitle as text)
					end if
				end repeat
				-- nested submenu items
				repeat with submenuItem in menu items of candidateMenu
					try
						repeat with nestedItem in menu items of menu 1 of submenuItem
							set nestedName to name of nestedItem
							if nestedName is bridgeScriptName or nestedName is bridgeScriptStem or nestedName contains bridgeScriptName or nestedName contains bridgeScriptStem then
								click nestedItem
								return "clicked " & nestedName & " via " & (menuTitle as text) & " submenu"
							end if
						end repeat
					end try
				end repeat
			end try
		end repeat
		error "Could not find " & bridgeScriptName & " in Octane X Script menu. Confirm Preferences -> Scripts path points to the repo octane_lua directory."
	end tell
end tell
