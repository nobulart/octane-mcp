#!/usr/bin/env python3
"""Queue the full butterfly-on-white-surface studio scene into the OctaneX MCP
queue. Single combined OBJ (one import) so the bridge wires every group; per
group_index material assignment; 3-point emissive softboxes (warm key / cool
fill / neutral top); NO environment -> black background ("dark as night").

Run from repo root: uv run python scripts/queue_butterfly_scene.py
"""
import sys
sys.path.insert(0, ".")
from octanex_mcp.bridge import Workspace, write_command

ws = Workspace()
ws.ensure()

queued = []


def q(op, payload):
    r = write_command(op, payload, ws)
    queued.append((op, r.get("command_id")))
    print(f"queued {op:16s} -> {r.get('command_id')}  ({r.get('path')})")


# --- 1. import the single combined OBJ (all groups in one mesh) ------------
q("import_geometry", {
    "path": "assets/butterfly_studio.obj",
    "format": "obj",
    "name": "butterfly_studio",
})

# --- 2. materials (one per usemtl group, 1-based order) --------------------
# order: 1 surface, 2 sb_key(warm), 3 sb_fill(cool), 4 sb_top, 5 wing, 6 body

q("create_material", {  # 1 white surface
    "name": "mat_surface",
    "kind": "diffuse",
    "color": [0.92, 0.92, 0.93],
    "roughness": 0.5,
})

q("create_material", {  # 2 warm key softbox (HDR emissive)
    "name": "mat_sb_key",
    "kind": "diffuse",
    "color": [1, 1, 1],
    "roughness": 1.0,
    "emission": [2.4, 1.5, 0.7],
})

q("create_material", {  # 3 cool fill softbox
    "name": "mat_sb_fill",
    "kind": "diffuse",
    "color": [1, 1, 1],
    "roughness": 1.0,
    "emission": [1.0, 1.25, 2.2],
})

q("create_material", {  # 4 neutral-warm top softbox
    "name": "mat_sb_top",
    "kind": "diffuse",
    "color": [1, 1, 1],
    "roughness": 1.0,
    "emission": [1.9, 1.7, 1.4],
})

q("create_material", {  # 5 blue wing (glossy + subtle blue emission for saturation)
    "name": "mat_wing",
    "kind": "glossy",
    "color": [0.07, 0.28, 1.0],
    "roughness": 0.3,
    "emission": [0.05, 0.15, 0.6],
})

q("create_material", {  # 6 dark body
    "name": "mat_body",
    "kind": "diffuse",
    "color": [0.05, 0.05, 0.07],
    "roughness": 0.4,
})

# --- 3. assign each material to its group (1-based, write order) -----------
assignments = [
    ("mat_surface", 1),
    ("mat_sb_key", 2),
    ("mat_sb_fill", 3),
    ("mat_sb_top", 4),
    ("mat_wing", 5),
    ("mat_body", 6),
]
for mat_name, gi in assignments:
    q("assign_material", {
        "object_name": "butterfly_studio",
        "material_name": mat_name,
        "group_index": gi,
    })

# --- 4. camera: 3/4 view from front-upper-right ----------------------------
q("set_camera", {
    "position": [5.0, 3.4, 7.2],
    "target": [0.0, 0.55, 0.2],
    "fov": 38,
})

# --- 5. save preview (single real render start via do_start=true) ----------
q("save_preview", {
    "path": "renders/butterfly_studio.png",
    "width": 1280,
    "height": 1024,
    "samples": 256,
    "min_samples": 64,
    "timeout_seconds": 45,
})

print(f"\nqueued {len(queued)} commands")
