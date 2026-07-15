#!/usr/bin/env python3
"""Re-queue a single frame's 18 commands (for a missed frame 239)."""
import os, sys, math
sys.path.insert(0, "/Users/craig/octanex-mcp")
from octanex_mcp.bridge import Workspace, write_command

ROOT = "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
ASSET_DIR = os.path.join(ROOT, "assets")
RENDER_DIR = os.path.join(ROOT, "renders")
FRAMES = 240
N_COLORS = 7
W, H, SAMPLES = 800, 800, 500
OBJ_NAME = "mandelbulb"
COLORS = [
    [1.0,0.15,0.15],[1.0,0.873,0.15],[0.405,1.0,0.15],[0.15,1.0,0.617],
    [0.15,0.66,1.0],[0.363,0.15,1.0],[1.0,0.15,0.915]]
BAND_NAMES = [f"mat_band_{i}" for i in range(N_COLORS)]

def lerp(a,b,t): return a+(b-a)*t
f = int(sys.argv[1])
t = f / max(1, (FRAMES-1))
az = math.radians(lerp(0.0, 330.0, t))
cam_r = lerp(11.0, 7.0, t)
cx, cz, cy = cam_r*math.cos(az), cam_r*math.sin(az), lerp(4.5, 2.8, t)
fp = os.path.join(ASSET_DIR, "mandelbulb_f%04d.obj" % f)
write_command("import_geometry", {"path": fp, "format": "obj", "name": OBJ_NAME})
for name, col in zip(BAND_NAMES, COLORS):
    write_command("create_material", {"name": name, "color": col, "kind": "glossy",
                                      "roughness": 0.1, "clearcoat": 0.5, "ior": 1.45})
for name in BAND_NAMES:
    write_command("assign_material", {"object_name": OBJ_NAME, "material_name": name})
write_command("set_camera", {"position": [round(cx,4), round(cy,4), round(cz,4)],
                             "target": [0,0,0], "fov": 45.0})
write_command("set_lighting", {"preset": "soft_studio"})
write_command("save_preview", {"path": os.path.join(RENDER_DIR, "frame_%04d.png" % f),
                               "samples": SAMPLES, "width": W, "height": H, "timeout_seconds": 16})
print("queued frame", f, "-> 18 commands (cam=[%.2f,%.2f,%.2f])" % (cx, cy, cz))
