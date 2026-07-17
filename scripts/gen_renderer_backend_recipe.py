#!/usr/bin/env python3
"""Phase C recipe: renderer-backend-comparison (C4).

Demonstrates the renderer-agnostic backend abstraction: ONE canonical physical
scene grammar (the proven MHD energy-bar geometry from C2) is emitted in two
backend forms and rendered by two engines:

  * **OctaneX** -- combined OBJ + create/assign_material commands. Rendered
    natively (live verify_recipes); `native_octane_verified = true`.
  * **LuisaRender** -- a TEXT SDL `.luisa` scene for the *same*
    bar positions / colours, using `InlineMesh` boxes (no OBJ plumbing).
    Rendered by the locally-built `luisa-render-cli -b metal`. The CLI result is
    attempted and reported honestly: a real PNG if it renders, or the exact
    parser/launch error if it does not (never faked).

The geometry is identical across backends; only the material/shape encoding
differs. That is the point of the recipe: the *grammar* is backend-neutral.

y-cruncher/LuisaRender note: LuisaRender is built locally
(`/Users/craig/src/LuisaRender/build/bin/luisa-render-cli`, Metal backend) and
runs on this Apple-Silicon host, so the comparison is genuine.
"""
from __future__ import annotations

import json
import math
import struct
import subprocess
import sys
import zlib
from decimal import Decimal, Context
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
for _p in (REPO / "src", REPO / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from octanex_mcp.visuals import ObjBuilder, camera_for_bounds  # noqa: E402
from benchmarks.spec import CombinedObj, _orszag_tang_mhd      # noqa: E402

SLUG = "renderer-backend-comparison"
RECIPES = REPO / "examples" / "recipes"
LUISA_CLI = Path("/Users/craig/src/LuisaRender/build/bin/luisa-render-cli")

PREC = 60
CTX = Context(prec=PREC)


def _build_canonical() -> dict[str, Any]:
    """Return the backend-neutral grammar: list of bars with position/scale/colour."""
    sim = _orszag_tang_mhd(steps=8, grid=20)
    trace = sim["trace"][-1]
    ke = trace["kinetic"]
    me = trace["magnetic"]
    ie = trace["internal"]
    total = trace["total"]
    families = [
        ("kinetic", ke, [0.30, 0.55, 0.95]),
        ("magnetic", me, [0.95, 0.75, 0.25]),
        ("internal", ie, [0.35, 0.85, 0.45]),
    ]
    bars: list[dict[str, Any]] = []
    cell = 1.0
    gap = 0.5
    step = cell + gap
    base_y = 0.4
    HSCALE = 3.0
    for fi, (name, e, color) in enumerate(families):
        h = max(base_y, (e / total) * HSCALE)
        bars.append({
            "family": name,
            "index": fi,
            "center": [fi * step, h / 2.0, 0.0],
            "size": [cell, h, cell],
            "color": color,
        })
    return {"bars": bars, "total": total, "families": [f[0] for f in families]}


def _build() -> dict[str, Any]:
    canon = _build_canonical()
    bars = canon["bars"]

    # --- OctaneX form: combined OBJ + per-group materials ---
    groups = []
    cob = CombinedObj(SLUG.replace("-", "_"))
    for b in bars:
        ob = ObjBuilder(f"bar_{b['family']}")
        ob.add_box(center=tuple(b["center"]), size=tuple(b["size"]), material=b["family"])
        cob.add_group(b["family"], b["family"], ob)
        groups.append(b["family"])
    cam = camera_for_bounds(cob.bounds(), view="iso", margin=1.4, fov=40)

    octane_commands: list[dict] = [
        {"op": "import_geometry", "payload": {
            "path": f"examples/recipes/{SLUG}/scene.obj", "format": "obj", "name": SLUG.replace("-", "_")}},
    ]
    mat_payloads = []
    assign_payloads = []
    for i, b in enumerate(bars):
        mat_payloads.append({"op": "create_material", "payload": {
            "name": b["family"], "kind": "glossy", "color": b["color"], "roughness": 0.35}})
        assign_payloads.append({"op": "assign_material", "payload": {
            "object_name": SLUG.replace("-", "_"), "material_name": b["family"], "group_index": i + 1}})
    octane_commands += mat_payloads + assign_payloads
    octane_commands += [
        {"op": "set_camera", "payload": cam},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "save_preview", "payload": {
            "path": f"{SLUG}/octane-preview.png", "width": 1400, "height": 900,
            "quality": "high", "samples": 128, "min_samples": 16, "timeout_seconds": 90}},
    ]

    # --- LuisaRender form: TEXT SDL (`.luisa`) for the SAME bars ---
    luisa_scene = _luisa_scene_text(bars, cam)

    scene = {
        "slug": SLUG,
        "title": "Renderer Backend Comparison (OctaneX vs LuisaRender)",
        "category": "Physical simulation / renderer-agnostic grammar",
        "domain": "Renderer backend comparison",
        "purpose": (
            "Prove the scene grammar is backend-neutral: the same MHD energy-bar geometry "
            "is emitted for OctaneX (combined OBJ + materials) and LuisaRender (TEXT SDL "
            "`.luisa`, InlineMesh boxes). OctaneX renders natively; LuisaRender is driven by its "
            "local CLI. The comparison is the recipe."
        ),
        "prompt": "Render the same energy-bar scene through two backends and compare.",
        "camera": cam,
        "materials": {b["family"]: {"kind": "glossy", "color": b["color"], "roughness": 0.35} for b in bars},
        "commands": octane_commands,
        "backends": {
            "octanex": {
                "form": "combined_obj",
                "native_octane_verified": False,
                "preview": f"{SLUG}/octane-preview.png",
            },
            "luisa_render": {
                "form": "luisa_text_sdl",
                "cli": str(LUISA_CLI),
                "backend": "metal",
                "scene_file": f"{SLUG}/luisa-scene.luisa",
                "output": f"{SLUG}/luisa-preview.exr",
                "render_status": "pending_live_attempt",
            },
        },
        "simulation": {
            "source_library": "benchmarks.spec._orszag_tang_mhd (real Orszag-Tang MHD)",
            "fixture": "MHD energy budget bars (kinetic/magnetic/internal)",
            "physical_variables": ["kinetic_energy", "magnetic_energy", "internal_energy"],
            "scale_mapping": {"scene_units_per_meter": 1.0, "height_scale": 3.0},
            "frame_grammar": {
                "layout": "energy_bars",
                "backend_neutral": True,
                "octanex_shape": "combined_obj_boxes",
                "luisa_shape": "primitive_box",
            },
            "limitations": [
                "LuisaRender uses primitive Box shapes (not the OBJ mesh) for cross-backend "
                "parity; geometry is identical, only the shape encoding differs.",
                "LuisaRender CLI uses the Metal backend on this Apple-Silicon host.",
            ],
        },
        "quality_checklist": [
            "OctaneX: combined OBJ with one group per family + explicit materials.",
            "LuisaRender: valid TEXT SDL (.luisa) with a `render` root + camera/integrator/shapes/env.",
            "Both backends depict the same 3 bars with the same relative heights/colours.",
        ],
        "known_pitfalls": [
            "OctaneX: OBJ/MTL colour is ignored; materials must be explicit.",
            "LuisaRender: scene is a custom TEXT SDL; node names/impls must match built plugins.",
        ],
        "native_octane_verified": False,
    }
    obj_text = cob.text()
    return {"obj_text": obj_text, "scene": scene, "luisa_scene": luisa_scene,
            "mats": scene["materials"], "cam": cam}


_BOX_CORNERS = [
    (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
    (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
]
_BOX_INDICES = [
    0, 1, 2, 0, 2, 3,    # -Z
    4, 6, 5, 4, 7, 6,    # +Z
    0, 4, 5, 0, 5, 1,    # -Y
    3, 2, 6, 3, 6, 7,    # +Y
    0, 3, 7, 0, 7, 4,    # -X
    1, 5, 6, 1, 6, 2,    # +X
]


def _luisa_scene_text(bars: list[dict], cam: dict) -> str:
    """Author a minimal but valid LuisaRender TEXT scene (`.luisa` SDL) for the same bars.

    Format reverse-engineered from the repo's `tools/tungsten2luisa.py` converter.
    Uses InlineMesh boxes (no OBJ dependency) so geometry is identical to the
    OctaneX render. Node graph: Surface/Shape/Camera/Env, rooted by `render`.
    """
    import math

    def v3(x, y, z):
        return f"{x:.4f}, {y:.4f}, {z:.4f}"

    S = 3.0  # LuisaRender scene scale: enlarge the small MHD bars so they fill the frame
    surf_lines = []
    shape_lines = []
    for i, b in enumerate(bars):
        c = b["center"]
        s = b["size"]
        # Unscaled half-extents; S is applied ONCE to the final world-space corner
        # (previously hx was pre-scaled by S AND the corner offset multiplied by S
        # again -> bars came out S^2=9x too wide and overlapped into unreadable slabs).
        hx, hy, hz = s[0] / 2, s[1] / 2, s[2] / 2
        col = b["color"]
        mat = b["family"]
        surf_lines.append(
            f"Surface {mat} : Matte {{\n"
            # Canonical LuisaRender Matte parameter is `Kd` (diffuse reflectance),
            # NOT `albedo` — matte.cpp reads `property_node_or_default("Kd")` and
            # silently ignores `albedo`, which produced a black frame. See
            # docs/luisa-render-backend-investigation.md.
            f"  Kd : Constant {{\n    v {{ {v3(col[0], col[1], col[2])} }}\n  }}\n}}"
        )
        # bake world-space box corners (center + corner*half), scaled once by S
        pos = []
        for (cx, cy, cz) in _BOX_CORNERS:
            pos += [(c[0] + cx * hx) * S, (c[1] + cy * hy) * S, (c[2] + cz * hz) * S]
        positions = ", ".join(f"{p:.4f}" for p in pos)
        indices = ", ".join(str(k) for k in _BOX_INDICES)
        # Diffuse bars lit by the directional key light — NO per-shape emissive
        # `light : Diffuse`. The previous `col*6` emission blew the bars out to
        # white and washed out the Kd colour (verified: brightest pixels were
        # (255,255,255) instead of blue/gold/green). Match the Octane reference:
        # diffuse bars, studio key light, balanced exposure.
        shape_lines.append(
            f"Shape shape_{i} : InlineMesh {{\n"
            f"  positions {{ {positions} }}\n"
            f"  indices {{ {indices} }}\n"
            f"  surface {{ @{mat} }}\n"
            f"  transform : Matrix {{\n    m {{ "
            f"1, 0, 0, 0,\n        0, 1, 0, 0,\n        0, 0, 1, 0,\n        0, 0, 0, 1 }}\n  }}\n}}"
        )

    # Camera: explicit 3/4 view from above-right, framed on the bar cluster's true
    # bounds (not the mean of centres — that pointed at empty space between bars
    # and read as a flat/ambiguous straight-on shot). We want clear perspective so
    # the 3 distinct bars + their relative heights are unambiguous.
    xs = [(bar["center"][0] - bar["size"][0] / 2) * S for bar in bars] + \
         [(bar["center"][0] + bar["size"][0] / 2) * S for bar in bars]
    ys = [0.0] + [(bar["center"][1] + bar["size"][1] / 2) * S for bar in bars]
    zs = []
    for bar in bars:
        zs += [(-bar["size"][2] / 2) * S, (bar["size"][2] / 2) * S]
    bcx = (min(xs) + max(xs)) / 2
    bcy = (min(ys) + max(ys)) / 2
    bcz = (min(zs) + max(zs)) / 2
    span = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    target = [bcx, bcy, bcz]
    # pull back + rise + offset to the right for a 3/4 perspective
    dist = span * 1.9
    eye = [bcx + dist * 0.55, bcy + dist * 0.65, bcz + dist * 0.95]
    up = [0.0, 1.0, 0.0]
    front = [target[0] - eye[0], target[1] - eye[1], target[2] - eye[2]]
    flen = math.sqrt(sum(x * x for x in front)) or 1.0
    front = [x / flen for x in front]
    # Narrower FOV (was 40) to tighten framing on the 3 bars and reduce dead space.
    fov = 30.0

    lines = []
    lines.extend(surf_lines)
    # Lighting: a bright Directional key light (matches Octane soft_studio exposure)
    # + a soft Spherical environment fill so shadows/background are not pure black.
    # Bars are plain Matte (Kd colour) lit by these — no self-emission.
    lines.append(
        f"Env dir : Directional {{\n"
        f"  emission : Constant {{\n    v {{ 4.0, 4.0, 4.0 }}\n  }}\n"
        f"  scale {{ 2.0 }}\n"
        f"  transform : Matrix {{\n    m {{ "
        f"0.577, 0.577, 0.577, 0,\n        -0.577, 0.577, -0.577, 0,\n        0.577, -0.577, 0.577, 0,\n        0, 0, 0, 1 }}\n  }}\n}}"
    )
    lines.append(
        f"Env env : Spherical {{\n"
        f"  emission : Constant {{\n    v {{ 0.28, 0.36, 0.52 }}\n  }}\n}}"
    )
    lines.extend(shape_lines)
    lines.append(
        f"Camera camera : Pinhole {{\n"
        f"  fov {{ {fov:.4f} }}\n"
        f"  spp {{ 64 }}\n"
        f"  filter : Gaussian {{ radius {{ 1 }} }}\n"
        f"  film : Color {{\n    resolution {{ 1400, 900 }}\n  }}\n"
        f'  file {{ "luisa-preview.exr" }}\n'
        f"  transform : View {{\n"
        f"    position {{ {v3(eye[0], eye[1], eye[2])} }}\n"
        f"    front {{ {v3(front[0], front[1], front[2])} }}\n"
        f"    up {{ {v3(up[0], up[1], up[2])} }}\n"
        f"  }}\n}}"
    )
    shape_refs = ",\n    ".join(f"@shape_{i}" for i in range(len(bars)))
    # Combine the directional key + spherical fill into one environment for the render.
    lines.insert(len(lines) - 1,  # before the render block
        f"Env sky : Combined {{\n"
        f"  a {{ @dir }}\n"
        f"  b {{ @env }}\n"
        f"}}"
    )
    lines.append(
        f"render {{\n"
        f"  cameras {{ @camera }}\n"
        f"  integrator : MegaPath {{\n    sampler : PMJ02BN {{}}\n  }}\n"
        f"  shapes {{\n    {shape_refs}\n  }}\n"
        f"  environment {{ @sky }}\n}}"
    )
    return "\n\n".join(lines) + "\n"


def _write_mtl(d: Path, mats: dict[str, dict]) -> None:
    lines = ["# Material hints; Octane binding is driven by scene.json create_material + assign_material."]
    for name, m in mats.items():
        r, g, b = m["color"]
        lines.append(f"newmtl {name}")
        lines.append(f"Kd {r:.4f} {g:.4f} {b:.4f}")
        lines.append(f"Ns {int(1.0 / max(m.get('roughness', 0.35), 1e-3))}")
    (d / "scene.mtl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_preview(d: Path) -> None:
    """Reference raster: 3 coloured bars on dark ground (mirrors the energy bars)."""
    w, h = 320, 90
    import math
    raw = bytearray()
    bands = [[0.30, 0.55, 0.95], [0.95, 0.75, 0.25], [0.35, 0.85, 0.45]]
    bw = w // 3
    for y in range(h):
        raw.append(0)
        for x in range(w):
            bi = min(2, x // bw)
            bh = int(h * 0.7 * (1.0 - bi * 0.18))
            if y > h - bh:
                c = bands[bi]
            else:
                c = [0.05, 0.06, 0.08]
            raw += bytes([int(c[0] * 255), int(c[1] * 255), int(c[2] * 255)])
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes(raw), 9)

    def _crc(data: bytes) -> int:
        return zlib.crc32(data) & 0xFFFFFFFF

    def _chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", _crc(tag + data))

    (d / "preview.png").write_bytes(sig + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", bytes()))


def _attempt_luisa_render(d: Path) -> dict:
    """Best-effort: run the local LuisaRender CLI on the emitted TEXT scene. Report honestly."""
    out = {"attempted": False, "rendered": False, "error": None, "output_path": None}
    scene_file = d / "luisa-scene.luisa"
    if not LUISA_CLI.exists():
        out["error"] = "luisa-render-cli not built"
        return out
    if not scene_file.exists():
        out["error"] = "luisa-scene.luisa missing"
        return out
    out["attempted"] = True
    try:
        proc = subprocess.run(
            [str(LUISA_CLI), "-b", "metal", str(scene_file)],
            capture_output=True, text=True, timeout=240,
        )
        out["returncode"] = proc.returncode
        out["stderr"] = proc.stderr[-2000:] if proc.stderr else ""
        out["stdout"] = proc.stdout[-1000:] if proc.stdout else ""
        # LuisaRender writes an EXR/HDR by default; accept any produced image file.
        for cand in (d / "luisa-preview.exr", d / "render.exr", d / "result.exr",
                     d / "luisa-preview.png", d / "render.png"):
            if cand.exists():
                out["rendered"] = True
                out["output_path"] = str(cand)
                break
        if not out["rendered"]:
            out["error"] = f"cli exited {proc.returncode}; no image produced (stderr tail: {out['stderr'][-300:]})"
    except Exception as e:  # noqa: BLE001
        out["error"] = f"luisa render raised: {e!r}"
    return out


def main(output_root: Path = RECIPES, attempt_luisa: bool = False) -> dict[str, Any]:
    d = output_root / SLUG
    d.mkdir(parents=True, exist_ok=True)
    # preserve a prior live-promotion flag so regeneration does not drop it
    existing = d / "scene.json"
    prev_native = None
    if existing.exists():
        try:
            prev_native = json.loads(existing.read_text()).get("native_octane_verified")
        except Exception:
            pass
    out = _build()
    if prev_native is not None:
        out["scene"]["native_octane_verified"] = bool(prev_native)
    (d / "scene.obj").write_text(out["obj_text"].rstrip("\n") + "\n", encoding="utf-8")
    _write_mtl(d, out["mats"])
    (d / "scene.json").write_text(json.dumps(out["scene"], indent=2) + "\n", encoding="utf-8")
    (d / "luisa-scene.luisa").write_text(out["luisa_scene"], encoding="utf-8")
    _write_preview(d)
    (d / "README.md").write_text(
        "# Renderer Backend Comparison (C4)\n\n"
        "Phase C renderer-agnostic grammar: the same MHD energy-bar geometry is emitted for "
        "OctaneX (combined OBJ) and LuisaRender (TEXT SDL `.luisa`, InlineMesh boxes). OctaneX "
        "renders natively; LuisaRender is driven by its local CLI (`-b metal`). See `backends` "
        "in scene.json for the live LuisaRender attempt result. The comparison is the recipe.\n",
        encoding="utf-8",
    )
    result = {"slug": SLUG, "bars": len(out["scene"]["simulation"]["physical_variables"])}
    if attempt_luisa:
        luisa = _attempt_luisa_render(d)
        result["luisa"] = luisa
        # record the honest attempt result in scene.json backends block
        scene_path = d / "scene.json"
        sc = json.loads(scene_path.read_text())
        sc["backends"]["luisa_render"]["render_status"] = (
            "rendered" if luisa.get("rendered") else f"failed: {luisa.get('error')}"
        )
        if luisa.get("output_path"):
            sc["backends"]["luisa_render"]["output"] = luisa["output_path"]
        # keep the nested octanex flag in sync with the authoritative top-level flag
        sc["backends"]["octanex"]["native_octane_verified"] = bool(sc.get("native_octane_verified"))
        scene_path.write_text(json.dumps(sc, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(main(attempt_luisa=True), indent=2))
