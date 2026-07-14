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


def recipe_to_canvas_scene(slug: str, recipes_root: Path = RECIPES_ROOT) -> dict[str, Any]:
    """Instantiate a recipe's bundled ``scene.obj`` as a live ``canvas.scene.v1``.

    The recipe is a pre-built scene: its geometry lives in ``scene.obj``
    (``mtllib scene.mtl``, one ``o`` group, optional ``usemtl`` sub-groups).
    We parse the OBJ into mesh objects so the WebGL canvas can render and
    pick/edit them exactly like a freshly-built scene — the recipe becomes a
    real starting point for interactive development, not a flat screenshot.

    Returns a ``canvas.scene.v1``-shaped dict. Raises ``ValueError`` if the
    recipe has no meshable ``scene.obj``.
    """
    recipe_dir = _find_recipe_dir(slug, recipes_root)
    obj_path = recipe_dir / "scene.obj"
    if not obj_path.exists():
        raise ValueError(f"recipe {slug!r} has no scene.obj to instantiate")

    verts: list[list[float]] = []
    normals: list[list[float]] = []
    # One mesh per material *region*: every `o`/`g`/`usemtl` line starts a new
    # region so the full mesh hierarchy loads (a generated OBJ may carry dozens
    # of `usemtl` blocks under a single `o` group). Keyed by a monotonic
    # region index, not the (group, mtl) tuple, which would silently merge
    # distinct regions that reuse a material name.
    groups: dict[int, dict[str, Any]] = {}
    active_group = "_default"
    active_mtl = None
    mtllib_name = None
    region = 0

    def _face(indices: list[str]) -> list[int]:
        # OBJ faces are 1-based; support v/vt/vn triples, ignore vt/vn here.
        return [int(tok.split("/")[0]) for tok in indices]

    def _new_region() -> dict[str, Any]:
        nonlocal region
        region += 1
        g = {"mtl": active_mtl, "faces": []}
        groups[region] = g
        return g

    _new_region()

    for raw in obj_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        tag = parts[0]
        if tag == "mtllib":
            mtllib_name = parts[1] if len(parts) > 1 else None
        elif tag == "o" or tag == "g":
            active_group = " ".join(parts[1:]) or active_group
            _new_region()
        elif tag == "v":
            verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
        elif tag == "vn":
            normals.append([float(parts[1]), float(parts[2]), float(parts[3])])
        elif tag == "usemtl":
            active_mtl = parts[1] if len(parts) > 1 else None
            _new_region()
        elif tag == "f":
            groups[region]["faces"].append(_face(parts[1:]))

    if not verts or all(not g["faces"] for g in groups.values()):
        raise ValueError(f"recipe {slug!r} scene.obj has no meshable faces")

    # Materials: prefer colors from scene.mtl (newmtl + Kd). When the OBJ has
    # no mtl (generated visualizer meshes), derive a stable per-region shade
    # so the hierarchy reads as distinct parts instead of one grey blob.
    mat_colors: dict[str, list[float]] = {}
    mtl_path = recipe_dir / (mtllib_name or "scene.mtl")
    if mtl_path.exists():
        cur = None
        for ml in mtl_path.read_text(encoding="utf-8", errors="replace").splitlines():
            mp = ml.strip().split()
            if not mp:
                continue
            if mp[0] == "newmtl":
                cur = mp[1]
                mat_colors[cur] = [0.8, 0.8, 0.8]
            elif mp[0] == "Kd" and cur:
                try:
                    mat_colors[cur] = [float(mp[1]), float(mp[2]), float(mp[3])]
                except (IndexError, ValueError):
                    pass

    def _rgb_to_hex(rgb: list[float]) -> str:
        return "#" + "".join(f"{int(max(0.0, min(1.0, c)) * 255):02x}" for c in rgb)

    def _fallback_color(i: int) -> list[float]:
        # Even hue walk; desaturate so it reads as a CAD/diagram palette.
        import colorsys
        h = (i * 0.137) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, 0.45, 0.85)
        return [r, g, b]

    materials: list[dict[str, Any]] = []
    objects: list[dict[str, Any]] = []

    for gi, (rid, gdata) in enumerate(groups.items()):
        if not gdata["faces"]:
            continue
        mtl = gdata.get("mtl")
        mat_id = f"mat_{gi}"
        color = mat_colors.get(mtl, _fallback_color(gi)) if mtl else _fallback_color(gi)
        materials.append({"id": mat_id, "color": _rgb_to_hex(color), "roughness": 0.6, "metalness": 0.0})
        # Pack positions as a flat triangle list (fan/triangle fan per face).
        positions: list[float] = []
        for f in gdata["faces"]:
            if len(f) < 3:
                continue
            tri = f[:3]
            for vi in tri:
                v = verts[vi - 1]
                positions.extend([float(v[0]), float(v[1]), float(v[2])])
            # Triangulate polygons with 4+ verts as a fan.
            for k in range(2, len(f) - 1):
                for vi in (f[0], f[k], f[k + 1]):
                    v = verts[vi - 1]
                    positions.extend([float(v[0]), float(v[1]), float(v[2])])
        label = (mtl or f"region {gi}").split("/")[-1]
        objects.append({
            "id": f"{slug}_{gi}",
            "type": "mesh",
            "label": label,
            "material": mat_id,
            "geometry": {"type": "triangles", "positions": positions},
        })

    if not objects:
        raise ValueError(f"recipe {slug!r} produced no mesh objects")

    scene = {
        "schema_version": SCHEMA_VERSION,
        "scene_id": slug,
        "title": slug.replace("-", " ").title(),
        "provenance": {"source": "recipe", "slug": slug},
        "objects": objects,
        "materials": materials,
        "environment": {"background": "#070a0e", "lighting": "soft_studio"},
    }
    return scene


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


def _is_regenerable_recipe(slug: str, recipe_dir: Path, data: Mapping[str, Any]) -> bool:
    """True when a missing scene.obj is acceptable because it is regenerable.

    The repo deliberately gitignores some large recipe OBJs (e.g.
    ``earth-hemisphere``, excluded on the Mac Studio working copy for size).
    Those recipes ship a committed generator (``scripts/gen_<slug>.py``) that
    produces ``scene.obj`` locally, so the OBJ is NOT a checkout-required asset
    and its absence must not fail the offline contract on a clean clone.

    Judges regenerability from the presence of a committed generator plus
    evidence the recipe references the OBJ (a top-level field or a ``scene.obj``
    mention in scene.json).
    """
    gen = REPO_ROOT / "scripts" / f"gen_{slug.replace('-', '_')}.py"
    if not gen.exists():
        return False
    for token in (data.get("obj_path"), data.get("path"), data.get("geometry_path")):
        if isinstance(token, str) and token.replace("/", "").endswith("scene.obj"):
            return True
    try:
        blob = (recipe_dir / "scene.json").read_text(encoding="utf-8")
        if "scene.obj" in blob:
            return True
    except OSError:
        pass
    return False


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
            # scene.obj: a missing OBJ is a hard error UNLESS the recipe is
            # regenerable (large OBJ gitignored with a committed generator —
            # e.g. earth-hemisphere). In that case the contract still holds on a
            # clean checkout without committing the asset, so it is not an error.
            if not (recipe_dir / "scene.obj").exists() and not _is_regenerable_recipe(meta["slug"], recipe_dir, data):
                errors.append("missing scene.obj")
            if not (recipe_dir / "README.md").exists():
                errors.append("missing README.md")
            if not (recipe_dir / "scene.json").exists():
                errors.append("missing scene.json")
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
