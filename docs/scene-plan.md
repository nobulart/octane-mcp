# Scene plans

Scene plans are semantic manifests that compile into the existing allowlisted Octane command queue. They are the bridge between one-off visual generators and reusable scene graphs.

## Minimal schema

```json
{
  "schema_version": "1.0",
  "scene_id": "terrain_markers_001",
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
  "render": {"samples": 128, "width": 1280, "height": 1280}
}
```

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

Current support is intentionally narrow: mesh objects plus material assignment, camera, lighting, and render settings. Add richer object types by extending the compiler while keeping the emitted command DSL allowlisted.
