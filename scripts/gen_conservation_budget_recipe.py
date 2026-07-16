#!/usr/bin/env python3
"""Phase C recipe: conservation-budget-panels (C2).

Extends the `t8_conservation_budget` benchmark grammar into a standalone,
fixture-first recipe. The physical claim is *near-conservation*: across MHD
timesteps the kinetic / magnetic / internal energy bars stay close to their
initial values and the total is approximately flat, while a fourth family
(relative energy drift = |E_t - E_0| / E_0) shows the *error* budget shrinking
or staying small. Geometry carries the claim (relative bar heights + the drift
panel), no external simulator at render time.

Reuses `benchmarks.spec._orszag_tang_mhd` for a real Orszag-Tang integration
trace, so the numbers are genuine, but the recipe is deterministic and
offline-verifiable like every other Phase C build.
"""
from __future__ import annotations

import json
import struct
import sys
import zlib
from pathlib import Path
from typing import Any

# repo imports
REPO = Path(__file__).resolve().parents[1]
for _p in (REPO / "src", REPO / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from benchmarks.spec import _orszag_tang_mhd, _mat, CombinedObj  # noqa: E402
from octanex_mcp.visuals import ObjBuilder, camera_for_bounds  # noqa: E402

SLUG = "conservation-budget-panels"
RECIPES = REPO / "examples" / "recipes"


def _write_mtl(d: Path, mats: dict[str, dict]) -> None:
    lines = ["# Material hints; Octane binding is driven by scene.json create_material + assign_material."]
    for name, m in mats.items():
        r, g, b = m["color"]
        lines.append(f"newmtl {name}")
        lines.append(f"Kd {r:.4f} {g:.4f} {b:.4f}")
        lines.append(f"Ns {int(1.0 / max(m.get('roughness', 0.3), 1e-3))}")
    (d / "scene.mtl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_preview(d: Path) -> None:
    """Lightweight reference raster: 3 energy families + drift, one band per step.

    PNG requires a per-scanline filter byte (type 0 = None) before zlib.
    """
    w, h = 320, 90
    fam_colors = [
        (0.2, 0.7, 0.95),   # kinetic  - cyan
        (0.95, 0.7, 0.2),   # magnetic - amber
        (0.6, 0.85, 0.4),   # internal - green
        (0.95, 0.3, 0.35),  # drift    - red
    ]
    nfam = len(fam_colors)
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            band = min(nfam - 1, x * nfam // w)
            c = fam_colors[band]
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


def _build() -> dict[str, Any]:
    sim = _orszag_tang_mhd(steps=8, grid=20)
    trace = sim["trace"]
    steps_n = len(trace)
    e0 = trace[0]["total"]

    groups = ["kinetic", "magnetic", "internal", "drift"]
    group_colors = {
        "kinetic": [0.2, 0.7, 0.95],
        "magnetic": [0.95, 0.7, 0.2],
        "internal": [0.6, 0.85, 0.4],
        "drift": [0.95, 0.3, 0.35],
    }
    max_total = max(t["total"] for t in trace) or 1.0
    height_scale = 2.4 / max_total
    min_bar_h = 0.06

    obj = CombinedObj("conservation_budget")
    assignments = []
    gi = 0
    x = 0.0
    bar_w = 0.78
    gap = 0.22
    group_gap = 0.55
    for t in trace:
        # energy families
        for g in ("kinetic", "magnetic", "internal"):
            h = max(t[g] * height_scale, min_bar_h)
            b = ObjBuilder(f"b{gi}")
            b.add_box(center=(x + bar_w / 2, 0.0, h / 2), size=(bar_w, bar_w, h), material=f"{g}_mat")
            gi += 1
            obj.add_group(f"b{gi - 1}", f"{g}_mat", b)
            assignments.append({"group_index": gi, "material_name": f"{g}_mat"})
            x += bar_w + gap
        # drift / error family: relative total-energy drift from step 0
        drift = abs(t["total"] - e0) / (e0 or 1.0)
        # scale drift into a visible bar (drift is small, so use a x20 exaggeration
        # with a floor, and label honestly in the simulation block)
        h = max(drift * 20.0 * height_scale, min_bar_h)
        b = ObjBuilder(f"b{gi}")
        b.add_box(center=(x + bar_w / 2, 0.0, h / 2), size=(bar_w, bar_w, h), material="drift_mat")
        gi += 1
        obj.add_group(f"b{gi - 1}", "drift_mat", b)
        assignments.append({"group_index": gi, "material_name": "drift_mat"})
        x += bar_w + gap
        x += group_gap

    floor_b = ObjBuilder("floor")
    floor_b.add_box(center=((x - group_gap) / 2, 0, -0.05),
                    size=(x - group_gap + 1.0, 2.5, 0.04), material="floor_mat")
    gi += 1
    obj.add_group("floor", "floor_mat", floor_b)
    assignments.append({"group_index": gi, "material_name": "floor_mat"})

    mats = {
        "kinetic_mat": {"kind": "glossy", "color": group_colors["kinetic"], "roughness": 0.3},
        "magnetic_mat": {"kind": "glossy", "color": group_colors["magnetic"], "roughness": 0.3},
        "internal_mat": {"kind": "glossy", "color": group_colors["internal"], "roughness": 0.3},
        "drift_mat": {"kind": "glossy", "color": group_colors["drift"], "roughness": 0.3},
        "floor_mat": {"kind": "diffuse", "color": [0.06, 0.07, 0.09], "roughness": 0.9},
    }
    commands: list[dict] = [
        {"op": "import_geometry", "payload": {
            "path": f"examples/recipes/{SLUG}/scene.obj", "format": "obj", "name": SLUG.replace("-", "_")}},
    ]
    for name, m in mats.items():
        commands.append({"op": "create_material", "payload": {
            "name": name, "kind": m["kind"], "color": m["color"], "roughness": m["roughness"]}})
    for a in assignments:
        commands.append({"op": "assign_material", "payload": {
            "object_name": SLUG.replace("-", "_"),
            "material_name": a["material_name"], "group_index": a["group_index"]}})
    commands.extend([
        {"op": "set_camera", "payload": camera_for_bounds(obj.bounds(), view="iso", margin=1.05, fov=38)},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "save_preview", "payload": {
            "path": f"{SLUG}/octane-preview.png", "width": 1400, "height": 900,
            "quality": "high", "samples": 128, "min_samples": 16, "timeout_seconds": 90}},
    ])

    # expose per-step budget for tests/metadata
    budget_rows = []
    for i, t in enumerate(trace):
        drift = abs(t["total"] - e0) / (e0 or 1.0)
        budget_rows.append({
            "step": i, "kinetic": t["kinetic"], "magnetic": t["magnetic"],
            "internal": t["internal"], "total": t["total"], "drift_rel": drift,
        })

    scene = {
        "slug": SLUG,
        "title": "Conservation Budget Panels (MHD energy + drift)",
        "category": "Physical simulation / numerical diagnostics",
        "domain": "Physics simulation",
        "purpose": (
            "Show simulation correctness as geometry, not just a pretty render. Across "
            "MHD timesteps the kinetic / magnetic / internal energy bars stay close to "
            "their initial values (near-conservation) and the red drift bars show the "
            "relative total-energy error budget staying small. This is the Phase C "
            "numerical-diagnostics grammar: physical correctness made visible."
        ),
        "prompt": "Visualise MHD energy conservation as 3D budget bars with a drift/error panel.",
        "camera": camera_for_bounds(obj.bounds(), view="iso", margin=1.05, fov=38),
        "materials": mats,
        "commands": commands,
        "simulation": {
            "source_library": "MPIPyMHD (real Orszag-Tang MHD integration, reused)",
            "fixture": "embedded 8-step Orszag-Tang trace, grid=20, deterministic",
            "physical_variables": ["kinetic_energy", "magnetic_energy", "internal_energy", "total_energy_drift"],
            "units": {"energy": "code_units"},
            "scale_mapping": {
                "scene_units_per_meter": 1.0,
                "height_scale": height_scale,
                "bar_width": bar_w,
                "drift_exaggeration": 20.0,
                "families": groups,
                "steps": steps_n,
            },
            "time": {"frames": steps_n, "t_seconds": steps_n * 0.02},
            "null_model": "idealised conserved total (flat bars, zero drift)",
            "frame_grammar": {
                "layout": "timestep_bar_row",
                "orientation": "left_to_right_increasing_time",
                "per_family_group": True,
                "drift_panel_encodes_error": True,
            },
            "limitations": [
                "drift bars are exaggeration x20 of true relative drift, labelled as error budget",
                "no live PDE solve at render time; trace is a committed deterministic fixture",
            ],
            "budget_rows": budget_rows,
        },
        "quality_checklist": [
            "Three energy families (cyan/magnetic/amber-green) visible as bar rows.",
            "Red drift bars present and small relative to the energy bars.",
            "Total energy approximately flat across steps (conservation claim).",
            "Each bar group has an explicit create_material + assign_material(group_index).",
        ],
        "known_pitfalls": [
            "OBJ/MTL colours are ignored by the bridge; families need explicit materials.",
            "Many bars => many groups; keep steps modest (8) until animation workflows mature.",
        ],
        "native_octane_verified": False,
    }
    return {"obj_text": obj.text(), "scene": scene, "mats": mats, "bounds": obj.bounds()}


def main(output_root: Path = RECIPES) -> dict[str, Any]:
    d = output_root / SLUG
    d.mkdir(parents=True, exist_ok=True)
    out = _build()
    (d / "scene.obj").write_text(str(out["obj_text"]).rstrip("\n") + "\n", encoding="utf-8")
    _write_mtl(d, out["mats"])
    (d / "scene.json").write_text(json.dumps(out["scene"], indent=2) + "\n", encoding="utf-8")
    _write_preview(d)
    (d / "README.md").write_text(
        "# Conservation Budget Panels (C2)\n\n"
        "Phase C numerical-diagnostics recipe. Shows MHD energy near-conservation as "
        "3D bars across 8 timesteps (kinetic / magnetic / internal) plus a red "
        "relative-drift (error) panel. Trace from a real Orszag-Tang MHD integration "
        "(`benchmarks.spec._orszag_tang_mhd`), committed deterministically.\n\n"
        "Re-render:\n\n"
        "```\n"
        "PYTHONPATH=scripts:. uv run python scripts/gen_conservation_budget_recipe.py\n"
        "```\n\n"
        "Promote via the live Octane path: `benchmarks.verify_recipes --live --copy-back "
        "--slug conservation-budget-panels`.\n",
        encoding="utf-8",
    )
    return {
        "slug": SLUG,
        "bars": len(out["scene"]["simulation"]["budget_rows"]) * 4,
        "steps": out["scene"]["simulation"]["scale_mapping"]["steps"],
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
