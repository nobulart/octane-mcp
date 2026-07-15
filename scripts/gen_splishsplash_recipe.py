#!/usr/bin/env python3
"""Phase B adapter: SPlisHSPlasH particle fixture -> OctaneX recipe.

This is the *adapter* boundary described in docs/physical-simulation-recipe-suite.md.
It consumes a committed SPlisHSPlasH export (``examples/fixtures/particles/``)
through ``scripts/physics_fixture_io.py`` (no runtime SPlisHSPlasH dependency) and
emits a contract-correct recipe directory under ``examples/recipes/``:

  * scene.obj    — one usemtl group per particle (liquid / foam mapped by phase),
                   built with the project ObjBuilder so index behaviour matches
                   every other recipe.
  * scene.mtl    — material hints (documentation only; bridge uses scene.json).
  * scene.json   — verified-recipe contract: import + create_material per group
                   + assign_material(group_index) per group + camera + soft_studio
                   lighting + save_preview. Carries the fixture provenance in the
                   ``simulation`` block so the chain source -> render is honest.
  * preview.png  — lightweight reference raster (stdlib PNG, no PIL).
  * README.md    — purpose, provenance, re-render command, pitfalls.

Run:
    PYTHONPATH=scripts:. uv run python scripts/gen_splishsplash_recipe.py
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
from physics_fixture_io import Fixtures, load_csv_particles  # noqa: E402

SOURCE = "splishsplash"
SLUG = "dam-break-splash"
FIXTURE_SLUG = "dam-break-small"
FIXTURE_FILE = "dam-break-small.csv"

LIQUID_COLOR = [0.1, 0.7, 0.85]
FOAM_COLOR = [0.9, 0.95, 1.0]
LIQUID_R = 0.11
FOAM_R = 0.07


def _materials() -> dict[str, dict]:
    return {
        "liquid_mat": {"kind": "glossy", "color": LIQUID_COLOR, "roughness": 0.15, "opacity": 0.85},
        "foam_mat": {"kind": "diffuse", "color": FOAM_COLOR, "roughness": 0.7},
    }


def _write_mtl(d: Path, mats: dict[str, dict]) -> None:
    lines = ["# Material hints; Octane binding is driven by scene.json create_material + assign_material."]
    for name, m in mats.items():
        r, g, b = m["color"]
        lines.append(f"newmtl {name}")
        lines.append(f"Kd {r:.4f} {g:.4f} {b:.4f}")
        lines.append(f"Ns {int(1.0 / max(m.get('roughness', 0.3), 1e-3))}")
    (d / "scene.mtl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_preview(d: Path) -> None:
    # 160x160 stdlib raster: liquid teal on left, foam white on right (proxy only).
    w = h = 160
    raw = bytearray()
    for y in range(h):
        for x in range(w):
            if x < w * 0.7:
                raw += bytes([int(255 * LIQUID_COLOR[0]), int(255 * LIQUID_COLOR[1]), int(255 * LIQUID_COLOR[2])])
            else:
                raw += bytes([int(255 * FOAM_COLOR[0]), int(255 * FOAM_COLOR[1]), int(255 * FOAM_COLOR[2])])
    def _crc32(data):
        return zlib.crc32(data) & 0xFFFFFFFF
    def _chunk_png(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", _crc32(tag + data))
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes(raw), 9)
    png = sig + _chunk_png(b"IHDR", ihdr) + _chunk_png(b"IDAT", idat) + _chunk_png(b"IEND", b"")
    with (d / "preview.png").open("wb") as fh:
        fh.write(png)


def _build() -> dict[str, Any]:
    res = load_csv_particles(Fixtures.path("particles", FIXTURE_SLUG, FIXTURE_FILE), source="splishsplash")
    cloud = res["cloud"]
    prov = res["provenance"]

    mats = _materials()
    obj = ObjBuilder(SLUG.replace("-", "_"))
    groups: list[str] = []
    for (x, y, z), phase in zip(cloud.positions, cloud.phases):
        mat = "liquid_mat" if phase == 0 else "foam_mat"
        r = LIQUID_R if mat == "liquid_mat" else FOAM_R
        obj.add_ellipsoid(center=(x, y, z), radii=(r, r, r), material=mat, segments_u=6, segments_v=4)
        groups.append(mat)

    obj_text = obj.text()
    cam = camera_for_bounds(obj.bounds(), view="iso", margin=1.5, fov=42)

    commands: list[dict] = [
        {"op": "import_geometry", "payload": {
            "path": f"examples/recipes/{SLUG}/scene.obj", "format": "obj", "name": SLUG.replace("-", "_")}},
    ]
    for name in ("liquid_mat", "foam_mat"):
        m = mats[name]
        payload = {"name": name, "kind": m["kind"], "color": m["color"], "roughness": m["roughness"]}
        if "opacity" in m:
            payload["opacity"] = m["opacity"]
        commands.append({"op": "create_material", "payload": payload})
    for idx, name in enumerate(groups, start=1):
        commands.append({"op": "assign_material", "payload": {
            "object_name": SLUG.replace("-", "_"), "material_name": name, "group_index": idx}})
    commands.extend([
        {"op": "set_camera", "payload": cam},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "save_preview", "payload": {
            "path": f"{SLUG}/octane-preview.png", "width": 1024, "height": 1024,
            "quality": "standard", "samples": 64, "min_samples": 16, "timeout_seconds": 90}},
    ])

    scene = {
        "slug": SLUG,
        "title": "Dam-Break Splash (SPlisHSPlasH fixture)",
        "category": "Physical simulation / particles",
        "domain": "Physics simulation",
        "purpose": (
            "Render a committed SPlisHSPlasH dam-break export (liquid + foam phases) as a "
            "particle cloud. This is the Phase B adapter boundary: the source simulator ran "
            "once, its export is committed under examples/fixtures/particles/, and this recipe "
            "consumes it through scripts/physics_fixture_io.py with NO runtime SPlisHSPlasH "
            "dependency."),
        "prompt": "Visualise a dam-break splash from a SPlisHSPlasH particle fixture (liquid + foam).",
        "camera": cam,
        "materials": mats,
        "commands": commands,
        "simulation": {
            "source_library": "splishsplash",
            **prov,
            "physical_variables": ["position", "velocity", "phase"],
            "units": {"length": "m", "time": "s"},
            "scale_mapping": {"scene_units_per_meter": 1.0, "particle_radius_m": LIQUID_R},
            "null_model": "uniform random particle cloud with no gravity-driven front",
            "limitations": [
                "fixture is a single exported frame, not a live SPH solve",
                "particle radii are render proxies, not physical SPH kernel radius",
            ],
        },
        "quality_checklist": [
            "Two colour families visible: teal liquid particles and white foam particles.",
            "Particles read as a splashing cloud, not a solid mesh.",
            "Each particle group has an explicit create_material + assign_material(group_index).",
        ],
        "known_pitfalls": [
            "OBJ/MTL colours are ignored by the bridge; the split comes from explicit create_material + assign_material.",
            "One usemtl group PER particle yields a large scene.obj; the bridge handles it but live render is heavy.",
        ],
    }
    return {"obj_text": obj_text, "scene": scene, "mats": mats}


def main(output_root: Path = RECIPES) -> dict[str, Any]:
    d = output_root / SLUG
    d.mkdir(parents=True, exist_ok=True)
    out = _build()
    (d / "scene.obj").write_text(str(out["obj_text"]).rstrip("\n") + "\n", encoding="utf-8")
    _write_mtl(d, out["mats"])  # type: ignore[arg-type]
    (d / "scene.json").write_text(json.dumps(out["scene"], indent=2) + "\n", encoding="utf-8")
    _write_preview(d)
    (d / "README.md").write_text(
        "# Dam-Break Splash (SPlisHSPlasH fixture)\n\n"
        "Phase B adapter recipe. Source: `examples/fixtures/particles/dam-break-small/dam-break-small.csv` "
        f"(sha256 `{out['scene']['simulation']['fixture_sha256'][:16]}…`), loaded via "
        "`scripts/physics_fixture_io.py`.\n\n"
        "Re-render:\n\n"
        "```\n"
        "PYTHONPATH=scripts:. uv run python scripts/gen_splishsplash_recipe.py\n"
        "```\n\n"
        "Then promote via the live Octane path with `benchmarks.verify_recipes --live --copy-back`.\n",
        encoding="utf-8",
    )
    stats = {
        "slug": SLUG,
        "particles": out["scene"]["simulation"]["fixture_shape"][0],
        "render_commands": len(out["scene"]["commands"]) - 3,  # minus camera/lighting/save
    }
    return stats


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
