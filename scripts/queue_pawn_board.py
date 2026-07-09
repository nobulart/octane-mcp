#!/usr/bin/env python3
"""Queue the pawn-on-board scene into the OctaneX command queue.

The board OBJ has 3 usemtl groups in fixed order:
  1 = cb_base   (dark board)
  2 = cb_light  (cream squares)
  3 = pawn      (green pawn)
The MCP assign_material tool has no group_index field, so we write the
command envelopes directly (same shape write_command produces).
"""
import json
import os
import time
import uuid

ROOT = os.path.expanduser("~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP")
OBJ = os.path.join(ROOT, "assets", "pawn_on_board.obj")
NAME = "pawn_board"
PREVIEW = os.path.join(ROOT, "renders", "pawn_on_board_preview.png")
SCHEMA_VERSION = "1.0"

COMMANDS = [
    {"op": "import_geometry", "payload": {"path": OBJ, "format": "obj", "name": NAME}},
    {"op": "create_material", "payload": {"name": "cb_base", "kind": "glossy",
                                          "color": [0.06, 0.06, 0.07], "roughness": 0.4}},
    {"op": "create_material", "payload": {"name": "cb_light", "kind": "glossy",
                                          "color": [0.86, 0.83, 0.74], "roughness": 0.35}},
    {"op": "create_material", "payload": {"name": "pawn", "kind": "glossy",
                                          "color": [0.12, 0.72, 0.28], "roughness": 0.2,
                                          "clearcoat": 0.6, "specular": 0.5}},
    {"op": "assign_material", "payload": {"object_name": NAME, "material_name": "cb_base", "group_index": 1}},
    {"op": "assign_material", "payload": {"object_name": NAME, "material_name": "cb_light", "group_index": 2}},
    {"op": "assign_material", "payload": {"object_name": NAME, "material_name": "pawn", "group_index": 3}},
    {"op": "set_camera", "payload": {"position": [4.2, 3.0, 4.2], "target": [0, 0.6, 0], "fov": 36}},
    {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
    {"op": "save_preview", "payload": {"path": PREVIEW, "width": 1280, "height": 1280,
                                       "samples": 256, "min_samples": 24, "timeout_seconds": 60}},
]


def write_command(op, payload):
    cid = f"{time.time_ns()}-{uuid.uuid4().hex[:8]}"
    cmd = {
        "schema_version": SCHEMA_VERSION,
        "id": cid,
        "op": op,
        "payload": payload,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "octanex-mcp",
    }
    path = os.path.join(ROOT, "queue", f"{cid}.json")
    with open(path, "w") as fh:
        json.dump(cmd, fh, indent=2)
    return path


def main():
    for c in COMMANDS:
        p = write_command(c["op"], c["payload"])
        print(f"queued {c['op']:16s} -> {os.path.basename(p)}")


if __name__ == "__main__":
    main()
