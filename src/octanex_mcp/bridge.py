from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

DEFAULT_APP_PATH = Path("/Applications/Octane X.app")
# Octane X is a sandboxed Mac App Store app. When its Lua runtime opens
# /Users/craig/OctaneMCP, macOS redirects it into the app container. Hermes must
# therefore write to the real container path for Octane to see inbox commands.
DEFAULT_WORKSPACE = Path.home() / "Library" / "Containers" / "com.otoy.rndrviewer" / "Data" / "OctaneMCP"
REPO_ROOT = Path(__file__).resolve().parents[2]
RECIPE_BOOK_PATH = REPO_ROOT / "docs" / "recipe-book.md"

ALLOWED_OPS = {
    "ping",
    "open_or_create_project",
    "import_geometry",
    "create_material",
    "assign_material",
    "set_camera",
    "set_lighting",
    "start_render",
    "pause_render",
    "save_preview",
    "save_scene",
    "scene_summary",
    "build_concept",
}


@dataclass(frozen=True)
class Workspace:
    root: Path = DEFAULT_WORKSPACE

    @property
    def queue_dir(self) -> Path:
        return self.root / "queue"

    @property
    def processed_dir(self) -> Path:
        return self.root / "processed"

    @property
    def failed_dir(self) -> Path:
        return self.root / "failed"

    @property
    def assets_dir(self) -> Path:
        return self.root / "assets"

    @property
    def renders_dir(self) -> Path:
        return self.root / "renders"

    @property
    def status_path(self) -> Path:
        return self.root / "status.json"

    def ensure(self) -> None:
        for path in [self.root, self.queue_dir, self.processed_dir, self.failed_dir, self.assets_dir, self.renders_dir]:
            path.mkdir(parents=True, exist_ok=True)


def octane_app_status(app_path: Path = DEFAULT_APP_PATH) -> Dict[str, Any]:
    exe = app_path / "Contents" / "MacOS" / "Octane X"
    plist = app_path / "Contents" / "Info.plist"
    return {
        "app_path": str(app_path),
        "app_exists": app_path.exists(),
        "executable": str(exe),
        "executable_exists": exe.exists(),
        "info_plist_exists": plist.exists(),
        "workspace": str(DEFAULT_WORKSPACE),
    }


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def read_status(workspace: Workspace = Workspace()) -> Dict[str, Any]:
    workspace.ensure()
    if not workspace.status_path.exists():
        return {
            "bridge_seen": False,
            "status_path": str(workspace.status_path),
            "message": "No status file yet. Start hermes_bridge.lua inside Octane X.",
        }
    try:
        return json.loads(workspace.status_path.read_text())
    except Exception as exc:
        return {"bridge_seen": True, "status_error": str(exc), "status_path": str(workspace.status_path)}


def write_command(op: str, payload: Optional[Dict[str, Any]] = None, workspace: Workspace = Workspace()) -> Dict[str, Any]:
    if op not in ALLOWED_OPS:
        raise ValueError(f"Unsupported op {op!r}; allowed: {sorted(ALLOWED_OPS)}")
    workspace.ensure()
    # Nanosecond timestamp keeps lexicographic filename ordering aligned with
    # queue order even when several commands are emitted in the same millisecond.
    command_id = f"{time.time_ns()}-{uuid.uuid4().hex[:8]}"
    command = {
        "id": command_id,
        "op": op,
        "payload": payload or {},
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "octanex-mcp",
    }
    text = json.dumps(command, indent=2, default=_json_default)
    tmp_path = workspace.queue_dir / f".{command_id}.json.tmp"
    final_path = workspace.queue_dir / f"{command_id}.json"
    tmp_path.write_text(text)
    os.replace(tmp_path, final_path)

    # Octane X's embedded Lua runtime cannot safely poll/list directories from
    # the UI thread. For the in-app bridge, also publish the latest command to a
    # fixed inbox file that hermes_bridge.lua processes once and exits.
    inbox_tmp = workspace.root / ".inbox.json.tmp"
    inbox_path = workspace.root / "inbox.json"
    inbox_tmp.write_text(text)
    os.replace(inbox_tmp, inbox_path)

    return {
        "queued": True,
        "command_id": command_id,
        "op": op,
        "path": str(final_path),
        "inbox_path": str(inbox_path),
        "status": read_status(workspace),
    }


def list_commands(workspace: Workspace = Workspace()) -> Dict[str, Any]:
    workspace.ensure()
    def names(path: Path) -> list[str]:
        return sorted(p.name for p in path.glob("*.json"))
    return {
        "queue": names(workspace.queue_dir),
        "processed": names(workspace.processed_dir)[-20:],
        "failed": names(workspace.failed_dir)[-20:],
        "status": read_status(workspace),
    }


def _recipe_heading(title: str) -> str:
    safe = " ".join(title.strip().split())
    return safe[:96] or "Untitled recipe"


def record_recipe_entry(
    *,
    title: str,
    outcome: str,
    context: str,
    steps: Iterable[str],
    signals: Iterable[str] = (),
    follow_ups: Iterable[str] = (),
    recipe_path: Path = RECIPE_BOOK_PATH,
) -> Dict[str, Any]:
    """Append a compact success/failure lesson to the agent recipe book.

    The recipe book is intentionally markdown so small local models can read and
    copy patterns without needing a database, embeddings, or bespoke tooling.
    """
    normalized_outcome = outcome.strip().lower()
    if normalized_outcome not in {"success", "failure", "partial", "pitfall"}:
        raise ValueError("outcome must be one of: success, failure, partial, pitfall")
    recipe_path.parent.mkdir(parents=True, exist_ok=True)
    if not recipe_path.exists():
        recipe_path.write_text("# OctaneX MCP Recipe Book\n\nReusable field notes from real MCP usage.\n\n", encoding="utf-8")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    clean_steps = [f"- {item.strip()}" for item in steps if item and item.strip()]
    clean_signals = [f"- {item.strip()}" for item in signals if item and item.strip()]
    clean_follow_ups = [f"- {item.strip()}" for item in follow_ups if item and item.strip()]
    section = [
        f"## {_recipe_heading(title)}",
        "",
        f"- **Outcome:** {normalized_outcome}",
        f"- **Recorded:** {stamp}",
        f"- **Context:** {context.strip() or 'Not specified.'}",
        "",
        "### Steps",
        *(clean_steps or ["- Not specified."]),
        "",
        "### Signals / evidence",
        *(clean_signals or ["- Not specified."]),
        "",
        "### Follow-ups",
        *(clean_follow_ups or ["- None."]),
        "",
    ]
    with recipe_path.open("a", encoding="utf-8") as handle:
        handle.write("\n" + "\n".join(section))
    return {"recorded": True, "path": str(recipe_path), "title": _recipe_heading(title), "outcome": normalized_outcome}


def read_recipe_book(limit_chars: int = 12000, recipe_path: Path = RECIPE_BOOK_PATH) -> Dict[str, Any]:
    if not recipe_path.exists():
        return {"path": str(recipe_path), "exists": False, "content": ""}
    text = recipe_path.read_text(encoding="utf-8")
    if len(text) > limit_chars:
        text = text[: limit_chars // 2] + "\n\n... [truncated] ...\n\n" + text[-limit_chars // 2 :]
    return {"path": str(recipe_path), "exists": True, "content": text}


def create_simple_obj(name: str = "mcp_cube", size: float = 1.0, workspace: Workspace = Workspace()) -> Dict[str, Any]:
    """Create a tiny cube OBJ as an importable smoke-test asset."""
    workspace.ensure()
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name) or "mcp_cube"
    s = float(size) / 2.0
    obj = f"""# Generated by octanex-mcp\no {safe_name}\nusemtl default\nv {-s} {-s} {-s}\nv {s} {-s} {-s}\nv {s} {s} {-s}\nv {-s} {s} {-s}\nv {-s} {-s} {s}\nv {s} {-s} {s}\nv {s} {s} {s}\nv {-s} {s} {s}\nf 1 2 3 4\nf 5 8 7 6\nf 1 5 6 2\nf 2 6 7 3\nf 3 7 8 4\nf 5 1 4 8\n"""
    path = workspace.assets_dir / f"{safe_name}.obj"
    path.write_text(obj)
    return {"path": str(path), "name": safe_name, "size": size}


def concept_to_commands(prompt: str) -> list[Dict[str, Any]]:
    """Very small deterministic concept compiler for MVP smoke tests.

    This is intentionally simple. Later versions should ask the model to emit
    a validated scene plan, not raw Lua.
    """
    lower = prompt.lower()
    material = {
        "name": "concept_primary_material",
        "kind": "glossy",
        "color": [0.8, 0.8, 0.8],
        "roughness": 0.25,
    }
    if "cyber" in lower or "neon" in lower:
        material.update({"color": [0.05, 0.75, 1.0], "roughness": 0.12})
    if "gold" in lower:
        material.update({"color": [1.0, 0.67, 0.18], "metallic": 1.0, "roughness": 0.18})
    return [
        {"op": "open_or_create_project", "payload": {"name": "Hermes Concept"}},
        {"op": "create_material", "payload": material},
        {"op": "set_camera", "payload": {"position": [2.8, 1.8, 4.2], "target": [0, 0.4, 0], "fov": 45}},
        {"op": "set_lighting", "payload": {"preset": "studio_neon" if "neon" in lower else "soft_studio"}},
        {"op": "start_render", "payload": {"samples": 128, "width": 1280, "height": 1280}},
        {"op": "build_concept", "payload": {"prompt": prompt, "note": "MVP placeholder: bridge should import generated assets and map this prompt to scene nodes."}},
    ]
