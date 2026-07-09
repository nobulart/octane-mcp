from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .config import OctaneConfig, resolve_config

DEFAULT_TIMEOUT_SECONDS = 15


@dataclass(frozen=True)
class BridgeScript:
    mode: str
    path: Path

    @property
    def menu_name(self) -> str:
        return self.path.name


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


def render_run_bridge_applescript(config: OctaneConfig, script: BridgeScript) -> str:
    """Build the AppleScript used to run a generated bridge from Octane's Scripts menu."""

    app_path = json.dumps(str(config.app_path))
    menu_name = json.dumps(script.menu_name)
    stem_name = json.dumps(script.path.stem)
    return f'''set appPath to {app_path}
set bridgeScriptName to {menu_name}
set bridgeScriptStem to {stem_name}

do shell script "open -a " & quoted form of appPath
delay 0.5

tell application "System Events"
    if not (exists process "Octane X") then error "Octane X process is not running after activate"
    tell process "Octane X"
        set frontmost to true
        -- Probe menu-bar access first. If macOS denies assistive access the
        -- inner "menu 1 of menu bar item" throws -1719; surface it verbatim
        -- instead of masking it as a "script not found" error.
        try
            set _probe to count of menu bar items of menu bar 1
        on error errMsg number errNum
            if errNum is -1719 then
                error "assistive access denied (-1719): grant Accessibility to the app running osascript in System Settings -> Privacy & Security -> Accessibility" number errNum
            else
                error errMsg number errNum
            end if
        end try
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
    apple_script = render_run_bridge_applescript(config, script)
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
    proc = _run(["osascript", "-e", apple_script], timeout_seconds=timeout_seconds)
    result.update({
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "ok": proc.returncode == 0,
        "status": octane_process_status(config),
    })
    if proc.returncode != 0:
        result["error"] = proc.stderr.strip() or "osascript failed"
        result["next_steps"] = [
            "Confirm Octane X Preferences -> Scripts path points to this repo's octane_lua directory.",
            "If macOS reports assistive-access errors, grant the calling terminal/Hermes app Accessibility permission.",
            "If the persistent bridge is already open, queued commands can still process via that window/timer even when menu automation fails.",
        ]
        # macOS TCC gate: UI-scripting (clicking Octane's Scripts menu) requires
        # Accessibility permission for the process that runs osascript. Without it
        # the bridge silently fails to launch and the queue never drains. Detect and
        # surface the exact one-time fix instead of a vague hint.
        _stderr_l = result["error"].lower()
        if "assistive access" in _stderr_l or "-1719" in _stderr_l:
            _hermes_app = "/Users/craig/.hermes/hermes-agent/apps/desktop/release/mac-arm64/Hermes.app"
            result["tcc_blocked"] = True
            result["next_steps"] = [
                "macOS blocked UI-scripting (Accessibility/TCC). Grant it once:",
                "  1. System Settings -> Privacy & Security -> Accessibility",
                f"  2. Click + and add: {_hermes_app}",
                "  3. If already listed, remove + re-add to refresh the TCC token, then restart Hermes.",
                "This is a one-time OS permission; the launch code itself is correct.",
            ]
    return result
