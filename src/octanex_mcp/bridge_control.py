from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .config import OctaneConfig, resolve_config

DEFAULT_TIMEOUT_SECONDS = 30
# How long to wait (seconds) for a freshly launched Octane X to expose its
# menu bar before we give up and report a launch failure (instead of a
# spurious "script not found" from probing a not-yet-ready UI).
LAUNCH_READINESS_WAIT_SECONDS = 10
# macOS Accessibility/TCC must be granted to the PROCESS WHOSE DESCENDANT RUNS
# osascript. For this deployment the osascript caller is the Hermes AGENT
# RUNTIME python (the parent of the octanex-mcp server), NOT Hermes.app (the
# desktop GUI is a separate process). Granting Hermes.app alone does NOT clear
# -1719. Allow an env override so the hint is portable and not hardcoded.
# Corrected 2026-07-09: the earlier "grant Hermes.app" guidance was wrong for
# this deployment — a live -1719 against a supposedly-granted Hermes.app is the
# tell that the agent-runtime binary (or its shell/terminal ancestor) is the
# target TCC must grant.
HERMES_APP_HINT = os.environ.get(
    "OCTANEX_TCC_APP",
    "/Users/craig/.hermes/hermes-agent/venv/bin/python",
)


@dataclass(frozen=True)
class BridgeScript:
    mode: str
    path: Path

    @property
    def menu_name(self) -> str:
        return self.path.name

    @property
    def stem_name(self) -> str:
        return self.path.stem


def bridge_script(config: OctaneConfig, mode: str) -> BridgeScript:
    normalized = mode.strip().lower().replace("_", "-")
    if normalized in {"oneshot", "one-shot"}:
        return BridgeScript("oneshot", config.oneshot_generated_path)
    if normalized == "persistent":
        return BridgeScript("persistent", config.persistent_generated_path)
    raise ValueError("mode must be 'oneshot' or 'persistent'")


def _run(command: Sequence[str], *, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, timeout=timeout_seconds)


def octane_process_status(config: OctaneConfig | None = None) -> dict[str, Any]:
    """Return app/process/script readiness for on-demand bridge control."""

    config = resolve_config() if config is None else config
    pgrep = _run(["pgrep", "-x", "Octane X"], timeout_seconds=3)
    pids = [line.strip() for line in pgrep.stdout.splitlines() if line.strip()]
    status: dict[str, Any] = {
        "app_path": str(config.app_path),
        "app_exists": config.app_path.exists(),
        "running": bool(pids),
        "pids": pids,
        "workspace": str(config.workspace),
        "scripts": {
            "oneshot": str(config.oneshot_generated_path),
            "persistent": str(config.persistent_generated_path),
        },
        "script_exists": {
            "oneshot": config.oneshot_generated_path.exists(),
            "persistent": config.persistent_generated_path.exists(),
        },
    }
    status_path = config.workspace / "status.json"
    if status_path.exists():
        try:
            payload = json.loads(status_path.read_text(encoding="utf-8"))
        except Exception as exc:
            payload = {"status_error": str(exc)}
        status["bridge_status"] = payload
        status["bridge_status_path"] = str(status_path)
        status["bridge_status_age_seconds"] = round(max(0.0, time.time() - status_path.stat().st_mtime), 3)
    else:
        status["bridge_status"] = {"seen": False, "message": "No status.json yet."}
        status["bridge_status_path"] = str(status_path)
    return status


def classify_osascript_error(stderr: str) -> dict[str, Any]:
    """Classify an osascript failure into actionable categories.

    macOS returns these AppleScript error numbers for Octane X control:
      -1719  accessibility (TCC) denied — grant Accessibility to the Hermes
             AGENT-RUNTIME python (parent of the octanex-mcp server), NOT
             Hermes.app; a live -1719 against a granted Hermes.app is the tell.
      -1700  can't make data into expected type — Octane busy / mid-render modal
      -2741  expected end of line — caller used `run script file` on Lua (wrong trigger)
      -2753  variable not defined — mis-targeted / not the Octane process
    A missing/never-ready Scripts menu surfaces as the plain "Could not find ..."
    message we emit ourselves.
    """

    s = (stderr or "").strip()
    low = s.lower()
    code = None
    for token in ("-1719", "-1700", "-2741", "-2753", "-1728"):
        if token in s:
            code = token
            break

    tcc_blocked = ("-1719" in s) or ("assistive access" in low)
    busy = ("-1700" in s) or ("can't make" in low and "expected type" in low)
    wrong_trigger = "-2741" in s
    not_found = ("could not find" in low) or ("preferences" in low and "scripts path" in low)

    kind = "unknown"
    if tcc_blocked:
        kind = "tcc_denied"
    elif busy:
        kind = "app_busy"
    elif wrong_trigger:
        kind = "wrong_trigger"
    elif not_found:
        kind = "script_not_found"

    result: dict[str, Any] = {
        "code": code,
        "kind": kind,
        "tcc_blocked": tcc_blocked,
        "busy": busy,
        "wrong_trigger": wrong_trigger,
        "script_not_found": not_found,
    }
    if tcc_blocked:
        result["fix"] = [
            "macOS blocked UI-scripting (Accessibility/TCC). Grant it once to the "
            "PROCESS WHOSE DESCENDANT RUNS osascript:",
            "  1. System Settings -> Privacy & Security -> Accessibility",
            f"  2. Click + and add: {HERMES_APP_HINT}  (the Hermes AGENT-RUNTIME python —",
            "     the parent of the octanex-mcp server, NOT Hermes.app the GUI).",
            "  3. If the binary is awkward to select, grant the shell/terminal that launches",
            "     Hermes (TCC walks up to the nearest granted ancestor). Hermes.app alone",
            "     does NOT clear -1719.",
            "  4. If already listed, remove + re-add to refresh the TCC token, then restart Hermes.",
        ]
    elif busy:
        result["fix"] = [
            "Octane X is mid-render or showing a modal (osascript -1700).",
            "Wait for the current render to settle, then retry the click.",
            "Do NOT keep re-clicking — a second bridge click while Octane is busy is ignored.",
        ]
    elif wrong_trigger:
        result["fix"] = [
            "AppleScript -2741: the Lua bridge was driven via `run script file`, which compiles "
            "Lua as AppleScript. Use the Scripts-menu click path (bridge_control does this).",
        ]
    elif not_found:
        result["fix"] = [
            "Confirm Octane X Preferences -> Scripts path points to this repo's octane_lua directory,",
            "then restart Octane X so the script appears in the Scripts menu.",
        ]
    return result


def render_launch_and_run_applescript(
    config: OctaneConfig,
    script: BridgeScript,
    *,
    launch_wait: int = LAUNCH_READINESS_WAIT_SECONDS,
) -> str:
    """Build the AppleScript that launches Octane X (if needed), waits for its
    menu bar to become UI-ready, then clicks the bridge script from the Scripts
    menu.

    The launch + readiness wait is done inside a single AppleScript so there is
    no race between an `open -a` shell call and the menu-probe osascript call.
    """

    app_path = json.dumps(str(config.app_path))
    menu_name = json.dumps(script.menu_name)
    stem_name = json.dumps(script.path.stem)
    return f'''set appPath to {app_path}
set bridgeScriptName to {menu_name}
set bridgeScriptStem to {stem_name}
set launchWait to {int(launch_wait)}

-- Launch (or activate) Octane X and wait until its menu bar is UI-ready.
do shell script "open -a " & quoted form of appPath
tell application "System Events"
    set launchDeadline to (current date) + launchWait
    set launched to false
    repeat while (current date) < launchDeadline
        try
            -- Probe menu-bar access first. If macOS denies assistive access the
            -- inner "menu 1 of menu bar item" throws -1719; surface it verbatim
            -- instead of masking it as a "script not found" error.
            set _probe to count of menu bar items of menu bar 1 of process "Octane X"
            if _probe > 0 then
                set launched to true
                exit repeat
            end if
        on error errMsg number errNum
            if errNum is -1719 then
                error "assistive access denied (-1719): grant Accessibility to the app running osascript in System Settings -> Privacy & Security -> Accessibility" number errNum
            else
                -- process not up yet / transient; keep waiting
            end if
        end try
        delay 0.3
    end repeat
end tell
if not launched then
    error "Octane X did not become UI-ready within " & launchWait & "s after launch (menus not populated)."
end if

tell application "System Events"
    tell process "Octane X"
        set frontmost to true
        set menuCandidates to {{"Scripts", "Script", "Lua", "File"}}
        repeat with menuTitle in menuCandidates
            try
                set candidateMenu to menu 1 of menu bar item (menuTitle as text) of menu bar 1
                repeat with directItem in menu items of candidateMenu
                    set itemName to name of directItem
                    if itemName is bridgeScriptName or itemName is bridgeScriptStem or itemName contains bridgeScriptName or itemName contains bridgeScriptStem then
                        click directItem
                        return "clicked " & itemName & " via " & (menuTitle as text)
                    end if
                end repeat
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
        error "Could not find " & bridgeScriptName & " in Octane X Scripts menu. Confirm Preferences -> Scripts path points to the repo octane_lua directory."
    end tell
end tell
'''


def run_bridge_script(
    mode: str,
    *,
    config: OctaneConfig | None = None,
    dry_run: bool = False,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Open Octane X if needed and run a generated bridge script via AppleScript."""

    config = resolve_config() if config is None else config
    script = bridge_script(config, mode)
    apple_script = render_launch_and_run_applescript(config, script)
    result: dict[str, Any] = {
        "ok": False,
        "mode": script.mode,
        "script_path": str(script.path),
        "script_exists": script.path.exists(),
        "app_path": str(config.app_path),
        "app_exists": config.app_path.exists(),
        "dry_run": dry_run,
        "apple_script": apple_script,
    }
    if not config.app_path.exists():
        result["error"] = "Octane X app bundle not found. Set OCTANEX_APP_PATH if it lives elsewhere."
        return result
    if not script.path.exists():
        result["error"] = "Generated bridge script not found. Run `octanex-mcp init` first."
        return result
    if dry_run:
        result["ok"] = True
        result["message"] = "Dry run only; AppleScript was generated but not executed."
        return result
    try:
        proc = _run(["osascript", "-e", apple_script], timeout_seconds=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        # A hung osascript means Octane is stuck on a modal / busy render and is
        # not accepting the click. Do NOT retry blindly — surface it so the
        # caller backs off.
        result.update({
            "ok": False,
            "timed_out": True,
            "timeout_seconds": timeout_seconds,
            "error": f"osascript timed out after {timeout_seconds}s (Octane X busy or unresponsive).",
            "next_steps": [
                "Octane X is unresponsive to UI-scripting (likely mid-render or a blocking modal).",
                "Wait for the render to settle or quit the modal, then retry once.",
                "If the hang persists, restart Octane X (it caches the bridge in memory).",
            ],
        })
        return result
    result.update({
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "ok": proc.returncode == 0,
        "status": octane_process_status(config),
    })
    if proc.returncode != 0:
        err = result["stderr"] or result["stdout"] or "osascript failed"
        result["error"] = err
        result.update(classify_osascript_error(err))
        if not result.get("tcc_blocked"):
            # Non-TCC failures: keep the generic next_steps but prefer the
            # classified fix when we have one.
            if result.get("fix"):
                result["next_steps"] = result["fix"]
            else:
                result["next_steps"] = [
                    "Confirm Octane X Preferences -> Scripts path points to this repo's octane_lua directory.",
                    "If macOS reports assistive-access errors, grant the calling terminal/Hermes app Accessibility permission.",
                    "If the persistent bridge is already open, queued commands can still process via that window/timer even when menu automation fails.",
                ]
    return result


def render_reset_scene_applescript() -> str:
    """AppleScript that performs File > New on a running Octane X (warm-engine
    reset). Kept separate from the launch+run script because a reset must NOT
    also launch/re-run the bridge."""

    return (
        'tell application "System Events"\n'
        '  if not (exists (process "Octane X" of application "System Events")) then error "Octane X not running"\n'
        '  tell process "Octane X"\n'
        '    set frontmost to true\n'
        '    try\n'
        '      set _probe to count of menu bar items of menu bar 1\n'
        '    on error errMsg number errNum\n'
        '      if errNum is -1719 then error "assistive access denied (-1719)" number errNum\n'
        '      error errMsg number errNum\n'
        '    end try\n'
        '    click menu item "New" of menu 1 of menu bar item "File" of menu bar 1\n'
        '  end tell\n'
        'end tell\n'
    )


def reset_octane_scene(
    *,
    config: OctaneConfig | None = None,
    timeout_seconds: int = 20,
) -> dict[str, Any]:
    """Warm-engine reset: File > New on the running Octane process.

    Used between recipes so ``request_render_restart`` does not wedge on stale
    scene-graph nodes. Returns {ok, error, kind?} so callers can branch on the
    failure class (TCC denied vs app busy vs not running).
    """

    config = resolve_config() if config is None else config
    script = render_reset_scene_applescript()
    if not config.app_path.exists():
        return {"ok": False, "error": "Octane X app bundle not found."}
    try:
        proc = _run(["osascript", "-e", script], timeout_seconds=timeout_seconds)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"osascript timed out after {timeout_seconds}s (Octane X busy/modal).", "timed_out": True}
    if proc.returncode == 0:
        return {"ok": True}
    err = (proc.stderr or proc.stdout or "").strip()
    result: dict[str, Any] = {"ok": False, "error": err or f"osascript rc={proc.returncode}"}
    result.update(classify_osascript_error(err))
    return result
