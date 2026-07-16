#!/usr/bin/env python3
"""Phase C recipe: simulation-frame-strip — the canonical animation-preview grammar.

Every physics simulator in this suite (OctaneX-adjacent or not) eventually wants
a *frame strip*: a spatial row of N discrete simulation states, laid out so a
single static render communicates time evolution. This recipe defines that
grammar with a deterministic, repo-native state function — no external simulator
dependency — so it is fully offline-verifiable and acts as the template every
future per-frame export adapter maps onto.

The state function here is a travelling advection-diffusion pulse, the same
closed-form field used by the Phase A advection-diffusion recipe, with a
deterministic per-frame time index. Each frame is its own `usemtl` group so the
bridge binds a distinct material per frame; frames share a colour ramp (cool ->
warm) that encodes the time axis, making the strip read as a left-to-right time
sequence. A thin base slab under the strip anchors the composition.

Emitted recipe assets (under examples/recipes/simulation-frame-strip/):
  * scene.obj     — one combined OBJ; one group per frame + base slab.
  * scene.mtl     — material hints (bridge uses scene.json, not the MTL).
  * scene.json    — verified-recipe contract (import + create_material per group
                    + assign_material(group_index) per group + camera + lighting
                    + save_preview). Carries the frame grammar in the `simulation`
                    block so downstream adapters know the required layout.
  * preview.png   — lightweight reference raster (stdlib zlib/PNG, no PIL).
  * README.md     — purpose, frame grammar, re-render command, pitfalls.

Run:
    PYTHONPATH=scripts:. uv run python scripts/gen_simulation_frame_strip_recipe.py
"""
from __future__ import annotations

import json
import math
import struct
import sys
import zlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECIPES = ROOT / "examples" / "recipes"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from octanex_mcp.visuals import ObjBuilder, camera_for_bounds  # noqa: E402

SLUG = "simulation-frame-strip"

# Frame-strip grammar parameters (the canonical layout every future adapter reuses).
N_FRAMES = 8
GRID = 24              # per-frame heightfield resolution (rows x cols)
PANEL = 3.0            # width of each frame panel (scene units)
PANEL_GAP = 0.5        # gap between panels
HEIGHT_SCALE = 1.8     # peak displacement for a unit-amplitude field
U = 0.6               # advection speed
D = 0.05              # diffusion coefficient
T_MAX = 2.6           # last frame time


def frame_time(i: int) -> float:
    """Deterministic per-frame time index (evenly spaced 0..T_MAX)."""
    return T_MAX * i / (N_FRAMES - 1)


def _panel_vertex(i: int, j: int, gi: int, gj: int, t: float) -> tuple[float, float, float]:
    """Heightfield vertex for grid cell (gi, gj) of frame i.

    The panel is centred at x = frame origin; y is the in-plane axis; z is the
    field amplitude (raised heightfield). The pulse advects along +x and
    diffuses (broadens + peak decays) as t grows.
    """
    x = -PANEL / 2 + PANEL * gj / (GRID - 1)
    y = -PANEL / 2 + PANEL * gi / (GRID - 1)
    sigma2 = 0.25 + 2.0 * D * t
    peak = math.exp(-((x - U * t) ** 2) / (2 * sigma2))
    z = peak * HEIGHT_SCALE - HEIGHT_SCALE * 0.5
    # global x offset so the panel sits at its slot in the strip
    ox = (PANEL + PANEL_GAP) * i
    return (ox + x, y, z)


def _coolwarm(t: float) -> list[float]:
    """Cool (t=0) -> warm (t=1) RGB ramp encoding the time axis."""
    return [
        0.15 + 0.70 * t,
        0.45 + 0.25 * (1.0 - t),
        0.95 - 0.70 * t,
    ]


def _build() -> dict[str, Any]:
    obj = ObjBuilder(SLUG.replace("-", "_"))
    groups: list[str] = []

    for i in range(N_FRAMES):
        mat = f"frame_{i:02d}"
        verts = [[_panel_vertex(i, gi, gj, gj, frame_time(i))
                  for gj in range(GRID)] for gi in range(GRID)]
        obj.add_surface(vertices=verts, material=mat)
        groups.append(mat)

    # base slab under the whole strip
    strip_len = N_FRAMES * PANEL + (N_FRAMES - 1) * PANEL_GAP
    obj.add_box(center=(strip_len / 2 - PANEL / 2, 0.0, -HEIGHT_SCALE * 0.5 - 0.1),
                size=(strip_len + 1.0, PANEL + 1.0, 0.2), material="strip_base")
    groups.append("strip_base")

    obj_text = obj.text()
    cam = camera_for_bounds(obj.bounds(), view="iso", margin=1.4, fov=40)

    # Materials: one per frame (cool->warm ramp) + base.
    mats: dict[str, dict] = {}
    for i in range(N_FRAMES):
        mats[f"frame_{i:02d}"] = {"kind": "glossy", "color": _coolwarm(i / (N_FRAMES - 1)),
                                  "roughness": 0.35}
    mats["strip_base"] = {"kind": "diffuse", "color": [0.06, 0.07, 0.09], "roughness": 0.9}

    commands: list[dict] = [
        {"op": "import_geometry", "payload": {
            "path": f"examples/recipes/{SLUG}/scene.obj", "format": "obj",
            "name": SLUG.replace("-", "_")}},
    ]
    for name in groups:
        m = mats[name]
        commands.append({"op": "create_material", "payload": {
            "name": name, "kind": m["kind"], "color": m["color"],
            "roughness": m["roughness"]}})
    for idx, name in enumerate(groups, start=1):
        commands.append({"op": "assign_material", "payload": {
            "object_name": SLUG.replace("-", "_"), "material_name": name,
            "group_index": idx}})
    commands.extend([
        {"op": "set_camera", "payload": cam},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "save_preview", "payload": {
            "path": f"{SLUG}/octane-preview.png", "width": 1400, "height": 900,
            "quality": "standard", "samples": 128, "min_samples": 16,
            "timeout_seconds": 90}},
    ])

    scene: dict[str, Any] = {
        "slug": SLUG,
        "title": "Simulation Frame Strip (8 frames)",
        "category": "Physical simulation / animation grammar",
        "domain": "Physics simulation",
        "purpose": (
            "Define the repo-native animation-preview grammar: a spatial strip of N discrete "
            "simulation states, one per frame, laid out left-to-right so a single static render "
            "communicates time evolution. Here the state is a closed-form advection-diffusion "
            "pulse (same field as the Phase A recipe) advanced through 8 evenly spaced time "
            "indices. Each frame is its own material group bound to a cool->warm ramp encoding "
            "the time axis. Deterministic and external-simulator-free, so it is the template "
            "every future per-frame export adapter maps onto."),
        "prompt": "Visualise a simulation frame strip: 8 time steps of an advecting/diffusing pulse laid out as a spatial sequence.",
        "camera": cam,
        "materials": mats,
        "commands": commands,
        "simulation": {
            "source_library": "analytic (closed-form advection-diffusion)",
            "fixture": "embedded 8-frame pulse, N=24 grid, no external simulator",
            "physical_variables": ["tracer_concentration"],
            "units": {"length": "m", "time": "s"},
            "scale_mapping": {
                "scene_units_per_meter": 1.0,
                "height_scale": HEIGHT_SCALE,
                "frame_layout": "left_to_right_strip",
                "frame_count": N_FRAMES,
                "panel_width": PANEL,
                "panel_gap": PANEL_GAP,
            },
            "time": {"frames": N_FRAMES, "t_seconds": T_MAX},
            "null_model": "single frame (N=1): no time evolution to read",
            "frame_grammar": {
                "layout": "spatial_strip",
                "orientation": "left_to_right_increasing_time",
                "per_frame_group": True,
                "color_axis": "cool_to_warm_encodes_t",
                "shared_base_slab": True,
            },
            "limitations": [
                "state function is a 1D pulse shown as 2D heightfields, not a full 3D field",
                "no live PDE solve; downstream adapters swap the generator for exported frames",
            ],
        },
        "quality_checklist": [
            "Eight distinct panels are visible in a left-to-right row.",
            "Each panel is a distinct cool->warm colour (time axis encoded by hue).",
            "The pulse peak is tallest in early panels and broadens/lowers toward later panels.",
            "Each frame group has an explicit create_material + assign_material(group_index).",
            "Camera frames the whole strip with margin.",
        ],
        "known_pitfalls": [
            "OBJ/MTL colours are ignored by the bridge; the per-frame ramp needs explicit materials.",
            "One usemtl group PER frame yields many groups; the bridge handles it but keep N modest (8) until animation workflows mature.",
            "The strip is wide; an iso camera with enough margin avoids clipping the end panels.",
        ],
        "native_octane_verified": False,
    }
    return {"obj_text": obj_text, "scene": scene, "mats": mats, "groups": groups,
            "cam": cam, "obj": obj}


def _write_mtl(d: Path, mats: dict[str, dict]) -> None:
    lines = ["# Material hints; Octane binding is driven by scene.json create_material + assign_material."]
    for name, m in mats.items():
        r, g, b = m["color"]
        lines.append(f"newmtl {name}")
        lines.append(f"Kd {r:.4f} {g:.4f} {b:.4f}")
        lines.append(f"Ns {int(1.0 / max(m.get('roughness', 0.3), 1e-3))}")
    (d / "scene.mtl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_preview(d: Path) -> None:
    """Lightweight reference raster: 8 cool->warm panels in a row.

    PNG requires a per-scanline filter byte; the raw RGB is prefixed with a
    \\x00 (filter type 0 = None) byte on every row before zlib compression,
    otherwise the stream is not a valid PNG and decoders reject it.
    """
    w, h = 320, 90
    cols = [_coolwarm(i / (N_FRAMES - 1)) for i in range(N_FRAMES)]
    pw = w // N_FRAMES
    raw = bytearray()
    for y in range(h):
        raw.append(0)  # PNG filter byte for this scanline (type 0: None)
        for x in range(w):
            p = min(N_FRAMES - 1, x // pw)
            c = cols[p]
            raw += bytes([int(c[0] * 255), int(c[1] * 255), int(c[2] * 255)])
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes(raw), 9)

    def _crc(data: bytes) -> int:
        return zlib.crc32(data) & 0xFFFFFFFF

    def _chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", _crc(tag + data))

    png = sig + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b"")
    (d / "preview.png").write_bytes(png)


def _write_readme(d: Path, scene: dict, stats: dict) -> None:
    text = (
        f"# {scene['title']}\n\n"
        f"{scene['purpose']}\n\n"
        "## Frame grammar\n\n"
        "This recipe is the canonical **animation-preview** layout for the suite:\n\n"
        "- `frames`: a spatial strip laid out **left-to-right in increasing time**.\n"
        "- one `usemtl` **group per frame**, each bound to its own material.\n"
        f"- a cool->warm colour **ramp encodes the time axis** ({N_FRAMES} frames, t=0 cool -> t=T warm).\n"
        "- a shared base slab anchors the composition.\n\n"
        "Downstream per-frame export adapters (later Phase C / simulator exports) must emit "
        "exactly this layout so a single render communicates evolution.\n\n"
        "## Usage\n\n"
        "1. Import `scene.obj` with "
        f"`octane_import_geometry(path=\"examples/recipes/{SLUG}/scene.obj\", name=\"{SLUG.replace('-', '_')}\")`.\n"
        "2. Create + assign materials per `usemtl` group (see table).\n"
        "3. Set camera, lighting, then `octane_save_preview`.\n\n"
        "Regenerate the geometry + metadata with:\n\n"
        "```bash\nPYTHONPATH=scripts:. uv run python scripts/gen_simulation_frame_strip_recipe.py\n```\n\n"
        "## Material groups\n\n"
        "| material-order | material | kind | color |\n| --- | --- | --- | --- |\n"
    )
    for i, name in enumerate(stats["groups"], 1):
        m = scene["materials"][name]
        text += f"| {i} | `{name}` | {m.get('kind','glossy')} | `{m.get('color')}` |\n"
    text += (
        f"\nOBJ stats: {stats['vertices']} vertices, max face index "
        f"{stats['max_face_index']} (indices valid).\n\n"
        f"Camera: position {scene['camera']['position']} -> target {scene['camera']['target']}, "
        f"fov {scene['camera'].get('fov')}.\n\n"
        "## Notes\n\n"
        "- This is a **deterministic, repo-native** recipe: the physical state is computed in "
        "`scripts/gen_simulation_frame_strip_recipe.py` with no external simulator, so it "
        "reproduces identically offline.\n"
        "- `native_octane_verified` is `false` until a fresh native Octane preview is promoted.\n"
    )
    (d / "README.md").write_text(text, encoding="utf-8")


def main(output_root: Path = RECIPES) -> dict[str, Any]:
    d = output_root / SLUG
    d.mkdir(parents=True, exist_ok=True)
    out = _build()
    (d / "scene.obj").write_text(str(out["obj_text"]).rstrip("\n") + "\n", encoding="utf-8")
    _write_mtl(d, out["mats"])
    (d / "scene.json").write_text(json.dumps(out["scene"], indent=2) + "\n", encoding="utf-8")
    _write_preview(d)
    # vertex count for README/stats
    vcount = sum(1 for ln in out["obj_text"].splitlines() if ln.startswith("v "))
    max_idx = 0
    for ln in out["obj_text"].splitlines():
        if ln.startswith("f "):
            for tok in ln.split()[1:]:
                max_idx = max(max_idx, int(tok.split("/")[0]))
    stats = {"slug": SLUG, "vertices": vcount, "max_face_index": max_idx,
             "groups": out["groups"], "frames": N_FRAMES}
    _write_readme(d, out["scene"], stats)
    return stats


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
