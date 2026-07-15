#!/usr/bin/env python3
"""Queue the full Mandelbulb render pipeline DIRECTLY via the repo write_command,
bypassing the (possibly stale) MCP server process. The bridge drains queue/.

Run: uv run python scripts/queue_mandelbulb.py
"""
import os
import sys

ROOT = "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
OBJ = os.path.join(ROOT, "assets", "mandelbulb.obj")
PREVIEW = os.path.join(ROOT, "renders", "mandelbulb_preview.png")

sys.path.insert(0, "/Users/craig/octanex-mcp")
from octanex_mcp.bridge import Workspace, write_command

ws = Workspace()
ws.ensure()

# 7 vivid rainbow bands (HSV hue sweep red->violet), diffuse
colors = [
    [1.0, 0.15, 0.15],   # mat_band_0 red
    [1.0, 0.873, 0.15],  # mat_band_1 yellow
    [0.405, 1.0, 0.15],  # mat_band_2 green
    [0.15, 1.0, 0.617],  # mat_band_3 teal
    [0.15, 0.66, 1.0],   # mat_band_4 blue
    [0.363, 0.15, 1.0],  # mat_band_5 indigo
    [1.0, 0.15, 0.915],  # mat_band_6 magenta
]
band_names = [f"mat_band_{i}" for i in range(len(colors))]

ids = []
ids.append(write_command("import_geometry", {"path": OBJ, "format": "obj", "name": "mandelbulb"})["command_id"])
for name, col in zip(band_names, colors):
    ids.append(write_command("create_material", {
        "name": name, "color": col, "kind": "glossy",
        "roughness": 0.1, "clearcoat": 0.5, "ior": 1.45,
    })["command_id"])
for name in band_names:
    ids.append(write_command("assign_material", {"object_name": "mandelbulb", "material_name": name})["command_id"])
ids.append(write_command("set_camera", {"position": [5.5, 3.5, 8.5], "target": [0, 0, 0], "fov": 45.0})["command_id"])
ids.append(write_command("set_lighting", {"preset": "soft_studio"})["command_id"])
ids.append(write_command("save_preview", {"path": PREVIEW, "samples": 1000, "width": 1080, "height": 1080, "timeout_seconds": 22})["command_id"])

print("QUEUED %d commands" % len(ids))
for i, c in enumerate(ids):
    print("  [%d] %s" % (i, c))
