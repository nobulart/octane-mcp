#!/usr/bin/env python3
"""Phase B adapter: Oceananigans-style shallow-water fixture -> OctaneX recipe.

This adapter consumes a small committed `.npz` fixture under
`examples/fixtures/oceananigans/shallow-water-front/` and emits a complete
recipe directory under `examples/recipes/oceananigans-shallow-water-front/`.
It does **not** import Julia/Oceananigans at runtime; the fixture is the adapter
boundary.

Run:
    PYTHONPATH=scripts:. uv run python scripts/gen_oceananigans_shallow_water_recipe.py
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
from physics_fixture_io import Fixtures, load_npz  # noqa: E402

SOURCE = "oceananigans"
SLUG = "oceananigans-shallow-water-front"
OBJECT_NAME = SLUG.replace("-", "_")
FIXTURE_SLUG = "shallow-water-front"
FIXTURE_FILE = "shallow-water-front.npz"

MATERIALS: dict[str, dict[str, Any]] = {
    "bathymetry_mat": {"kind": "diffuse", "color": [0.16, 0.13, 0.10], "roughness": 0.75},
    "cold_water_mat": {"kind": "glossy", "color": [0.05, 0.28, 0.72], "roughness": 0.28},
    "front_water_mat": {"kind": "glossy", "color": [0.05, 0.72, 0.82], "roughness": 0.22},
    "warm_water_mat": {"kind": "glossy", "color": [1.0, 0.20, 0.04], "roughness": 0.24},
    "velocity_mat": {"kind": "glossy", "color": [0.92, 0.95, 1.0], "roughness": 0.18},
    "coastline_mat": {"kind": "diffuse", "color": [0.48, 0.38, 0.22], "roughness": 0.7},
}


def _reshape(flat: list[float], shape: tuple[int, ...]) -> list[list[float]]:
    if len(shape) != 2:
        raise ValueError(f"expected 2-D array, got shape {shape}")
    rows, cols = shape
    if len(flat) != rows * cols:
        raise ValueError(f"array length {len(flat)} does not match shape {shape}")
    return [flat[i * cols : (i + 1) * cols] for i in range(rows)]


def _load_fixture() -> tuple[dict[str, list[list[float]]], dict[str, Any]]:
    path = Fixtures.path(SOURCE, FIXTURE_SLUG, FIXTURE_FILE)
    arrays = load_npz(path, source=SOURCE)
    required = {"eta", "u", "v", "bathymetry"}
    missing = sorted(required - set(arrays))
    if missing:
        raise ValueError(f"fixture missing arrays: {missing}")
    shaped: dict[str, list[list[float]]] = {}
    shape: tuple[int, ...] | None = None
    for name in sorted(required):
        item = arrays[name]
        item_shape = tuple(item["shape"])
        if shape is None:
            shape = item_shape
        elif item_shape != shape:
            raise ValueError(f"array {name} shape {item_shape} != {shape}")
        shaped[name] = _reshape([float(x) for x in item["data"]], item_shape)
    provenance = arrays["eta"]["provenance"]
    sidecar = path.with_suffix(".json")
    if sidecar.exists():
        provenance = {**provenance, **json.loads(sidecar.read_text(encoding="utf-8"))}
    provenance = {**provenance, "fixture_arrays": sorted(required)}
    return shaped, provenance


def _material_groups(obj_text: str) -> list[str]:
    out: list[str] = []
    for line in obj_text.splitlines():
        if line.startswith("usemtl "):
            name = line.split()[1]
            if name not in out:
                out.append(name)
    return out


def _write_mtl(path: Path) -> None:
    lines = ["# Material hints; Octane binding is driven by scene.json create_material + assign_material."]
    for name, spec in MATERIALS.items():
        r, g, b = spec["color"]
        lines.extend([
            f"newmtl {name}",
            f"Ka 1.0 1.0 1.0",
            f"Kd {r:.4f} {g:.4f} {b:.4f}",
            "Ks 0.5 0.5 0.5",
            f"Ns {(1.0 - spec.get('roughness', 0.3)) * 64:.1f}",
            "d 1.0",
        ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _commands(groups: list[str], camera: dict[str, Any]) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = [
        {"op": "import_geometry", "payload": {
            "path": f"examples/recipes/{SLUG}/scene.obj", "format": "obj", "name": OBJECT_NAME}},
    ]
    for name in groups:
        spec = MATERIALS[name]
        payload = {
            "name": name,
            "kind": spec.get("kind", "glossy"),
            "color": spec["color"],
            "roughness": spec.get("roughness", 0.3),
        }
        commands.append({"op": "create_material", "payload": payload})
    for idx, name in enumerate(groups, start=1):
        commands.append({"op": "assign_material", "payload": {
            "object_name": OBJECT_NAME, "material_name": name, "group_index": idx}})
    commands.extend([
        {"op": "set_camera", "payload": camera},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "save_preview", "payload": {
            "path": f"{SLUG}/octane-preview.png", "width": 1280, "height": 1280,
            "quality": "standard", "samples": 128, "min_samples": 16, "timeout_seconds": 90}},
    ])
    return commands


def _surface_vertices(field: list[list[float]], *, z_scale: float, z_offset: float = 0.0) -> list[list[tuple[float, float, float]]]:
    rows = len(field)
    cols = len(field[0])
    sx = 12.0 / (cols - 1)
    sy = 8.0 / (rows - 1)
    verts: list[list[tuple[float, float, float]]] = []
    for i in range(rows):
        y = -4.0 + i * sy
        row = []
        for j in range(cols):
            x = -6.0 + j * sx
            row.append((x, y, z_offset + field[i][j] * z_scale))
        verts.append(row)
    return verts


def _arrow_grid(obj: ObjBuilder, u: list[list[float]], v: list[list[float]]) -> int:
    rows = len(u)
    cols = len(u[0])
    count = 0
    for i in range(3, rows - 3, 6):
        for j in range(3, cols - 3, 6):
            x = -6.0 + j * 12.0 / (cols - 1)
            y = -4.0 + i * 8.0 / (rows - 1)
            uu = u[i][j]
            vv = v[i][j]
            mag = math.hypot(uu, vv)
            if mag < 0.02:
                continue
            scale = 1.25 / max(mag, 1e-6)
            p0 = (x, y, 1.15)
            p1 = (x + uu * scale, y + vv * scale, 1.15)
            obj.add_arrow(start_point=p0, end_point=p1, shaft_radius=0.035, head_radius=0.12,
                          head_height=0.22, segments=8, material="velocity_mat")
            count += 1
    return count


def _build_obj(fields: dict[str, list[list[float]]]) -> tuple[str, dict[str, Any]]:
    eta = fields["eta"]
    bathy = fields["bathymetry"]
    u = fields["u"]
    v = fields["v"]
    obj = ObjBuilder(OBJECT_NAME)
    obj.add_surface(vertices=_surface_vertices(bathy, z_scale=0.42, z_offset=-1.45), material="bathymetry_mat")

    rows = len(eta)
    cols = len(eta[0])
    # Split the free surface into three material strips so the physical front is
    # visible without texture support.
    for mat, j0, j1 in (
        ("cold_water_mat", 0, cols // 3 + 1),
        ("front_water_mat", cols // 3, 2 * cols // 3 + 1),
        ("warm_water_mat", 2 * cols // 3, cols),
    ):
        sub = [row[j0:j1] for row in eta]
        verts = _surface_vertices(sub, z_scale=0.72, z_offset=0.18)
        # Re-map x to the original column range after slicing.
        for i, row in enumerate(verts):
            for jj, (_x, y, z) in enumerate(row):
                j = j0 + jj
                x = -6.0 + j * 12.0 / (cols - 1)
                row[jj] = (x, y, z)
        obj.add_surface(vertices=verts, material=mat)

    # Coarse coastline / shelf marker at the warm-water side.
    obj.add_box(center=(5.9, 0.0, -0.72), size=(0.18, 8.6, 0.45), material="coastline_mat")
    arrows = _arrow_grid(obj, u, v)
    obj_text = obj.text()
    return obj_text, {"bounds": obj.bounds(), "velocity_glyphs": arrows, "grid_shape": [rows, cols]}


def _write_preview(path: Path, fields: dict[str, list[list[float]]]) -> None:
    eta = fields["eta"]
    rows = len(eta)
    cols = len(eta[0])
    w = h = 180
    e_min = min(min(r) for r in eta)
    e_max = max(max(r) for r in eta)
    px = bytearray()
    for y in range(h):
        i = min(rows - 1, int(y * rows / h))
        for x in range(w):
            j = min(cols - 1, int(x * cols / w))
            t = (eta[i][j] - e_min) / max(e_max - e_min, 1e-9)
            # dark blue -> cyan front -> orange high/warm water
            if t < 0.48:
                a = t / 0.48
                rgb = (int(15 + 10 * a), int(55 + 120 * a), int(145 + 60 * a))
            else:
                a = (t - 0.48) / 0.52
                rgb = (int(30 + 215 * a), int(185 - 50 * a), int(210 - 180 * a))
            px.extend(rgb)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw.extend(px[y * w * 3 : (y + 1) * w * 3])
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def _scene(camera: dict[str, Any], groups: list[str], provenance: dict[str, Any], stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "slug": SLUG,
        "title": "Oceananigans Shallow-Water Front",
        "category": "Physical simulation / ocean dynamics",
        "domain": "Physics simulation",
        "purpose": (
            "Render a small Oceananigans-style shallow-water export as a free-surface front "
            "with velocity glyphs and a bathymetry/coastline base. The Julia simulation is not "
            "run by the recipe; a committed fixture is the reproducible adapter boundary."),
        "prompt": "Visualise an Oceananigans shallow-water front with surface height, velocity arrows, and bathymetry.",
        "camera": camera,
        "materials": {name: {"name": name, **spec} for name, spec in MATERIALS.items()},
        "commands": _commands(groups, camera),
        "simulation": {
            **provenance,
            "source_library": "Oceananigans.jl",
            "source_path": "/Users/craig/src/Oceananigans.jl",
            "physical_variables": ["free_surface_eta", "u_velocity", "v_velocity", "bathymetry"],
            "units": {"length": "km", "time": "s", "surface_height": "m"},
            "scale_mapping": {"scene_units_per_km": 0.3, "height_scale": 1.35, "vector_scale": 1.25},
            "time": {"frame": 12, "t_seconds": 1800.0},
            "null_model": "flat free surface with zero velocity and no front gradient",
            "adapter_stats": stats,
            "limitations": [
                "fixture is a compact exported state, not a live Oceananigans solve",
                "water colour bands encode front regions because OBJ import has no texture field",
                "velocity arrows are downsampled glyphs, not a dense vector field",
            ],
        },
        "preview_note": "preview.png is a lightweight reference raster; octane-preview.png is the native Octane render after promotion.",
        "quality_checklist": [
            "Three water colour families show cold side, frontal zone, and warm side.",
            "White velocity glyphs visibly cross/curve along the surface front.",
            "Brown bathymetry/coastline base sits below the free surface.",
            "Every usemtl group has explicit create_material + assign_material(group_index).",
        ],
        "known_pitfalls": [
            "OBJ/MTL colours are ignored by the bridge; material binding comes from scene.json commands.",
            "The fixture is Oceananigans-style export data; tests must not import Julia/Oceananigans.",
            "OBJ line primitives may be dropped, so velocity vectors are tube/arrow geometry.",
        ],
        "visual_iteration_protocol": {
            "model": "ollama:glm-ocr",
            "reference_image": f"examples/recipes/{SLUG}/preview.png",
            "candidate_image": f"examples/recipes/{SLUG}/octane-preview.png",
            "max_iterations": 4,
            "review_focus": ["front readability", "velocity glyph visibility", "bathymetry separation", "framing"],
            "patch_dimensions": ["geometry", "camera", "lighting", "materials", "render_settings"],
            "required_evidence": [
                "bridge result metadata",
                "native Octane preview at octane-preview.png",
                "iteration records",
                "final native Octane render bundled as octane-preview.png",
            ],
            "baseline_sweep": {
                "camera_or_scene_variants": [
                    {"label": "default framing", "camera": camera},
                    {"label": "closer framing", "camera": {**camera, "position": [c * 0.72 for c in camera["position"]]}},
                    {"label": "wider framing", "camera": {**camera, "position": [c * 1.25 for c in camera["position"]]}},
                    {"label": "top-oblique", "camera": {**camera, "position": [camera["position"][0], camera["position"][1], camera["position"][2] + 3.0]}},
                ],
            },
            "stop_conditions": ["front is legible", "velocity arrows are visible", "surface/base separation is clear"],
        },
        "final_bundle": {
            "required": True,
            "native_render": f"examples/recipes/{SLUG}/octane-preview.png",
            "bundled_assets": ["scene.obj", "scene.mtl", "scene.json", "preview.png", "octane-preview.png"],
            "status": "pending_native_octane_iteration",
        },
        "native_octane_verified": False,
        "status": "built; native render pending (physical-simulation Phase B)",
    }


def _write_readme(path: Path, stats: dict[str, Any], provenance: dict[str, Any]) -> None:
    path.write_text(
        "# Oceananigans Shallow-Water Front\n\n"
        "Phase B fixture-first adapter recipe. It renders a compact Oceananigans-style shallow-water export "
        "as a front/eddy free surface with velocity glyphs and a bathymetry/coastline base.\n\n"
        "## Provenance\n\n"
        f"- Fixture: `{provenance['fixture']}`\n"
        f"- SHA-256: `{provenance['fixture_sha256']}`\n"
        f"- Grid: `{stats['grid_shape'][0]}×{stats['grid_shape'][1]}`\n"
        f"- Velocity glyphs: `{stats['velocity_glyphs']}`\n\n"
        "## Regenerate\n\n"
        "```bash\n"
        "python3 scripts/export_oceananigans_shallow_water_fixture.py --timeout 240\n"
        "PYTHONPATH=scripts:. uv run python scripts/gen_oceananigans_shallow_water_recipe.py\n"
        "```\n\n"
        "Then promote through the live Octane recipe verifier when ready.\n\n"
        "## Pitfalls\n\n"
        "- This recipe must not import Julia/Oceananigans during normal tests; the committed `.npz` is the boundary.\n"
        "- OBJ/MTL colours are documentation only. `scene.json` binds every material group explicitly.\n"
        "- Velocity vectors are arrow meshes, not OBJ line primitives.\n",
        encoding="utf-8",
    )


def main(output_root: Path = RECIPES) -> dict[str, Any]:
    fields, provenance = _load_fixture()
    recipe = output_root / SLUG
    recipe.mkdir(parents=True, exist_ok=True)
    obj_text, stats = _build_obj(fields)
    (recipe / "scene.obj").write_text(obj_text.rstrip("\n") + "\n", encoding="utf-8")
    _write_mtl(recipe / "scene.mtl")
    groups = _material_groups(obj_text)
    camera = camera_for_bounds(stats["bounds"], view="iso", margin=1.45, fov=42)
    scene = _scene(camera, groups, provenance, stats)
    (recipe / "scene.json").write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    _write_preview(recipe / "preview.png", fields)
    _write_readme(recipe / "README.md", stats, provenance)
    return {"slug": SLUG, "grid_shape": stats["grid_shape"], "velocity_glyphs": stats["velocity_glyphs"], "groups": groups}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
