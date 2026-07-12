#!/usr/bin/env python3
"""Queue the birthday-cake render pipeline to the OctaneX MCP bridge.

Single source of truth: examples/recipes/birthday-cake/scene.json
  - `materials`  -> the 16 create_material + assign_material(group_index) ops
  - `camera`     -> the set_camera op
  - `commands`   -> the full ordered op list (import, materials, camera, lighting, save)
The script walks `commands` and resolves material/camera payloads from
`materials`/`camera` so the OBJ groups and recipe can NEVER drift apart.

Order matters: the bridge drains the queue in lexical (chrono) filename order, so
import_geometry is written first, then the 16 create_material, then the 16
assign_material in 1-based group order, then camera + lighting + save_preview.
No start_render (save_preview already renders + saves).
"""
import json
import os
import time
import uuid
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.expanduser("~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP")
QUEUE = os.path.join(ROOT, "queue")
PREVIEW = os.path.join(ROOT, "renders", "birthday_cake_v2.png")
RECIPE = os.path.join(REPO, "examples", "recipes", "birthday-cake", "scene.json")
ASSET = os.path.join(ROOT, "assets", "birthday_cake.obj")
os.makedirs(QUEUE, exist_ok=True)

data = json.load(open(RECIPE))
materials = data["materials"]
camera = data["camera"]
commands = data["commands"]

# Resolve each command payload against the recipe's materials/camera maps so the
# queued envelope matches scene.json exactly (no dual-source drift).
MAT_ORDER = [
    "mat_plate", "mat_icing_lower", "mat_icing_upper", "mat_drip_a", "mat_drip_b",
    "mat_drip_c", "mat_candle", "mat_flame", "mat_sprinkle1", "mat_sprinkle2",
    "mat_sprinkle3", "mat_sprinkle4", "mat_sprinkle5", "mat_sprinkle6",
    "mat_sprinkle7", "mat_sprinkle8",
]

cmds = []
for raw in commands:
    op = raw["op"]
    if op == "import_geometry":
        # point at the container asset (the generator writes it there)
        cmds.append((op, {"path": ASSET, "format": "obj", "name": "birthday_cake"}))
    elif op == "create_material":
        name = raw["payload"]["name"]
        m = materials[name]
        payload = {"name": name, "kind": m["kind"], "color": m["color"]}
        for k in ("roughness", "specular", "metallic", "transmission", "ior", "opacity", "clearcoat"):
            if k in m:
                payload[k] = m[k]
        cmds.append((op, payload))
    elif op == "assign_material":
        cmds.append((op, dict(raw["payload"])))  # group_index already correct
    elif op == "set_camera":
        cmds.append((op, dict(camera)))
    elif op == "set_lighting":
        cmds.append((op, dict(raw["payload"])))
    elif op == "save_preview":
        p = dict(raw["payload"])
        p["path"] = PREVIEW
        cmds.append((op, p))
    else:
        cmds.append((op, dict(raw["payload"])))

# sanity: exactly 16 materials, group_index 1..16
assert len(MAT_ORDER) == 16, f"expected 16 materials, got {len(MAT_ORDER)}"
assigned = [c[1]["group_index"] for c in cmds if c[0] == "assign_material"]
assert assigned == list(range(1, 17)), f"assign group_index mismatch: {assigned}"

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
print(f"materials sourced from scene.json ({len(MAT_ORDER)} groups); camera={camera['position']}")
