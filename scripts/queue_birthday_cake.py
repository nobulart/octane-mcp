#!/usr/bin/env python3
"""Queue a full birthday-cake render pipeline to the OctaneX MCP bridge.

Sequence (must stay in this order; the bridge drains the queue lexically by
timestamp-prefixed filename, and import must precede material binding):
  1. import_geometry  (name=birthday_cake)
  2. create_material  x16 (one per usemtl group)
  3. assign_material  x16 (group_index = ordinal of first usemtl appearance)
  4. set_camera       (3/4 view, fits the ~2.8 wide / ~2.7 tall cake)
  5. set_lighting     soft_studio
  6. save_preview     (NO start_render — save_preview performs the single render)

The MCP `assign_material` *tool* lacks `group_index`, so we write the envelope
directly with that field (the validator ignores unknown keys and the oneshot
bridge handler reads cmd.payload.group_index).
"""
import json
import os
import time
import uuid

ROOT = os.path.expanduser("~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP")
QUEUE = os.path.join(ROOT, "queue")
OBJ = "birthday_cake.obj"  # sits in ROOT/assets/
PREVIEW = os.path.join(ROOT, "renders", "birthday_cake.png")

ASSETS = os.path.join(ROOT, "assets")
OBJ_PATH = os.path.join(ASSETS, OBJ)
assert os.path.exists(OBJ_PATH), f"missing {OBJ_PATH}"

# group order MUST match gen_birthday_cake.py write order
GROUPS = [
    "mat_plate", "mat_icing_lower", "mat_icing_upper",
    "mat_drip_a", "mat_drip_b", "mat_drip_c",
    "mat_candle", "mat_flame",
    "mat_sprinkle1", "mat_sprinkle2", "mat_sprinkle3", "mat_sprinkle4",
    "mat_sprinkle5", "mat_sprinkle6", "mat_sprinkle7", "mat_sprinkle8",
]

MAT = json.load(open(os.path.join(ASSETS, "birthday_cake.materials.json")))

# (position, target) chosen so a ~2.8-unit wide, ~2.7-unit tall cake fills frame
CAM_POS = [3.6, 2.4, 4.6]
CAM_TGT = [0.0, 1.0, 0.0]


def env(op, payload):
    return {
        "schema_version": "1.0",
        "id": f"{time.time_ns()}-{uuid.uuid4().hex[:8]}",
        "op": op,
        "payload": payload,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "octanex-mcp",
    }


def write(env):
    p = os.path.join(QUEUE, env["id"] + ".json")
    with open(p, "w") as fh:
        json.dump(env, fh, indent=2)
    return p


os.makedirs(QUEUE, exist_ok=True)
written = []

written.append(write(env("import_geometry", {
    "path": OBJ_PATH, "format": "obj", "name": "birthday_cake",
})))

for g in GROUPS:
    spec = MAT[g]
    payload = {"name": g, "kind": spec.get("kind", "diffuse"),
               "color": spec.get("color", [0.8, 0.8, 0.8])}
    for k in ("roughness", "metallic", "transmission", "ior", "opacity", "clearcoat"):
        if k in spec:
            payload[k] = spec[k]
    written.append(write(env("create_material", payload)))

for i, g in enumerate(GROUPS, start=1):
    written.append(write(env("assign_material", {
        "object_name": "birthday_cake", "material_name": g, "group_index": i,
    })))

written.append(write(env("set_camera", {
    "position": CAM_POS, "target": CAM_TGT, "fov": 38,
})))
written.append(write(env("set_lighting", {"preset": "soft_studio"})))
written.append(write(env("save_preview", {
    "path": PREVIEW, "width": 1280, "height": 1280,
    "samples": 256, "min_samples": 32, "timeout_seconds": 180,
})))

print(f"queued {len(written)} commands to {QUEUE}")
for w in written:
    print("  ", os.path.basename(w))
