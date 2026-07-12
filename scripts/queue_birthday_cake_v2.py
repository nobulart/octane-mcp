#!/usr/bin/env python3
"""Queue the birthday-cake (v2 realism pass) render pipeline to the OctaneX MCP bridge.

Order matters: the bridge drains the queue in lexical (chrono) filename order, so
import_geometry is written first, then the 16 create_material, then the 16
assign_material(group_index) in the SAME 1-based group order as scene.obj, then
camera + lighting + save_preview. No start_render (save_preview already
renders + saves)."""
import json
import os
import time
import uuid
from datetime import datetime, timezone

ROOT = os.path.expanduser("~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP")
QUEUE = os.path.join(ROOT, "queue")
PREVIEW = os.path.join(ROOT, "renders", "birthday_cake_v2.png")
os.makedirs(QUEUE, exist_ok=True)

MATS = [
    ("mat_plate", "glossy", [0.90, 0.90, 0.93], 0.45),
    ("mat_icing_lower", "glossy", [0.93, 0.52, 0.66], 0.5),
    ("mat_icing_upper", "glossy", [0.97, 0.63, 0.78], 0.5),
    ("mat_drip_a", "glossy", [0.55, 0.92, 0.78], 0.4),
    ("mat_drip_b", "glossy", [0.98, 0.86, 0.35], 0.4),
    ("mat_drip_c", "glossy", [0.45, 0.72, 0.96], 0.4),
    ("mat_candle", "diffuse", [0.96, 0.96, 0.92], None),
    ("mat_flame", "glossy", [1.0, 0.6, 0.12], 0.15),
    ("mat_sprinkle1", "glossy", [1.0, 0.2, 0.2], 0.45),
    ("mat_sprinkle2", "glossy", [0.2, 0.8, 0.2], 0.45),
    ("mat_sprinkle3", "glossy", [0.2, 0.4, 1.0], 0.45),
    ("mat_sprinkle4", "glossy", [1.0, 0.8, 0.1], 0.45),
    ("mat_sprinkle5", "glossy", [1.0, 0.4, 0.7], 0.45),
    ("mat_sprinkle6", "glossy", [0.0, 0.9, 0.9], 0.45),
    ("mat_sprinkle7", "glossy", [1.0, 0.5, 0.0], 0.45),
    ("mat_sprinkle8", "glossy", [0.6, 0.0, 0.8], 0.45),
]

cmds = []
cmds.append(("import_geometry", {"path": os.path.join(ROOT, "assets", "birthday_cake.obj"),
                                 "format": "obj", "name": "birthday_cake"}))
for i, (name, kind, color, rough) in enumerate(MATS, start=1):
    payload = {"name": name, "kind": kind, "color": color}
    if rough is not None:
        payload["roughness"] = rough
    cmds.append(("create_material", payload))
for i, (name, _kind, _color, _rough) in enumerate(MATS, start=1):
    cmds.append(("assign_material", {"object_name": "birthday_cake",
                                      "material_name": name, "group_index": i}))
cmds.append(("set_camera", {"position": [2.8, 2.2, 3.2], "target": [0, 1.0, 0], "fov": 38}))
cmds.append(("set_lighting", {"preset": "soft_studio"}))
cmds.append(("save_preview", {"path": PREVIEW, "width": 1280, "height": 1280,
                              "samples": 256, "min_samples": 32, "timeout_seconds": 60}))

t0 = time.time()
paths = []
for op, payload in cmds:
    micros = int((t0 + len(paths) * 0.001) * 1_000_000)
    ts = f"{micros:018d}"
    fname = f"{ts}-{os.urandom(4).hex()}.json"
    p = os.path.join(QUEUE, fname)
    env = {
        "schema_version": "1.0",
        "id": uuid.uuid4().hex,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "op": op,
        "payload": payload,
    }
    with open(p, "w") as fh:
        json.dump(env, fh)
    paths.append(p)

print(f"queued {len(paths)} commands -> {QUEUE}")
print(f"preview will write -> {PREVIEW}")
