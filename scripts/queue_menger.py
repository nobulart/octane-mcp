#!/usr/bin/env python3
"""Queue the full Menger-sponge render pipeline DIRECTLY via the repo
write_command, bypassing the (possibly stale) MCP server process. The bridge
drains queue/.

Regenerates the canonical OBJ from scripts/gen_menger.py, copies it into both
the repo recipe dir and the container workspace (Octane only reads the container
FS), flushes any stale shared-queue commands, then queues import -> material ->
assign -> camera -> lighting -> save_preview.

Run: uv run python scripts/queue_menger.py
"""
import os
import sys
import shutil

REPO = "/Users/craig/octanex-mcp"
ROOT = os.path.expanduser("~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP")
RECIPE_OBJ = os.path.join(REPO, "examples", "recipes", "menger-sponge", "scene.obj")
CONTAINER_OBJ = os.path.join(ROOT, "examples", "recipes", "menger-sponge", "scene.obj")
PREVIEW = os.path.join(ROOT, "examples", "recipes", "menger-sponge", "octane-preview.png")

sys.path.insert(0, REPO)
from octanex_mcp.bridge import Workspace, write_command, flush_queue
import scripts.gen_menger as gen

ws = Workspace()
ws.ensure()
flush_queue(ws)  # archive any stale shared-queue commands first

# Regenerate OBJ from the canonical generator, then stage it both places.
gen.main()
os.makedirs(os.path.dirname(CONTAINER_OBJ), exist_ok=True)
shutil.copyfile(RECIPE_OBJ, CONTAINER_OBJ)

SPONGE = [0.16, 0.34, 0.86]  # cool blue, glossy

ids = []
ids.append(write_command("import_geometry", {"path": CONTAINER_OBJ, "format": "obj", "name": "menger"})["command_id"])
ids.append(write_command("create_material", {
    "name": "mat_sponge", "color": SPONGE, "kind": "glossy",
    "roughness": 0.18, "clearcoat": 0.4, "ior": 1.45,
})["command_id"])
ids.append(write_command("assign_material", {"object_name": "menger", "material_name": "mat_sponge"})["command_id"])
ids.append(write_command("set_camera", {"position": [7.5, 5.5, 9.5], "target": [0, 0, 0], "fov": 45.0})["command_id"])
ids.append(write_command("set_lighting", {"preset": "soft_studio"})["command_id"])
ids.append(write_command("save_preview", {"path": PREVIEW, "samples": 1000, "width": 1280, "height": 1280, "timeout_seconds": 30})["command_id"])

print("QUEUED %d commands" % len(ids))
for i, c in enumerate(ids):
    print("  [%d] %s" % (i, c))
