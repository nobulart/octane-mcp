from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Sequence

# Keep bridge import separate to avoid circular import
# Workspace and write_command are used at module level
# octane_patch_scene is loaded lazily via __getattr__
from .bridge import Workspace, write_command
from .schema import SCHEMA_VERSION, validate_command
from .visuals import create_primitive_obj

if TYPE_CHECKING:
    from .bridge import octane_patch_scene as octane_patch_scene


def _safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.:-]+", "_", str(value).strip())
    return safe.strip("_") or "scene"


# Provide octane_patch_scene via lazy access
_octane_patch_scene = None


def _get_octane_patch_scene():
    global _octane_patch_scene
    if _octane_patch_scene is None:
        from .bridge import octane_patch_scene as _ops
        _octane_patch_scene = _ops
    return _octane_patch_scene


def __getattr__(name: str) -> Any:
    if name == "octane_patch_scene":
        return _get_octane_patch_scene()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def namespaced(scene_id: str, object_id: str) -> str:
    return f"Hermes::{_safe_id(scene_id)}::{_safe_id(object_id)}"


def normalize_scene_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    scene_id = _safe_id(str(plan.get("scene_id") or "scene"))
    normalized = dict(plan)
    normalized["schema_version"] = str(plan.get("schema_version") or SCHEMA_VERSION)
    normalized["scene_manifest_version"] = str(plan.get("scene_manifest_version") or "2.0")
    normalized["scene_id"] = scene_id
    normalized.setdefault("intent", "")
    normalized.setdefault("units", "arbitrary")
    normalized.setdefault("objects", [])
    normalized.setdefault("materials", [])
    normalized.setdefault("groups", [])
    normalized.setdefault("annotations", [])
    normalized.setdefault("camera", {})
    normalized.setdefault("lighting", {})
    normalized.setdefault("render", {})
    normalized.setdefault("quality_targets", {})
    normalized.setdefault("provenance", {})
    normalized["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not isinstance(normalized["objects"], list):
        raise ValueError("scene_plan.objects must be a list")
    if not isinstance(normalized["materials"], list):
        raise ValueError("scene_plan.materials must be a list")
    if not isinstance(normalized["groups"], list):
        raise ValueError("scene_plan.groups must be a list")
    _assign_stable_ids(normalized)
    return normalized


def _assign_stable_ids(scene: dict[str, Any]) -> None:
    """Assign persistent ``uid`` + human ``#N`` / ``#Gk`` labels to a scene.

    Human-facing indices are the bridge between the user's speech
    ("change object #43") and the stable node names the bridge uses. Two rules
    make them trustworthy:

    1. **Stable uid.** Every object/group gets a ``uid`` that never changes
       for the life of the scene. Node names stay ``Hermes::<scene>::<id>``,
       where ``<id>`` is the uid.
    2. **Never-renumbering labels.** The ``#N`` (objects) / ``#Gk`` (groups)
       badge shown in the dev overlay is assigned once and then *preserved* across
       add/remove. Removing an object leaves a gap (``#42``, ``#44`` with no
       ``#43``) rather than silently shifting every later index — otherwise the
       user's "#43" would point at a different object after any edit.

    The mapping ``labels: {"#43": "<uid>"}`` plus ``group_labels:
    {"#G2": "<guid>"}`` lets the ref-resolver turn "#6 through #10 and #54"
    into a concrete uid set without ever renumbering.
    """
    objects = scene.setdefault("objects", [])
    groups = scene.setdefault("groups", [])

    # Assign a stable uid per object. Seed from the human "id" when present
    # (so node names stay Hermes::<scene>::<id>, preserving the bridge's
    # find-by-name contract and swap_geometry's stable-node guarantee), and
    # mint "oNNNN" only when an id/uid is absent or would collide. Once set,
    # a uid is sticky across reloads (never reseeded from a changed id).
    used_uids: set[str] = set()
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        existing = obj.get("uid")
        if existing and existing not in used_uids:
            used_uids.add(existing)
            continue
        seed = obj.get("id") or obj.get("name")
        if seed and str(seed) not in used_uids:
            obj["uid"] = str(seed)
            used_uids.add(str(seed))
        else:
            n = 1
            while f"o{n:04d}" in used_uids:
                n += 1
            obj["uid"] = f"o{n:04d}"
            used_uids.add(obj["uid"])
    used_guids: set[str] = set()
    for grp in groups:
        if not isinstance(grp, dict):
            continue
        guid = grp.get("guid")
        if not guid or guid in used_guids:
            guid = f"g{len(used_guids) + 1:03d}"
            grp["guid"] = guid
        used_guids.add(guid)

    # Build / preserve the never-renumbering badge map.
    # Live objects keep their existing badge; dead badges (whose uid no longer
    # has a live object) are DROPPED, leaving a gap rather than a dangling
    # reference. New objects get the next free badge. This is the correct
    # "never renumber" contract: removing #2 leaves "#1, #3" (not "#1, #2"
    # with #2 now pointing at a different object).
    live_uids = {str(o.get("uid")) for o in objects if isinstance(o, dict)}
    labels = {
        badge: uid
        for badge, uid in (scene.get("labels") or {}).items()
        if uid in live_uids
    }
    label_for_uid: dict[str, str] = {v: k for k, v in labels.items()}
    next_obj_badge = 1
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        uid = obj["uid"]
        if uid in label_for_uid:
            continue  # keep the existing badge
        while f"#{next_obj_badge}" in labels:
            next_obj_badge += 1
        badge = f"#{next_obj_badge}"
        labels[badge] = uid
        label_for_uid[uid] = badge
        next_obj_badge += 1

    live_guids = {str(g.get("guid")) for g in groups if isinstance(g, dict)}
    group_labels = {
        badge: guid
        for badge, guid in (scene.get("group_labels") or {}).items()
        if guid in live_guids
    }
    glabel_for_guid: dict[str, str] = {v: k for k, v in group_labels.items()}
    next_grp_badge = 1
    for grp in groups:
        if not isinstance(grp, dict):
            continue
        guid = grp["guid"]
        if guid in glabel_for_guid:
            continue
        while f"#G{next_grp_badge}" in group_labels:
            next_grp_badge += 1
        badge = f"#G{next_grp_badge}"
        group_labels[badge] = guid
        glabel_for_guid[guid] = badge
        next_grp_badge += 1

    scene["labels"] = labels
    scene["group_labels"] = group_labels


def _object_uid(obj: Mapping[str, Any]) -> str:
    return str(obj.get("uid") or obj.get("id") or obj.get("name") or "object")


def _group_guid(grp: Mapping[str, Any]) -> str:
    return str(grp.get("guid") or grp.get("id") or "group")


def resolve_label_refs(scene: Mapping[str, Any], text: str) -> list[str]:
    """Resolve a human label phrase into a list of object uids.

    Handles ``#43``, ``#1 and #3``, ``#6 through #10``, ``#G2`` (groups expand
    to their member uids). Returns uids that exist in the scene; unknown badges
    are silently dropped (the caller should surface "no object #99" separately if
    needed — this keeps batch ops resilient).
    """
    labels: dict[str, str] = dict(scene.get("labels") or {})
    group_labels: dict[str, str] = dict(scene.get("group_labels") or {})
    group_members: dict[str, list[str]] = {
        str(g.get("guid") or g.get("id")): list(g.get("members") or [])
        for g in (scene.get("groups") or [])
        if isinstance(g, Mapping)
    }

    text = text.lower()
    uids: list[str] = []

    # "through/.." ranges first: #6 through #10
    for m in re.finditer(r"#\s*(\d+)\s*(?:through|to|-|–|—)\s*#?\s*(\d+)", text):
        a, b = int(m.group(1)), int(m.group(2))
        lo, hi = min(a, b), max(a, b)
        for n in range(lo, hi + 1):
            uid = labels.get(f"#{n}")
            if uid and uid not in uids:
                uids.append(uid)

    # single badges: #43, #G2
    for m in re.finditer(r"#\s*([a-z]?)\s*(\d+)", text):
        prefix, num = m.group(1), m.group(2)
        if prefix == "g":
            guid = group_labels.get(f"#G{num}")
            if guid:
                for member in group_members.get(guid, []):
                    if member not in uids:
                        uids.append(member)
        else:
            uid = labels.get(f"#{num}")
            if uid and uid not in uids:
                uids.append(uid)
    return uids


_PRIMITIVE_TYPES = {"box", "sphere", "ellipsoid", "cylinder"}


def build_scene_commands(plan: Mapping[str, Any], workspace: Workspace = Workspace()) -> list[dict[str, Any]]:
    scene = normalize_scene_plan(plan)
    scene_id = scene["scene_id"]
    commands: list[dict[str, Any]] = []
    material_names: dict[str, str] = {}

    for material in scene["materials"]:
        if not isinstance(material, Mapping):
            raise ValueError("scene_plan.materials entries must be objects")
        raw_name = str(material.get("name") or material.get("id") or "material")
        namespaced_name = namespaced(scene_id, raw_name)
        material_names[raw_name] = namespaced_name
        payload = dict(material)
        payload["name"] = namespaced_name
        commands.append({"op": "create_material", "payload": payload})

    for obj in scene["objects"]:
        if not isinstance(obj, Mapping):
            raise ValueError("scene_plan.objects entries must be objects")
        obj_type = str(obj.get("type", "mesh"))
        # Prefer the stable uid so the human "#N" label resolves to a fixed
        # node name (Hermes::<scene>::<uid>) regardless of list order.
        object_id = _object_uid(obj)
        object_name = namespaced(scene_id, object_id)
        if obj_type in _PRIMITIVE_TYPES:
            asset = create_primitive_obj(dict(obj), scene_id=scene_id, workspace=workspace)
            obj["path"] = asset["path"]
            obj["format"] = asset["format"]
            obj["bounds"] = asset["bounds"]
        elif obj_type != "mesh":
            raise ValueError(f"unsupported scene object type {obj_type!r}")
        path = obj.get("path")
        if not path:
            raise ValueError(f"scene object {object_id!r} is missing path")
        payload = {"path": str(path), "format": str(obj.get("format") or "obj"), "name": object_name}
        if obj.get("transform") is not None:
            payload["transform"] = obj.get("transform")
        if obj.get("bounds") is not None:
            payload["bounds"] = obj.get("bounds")
        commands.append({"op": "import_geometry", "payload": payload})
        material_ref = obj.get("material")
        if material_ref:
            material_name = material_names.get(str(material_ref), namespaced(scene_id, str(material_ref)))
            commands.append({"op": "assign_material", "payload": {"object_name": object_name, "material_name": material_name}})

    camera = scene.get("camera") or {}
    if camera:
        cmd_payload = dict(camera)
        # Ensure target is present for set_camera validation
        if "target" not in cmd_payload:
            cmd_payload["target"] = [0.0, 0.0, 0.0]
        commands.append({"op": "set_camera", "payload": cmd_payload})
    lighting = scene.get("lighting") or {}
    if lighting:
        commands.append({"op": "set_lighting", "payload": dict(lighting)})
    render = scene.get("render") or {}
    if render:
        commands.append({"op": "start_render", "payload": dict(render)})

    for idx, command in enumerate(commands):
        envelope = {
            "schema_version": SCHEMA_VERSION,
            "id": f"scene-{idx}",
            "op": command["op"],
            "payload": command["payload"],
            "created_at": "2026-01-01T00:00:00Z",
            "source": "octanex-mcp",
        }
        validation = validate_command(envelope)
        if not validation.ok:
            raise ValueError(f"invalid scene command {idx} ({command['op']}): " + "; ".join(validation.errors))
    return commands


def save_scene_manifest(plan: Mapping[str, Any], workspace: Workspace = Workspace()) -> dict[str, Any]:
    workspace.ensure()
    scene = normalize_scene_plan(plan)
    commands = build_scene_commands(scene, workspace)
    scene["commands"] = commands
    path = _scene_manifest_path(scene["scene_id"], workspace)
    path.write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    return {"saved": True, "path": str(path), "scene_id": scene["scene_id"], "command_count": len(commands)}


def _scene_manifest_path(scene_id: str, workspace: Workspace) -> Path:
    return workspace.scenes_dir / f"{_safe_id(scene_id)}.json"


def load_scene_manifest(scene_id: str, workspace: Workspace = Workspace()) -> dict[str, Any]:
    workspace.ensure()
    path = _scene_manifest_path(scene_id, workspace)
    if not path.exists():
        raise FileNotFoundError(f"scene manifest not found: {path}")
    scene = normalize_scene_plan(json.loads(path.read_text(encoding="utf-8")))
    return {"loaded": True, "path": str(path), "scene_id": scene["scene_id"], "scene": scene}


def _save_loaded_scene(scene: Mapping[str, Any], workspace: Workspace) -> dict[str, Any]:
    payload = dict(scene)
    payload.pop("commands", None)
    return save_scene_manifest(payload, workspace)


def add_scene_object(scene_id: str, object_spec: Mapping[str, Any], workspace: Workspace = Workspace()) -> dict[str, Any]:
    try:
        loaded = load_scene_manifest(scene_id, workspace)
    except FileNotFoundError:
        loaded = {"scene": {"scene_id": scene_id, "objects": [], "materials": []}}
        loaded["scene"].setdefault("objects", [])
        loaded["scene"].setdefault("materials", [])
    scene = loaded["scene"]
    obj = dict(object_spec)
    object_id = str(obj.get("id") or obj.get("name") or "object")
    if any(str(existing.get("id") or existing.get("name") or "object") == object_id for existing in scene["objects"]):
        raise ValueError(f"scene object already exists: {object_id}")
    scene["objects"].append(obj)
    saved = _save_loaded_scene(scene, workspace)
    return {**saved, "object": obj, "object_count": len(scene["objects"])}


def update_scene_object(scene_id: str, object_id: str, changes: Mapping[str, Any], workspace: Workspace = Workspace()) -> dict[str, Any]:
    loaded = load_scene_manifest(scene_id, workspace)
    scene = loaded["scene"]
    for obj in scene["objects"]:
        current_id = str(obj.get("id") or obj.get("name") or "object")
        if current_id == object_id:
            obj.update(dict(changes))
            saved = _save_loaded_scene(scene, workspace)
            return {**saved, "object": obj, "object_count": len(scene["objects"])}
    raise ValueError(f"scene object not found: {object_id}")


def remove_scene_object(scene_id: str, object_id: str, workspace: Workspace = Workspace()) -> dict[str, Any]:
    loaded = load_scene_manifest(scene_id, workspace)
    scene = loaded["scene"]
    kept = []
    removed = None
    for obj in scene["objects"]:
        current_id = str(obj.get("id") or obj.get("name") or "object")
        if current_id == object_id:
            removed = obj
        else:
            kept.append(obj)
    if removed is None:
        raise ValueError(f"scene object not found: {object_id}")
    scene["objects"] = kept
    saved = _save_loaded_scene(scene, workspace)
    return {**saved, "removed": removed, "object_count": len(kept)}


def swap_geometry(
    scene_id: str,
    object_id: str,
    new_path: str,
    format: str = "obj",
    queue: bool = False,
    workspace: Workspace = Workspace(),
) -> dict[str, Any]:
    """Replace an object's geometry asset in place while preserving its stable
    node name (``Hermes::scene::object``).

    This is the **replaceable-asset-files** primitive of the streaming data-grammar
    protocol (see ``docs/canvas-roadmap.md`` §2): the scene node identity stays fixed
    so the geometry can be hot-swapped without rebuilding the rest of the scene. It is
    the asset counterpart to the existing stable ``namespaced`` node-name scheme.

    Reuses the existing ``import_geometry`` op (no schema or Lua change). The new asset
    file must already exist on disk — this function swaps the reference, it does not
    fabricate geometry.

    Args:
        scene_id: target scene manifest id.
        object_id: id/name of the object whose asset to replace.
        new_path: path to the replacement OBJ/geometry file (must exist).
        format: geometry format passed through to ``import_geometry`` (default ``obj``).
        queue: when True, also write the swap command into the command queue so the
            bridge can hot-replace the mesh on the next drain.
        workspace: workspace override for tests.

    Returns a dict with the saved manifest result, the resolved stable ``node_name``,
    the new ``path``, and a schema-valid ``swap_command`` envelope targeting that node.
    """
    loaded = load_scene_manifest(scene_id, workspace)
    scene = loaded["scene"]
    target_id = str(object_id)
    for obj in scene["objects"]:
        current_id = str(obj.get("id") or obj.get("name") or "object")
        if current_id == target_id:
            new_p = Path(new_path)
            if not new_p.exists():
                raise FileNotFoundError(f"swap geometry target not found: {new_path}")
            obj["path"] = str(new_path)
            obj["format"] = format
            # The user now supplies their own geometry, so stop auto-generating a
            # primitive on rebuild — otherwise build_scene_commands regenerates the
            # OBJ from type+size and overwrites the swapped path.
            obj["type"] = "mesh"
            saved = _save_loaded_scene(scene, workspace)
            node_name = namespaced(scene["scene_id"], current_id)
            swap_command = {
                "schema_version": SCHEMA_VERSION,
                "id": f"swap-{scene['scene_id']}-{current_id}",
                "op": "import_geometry",
                "payload": {"path": str(new_path), "format": format, "name": node_name},
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "source": "octanex-mcp",
            }
            validation = validate_command(swap_command)
            if not validation.ok:
                raise ValueError("swap command failed validation: " + "; ".join(validation.errors))
            result: dict[str, Any] = {
                **saved,
                "object_id": current_id,
                "node_name": node_name,
                "path": str(new_path),
                "swap_command": swap_command,
            }
            if queue:
                from .bridge import write_command

                deferred = write_command(swap_command["op"], swap_command["payload"], workspace)
                result["queued_command"] = deferred
            return result
    raise ValueError(f"scene object not found: {object_id}")


def queue_scene_plan(plan: Mapping[str, Any], workspace: Workspace = Workspace()) -> dict[str, Any]:
    manifest = save_scene_manifest(plan, workspace)
    commands = build_scene_commands(plan, workspace)
    queued = [write_command(command["op"], command["payload"], workspace) for command in commands]
    return {"scene_id": manifest["scene_id"], "manifest": manifest, "queued_commands": queued}


def requeue_scene(scene_id: str, workspace: Workspace = Workspace()) -> dict[str, Any]:
    loaded = load_scene_manifest(scene_id, workspace)
    return queue_scene_plan(loaded["scene"], workspace)


def group_objects(
    scene_id: str,
    refs: str,
    group_name: str | None = None,
    workspace: Workspace = Workspace(),
) -> dict[str, Any]:
    """Merge the objects referenced by ``refs`` into one node (geometry grouping).

    ``refs`` is a human label phrase (``"#6 through #10 and #54"``). The resolved
    member OBJs are merged into a single asset via :func:`meshmod.merge_objs`,
    the members are removed (they are now represented by the merged node), and a
    new merged object plus a ``#Gk`` group entry are added. Because merged node
    identity is the group, the group can be addressed later as a unit.

    Returns the saved manifest plus ``merged_node`` (stable node name) and the
    new group guid.
    """
    loaded = load_scene_manifest(scene_id, workspace)
    scene = loaded["scene"]
    uids = resolve_label_refs(scene, refs)
    if not uids:
        raise ValueError(f"no objects resolved from refs: {refs!r}")
    by_uid = {_object_uid(o): o for o in scene["objects"] if isinstance(o, Mapping)}
    member_paths = []
    for uid in uids:
        obj = by_uid.get(uid)
        if obj is None:
            continue
        p = obj.get("path")
        if p:
            member_paths.append(str(p))
    if len(member_paths) < 2:
        raise ValueError("group needs at least two valid geometry objects")

    from . import meshmod

    name = group_name or _safe_id(f"{scene_id}_group_{len(scene.get('groups', [])) + 1}")
    merged = meshmod.merge_objs(member_paths, out_name=name, workspace=workspace)

    # Replace members with the merged node; record a group entry for #Gk.
    kept = [o for o in scene["objects"] if isinstance(o, Mapping) and _object_uid(o) not in set(uids)]
    merged_obj: dict[str, Any] = {
        "id": name,
        "type": "mesh",
        "path": merged["path"],
        "format": "obj",
        "bounds": merged["bounds"],
        "members": uids,
        "semantic_role": "group",
    }
    kept.append(merged_obj)
    scene["objects"] = kept
    guid = f"g{len(scene.get('groups', [])) + 1:03d}"
    scene.setdefault("groups", []).append(
        {"guid": guid, "id": name, "members": uids, "merged_node": name}
    )
    saved = _save_loaded_scene(scene, workspace)
    return {
        **saved,
        "merged_node": namespaced(scene["scene_id"], name),
        "merged_path": merged["path"],
        "group_guid": guid,
        "member_count": len(member_paths),
        "vertex_count": merged["vertex_count"],
    }


def modify_objects(
    scene_id: str,
    refs: str,
    modifier: str,
    workspace: Workspace = Workspace(),
    **opts: Any,
) -> dict[str, Any]:
    """Apply a mesh modifier to each object in ``refs``, in place.

    ``modifier`` is ``"resolution"`` (subdivide) or ``"smooth"`` (Laplacian
    smoothing). Each target node keeps its stable name via ``swap_geometry`` —
    only its asset is replaced with the modified one.

    Returns per-object swap results keyed by uid.
    """
    modifier = str(modifier).lower()
    if modifier not in ("resolution", "smooth"):
        raise ValueError(f"unsupported modifier {modifier!r}; use 'resolution' or 'smooth'")
    loaded = load_scene_manifest(scene_id, workspace)
    scene = loaded["scene"]
    uids = resolve_label_refs(scene, refs)
    if not uids:
        raise ValueError(f"no objects resolved from refs: {refs!r}")
    by_uid = {_object_uid(o): o for o in scene["objects"] if isinstance(o, Mapping)}

    from . import meshmod

    results: dict[str, Any] = {}
    for uid in uids:
        obj = by_uid.get(uid)
        if obj is None:
            results[uid] = {"error": "object not in manifest"}
            continue
        src = obj.get("path")
        if not src:
            results[uid] = {"error": "object has no geometry path"}
            continue
        if modifier == "resolution":
            mod = meshmod.subdivide_obj(src, workspace=workspace, **opts)
        else:
            mod = meshmod.smooth_obj(src, workspace=workspace, **opts)
        swap = swap_geometry(scene_id, uid, mod["path"], queue=False, workspace=workspace)
        results[uid] = {
            "node_name": swap["node_name"],
            "new_path": mod["path"],
            "bounds": mod["bounds"],
            "face_count": mod.get("face_count"),
            "vertex_count": mod.get("vertex_count"),
        }
    return {"scene_id": scene_id, "modifier": modifier, "refs": refs, "results": results}


def animate_objects(
    scene_id: str,
    refs: str,
    motion: str,
    *,
    axis: str = "y",
    degrees: float = 0.0,
    offset: Sequence[float] | None = None,
    scale: Sequence[float] | None = None,
    start_frame: Any = 0,
    end_frame: Any = 24,
    fps: int = 24,
    easing: str = "ease_in_out_quad",
    workspace: Workspace = Workspace(),
) -> dict[str, Any]:
    """Queue a transform animation for the objects addressed by ``refs``.

    ``motion`` is ``"rotate"`` / ``"translate"`` / ``"scale"``. Each resolved
    node gets its own :class:`ObjectAnimationManifest` (per-object motion is
    independent), baked into ``set_object_transform`` + ``save_preview`` commands
    per frame and written to the queue. ``start_frame``/``end_frame`` accept ints
    or timecode strings; ``fps`` defaults to 24 (a common standard) when the user
    does not specify.

    Requires the scene's nodes to already exist in Octane (build the scene via
    ``queue_scene_plan`` / ``octane_build_scene`` first) -- this queues only the
    per-frame transform + render commands, exactly like ``octane_build_animation``.

    Returns the per-object bake summaries and the queued command count.
    """
    from . import animation

    loaded = load_scene_manifest(scene_id, workspace)
    scene = loaded["scene"]
    uids = resolve_label_refs(scene, refs)
    if not uids:
        raise ValueError(f"no objects resolved from refs: {refs!r}")
    by_uid = {_object_uid(o): o for o in scene["objects"] if isinstance(o, Mapping)}

    baked: dict[str, Any] = {}
    all_commands: list[dict[str, Any]] = []
    for uid in uids:
        obj = by_uid.get(uid)
        if obj is None:
            baked[uid] = {"error": "object not in manifest"}
            continue
        node_name = namespaced(scene["scene_id"], uid)
        if motion == "rotate":
            man = animation.object_rotate_manifest(
                node_name, axis=axis, degrees=degrees,
                start_frame=start_frame, end_frame=end_frame, fps=fps, easing=easing,
            )
        elif motion == "translate":
            man = animation.object_translate_manifest(
                node_name, offset=animation._v3(offset or (0.0, 0.0, 0.0)),
                start_frame=start_frame, end_frame=end_frame, fps=fps, easing=easing,
            )
        elif motion == "scale":
            from .animation import ObjectKeyframe, ObjectAnimationManifest as OAM

            sf = animation._parse_frame(start_frame, fps)
            ef = animation._parse_frame(end_frame, fps)
            target = animation._v3(scale or (1.0, 1.0, 1.0))
            man = OAM(
                object_name=node_name, start_frame=sf, end_frame=ef, fps=fps, easing=easing,
                keyframes=(
                    ObjectKeyframe(frame=sf, scale=(1.0, 1.0, 1.0)),
                    ObjectKeyframe(frame=ef, scale=target),
                ),
            )
        else:
            raise ValueError(f"unsupported motion {motion!r}; use rotate/translate/scale")
        cmds = animation.build_object_animation_commands(man)
        baked[uid] = {
            "node_name": node_name,
            "start_frame": man.start_frame,
            "end_frame": man.end_frame,
            "frame_count": man.end_frame - man.start_frame + 1,
            "command_count": len(cmds),
        }
        all_commands.extend(cmds)

    # Queue all per-frame commands for every targeted node.
    queued = [write_command(c["op"], c["payload"], workspace) for c in all_commands]
    return {
        "scene_id": scene_id,
        "motion": motion,
        "refs": refs,
        "fps": fps,
        "queued_command_count": len(queued),
        "baked": baked,
    }
