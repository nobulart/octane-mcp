from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Mapping

from .bridge import REPO_ROOT, Workspace, flush_queue, write_command
from .schema import SCHEMA_VERSION, validate_command

RECIPES_ROOT = REPO_ROOT / "examples" / "recipes"


def _recipe_dirs(recipes_root: Path = RECIPES_ROOT) -> list[Path]:
    if not recipes_root.exists():
        return []
    return sorted(path for path in recipes_root.iterdir() if path.is_dir() and (path / "scene.json").exists())


def _read_scene_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"recipe scene.json must contain an object: {path}")
    return data


def _resolve_repo_path(value: Any, *, repo_root: Path = REPO_ROOT) -> Any:
    if not isinstance(value, str) or not value.strip():
        return value
    raw = Path(value).expanduser()
    if raw.is_absolute():
        return str(raw)
    if ".." in raw.parts:
        return value
    return str((repo_root / raw).resolve())


def _resolve_recipe_asset_path(value: Any, *, repo_root: Path = REPO_ROOT, workspace: Workspace | None = None) -> Any:
    """Resolve recipe asset paths for Octane.

    Offline recipe loading resolves paths inside the checkout. Live queueing
    must prefer sandbox-visible staged copies when available: Octane X may not
    be able to read the repo checkout path, which creates an apparently wired
    mesh node with no visible geometry.
    """

    if not isinstance(value, str) or not value.strip():
        return value
    raw = Path(value).expanduser()
    if raw.is_absolute() or ".." in raw.parts or workspace is None:
        return _resolve_repo_path(value, repo_root=repo_root)
    sandbox = (workspace.root / raw).resolve()
    if sandbox.exists():
        return str(sandbox)
    return _resolve_repo_path(value, repo_root=repo_root)


def _preview_path(recipe_dir: Path, data: Mapping[str, Any]) -> Path | None:
    for name in ("octane-preview.png", "preview.png", "photoreal-preview.png"):
        candidate = recipe_dir / name
        if candidate.exists():
            return candidate
    for key in ("preview", "preview_path", "target_preview"):
        value = data.get(key)
        if isinstance(value, str):
            candidate = recipe_dir / value
            if candidate.exists():
                return candidate
    return None


def _assets(recipe_dir: Path) -> list[str]:
    names = ["scene.obj", "scene.mtl", "scene.json", "preview.png", "photoreal-preview.png", "octane-preview.png"]
    return [str(recipe_dir / name) for name in names if (recipe_dir / name).exists()]


def _known_pitfalls(data: Mapping[str, Any]) -> list[str]:
    pitfalls = data.get("known_pitfalls")
    if isinstance(pitfalls, list):
        return [str(item) for item in pitfalls if str(item).strip()]
    out: list[str] = []
    native_note = data.get("native_render_note")
    if isinstance(native_note, str) and native_note.strip():
        out.append(native_note.strip())
    preview_note = data.get("preview_note")
    if isinstance(preview_note, str) and "not" in preview_note.lower():
        out.append(preview_note.strip())
    return out


def _metadata(recipe_dir: Path, data: Mapping[str, Any]) -> dict[str, Any]:
    slug = str(data.get("slug") or recipe_dir.name)
    preview = _preview_path(recipe_dir, data)
    octane_preview = recipe_dir / "octane-preview.png"
    native_verified = bool(data.get("native_octane_verified") is True or octane_preview.exists())
    raw_commands = data.get("commands")
    commands: list[Any] = raw_commands if isinstance(raw_commands, list) else []
    return {
        "slug": slug,
        "title": str(data.get("title") or slug.replace("-", " ").title()),
        "domain": str(data.get("domain") or data.get("category") or "uncategorized"),
        "purpose": str(data.get("purpose") or data.get("prompt") or ""),
        "recipe_dir": str(recipe_dir),
        "scene_json_path": str(recipe_dir / "scene.json"),
        "scene_json_exists": (recipe_dir / "scene.json").exists(),
        "preview_path": str(preview) if preview else None,
        "preview_exists": bool(preview and preview.exists()),
        "assets": _assets(recipe_dir),
        "command_count": len(commands),
        "quality_checklist": [str(item) for item in data.get("quality_checklist", [])] if isinstance(data.get("quality_checklist"), list) else [],
        "known_pitfalls": _known_pitfalls(data),
        "native_octane_verified": native_verified,
    }


def recipe_index(recipes_root: Path = RECIPES_ROOT) -> dict[str, Any]:
    """List checked-in example recipes with normalized metadata."""

    recipes: list[dict[str, Any]] = []
    for recipe_dir in _recipe_dirs(recipes_root):
        data = _read_scene_json(recipe_dir / "scene.json")
        recipes.append(_metadata(recipe_dir, data))
    return {"recipes_root": str(recipes_root), "count": len(recipes), "recipes": recipes}


def _find_recipe_dir(slug: str, recipes_root: Path = RECIPES_ROOT) -> Path:
    safe_slug = str(slug).strip()
    for recipe_dir in _recipe_dirs(recipes_root):
        data = _read_scene_json(recipe_dir / "scene.json")
        if safe_slug in {recipe_dir.name, str(data.get("slug") or "")}:
            return recipe_dir
    known = ", ".join(item["slug"] for item in recipe_index(recipes_root)["recipes"])
    raise ValueError(f"unknown recipe slug {slug!r}; known recipes: {known}")


def _resolved_commands(data: Mapping[str, Any], *, repo_root: Path = REPO_ROOT, workspace: Workspace | None = None) -> list[dict[str, Any]]:
    raw_commands = data.get("commands")
    if not isinstance(raw_commands, list):
        return []
    commands: list[dict[str, Any]] = []
    for raw in raw_commands:
        if not isinstance(raw, Mapping):
            continue
        command = copy.deepcopy(dict(raw))
        payload = command.get("payload")
        if isinstance(payload, dict) and "path" in payload:
            payload["path"] = _resolve_recipe_asset_path(payload["path"], repo_root=repo_root, workspace=workspace)
        commands.append(command)
    return commands


def load_recipe(slug: str, recipes_root: Path = RECIPES_ROOT) -> dict[str, Any]:
    """Load one recipe by slug and resolve repo-relative command paths."""

    recipe_dir = _find_recipe_dir(slug, recipes_root)
    data = _read_scene_json(recipe_dir / "scene.json")
    meta = _metadata(recipe_dir, data)
    commands = _resolved_commands(data, repo_root=recipes_root.parents[1])
    return {**meta, "commands": commands, "raw": data}


def _apply_overrides(commands: list[dict[str, Any]], overrides: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not overrides:
        return commands
    updated = copy.deepcopy(commands)
    for command in updated:
        op = command.get("op")
        patch = overrides.get(str(op)) if isinstance(op, str) else None
        if isinstance(patch, Mapping):
            payload = command.setdefault("payload", {})
            if isinstance(payload, dict):
                payload.update(dict(patch))
    return updated


def _rewrite_preview_outputs(commands: list[dict[str, Any]], *, slug: str, workspace: Workspace) -> list[dict[str, Any]]:
    """Save native previews inside the Octane sandbox so Octane can write them reliably."""

    updated = copy.deepcopy(commands)
    workspace.ensure()
    for command in updated:
        if command.get("op") != "save_preview":
            continue
        payload = command.setdefault("payload", {})
        if not isinstance(payload, dict):
            continue
        original_path = str(payload.get("path") or "").strip()
        filename = Path(original_path).name or f"{slug}-octane-preview.png"
        if not filename.lower().endswith(".png"):
            filename = f"{filename}.png"
        payload["bundle_path"] = original_path
        payload["path"] = str((workspace.renders_dir / filename).resolve())
    return updated


def _validate_recipe_command(command: Mapping[str, Any], idx: int) -> None:
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "id": f"recipe-{idx}",
        "op": command.get("op"),
        "payload": command.get("payload") or {},
        "created_at": "2026-01-01T00:00:00Z",
        "source": "octanex-mcp",
    }
    validation = validate_command(envelope)
    if not validation.ok:
        raise ValueError(f"invalid recipe command {idx} ({command.get('op')}): " + "; ".join(validation.errors))


def queue_recipe(slug: str, overrides: Mapping[str, Any] | None = None, *, workspace: Workspace = Workspace(), recipes_root: Path = RECIPES_ROOT) -> dict[str, Any]:
    """Queue a checked-in recipe command sequence by slug.

    ALWAYS flushes the shared/persistent queue first — unconditionally, even
    when the queue looks empty. The container ``queue/`` is shared across
    sessions, the autonomous steward, and parallel agents, so it refills
    silently; a leftover backlog would render the wrong scene or wedge the
    drain. flush_queue MOVEs files into a dated backup dir (never deletes), so
    the operation is recoverable.
    """

    flush_res = flush_queue(workspace)
    recipe_dir = _find_recipe_dir(slug, recipes_root)
    data = _read_scene_json(recipe_dir / "scene.json")
    meta = _metadata(recipe_dir, data)
    commands = _resolved_commands(data, repo_root=recipes_root.parents[1], workspace=workspace)
    commands = _apply_overrides(commands, overrides)
    commands = _rewrite_preview_outputs(commands, slug=meta["slug"], workspace=workspace)
    queued = []
    for idx, command in enumerate(commands):
        _validate_recipe_command(command, idx)
        queued.append(write_command(str(command["op"]), dict(command.get("payload") or {}), workspace))
    return {
        "slug": meta["slug"],
        "title": meta["title"],
        "flushed": flush_res["flushed"],
        "queued_count": len(queued),
        "queued_commands": queued,
        "expected_next_action": "Run octane_lua/hermes_bridge_oneshot.generated.lua inside Octane X, then save/review preview evidence before claiming native render success.",
    }


def validate_recipe_library(recipes_root: Path = RECIPES_ROOT) -> dict[str, Any]:
    """Validate recipe files, metadata, assets, and command payloads."""

    items: list[dict[str, Any]] = []
    for recipe_dir in _recipe_dirs(recipes_root):
        errors: list[str] = []
        try:
            data = _read_scene_json(recipe_dir / "scene.json")
            meta = _metadata(recipe_dir, data)
            if meta["slug"] != recipe_dir.name:
                errors.append("slug should match recipe directory name")
            for filename in ("README.md", "scene.obj", "scene.json"):
                if not (recipe_dir / filename).exists():
                    errors.append(f"missing {filename}")
            if not meta["preview_exists"]:
                errors.append("missing preview.png, photoreal-preview.png, or octane-preview.png")
            commands = _resolved_commands(data, repo_root=recipes_root.parents[1])
            if not commands:
                errors.append("commands must not be empty")
            for idx, command in enumerate(commands):
                try:
                    _validate_recipe_command(command, idx)
                except ValueError as exc:
                    errors.append(str(exc))
        except Exception as exc:
            meta = {"slug": recipe_dir.name, "scene_json_path": str(recipe_dir / "scene.json")}
            errors.append(str(exc))
        items.append({"slug": meta["slug"], "path": str(recipe_dir), "ok": not errors, "errors": errors})
    invalid = sum(1 for item in items if not item["ok"])
    return {"ok": invalid == 0, "checked": len(items), "invalid": invalid, "items": items}
