# Scene plans

Scene plans are semantic manifests that compile into the existing allowlisted Octane command queue. They are the bridge between one-off visual generators and reusable scene graphs.

## Minimal schema

```json
{
  "schema_version": "1.0",
  "scene_manifest_version": "2.0",
  "scene_id": "terrain_markers_001",
  "intent": "show terrain with marker primitives",
  "units": "arbitrary",
  "objects": [
    {
      "id": "surface",
      "type": "mesh",
      "path": "/absolute/path/to/surface.obj",
      "format": "obj",
      "material": "terrain_mat"
    }
  ],
  "materials": [
    {
      "name": "terrain_mat",
      "kind": "glossy",
      "color": [0.2, 0.7, 0.3],
      "roughness": 0.25
    }
  ],
  "camera": {"position": [1, -3, 2], "target": [0, 0, 0], "fov": 40},
  "lighting": {"preset": "soft_studio"},
  "render": {"samples": 128, "width": 1280, "height": 1280},
  "groups": [],
  "annotations": [],
  "quality_targets": {},
  "provenance": {}
}
```

## Primitive objects

Scene manifest v2 can compile simple primitives to OBJ assets before queueing `import_geometry`. Supported initial primitive types are `box`, `sphere`, `ellipsoid`, and `cylinder`.

```json
{
  "id": "marker_box",
  "type": "box",
  "size": [1, 1, 0.25],
  "material": "terrain_mat",
  "transform": {
    "translate": [1, 2, 0.5],
    "rotate_euler": [0, 0, 45],
    "scale": [1, 2, 1]
  },
  "semantic_role": "annotation_marker",
  "tags": ["primitive", "marker"]
}
```

Generated manifests write the asset `path`, `format`, and `bounds` back into each primitive object. The queued `import_geometry` payload also carries `transform` and `bounds` metadata so the Lua bridge and future patch tools can preserve semantic intent even though the current OBJ compiler bakes translation/scale into vertices.

## Stable namespacing

Compiled Octane node names use:

```text
Hermes::<scene_id>::<object_or_material_id>
```

For example, object `surface` in scene `terrain_markers_001` becomes:

```text
Hermes::terrain_markers_001::surface
```

This gives future replace/update commands stable object identity instead of relying on ad-hoc mesh names.

## Tools

- `octane_save_scene_manifest(scene_plan)` saves the normalized manifest under `scenes/<scene_id>.json` without queueing commands.
- `octane_build_scene(scene_plan)` saves the manifest and queues validated `create_material`, `import_geometry`, `assign_material`, `set_camera`, `set_lighting`, and `start_render` commands.
- `octane_load_scene_manifest(scene_id)` loads a saved manifest.
- `octane_add_object(scene_id, object_spec)`, `octane_update_object(scene_id, object_id, changes)`, and `octane_remove_object(scene_id, object_id)` incrementally edit saved manifests while keeping object IDs stable.
- `octane_requeue_scene(scene_id)` loads a saved manifest and queues its validated commands again.

Current support is intentionally narrow: mesh objects, first-pass primitives, material assignment, camera, lighting, and render settings. Add richer object types by extending the compiler while keeping the emitted command DSL allowlisted.
