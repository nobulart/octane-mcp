#!/usr/bin/env python3
"""Queue a full pipeline scene to show a cube in Octane X."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

WS = Path.home() / "Library" / "Containers/com.otoy.rndrviewer/Data/OctaneMCP"
QDIR = WS / "queue"


def queue_file(op: str, payload: dict):
    cid = f"{time.time_ns()}-{uuid.uuid4().hex[:8]}"
    txt = json.dumps(
        {"id": cid, "op": op, "payload": payload or {}}, indent=2
    )
    path = QDIR / f"{cid}.json"
    path.write_text(txt)
    print(f"QUEUED: {cid} -> {op}")
    return cid


if __name__ == "__main__":
    ws = WS

    # Build cube OBJ
    assets_dir = ws / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    s = 0.5
    verts = [
        (-s, -s, -s), (s, -s, -s), (s, s, -s), (-s, s, -s),
        (-s, -s, s),   (s, -s, s),   (s, s, s),   (-s, s, s),
    ]
    lines = ["# showcase cube"]
    for v in verts:
        lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
    faces = [
        (1, 5, 8), (1, 8, 4),   # -X face
        (2, 3, 7), (2, 7, 6),   # +X face
        (3, 4, 8), (3, 8, 7),   # +Y face
        (1, 2, 6), (1, 6, 5),   # -Z face
        (4, 3, 7),               # +Z face
        (5, 6, 7), (5, 7, 8),   # -Y face
    ]
    for f in faces:
        lines.append(f"f {f[0]} {f[1]} {f[2]}")

    cube_file = assets_dir / "showcase_cube.obj"
    cube_file.write_text("\n".join(lines))
    print(f"CUBE FILE WRITTEN: {cube_file}\n")

    # Queue commands in order
    queue_file("import_geometry", {
        "path": str(cube_file),
        "format": "obj",
        "name": "showcase_cube",
    })
    queue_file("create_material", {
        "name": "golden_metal",
        "kind": "metallic",
        "color": [1.0, 0.75, 0.15],
        "roughness": 0.25,
        "metallic": 1.0,
    })
    queue_file("assign_material", {
        "object_name": "showcase_cube",
        "material_name": "golden_metal",
    })
    queue_file("set_camera", {
        "position": [2.5, 2.0, 3.0],
        "target": [0.0, 0.0, 0.0],
        "fov": 45,
    })
    queue_file("start_render", {
        "samples": 256,
    })

    print("\nAll commands queued into Octane X bridge!")
