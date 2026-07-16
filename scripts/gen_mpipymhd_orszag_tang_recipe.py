#!/usr/bin/env python3
"""Generate the MPIPyMHD Orszag-Tang vortex recipe from a committed fixture."""
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

SOURCE = "mpipymhd"
SLUG = "mhd-orszag-tang-vortex"
OBJECT_NAME = SLUG.replace("-", "_")
FIXTURE_SLUG = "orszag-tang-vortex"
FIXTURE_FILE = "orszag-tang-vortex.npz"

MATERIALS: dict[str, dict[str, Any]] = {
    "base_mat": {"kind": "diffuse", "color": [0.04, 0.045, 0.06], "roughness": 0.8},
    "density_mat": {"kind": "glossy", "color": [0.08, 0.36, 0.92], "roughness": 0.35},
    "pressure_mat": {"kind": "glossy", "color": [0.92, 0.30, 0.08], "roughness": 0.35},
    "magnetic_mat": {"kind": "glossy", "color": [0.72, 0.25, 1.0], "roughness": 0.2},
    "velocity_mat": {"kind": "glossy", "color": [0.10, 0.95, 0.75], "roughness": 0.25},
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
    arrays = load_npz(path, source="MPIPyMHD")
    required = {"Bx", "By", "density", "pressure", "vx", "vy"}
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
    provenance = arrays["density"]["provenance"]
    sidecar = path.with_suffix(".json")
    if sidecar.exists():
        provenance = {**provenance, **json.loads(sidecar.read_text(encoding="utf-8"))}
    provenance = {**provenance, "fixture_arrays": ["Bx", "By", "density", "pressure", "vx", "vy"]}
    return shaped, provenance


def _norm_range(field: list[list[float]]) -> tuple[float, float]:
    vals = [v for row in field for v in row]
    return min(vals), max(vals)


def _surface(field: list[list[float]], *, z_scale: float, z_offset: float, material: str) -> tuple[list[list[tuple[float, float, float]]], str]:
    rows, cols = len(field), len(field[0])
    lo, hi = _norm_range(field)
    span = max(hi - lo, 1e-9)
    sx = 10.0 / (cols - 1)
    sy = 10.0 / (rows - 1)
    verts: list[list[tuple[float, float, float]]] = []
    for i in range(rows):
        y = -5.0 + i * sy
        row = []
        for j in range(cols):
            x = -5.0 + j * sx
            z = z_offset + ((field[i][j] - lo) / span - 0.5) * z_scale
            row.append((x, y, z))
        verts.append(row)
    return verts, material


def _arrow_grid(obj: ObjBuilder, xfield: list[list[float]], yfield: list[list[float]], *, z: float, material: str, stride: int = 5) -> int:
    rows, cols = len(xfield), len(xfield[0])
    count = 0
    for i in range(2, rows - 2, stride):
        for j in range(2, cols - 2, stride):
            x = -5.0 + j * 10.0 / (cols - 1)
            y = -5.0 + i * 10.0 / (rows - 1)
            vx = xfield[i][j]
            vy = yfield[i][j]
            mag = math.hypot(vx, vy)
            if mag < 0.05:
                continue
            scale = 0.85 / max(mag, 1e-9)
            obj.add_arrow(start_point=(x, y, z), end_point=(x + vx * scale, y + vy * scale, z),
                          shaft_radius=0.025, head_radius=0.09, head_height=0.18,
                          segments=8, material=material)
            count += 1
    return count


def _material_groups(obj_text: str) -> list[str]:
    groups: list[str] = []
    for line in obj_text.splitlines():
        if line.startswith("usemtl "):
            name = line.split()[1]
            if name not in groups:
                groups.append(name)
    return groups


def _write_mtl(path: Path) -> None:
    lines = ["# Material hints; Octane binding is driven by scene.json commands."]
    for name, spec in MATERIALS.items():
        r, g, b = spec["color"]
        lines.extend([f"newmtl {name}", f"Kd {r:.4f} {g:.4f} {b:.4f}", "Ks 0.4 0.4 0.4", "d 1.0"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _commands(groups: list[str], camera: dict[str, Any]) -> list[dict[str, Any]]:
    commands = [{"op": "import_geometry", "payload": {"path": f"examples/recipes/{SLUG}/scene.obj", "format": "obj", "name": OBJECT_NAME}}]
    for name in groups:
        spec = MATERIALS[name]
        commands.append({"op": "create_material", "payload": {"name": name, "kind": spec["kind"], "color": spec["color"], "roughness": spec["roughness"]}})
    for idx, name in enumerate(groups, start=1):
        commands.append({"op": "assign_material", "payload": {"object_name": OBJECT_NAME, "material_name": name, "group_index": idx}})
    commands.extend([
        {"op": "set_camera", "payload": camera},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "save_preview", "payload": {"path": f"{SLUG}/octane-preview.png", "width": 1280, "height": 1280, "quality": "standard", "samples": 128, "min_samples": 16, "timeout_seconds": 90}},
    ])
    return commands


def _build_obj(fields: dict[str, list[list[float]]]) -> tuple[str, dict[str, Any]]:
    obj = ObjBuilder(OBJECT_NAME)
    obj.add_box(center=(0, 0, -1.1), size=(10.8, 10.8, 0.12), material="base_mat")
    density_surface, _ = _surface(fields["density"], z_scale=1.4, z_offset=-0.1, material="density_mat")
    pressure_surface, _ = _surface(fields["pressure"], z_scale=0.7, z_offset=0.85, material="pressure_mat")
    obj.add_surface(vertices=density_surface, material="density_mat")
    obj.add_surface(vertices=pressure_surface, material="pressure_mat")
    magnetic = _arrow_grid(obj, fields["Bx"], fields["By"], z=1.55, material="magnetic_mat")
    velocity = _arrow_grid(obj, fields["vx"], fields["vy"], z=1.95, material="velocity_mat")
    text = obj.text()
    return text, {"bounds": obj.bounds(), "grid_shape": [len(fields["density"]), len(fields["density"][0])], "magnetic_glyphs": magnetic, "velocity_glyphs": velocity}


def _png(path: Path, fields: dict[str, list[list[float]]]) -> None:
    w = h = 180
    density = fields["density"]
    lo, hi = _norm_range(density)
    rows, cols = len(density), len(density[0])
    raw_rgb = bytearray()
    for y in range(h):
        i = min(rows - 1, int(y * rows / h))
        for x in range(w):
            j = min(cols - 1, int(x * cols / w))
            t = (density[i][j] - lo) / max(hi - lo, 1e-9)
            raw_rgb.extend((int(30 + 190 * t), int(50 + 70 * (1 - t)), int(130 + 100 * (1 - t))))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw.extend(raw_rgb[y * w * 3:(y + 1) * w * 3])
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    path.write_bytes(png)


def _scene(camera: dict[str, Any], groups: list[str], provenance: dict[str, Any], stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "slug": SLUG,
        "title": "MHD Orszag-Tang Vortex",
        "category": "Physical simulation / magnetohydrodynamics",
        "domain": "Physics simulation",
        "purpose": "Render an Orszag-Tang-style MHD snapshot with density and pressure surfaces plus magnetic and velocity glyph fields.",
        "prompt": "Visualise an MPIPyMHD Orszag-Tang vortex with density, pressure, magnetic-field arrows, and velocity glyphs.",
        "camera": camera,
        "materials": {name: {"name": name, **spec} for name, spec in MATERIALS.items()},
        "commands": _commands(groups, camera),
        "simulation": {
            **provenance,
            "source_library": "MPIPyMHD",
            "source_path": "/Users/craig/src/MPIPyMHD-Magnetohydrodynamics-Simulation-Framework",
            "physical_variables": ["density", "pressure", "velocity", "magnetic_field"],
            "units": {"length": "normalized", "time": "normalized"},
            "scale_mapping": {"scene_units_per_domain": 10.0, "density_height_scale": 1.4, "pressure_height_scale": 0.7, "vector_scale": 0.85},
            "null_model": "uniform density/pressure with zero velocity and magnetic field",
            "adapter_stats": stats,
            "limitations": [
                "fixture is an analytic Orszag-Tang-style snapshot, not a full time-integrated MHD solve",
                "magnetic and velocity vectors are downsampled glyphs",
                "normal tests do not import mpi4py or require an MPI runtime",
            ],
        },
        "preview_note": "preview.png is a lightweight reference raster; octane-preview.png is the native Octane render after promotion.",
        "quality_checklist": [
            "Density and pressure surfaces are visibly separated.",
            "Purple magnetic glyphs and teal velocity glyphs are both visible.",
            "Every usemtl group has explicit create_material + assign_material(group_index).",
        ],
        "known_pitfalls": [
            "OBJ/MTL colours are ignored by the bridge; scene.json material commands are required.",
            "The committed fixture is analytic until the local MPIPyMHD solver grows a real Orszag-Tang integrator.",
            "OBJ line primitives may be dropped, so vectors are arrow meshes.",
        ],
        "visual_iteration_protocol": {
            "model": "ollama:glm-ocr",
            "reference_image": f"examples/recipes/{SLUG}/preview.png",
            "candidate_image": f"examples/recipes/{SLUG}/octane-preview.png",
            "max_iterations": 4,
            "review_focus": ["surface separation", "magnetic glyph visibility", "velocity glyph visibility", "framing"],
            "patch_dimensions": ["geometry", "camera", "lighting", "materials", "render_settings"],
            "required_evidence": ["bridge result metadata", "native Octane preview at octane-preview.png", "iteration records", "final native Octane render bundled as octane-preview.png"],
            "baseline_sweep": {"camera_or_scene_variants": [
                {"label": "default framing", "camera": camera},
                {"label": "closer framing", "camera": {**camera, "position": [c * 0.75 for c in camera["position"]]}},
                {"label": "wider framing", "camera": {**camera, "position": [c * 1.25 for c in camera["position"]]}},
                {"label": "top-oblique", "camera": {**camera, "position": [camera["position"][0], camera["position"][1], camera["position"][2] + 3.0]}},
            ]},
            "stop_conditions": ["magnetic glyphs are legible", "surface layers are distinguishable"],
        },
        "final_bundle": {"required": True, "native_render": f"examples/recipes/{SLUG}/octane-preview.png", "bundled_assets": ["scene.obj", "scene.mtl", "scene.json", "preview.png", "octane-preview.png"], "status": "pending_native_octane_iteration"},
        "native_octane_verified": False,
        "status": "built; native render pending (physical-simulation Phase B)",
    }


def _write_readme(path: Path, stats: dict[str, Any], provenance: dict[str, Any]) -> None:
    path.write_text(
        "# MHD Orszag-Tang Vortex\n\n"
        "Phase B fixture-first adapter recipe for an MPIPyMHD/Orszag-Tang-style MHD snapshot.\n\n"
        "## Provenance\n\n"
        f"- Fixture: `{provenance['fixture']}`\n"
        f"- SHA-256: `{provenance['fixture_sha256']}`\n"
        f"- Grid: `{stats['grid_shape'][0]}×{stats['grid_shape'][1]}`\n"
        f"- Magnetic glyphs: `{stats['magnetic_glyphs']}`\n"
        f"- Velocity glyphs: `{stats['velocity_glyphs']}`\n\n"
        "## Regenerate\n\n"
        "```bash\n"
        "python3 scripts/export_mpipymhd_orszag_tang_fixture.py\n"
        "PYTHONPATH=scripts:. uv run python scripts/gen_mpipymhd_orszag_tang_recipe.py\n"
        "```\n\n"
        "## Pitfalls\n\n"
        "- Normal tests must not require mpi4py or an MPI runtime; the committed `.npz` is the boundary.\n"
        "- The fixture is an analytic Orszag-Tang-style snapshot until the local MPIPyMHD source grows a full solver.\n"
        "- Vector fields are arrow meshes, not OBJ line primitives.\n",
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
    _png(recipe / "preview.png", fields)
    _write_readme(recipe / "README.md", stats, provenance)
    return {"slug": SLUG, "grid_shape": stats["grid_shape"], "magnetic_glyphs": stats["magnetic_glyphs"], "velocity_glyphs": stats["velocity_glyphs"], "groups": groups}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
