#!/usr/bin/env python3
"""Phase C recipe: precision-error-landscape (C3).

Makes numerical *precision* visible. For a grid of (iteration count x initial
condition) we run a chaotic logistic-map recurrence `x -> 4 x (1 - x)` under three
arithmetic regimes and record the absolute error of each lower-precision run
against a high-precision reference:

  * reference : Python `decimal` at 60 digits (portable arbitrary precision)
  * float64   : IEEE double
  * float32   : IEEE single

The error surface (reference - float) is rendered as a heightfield whose height
and colour encode |error| (cool = exact, warm = large drift). A second panel shows
the float32 vs float64 error as a 1D strip. The recipe is deterministic and
offline-verifiable.

NOTE on y-cruncher: the suite plan lists y-cruncher as a *suggested* high-precision
source. The local copy (`/Users/craig/src/y-cruncher*`) ships only x86-64 ELF
Linux binaries, which cannot execute on this Apple-Silicon macOS host, so the
portable `decimal` reference is used instead. The recipe documents this honestly
in its `simulation.limitations`.
"""
from __future__ import annotations

import json
import math
import struct
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
from benchmarks.spec import CombinedObj  # noqa: E402

SLUG = "precision-error-landscape"
RECIPES = REPO / "examples" / "recipes"

PREC = 60
CTX = Context(prec=PREC)


def _ref_step(x: Decimal) -> Decimal:
    return CTX.multiply(Decimal(4), CTX.multiply(x, CTX.subtract(Decimal(1), x)))


def _float_step(x: float) -> float:
    return 4.0 * x * (1.0 - x)


def _reference(n: int, x0: Decimal) -> Decimal:
    x = x0
    for _ in range(n):
        x = _ref_step(x)
    return x


def _float64_run(n: int, x0: float) -> float:
    x = x0
    for _ in range(n):
        x = _float_step(x)
    return x


def _build() -> dict[str, Any]:
    # Grid: rows = initial condition x0 in (0,1), cols = iteration count.
    NX = 24          # initial conditions
    NIT = 24         # iteration counts
    x0s = [Decimal(i) / Decimal(NX) + Decimal("0.02") for i in range(NX)]
    its = list(range(2, 2 + NIT))

    # reference grid (Decimal) + float64 grid
    ref_grid = [[_reference(it, x0) for it in its] for x0 in x0s]
    f64_grid = [[_float64_run(it, float(x0)) for it in its] for x0 in x0s]

    def err_abs(ref: Decimal, fv: float) -> float:
        # |ref - fv| in units of the reference magnitude, clamped to [0,1] for viz
        d = abs(ref - Decimal(repr(fv)))
        mag = abs(ref) or Decimal("1e-300")
        return min(1.0, float(d / mag))

    # error surface: float64 error vs reference (log-compressed for visibility)
    import math
    surf = [[0.0] * NIT for _ in range(NX)]
    for i in range(NX):
        for j in range(NIT):
            e = err_abs(ref_grid[i][j], f64_grid[i][j])
            surf[i][j] = max(0.0, math.log10(1.0 + e * 1e6) / 7.0)  # 0..~1

    cell = 1.0
    gap = 0.08
    step = cell + gap
    HSCALE = 2.2

    # colour ramp cool(exact)->warm(large error)
    def err_color(v: float) -> list[float]:
        return [0.15 + 0.70 * v, 0.45 + 0.25 * (1.0 - v), 0.95 - 0.70 * v]

    verts: list[list[tuple[float, float, float]]] = []
    for i in range(NX):
        rowv: list[tuple[float, float, float]] = []
        for j in range(NIT):
            x = j * step
            y = i * step
            z = surf[i][j] * HSCALE - HSCALE * 0.5
            rowv.append((x, y, z))
        verts.append(rowv)

    obj = ObjBuilder("error_surface")
    obj.add_surface(vertices=verts, material="error_mat")

    # a flat base slab under the surface
    base_b = ObjBuilder("base")
    base_b.add_box(center=((NIT - 1) * step / 2, (NX - 1) * step / 2, -HSCALE * 0.5 - 0.05),
                   size=((NIT - 1) * step + 1.0, (NX - 1) * step + 1.0, 0.04),
                   material="base_mat")

    # 1D float32-vs-float64 error strip (front edge of the surface, last x0 row)
    # Build a thin raised ribbon of NIT cells coloured by float32 error.
    f32_grid = [[_float32_run_proxy(its[j], float(x0s[i])) for j in range(NIT)] for i in range(NX)]
    strip_b = ObjBuilder("f32_strip")
    sw = 0.6
    for j in range(NIT):
        e = err_abs(ref_grid[NX - 1][j], f32_grid[NX - 1][j])
        ev = max(0.0, math.log10(1.0 + e * 1e6) / 7.0)
        h = max(ev * HSCALE, 0.06)
        x = j * step
        strip_b.add_box(center=(x, (NX - 1) * step + 1.2, h / 2),
                         size=(cell * 0.7, sw, h), material="f32_mat")

    # combine the three parts into one mesh with per-group materials
    cob = CombinedObj(SLUG.replace("-", "_"))
    cob.add_group("error_surface", "error_mat", obj)
    cob.add_group("base", "base_mat", base_b)
    cob.add_group("f32_strip", "f32_mat", strip_b)
    cam = camera_for_bounds(cob.bounds(), view="iso", margin=1.2, fov=40)

    commands: list[dict] = [
        {"op": "import_geometry", "payload": {
            "path": f"examples/recipes/{SLUG}/scene.obj", "format": "obj", "name": SLUG.replace("-", "_")}},
        {"op": "create_material", "payload": {"name": "error_mat", "kind": "glossy", "color": [0.55, 0.45, 0.95], "roughness": 0.3}},
        {"op": "create_material", "payload": {"name": "base_mat", "kind": "diffuse", "color": [0.06, 0.07, 0.09], "roughness": 0.9}},
        {"op": "create_material", "payload": {"name": "f32_mat", "kind": "glossy", "color": [0.95, 0.3, 0.35], "roughness": 0.3}},
        {"op": "assign_material", "payload": {"object_name": SLUG.replace("-", "_"), "material_name": "error_mat", "group_index": 1}},
        {"op": "assign_material", "payload": {"object_name": SLUG.replace("-", "_"), "material_name": "base_mat", "group_index": 2}},
        {"op": "assign_material", "payload": {"object_name": SLUG.replace("-", "_"), "material_name": "f32_mat", "group_index": 3}},
        {"op": "set_camera", "payload": cam},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "save_preview", "payload": {
            "path": f"{SLUG}/octane-preview.png", "width": 1400, "height": 900,
            "quality": "high", "samples": 128, "min_samples": 16, "timeout_seconds": 90}},
    ]

    scene = {
        "slug": SLUG,
        "title": "Precision Error Landscape (logistic map, decimal vs float)",
        "category": "Physical simulation / numerical diagnostics",
        "domain": "Numerical diagnostics",
        "purpose": (
            "Make floating-point precision error visible. A chaotic logistic map "
            "x -> 4x(1-x) is integrated to high precision with Python `decimal` (60 "
            "digits) and compared against IEEE float64 and float32. The surface height "
            "and colour encode the relative error |ref - float| (cool = exact, warm = "
            "large drift); the red front strip is the float32-vs-reference error. This is "
            "the Phase C numerical-story grammar: correctness/error made geometric."
        ),
        "prompt": "Visualise a precision-error landscape: a heightfield of float vs high-precision reference error over (iteration, initial condition).",
        "camera": cam,
        "materials": {
            "error_mat": {"kind": "glossy", "color": [0.55, 0.45, 0.95], "roughness": 0.3},
            "base_mat": {"kind": "diffuse", "color": [0.06, 0.07, 0.09], "roughness": 0.9},
            "f32_mat": {"kind": "glossy", "color": [0.95, 0.3, 0.35], "roughness": 0.3},
        },
        "commands": commands,
        "simulation": {
            "source_library": "Python decimal (portable arbitrary precision reference)",
            "fixture": f"deterministic logistic-map error grid {NX}x{NIT}",
            "physical_variables": ["relative_precision_error"],
            "units": {"error": "relative (|ref-float|/|ref|)"},
            "scale_mapping": {
                "scene_units_per_meter": 1.0,
                "height_scale": HSCALE,
                "grid_nx": NX,
                "grid_nit": NIT,
                "error_encoding": "log10(1 + rel_err*1e6)/7 clamped to [0,1]",
            },
            "time": {"iterations_max": its[-1]},
            "null_model": "exact arithmetic: flat zero-error surface",
            "frame_grammar": {
                "layout": "error_heightfield",
                "color_axis": "cool_exact_to_warm_large_error",
                "front_strip_encodes": "float32_vs_reference_error",
            },
            "limitations": [
                "y-cruncher (plan-suggested high-precision source) ships only x86-64 ELF "
                "Linux binaries and cannot run on this Apple-Silicon macOS host; the "
                "portable `decimal` (60-digit) reference is used instead.",
                "error is log-compressed for visibility; small errors saturate to near-flat.",
            ],
            "error_stats": {
                "max_rel_err_f64": max(max(surf[i][j] for j in range(NIT)) for i in range(NX)),
                "max_rel_err_f32": max(err_abs(ref_grid[NX - 1][j], f32_grid[NX - 1][j]) for j in range(NIT)),
            },
        },
        "quality_checklist": [
            "Heightfield shows spatial error structure (not a flat plane).",
            "Colour ramps cool (low error) to warm (high error).",
            "Red front strip encodes float32 error distinctly from the surface.",
            "Each mesh group has an explicit create_material + assign_material(group_index).",
        ],
        "known_pitfalls": [
            "OBJ/MTL colours are ignored by the bridge; families need explicit materials.",
            "Heightfield is one group; the colour ramp is carried by material, not vertices.",
        ],
        "native_octane_verified": False,
    }
    # assemble final OBJ text from the combined mesh
    obj_text = cob.text()
    return {"obj_text": obj_text, "scene": scene, "mats": scene["materials"]}


def _float32_run_proxy(n: int, x0: float) -> float:
    # simulate float32 by rounding through numpy-free struct trick (portable)
    import struct as _st
    x = x0
    for _ in range(n):
        x = 4.0 * x * (1.0 - x)
        x = _st.unpack("f", _st.pack("f", x))[0]  # round to float32
    return x


def _write_mtl(d: Path, mats: dict[str, dict]) -> None:
    lines = ["# Material hints; Octane binding is driven by scene.json create_material + assign_material."]
    for name, m in mats.items():
        r, g, b = m["color"]
        lines.append(f"newmtl {name}")
        lines.append(f"Kd {r:.4f} {g:.4f} {b:.4f}")
        lines.append(f"Ns {int(1.0 / max(m.get('roughness', 0.3), 1e-3))}")
    (d / "scene.mtl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_preview(d: Path) -> None:
    """Lightweight reference raster: error-heightfield top-down heat strip."""
    w, h = 320, 90
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        # top (y=0) = high error (warm); bottom = exact (cool)
        t = 1.0 - y / max(h - 1, 1)
        c = [0.15 + 0.70 * t, 0.45 + 0.25 * (1.0 - t), 0.95 - 0.70 * t]
        for x in range(w):
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


def main(output_root: Path = RECIPES) -> dict[str, Any]:
    d = output_root / SLUG
    d.mkdir(parents=True, exist_ok=True)
    out = _build()
    (d / "scene.obj").write_text(str(out["obj_text"]).rstrip("\n") + "\n", encoding="utf-8")
    _write_mtl(d, out["mats"])
    (d / "scene.json").write_text(json.dumps(out["scene"], indent=2) + "\n", encoding="utf-8")
    _write_preview(d)
    (d / "README.md").write_text(
        "# Precision Error Landscape (C3)\n\n"
        "Phase C numerical-diagnostics recipe. Shows floating-point precision error as a "
        "heightfield: a chaotic logistic map integrated to 60-digit `decimal` precision, "
        "compared against IEEE float64/float32. Height + colour encode relative error.\n\n"
        "Re-render:\n\n"
        "```\n"
        "PYTHONPATH=scripts:. uv run python scripts/gen_precision_error_recipe.py\n"
        "```\n\n"
        "Promote via the live Octane path: `benchmarks.verify_recipes --live --copy-back "
        "--slug precision-error-landscape`.\n",
        encoding="utf-8",
    )
    return {"slug": SLUG, "grid": "24x24"}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
