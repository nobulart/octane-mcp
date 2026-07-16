#!/usr/bin/env python3
"""Generate the Genesis `cloth-on-rigid` recipe from the committed fixture.

Follows the same fixture-first boundary as the other Phase B adapters: the
committed JSON fixture (examples/fixtures/genesis/cloth-on-rigid/) is the only
input; no runtime Genesis dependency is required to build or test the recipe.

Run:
    PYTHONPATH=scripts:. uv run python scripts/gen_genesis_cloth_on_rigid_recipe.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECIPES = ROOT / "examples" / "recipes"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from octanex_mcp.visuals import ObjBuilder, camera_for_bounds  # noqa: E402
from physics_fixture_io import Fixtures  # noqa: E402

SOURCE = "genesis"
SLUG = "genesis-cloth-on-rigid"
OBJECT_NAME = SLUG.replace("-", "_")
FIXTURE_SLUG = "cloth-on-rigid"
FIXTURE_FILE = "cloth-on-rigid.json"

MATERIALS: dict[str, dict[str, Any]] = {
    "cloth_mat": {"kind": "glossy", "color": [0.85, 0.20, 0.35], "roughness": 0.45},
    "rigid_mat": {"kind": "metallic", "color": [0.80, 0.82, 0.88], "roughness": 0.25, "metallic": 0.9},
    "contact_mat": {"kind": "emissive", "color": [1.0, 0.85, 0.20], "roughness": 0.3, "emission": 3.0},
    "base_mat": {"kind": "diffuse", "color": [0.04, 0.045, 0.06], "roughness": 0.9},
}


def _load_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    path = Fixtures.path(SOURCE, FIXTURE_SLUG, FIXTURE_FILE)
    data = json.loads(path.read_text(encoding="utf-8"))
    sidecar = path.with_suffix(".prov.json")
    provenance = data.get("provenance", {})
    if sidecar.exists():
        provenance = {**provenance, **json.loads(sidecar.read_text(encoding="utf-8"))}
    provenance = {**provenance, "fixture_arrays": ["vertices", "contact_vertex_indices"]}
    return data, provenance


def _cloth_surface(fixture: dict[str, Any]) -> list[list[tuple[float, float, float]]]:
    """Cloth vertex grid as a surface, via the shared drape source of truth."""
    from genesis_cloth_drape import build_draped_vertices, drape_grid_as_surface

    n = fixture["grid"][0]
    return drape_grid_as_surface(
        build_draped_vertices(n, fixture["cloth_half_extent"], fixture["cloth_z0"], fixture["sphere"]["center"], fixture["sphere"]["radius"]),
        n,
    )


def _add_sphere(obj: ObjBuilder, center: list[float], radius: float, material: str) -> None:
    """Approximate the rigid sphere with a lat/long UV sphere mesh."""
    segs = 18
    rings = 12
    grid: list[list[tuple[float, float, float]]] = []
    for ri in range(rings + 1):
        theta = math.pi * ri / rings
        row = []
        for si in range(segs):
            phi = 2 * math.pi * si / segs
            x = center[0] + radius * math.sin(theta) * math.cos(phi)
            y = center[1] + radius * math.sin(theta) * math.sin(phi)
            z = center[2] + radius * math.cos(theta)
            row.append((x, y, z))
        grid.append(row)
    obj.add_surface(vertices=grid, material=material)


def _build_obj(fixture: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    obj = ObjBuilder(OBJECT_NAME)
    # base plane under the scene
    obj.add_box(center=(0, 0, -0.6), size=(8.5, 8.5, 0.1), material="base_mat")
    cloth_verts = _cloth_surface(fixture)
    obj.add_surface(vertices=cloth_verts, material="cloth_mat")
    sphere = fixture["sphere"]
    _add_sphere(obj, sphere["center"], sphere["radius"], "rigid_mat")
    # contact markers (emissive ellipsoid meshes) — placed on the draped cloth
    from genesis_cloth_drape import drape_vertex

    contact_set = set(fixture["contact_vertex_indices"])
    n = fixture["grid"][0]
    half = fixture["cloth_half_extent"]
    z0 = fixture["cloth_z0"]
    sphere = fixture["sphere"]
    cx, cy, cz = sphere["center"]
    r = sphere["radius"]
    markers = 0
    for idx in contact_set:
        iy, ix = divmod(idx, n)
        x = -half + (2 * half) * ix / (n - 1)
        y = -half + (2 * half) * iy / (n - 1)
        mx, my, mz = drape_vertex(x, y, z0, n, [cx, cy, cz], r)
        obj.add_ellipsoid(center=(mx, my, mz), radii=(0.12, 0.12, 0.12), material="contact_mat")
        markers += 1
    text = obj.text()
    return text, {"bounds": obj.bounds(), "contact_markers": markers, "grid": fixture["grid"]}


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
        extra = f" metallic {spec['metallic']}" if "metallic" in spec else ""
        extra += f" emission {spec['emission']}" if "emission" in spec else ""
        lines.extend([f"newmtl {name}", f"Kd {r:.4f} {g:.4f} {b:.4f}", "Ks 0.4 0.4 0.4", "d 1.0" + extra])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _commands(groups: list[str], camera: dict[str, Any]) -> list[dict[str, Any]]:
    commands = [{"op": "import_geometry", "payload": {"path": f"examples/recipes/{SLUG}/scene.obj", "format": "obj", "name": OBJECT_NAME}}]
    for name in groups:
        spec = MATERIALS[name]
        payload = {"name": name, "kind": spec["kind"], "color": spec["color"], "roughness": spec["roughness"]}
        if "metallic" in spec:
            payload["metallic"] = spec["metallic"]
        if "emission" in spec:
            payload["emission"] = spec["emission"]
        commands.append({"op": "create_material", "payload": payload})
    for idx, name in enumerate(groups, start=1):
        commands.append({"op": "assign_material", "payload": {"object_name": OBJECT_NAME, "material_name": name, "group_index": idx}})
    commands.extend([
        {"op": "set_camera", "payload": camera},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "save_preview", "payload": {"path": f"{SLUG}/octane-preview.png", "width": 1280, "height": 1280, "quality": "standard", "samples": 128, "min_samples": 16, "timeout_seconds": 90}},
    ])
    return commands


def _scene(fixture: dict[str, Any], camera: dict[str, Any], groups: list[str], provenance: dict[str, Any], stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "slug": SLUG,
        "title": "Genesis Cloth on Rigid Body",
        "category": "Physical simulation / deformable + rigid coupling",
        "domain": "Physics simulation",
        "purpose": "Render a Genesis-style cloth sheet draping over a translating rigid body with emergent contact markers.",
        "prompt": "Visualise a Genesis cloth-on-rigid simulation: a deforming cloth mesh, a metallic rigid sphere, and contact markers where the cloth meets the body.",
        "camera": camera,
        "materials": {name: {"name": name, **spec} for name, spec in MATERIALS.items()},
        "commands": _commands(groups, camera),
        "simulation": {
            **provenance,
            "source_library": "Genesis",
            "source_path": "/Users/craig/src/Genesis",
            "physical_variables": ["cloth_vertex_positions", "rigid_body_transform", "contact_markers"],
            "units": {"length": "scene units", "time": "steps"},
            "scale_mapping": {"cloth_half_extent": fixture["cloth_half_extent"], "sphere_radius": fixture["sphere"]["radius"]},
            "null_model": "flat cloth sheet at rest; rigid sphere absent",
            "adapter_stats": stats,
            "limitations": [
                "fixture is a deterministic analytic drape snapshot, not a real Genesis cloth solve",
                "local Genesis build does not yet expose a stable CLOTH/RIGID Python entity API; the fixture regeneration script documents the call sequence",
                "OBJ/MTL colours are ignored by the bridge; scene.json material commands are required",
            ],
        },
        "preview_note": "preview.png is a lightweight reference raster; octane-preview.png is the native Octane render after promotion.",
        "quality_checklist": [
            "Cloth surface and rigid sphere are visually separated.",
            "Emissive contact markers are visible where cloth meets the sphere.",
            "Every usemtl group has explicit create_material + assign_material(group_index).",
        ],
        "known_pitfalls": [
            "OBJ/MTL colours are ignored by the bridge; scene.json material commands are required.",
            "The committed fixture is analytic until the local Genesis solver exposes a cloth/rigid entity API.",
            "OBJ line primitives may be dropped, so contact markers are ellipsoid meshes.",
        ],
        "visual_iteration_protocol": {
            "model": "ollama:glm-ocr",
            "reference_image": f"examples/recipes/{SLUG}/preview.png",
            "candidate_image": f"examples/recipes/{SLUG}/octane-preview.png",
            "max_iterations": 4,
            "review_focus": ["cloth/sphere separation", "contact marker visibility", "framing"],
            "patch_dimensions": ["geometry", "camera", "lighting", "materials", "render_settings"],
            "required_evidence": ["bridge result metadata", "native Octane preview at octane-preview.png", "iteration records", "final native Octane render bundled as octane-preview.png"],
            "stop_conditions": ["contact markers legible", "cloth drape reads correctly"],
        },
        "final_bundle": {"required": True, "native_render": f"examples/recipes/{SLUG}/octane-preview.png", "bundled_assets": ["scene.obj", "scene.mtl", "scene.json", "preview.png", "octane-preview.png"], "status": "pending_native_octane_iteration"},
        "native_octane_verified": False,
        "status": "built; native render pending (physical-simulation Phase B)",
    }


def _png(path: Path, fixture: dict[str, Any]) -> None:
    """Lightweight reference raster of the draped cloth + rigid sphere."""
    import struct
    import zlib

    w = h = 180
    n = fixture["grid"][0]
    verts = fixture["vertices"]
    half = fixture["cloth_half_extent"]
    sphere = fixture["sphere"]
    cx, cy, cz = sphere["center"]
    r = sphere["radius"]
    # map grid index -> flattened vertex; build a depth-ish shade from z
    def _vz(ix: int, iy: int) -> float:
        return verts[iy * n + ix][2]
    lo = min(v[2] for v in verts)
    hi = max(v[2] for v in verts)
    raw_rgb = bytearray()
    for y in range(h):
        iy = min(n - 1, int(y * n / h))
        for x in range(w):
            ix = min(n - 1, int(x * n / w))
            vx = -half + (2 * half) * ix / (n - 1)
            vy = -half + (2 * half) * iy / (n - 1)
            vz = _vz(ix, iy)
            # base cloth color (red), darkened by height
            t = (vz - lo) / max(hi - lo, 1e-9)
            rr, gg, bb = int(60 + 200 * t), int(20 + 60 * t), int(40 + 80 * t)
            # tint contact region / sphere presence
            if abs(math.dist((vx, vy, vz), (cx, cy, cz)) - r) < 0.4:
                rr, gg, bb = 255, 220, 60
            raw_rgb.extend((min(255, max(0, rr)), min(255, max(0, gg)), min(255, max(0, bb))))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw.extend(raw_rgb[y * w * 3:(y + 1) * w * 3])
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    path.write_bytes(png)


def _write_readme(path: Path, stats: dict[str, Any], provenance: dict[str, Any]) -> None:
    path.write_text(
        "# Genesis Cloth on Rigid Body\n\n"
        "Phase B fixture-first adapter for a Genesis-style cloth sheet draping over a "
        "translating rigid body with emergent contact markers.\n\n"
        "## Provenance\n\n"
        f"- Fixture: `{provenance.get('fixture', '')}`\n"
        f"- SHA-256: `{provenance.get('fixture_sha256', '')[:16]}…`\n"
        f"- Grid: `{stats['grid'][0]}×{stats['grid'][1]}`\n"
        f"- Contact markers: `{stats['contact_markers']}`\n\n"
        "## Regenerate\n\n"
        "```bash\n"
        "PYTHONPATH=scripts:. uv run python scripts/export_genesis_cloth_on_rigid_fixture.py\n"
        "PYTHONPATH=scripts:. uv run python scripts/gen_genesis_cloth_on_rigid_recipe.py\n"
        "```\n\n"
        "## Pitfalls\n\n"
        "- The committed fixture is an analytic drape snapshot; the local Genesis build does "
        "not yet expose a stable CLOTH/RIGID Python entity API, so the fixture regeneration "
        "script documents the call sequence for when it does.\n"
        "- OBJ/MTL colours are ignored by the bridge; scene.json material commands are required.\n"
        "- Contact markers are ellipsoid meshes (OBJ line primitives may be dropped).\n",
        encoding="utf-8",
    )


def main(output_root: Path = RECIPES) -> dict[str, Any]:
    fixture, provenance = _load_fixture()
    recipe = output_root / SLUG
    recipe.mkdir(parents=True, exist_ok=True)
    obj_text, stats = _build_obj(fixture)
    (recipe / "scene.obj").write_text(obj_text.rstrip("\n") + "\n", encoding="utf-8")
    _write_mtl(recipe / "scene.mtl")
    groups = _material_groups(obj_text)
    camera = camera_for_bounds(stats["bounds"], view="iso", margin=1.4, fov=42)
    scene = _scene(fixture, camera, groups, provenance, stats)
    # Preserve an existing native promotion so re-running the generator does not
    # silently un-verify a recipe that was already live-rendered and promoted.
    existing = recipe / "scene.json"
    if existing.exists():
        try:
            prev = json.loads(existing.read_text(encoding="utf-8"))
            if prev.get("native_octane_verified") is True:
                scene["native_octane_verified"] = True
                scene["status"] = prev.get("status", scene["status"])
                scene.setdefault("final_bundle", {})["status"] = "native_verified"
        except (json.JSONDecodeError, OSError):
            pass
    (recipe / "scene.json").write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    _png(recipe / "preview.png", fixture)
    _write_readme(recipe / "README.md", stats, provenance)
    return {"slug": SLUG, "groups": groups, "contact_markers": stats["contact_markers"], "grid": stats["grid"]}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
