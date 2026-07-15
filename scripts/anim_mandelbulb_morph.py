#!/usr/bin/env python3
"""Mandelbulb EVOLUTIONARY MORPH animation driver (self-contained frames).

Power one-way 6->11, radius 2.2->3.2, slow camera orbit (0->330 deg) + dolly-in
(radius 11->7). Each frame is a COMPLETE, self-contained unit:
    import_geometry + 7x create_material + 7x assign_material + set_camera
    + set_lighting + save_preview
so nothing depends on cross-frame node identity (the same pattern that produced
the successful glossy stills). Queued via the repo write_command directly.

Run:
  python scripts/anim_mandelbulb_morph.py [frames=240] [res=140] [smoke=0]
"""
import os
import sys
import math
import subprocess

ROOT = "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
ASSET_DIR = os.path.join(ROOT, "assets")
RENDER_DIR = os.path.join(ROOT, "renders")
os.makedirs(ASSET_DIR, exist_ok=True)
os.makedirs(RENDER_DIR, exist_ok=True)

FRAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 240
RES = int(sys.argv[2]) if len(sys.argv) > 2 else 140
SMOKE = int(sys.argv[3]) if len(sys.argv) > 3 else 0
N_COLORS = 7
POWER_A, POWER_B = 6.0, 11.0
RAD_A, RAD_B = 2.2, 3.2
W, H = 800, 800
SAMPLES = 500
OBJ_NAME = "mandelbulb"

REPO = "/Users/craig/octanex-mcp"
GEN = os.path.join(REPO, "scripts", "gen_mandelbulb.py")
PY = "/Users/craig/octanex-mcp/.venv/bin/python"
ENV = {**os.environ, "PYTHONPATH": ""}

COLORS = [
    [1.0, 0.15, 0.15], [1.0, 0.873, 0.15], [0.405, 1.0, 0.15],
    [0.15, 1.0, 0.617], [0.15, 0.66, 1.0], [0.363, 0.15, 1.0],
    [1.0, 0.15, 0.915],
]
BAND_NAMES = [f"mat_band_{i}" for i in range(N_COLORS)]


def run(cmd):
    p = subprocess.run(cmd, env=ENV, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError("CMD FAIL %s\n%s" % (" ".join(cmd), p.stderr[-2000:]))


def lerp(a, b, t):
    return a + (b - a) * t


def main():
    # precompute meshes
    last = 2 if SMOKE else FRAMES
    frame_paths = []
    print(">> generating %d morph meshes (res %d)..." % (last, RES))
    for f in range(last):
        t = f / max(1, (FRAMES - 1))
        power = lerp(POWER_A, POWER_B, t)
        rad = lerp(RAD_A, RAD_B, t)
        fp = os.path.join(ASSET_DIR, "mandelbulb_f%04d.obj" % f)
        run([PY, GEN, str(N_COLORS), "%.4f" % power, str(RES), "%.4f" % rad, fp])
        frame_paths.append(fp)
    print(">> meshes done")

    sys.path.insert(0, REPO)
    from octanex_mcp.bridge import Workspace, write_command
    ws = Workspace()
    ws.ensure()

    per = 0
    for f in range(last):
        t = f / max(1, (FRAMES - 1))
        az = math.radians(lerp(0.0, 330.0, t))
        cam_r = lerp(11.0, 7.0, t)
        cx = cam_r * math.cos(az)
        cz = cam_r * math.sin(az)
        cy = lerp(4.5, 2.8, t)
        write_command("import_geometry", {"path": frame_paths[f], "format": "obj", "name": OBJ_NAME})
        for name, col in zip(BAND_NAMES, COLORS):
            write_command("create_material", {"name": name, "color": col, "kind": "glossy",
                                              "roughness": 0.1, "clearcoat": 0.5, "ior": 1.45})
        for name in BAND_NAMES:
            write_command("assign_material", {"object_name": OBJ_NAME, "material_name": name})
        write_command("set_camera", {"position": [round(cx, 4), round(cy, 4), round(cz, 4)],
                                      "target": [0, 0, 0], "fov": 45.0})
        write_command("set_lighting", {"preset": "soft_studio"})
        write_command("save_preview", {"path": os.path.join(RENDER_DIR, "frame_%04d.png" % f),
                                       "samples": SAMPLES, "width": W, "height": H, "timeout_seconds": 16})
        per += 17

    print(">> QUEUED TOTAL: %d commands (%d per frame x%d)" % (per, 17, last))
    if SMOKE:
        print(">> SMOKE MODE: stop after %d frames." % last)


if __name__ == "__main__":
    main()
