#!/usr/bin/env python3
"""Queue a SINGLE-MATERIAL math-surface scene (the known-good baseline).

Pipeline (queue order, v2 one-shot bridge processes sequentially):
  flush -> import_geometry -> create_material -> assign_material ->
  set_camera -> set_lighting -> save_preview

No gradients, no bands, no vertex colours. One glossy material, one colour.
Warm-resets (File > New) are the caller's responsibility between surfaces.
"""
import json, os, time, uuid, shutil, sys, math
from pathlib import Path

ROOT = Path(os.path.expanduser(
    "~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"))
QUEUE = ROOT / "queue"


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_cmd(op, payload):
    QUEUE.mkdir(parents=True, exist_ok=True)
    cid = f"{time.time_ns()}-{uuid.uuid4().hex[:8]}"
    cmd = {"schema_version": "1.0", "id": cid, "op": op,
           "payload": payload, "created_at": now_iso(), "source": "octanex-mcp"}
    p = QUEUE / f"{cid}.json"
    p.write_text(json.dumps(cmd, indent=2))
    (ROOT / "inbox.json").write_text(json.dumps(cmd, indent=2))
    return p


def flush(backup=True):
    pending = sorted(QUEUE.glob("*.json"))
    moved = 0
    bdir = None
    if pending and backup:
        stamp = time.strftime("%Y-%m-%dT%H-%M-%SZ", time.gmtime())
        bdir = ROOT / "queue_backups" / stamp
        bdir.mkdir(parents=True, exist_ok=True)
    for p in pending:
        moved += 1
        if bdir:
            shutil.move(str(p), str(bdir / p.name))
        else:
            p.unlink()
    return moved


def obj_bounds(obj_path):
    xs = ys = zs = 0.0
    n = 0
    with open(obj_path) as f:
        for line in f:
            if line.startswith("v "):
                parts = line[2:].split()
                if len(parts) < 3:
                    continue
                xs += float(parts[0]); ys += float(parts[1]); zs += float(parts[2])
                n += 1
    cx, cy, cz = xs / n, ys / n, zs / n
    r = 0.0
    with open(obj_path) as f:
        for line in f:
            if line.startswith("v "):
                parts = line[2:].split()
                if len(parts) < 3:
                    continue
                dx = float(parts[0]) - cx; dy = float(parts[1]) - cy; dz = float(parts[2]) - cz
                d = math.sqrt(dx * dx + dy * dy + dz * dz)
                if d > r:
                    r = d
    return [cx, cy, cz], r


def camera_from_bounds(center, radius, fov_deg=40.0, margin=1.25,
                      direction=(1.0, 0.35, 1.0), rot_x_deg=0.0, rot_z_deg=0.0):
    import math as _m
    dx, dy, dz = direction
    norm = _m.sqrt(dx * dx + dy * dy + dz * dz)
    dx, dy, dz = dx / norm, dy / norm, dz / norm
    # Apply rotation about X axis, then Z axis (user-specified oblique view).
    rx = _m.radians(rot_x_deg); rz = _m.radians(rot_z_deg)
    # rot X
    y1 = dy * _m.cos(rx) - dz * _m.sin(rx)
    z1 = dy * _m.sin(rx) + dz * _m.cos(rx)
    dy, dz = y1, z1
    # rot Z
    x1 = dx * _m.cos(rz) - dy * _m.sin(rz)
    y1 = dx * _m.sin(rz) + dy * _m.cos(rz)
    dx, dy = x1, y1
    n2 = _m.sqrt(dx*dx + dy*dy + dz*dz)
    dx, dy, dz = dx/n2, dy/n2, dz/n2
    half = _m.radians(fov_deg) / 2.0
    dist = (radius / _m.tan(half)) * margin
    pos = [center[0] + dx * dist, center[1] + dy * dist, center[2] + dz * dist]
    return pos, list(center)


def main():
    obj_path = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else "surface"
    tag = f"hermes_{name}"
    preview = ROOT / "renders" / f"{name}_octane-preview.png"
    if preview.exists():
        preview.unlink()

    center, radius = obj_bounds(obj_path)
    cam_pos, target = camera_from_bounds(center, radius, rot_x_deg=60.0, rot_z_deg=30.0)
    print(f"bounds center={[round(c, 3) for c in center]} radius={radius:.3f} cam={[round(c, 3) for c in cam_pos]}")

    # Per-surface palette (distinct solid colour per surface) — from docs/recipe-book.md.
    # Keyed by surface name; falls back to gyroid blue.
    PALETTE = {
        "gyroid":   [0.12, 0.45, 0.92],
        "neovius":  [0.95, 0.55, 0.15],
        "schwarz_h":[0.20, 0.80, 0.40],
        "schwarz_p":[0.20, 0.80, 0.40],
        "schwarz":  [0.20, 0.80, 0.40],
        "lidinoid": [0.92, 0.30, 0.70],
        "schwarz_pd":[0.15, 0.80, 0.90],
        "diamond":  [0.80, 0.80, 0.20],
    }
    color = PALETTE.get(name, PALETTE["gyroid"])

    flushed = flush(backup=True)
    print(f"flushed {flushed} stale command(s)")

    paths = []
    paths.append(write_cmd("import_geometry", {"path": obj_path, "format": "obj", "name": tag}))
    paths.append(write_cmd("create_material", {"name": f"{tag}_mat", "kind": "glossy",
        "color": color, "roughness": 0.35, "metallic": 0.0}))
    paths.append(write_cmd("assign_material", {"object_name": tag, "material_name": f"{tag}_mat"}))
    paths.append(write_cmd("set_camera", {"position": cam_pos, "target": target, "fov": 40}))
    paths.append(write_cmd("set_lighting", {"preset": "dark_studio"}))
    paths.append(write_cmd("save_preview", {"path": str(preview), "width": 1280, "height": 1280,
        "samples": 1200, "min_samples": 64, "timeout_seconds": 300, "max_render_time": 600}))
    print(f"queued {len(paths)} commands for {name}")
    print(f"preview target: {preview}")


if __name__ == "__main__":
    main()
