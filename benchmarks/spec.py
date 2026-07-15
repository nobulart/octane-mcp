"""OctaneX MCP benchmark suite specification.

Progressive, machine-checkable visualisation tasks that drive the bridge from
primitive smoke tests up to photoreal / multi-material stress scenes. Each task
emits a *single combined OBJ* (the bridge connects one mesh per render target,
so multi-object scenes must merge geometry and assign materials per `o` group),
a material list, per-group assignments, a bounds-aware camera, a lighting
preset, and an acceptance checklist of pixel-level criteria.

The acceptance criteria are intentionally evaluated with **pixel analysis only**
(the stdlib PNG reader in `octanex_mcp.review`), never a vision model, because
hallucinating vision models have previously mis-reported empty renders as
correct (see docs/recipe-book.md chess-pawn entry).

A task's `build()` is deterministic and has no side effects; the harness
(`harness.py`) writes the OBJ into the container workspace, queues the command
sequence, optionally drains the bridge, and then verifies the saved PNG.

Contract returned by `build()`:
    {
      "mesh_name": str,                # import_geometry name (one mesh node)
      "obj": str,                      # combined OBJ text with `o`/`usemtl` groups
      "bounds": dict,                  # union bounds (min/max/center/radius)
      "materials": [ {"name","kind","color",...} ],
      "assignments": [ {"group_index":int,"material_name":str} ],  # 1-based groups
      "camera": {"position":[3],"target":[3],"fov":float},
      "lighting": str,                 # preset name
      "save": {"quality":str,"width":int,"height":int},
      "acceptance": [ <criterion dict> ],
    }

Acceptance criterion kinds (handled in acceptance.py):
    non_empty            {min_mean_dev, min_nonbg}
    review_ok            {fail_on:[issues]}   (uses octanex_mcp.review diagnostics)
    color_present        {target:[r,g,b] 0..1, tol, min_fraction}
    color_absent         {target:[r,g,b] 0..1, tol, max_fraction}
    shape_profile        {min_rows}           (silhouette has vertical structure)
    bright_fraction      {min_near_white}     (emissive glow / clipped highlights)
    file_size            {min_bytes}
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from octanex_mcp.visuals import (
    ObjBuilder,
    bounds_from_points,
    camera_for_bounds,
)

# ---------------------------------------------------------------------------
# Combined-OBJ builder: merge multiple ObjBuilder groups into one mesh with
# correctly offset (1-based) face indices. This is the #1 empty-render cause
# (pitfall #13 / #19) so it is implemented once, carefully, here.
# ---------------------------------------------------------------------------


class CombinedObj:
    """Accumulate ObjBuilder groups into one combined OBJ with global indices."""

    def __init__(self, mesh_name: str) -> None:
        self.mesh_name = mesh_name
        self._v_lines: list[str] = []
        self._groups: list[tuple[str, str, list[str]]] = []  # (group, material, face_lines)
        self._global_v = 0
        self._points: list[tuple[float, float, float]] = []

    def add_group(self, group_name: str, material: str, builder: ObjBuilder) -> None:
        v_lines: list[str] = []
        f_lines: list[str] = []
        for line in builder.lines:
            if line.startswith("v "):
                v_lines.append(line)
                # record point for bounds (parse x y z)
                parts = line.split()
                self._points.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif line.startswith("f "):
                tokens = line.split()
                new_indices = " ".join(str(int(t) + self._global_v) for t in tokens[1:])
                f_lines.append("f " + new_indices)
        self._groups.append((group_name, material, f_lines))
        self._v_lines.extend(v_lines)
        self._global_v += builder.vertex_count

    def text(self) -> str:
        out = [f"# combined mesh {self.mesh_name}"]
        for group, material, f_lines in self._groups:
            out.append(f"o {group}")
            out.append(f"usemtl {material}")
            out.extend(self._v_lines_in_group(group))
        # re-emit vertices once per group is wasteful; instead: emit all v once.
        return self._render()

    def _v_lines_in_group(self, group: str) -> list[str]:
        # vertices are shared across the whole mesh; we emit them once globally.
        return []

    def _render(self) -> str:
        out = [f"# combined mesh {self.mesh_name}", "o " + self.mesh_name]
        for group, material, f_lines in self._groups:
            out.append(f"g {group}")
            out.append(f"usemtl {material}")
            out.extend(f_lines)
        header = "\n".join([f"# combined mesh {self.mesh_name}"])
        verts = "\n".join(self._v_lines)
        body = "\n".join(out[1:])
        return header + "\n" + verts + "\n" + body + "\n"

    def bounds(self) -> dict[str, Any]:
        return bounds_from_points(self._points)


def _mat(name: str, kind: str, color: list[float], roughness: float = 0.25,
         **extra: Any) -> dict[str, Any]:
    m: dict[str, Any] = {"name": name, "kind": kind, "color": list(color), "roughness": roughness}
    m.update(extra)
    return m


# ---------------------------------------------------------------------------
# Task model
# ---------------------------------------------------------------------------


@dataclass
class BenchmarkTask:
    tier: int
    slug: str
    title: str
    archetype: str
    description: str
    build: Callable[[], dict[str, Any]]
    native_octane_verified: bool = False

    def build_scene(self) -> dict[str, Any]:
        return self.build()


# ---------------------------------------------------------------------------
# Tier 1 — Foundations: single primitive, one material, one OBJ group
# ---------------------------------------------------------------------------


def _t1_glossy_cube() -> dict[str, Any]:
    b = ObjBuilder("cube")
    b.add_box(center=(0, 0, 0), size=(2, 2, 2), material="cube_mat")
    obj = CombinedObj("t1_cube")
    obj.add_group("cube", "cube_mat", b)
    return {
        "mesh_name": "t1_cube",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": [_mat("cube_mat", "glossy", [0.12, 0.45, 0.95], roughness=0.2)],
        "assignments": [{"group_index": 1, "material_name": "cube_mat"}],
        "camera": camera_for_bounds(obj.bounds(), view="iso", margin=1.4),
        "lighting": "soft_studio",
        "save": {"quality": "high", "width": 1280, "height": 1280},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white", "likely object too small"]},
            {"kind": "color_present", "target": [0.12, 0.45, 0.95], "tol": 0.18, "min_fraction": 0.02},
        ],
    }


def _t1_metallic_sphere() -> dict[str, Any]:
    b = ObjBuilder("sphere")
    b.add_ellipsoid(center=(0, 0, 0), radii=(1.1, 1.1, 1.1), material="gold_mat")
    obj = CombinedObj("t1_sphere")
    obj.add_group("sphere", "gold_mat", b)
    return {
        "mesh_name": "t1_sphere",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": [_mat("gold_mat", "metallic", [1.0, 0.67, 0.18], roughness=0.18, metallic=0.55)],
        "assignments": [{"group_index": 1, "material_name": "gold_mat"}],
        "camera": camera_for_bounds(obj.bounds(), view="iso", margin=1.4),
        "lighting": "soft_studio",
        "save": {"quality": "high", "width": 1280, "height": 1280},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white", "likely object too small"]},
            {"kind": "color_family", "target": [1.0, 0.67, 0.18], "hue_tol": 45, "min_fraction": 0.02},
        ],
    }


def _t1_surface_field() -> dict[str, Any]:
    b = ObjBuilder("surface")
    xmin = ymin = -3.0
    xmax = ymax = 3.0
    steps = 48
    raw: list[list[tuple[float, float, float]]] = []
    zs: list[float] = []
    for iy in range(steps + 1):
        y = ymin + (ymax - ymin) * iy / steps
        row = []
        for ix in range(steps + 1):
            x = xmin + (xmax - xmin) * ix / steps
            r = math.hypot(x, y)
            z = math.sin(r) / max(r, 0.25)
            z = max(min(z, 10.0), -10.0)
            zs.append(z)
            row.append((x, y, z))
        raw.append(row)
    mabs = max(abs(z) for z in zs) or 1.0
    scale = 1.6 / mabs
    verts = [[(x, y, z * scale) for x, y, z in row] for row in raw]
    b.add_box(center=(0, 0, -0.06), size=(6.4, 6.4, 0.04), material="base_mat")
    b.add_surface(vertices=verts, material="surface_mat")
    obj = CombinedObj("t1_surface")
    obj.add_group("surface", "surface_mat", b)
    return {
        "mesh_name": "t1_surface",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": [_mat("surface_mat", "glossy", [0.85, 0.55, 0.25], roughness=0.3)],
        "assignments": [{"group_index": 1, "material_name": "surface_mat"}],
        "camera": camera_for_bounds(obj.bounds(), view="iso", margin=1.3, fov=42),
        "lighting": "soft_studio",
        "save": {"quality": "high", "width": 1280, "height": 1280},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white", "likely object too small"]},
            {"kind": "shape_profile", "min_rows": 6},
        ],
    }


# ---------------------------------------------------------------------------
# Tier 2 — Composition & camera framing: multiple meshes in one combined OBJ
# ---------------------------------------------------------------------------


def _t2_bar_chart() -> dict[str, Any]:
    b = ObjBuilder("bars")
    values = [1.0, 2.4, 1.6, 3.1, 2.0]
    max_abs = max(values)
    scale = 2.6 / max_abs
    chart_width = max(3.0, len(values) * 0.75)
    b.add_box(center=(0, 0, -0.035), size=(chart_width + 0.6, 1.1, 0.07), material="base_mat")
    b.add_box(center=(0, -0.58, 0.02), size=(chart_width + 0.7, 0.04, 0.04), material="axis_mat")
    start_x = -((len(values) - 1) * 0.75) / 2.0
    for idx, v in enumerate(values):
        h = v * scale
        x = start_x + idx * 0.75
        b.add_box(center=(x, 0, h / 2.0), size=(0.46, 0.65, max(h, 0.04)), material="bar_mat")
    obj = CombinedObj("t2_bars")
    obj.add_group("bars", "bar_mat", b)
    return {
        "mesh_name": "t2_bars",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": [_mat("bar_mat", "glossy", [0.05, 0.75, 1.0], roughness=0.2)],
        "assignments": [{"group_index": 1, "material_name": "bar_mat"}],
        "camera": camera_for_bounds(obj.bounds(), view="iso", margin=1.3),
        "lighting": "soft_studio",
        "save": {"quality": "high", "width": 1280, "height": 1280},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white", "likely object too small"]},
            {"kind": "color_family", "target": [0.05, 0.75, 1.0], "hue_tol": 40, "min_fraction": 0.02},
            {"kind": "shape_profile", "min_rows": 6},
        ],
    }


def _t2_multi_material() -> dict[str, Any]:
    cube = ObjBuilder("cube")
    cube.add_box(center=(-1.4, 0, 0), size=(1.6, 1.6, 1.6), material="red_mat")
    sphere = ObjBuilder("sphere")
    sphere.add_ellipsoid(center=(1.4, 0, 0), radii=(1.0, 1.0, 1.0), material="green_mat")
    obj = CombinedObj("t2_mm")
    obj.add_group("cube", "red_mat", cube)
    obj.add_group("sphere", "green_mat", sphere)
    return {
        "mesh_name": "t2_mm",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": [
            _mat("red_mat", "glossy", [1.0, 0.2, 0.25], roughness=0.25),
            _mat("green_mat", "glossy", [0.2, 0.85, 0.35], roughness=0.25),
        ],
        "assignments": [
            {"group_index": 1, "material_name": "red_mat"},
            {"group_index": 2, "material_name": "green_mat"},
        ],
        "camera": camera_for_bounds(obj.bounds(), view="iso", margin=1.5),
        "lighting": "soft_studio",
        "save": {"quality": "high", "width": 1280, "height": 1280},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white"]},
            {"kind": "color_family", "target": [1.0, 0.2, 0.25], "hue_tol": 45, "min_fraction": 0.01},
            {"kind": "color_family", "target": [0.2, 0.85, 0.35], "hue_tol": 45, "min_fraction": 0.01},
        ],
    }


def _t2_scatter() -> dict[str, Any]:
    pts = [
        (-1.5, -1.2, 0.3), (-0.6, 0.4, 1.1), (0.5, -0.8, 0.6),
        (1.3, 1.0, -0.4), (-0.2, 1.6, 1.4), (1.8, -0.3, 0.9),
        (-1.7, 0.7, -1.0), (0.8, -1.7, 0.2),
    ]
    b = ObjBuilder("scatter")
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    zs = [p[2] for p in pts]
    span_x = max(xs) - min(xs) or 1.0
    span_y = max(ys) - min(ys) or 1.0
    b.add_box(center=(sum(xs) / len(xs), sum(ys) / len(ys), min(zs) - 0.2),
              size=(span_x + 1.0, span_y + 1.0, 0.1), material="base_mat")
    for i, (x, y, z) in enumerate(pts):
        b.add_box(center=(x, y, z), size=(0.32, 0.32, 0.32), material="pt_mat")
    obj = CombinedObj("t2_scatter")
    obj.add_group("scatter", "pt_mat", b)
    return {
        "mesh_name": "t2_scatter",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": [_mat("pt_mat", "glossy", [1.0, 0.42, 0.12], roughness=0.2)],
        "assignments": [{"group_index": 1, "material_name": "pt_mat"}],
        "camera": camera_for_bounds(obj.bounds(), view="iso", margin=1.4),
        "lighting": "soft_studio",
        "save": {"quality": "high", "width": 1280, "height": 1280},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white", "likely object too small"]},
            {"kind": "color_family", "target": [1.0, 0.42, 0.12], "hue_tol": 45, "min_fraction": 0.01},
        ],
    }


# ---------------------------------------------------------------------------
# Tier 3 — Lighting & materials: PBR fields, emissive, product studio
# ---------------------------------------------------------------------------


def _t3_glass_like() -> dict[str, Any]:
    b = ObjBuilder("glass")
    b.add_ellipsoid(center=(0, 0, 0), radii=(1.1, 1.1, 1.1), material="glass_mat")
    obj = CombinedObj("t3_glass")
    obj.add_group("glass", "glass_mat", b)
    return {
        "mesh_name": "t3_glass",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": [_mat("glass_mat", "glossy", [0.8, 0.9, 1.0], roughness=0.05,
                            transmission=1.0, ior=1.5, opacity=0.4)],
        "assignments": [{"group_index": 1, "material_name": "glass_mat"}],
        "camera": camera_for_bounds(obj.bounds(), view="iso", margin=1.4),
        "lighting": "soft_studio",
        "save": {"quality": "high", "width": 1280, "height": 1280},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "likely object too small"]},
        ],
    }


def _t3_emissive() -> dict[str, Any]:
    b = ObjBuilder("emit")
    b.add_ellipsoid(center=(0, 0, 0), radii=(1.2, 1.2, 1.2), material="emit_mat")
    obj = CombinedObj("t3_emit")
    obj.add_group("emit", "emit_mat", b)
    return {
        "mesh_name": "t3_emit",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": [_mat("emit_mat", "glossy", [1.0, 0.55, 0.1], roughness=0.3, emission=8.0)],
        "assignments": [{"group_index": 1, "material_name": "emit_mat"}],
        "camera": camera_for_bounds(obj.bounds(), view="iso", margin=1.4),
        "lighting": "soft_studio",
        "save": {"quality": "high", "width": 1280, "height": 1280},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 2.0, "min_nonbg": 2.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "likely object too small"]},
            # Emissive glow under cool soft_studio reads as a chromatic rim
            # (cyan + amber), not a white-out: only a small population of
            # near-white highlights actually appears (~0.8% measured). Assert
            # the glow produced bright highlight pixels without over-specifying
            # pure white.
            {"kind": "bright_fraction", "min_near_white": 0.5},
        ],
    }


def _t3_product_studio() -> dict[str, Any]:
    backdrop = ObjBuilder("cyc")
    backdrop.add_box(center=(0, -1.6, 0), size=(8, 0.4, 8), material="cyc_mat")
    backdrop.add_box(center=(0, 0, -3.0), size=(8, 5, 0.4), material="cyc_mat")
    hero = ObjBuilder("hero")
    hero.add_ellipsoid(center=(0, 0, 0), radii=(1.0, 1.0, 1.0), material="hero_mat")
    obj = CombinedObj("t3_studio")
    obj.add_group("cyc", "cyc_mat", backdrop)
    obj.add_group("hero", "hero_mat", hero)
    return {
        "mesh_name": "t3_studio",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": [
            _mat("cyc_mat", "diffuse", [0.9, 0.9, 0.92], roughness=0.9),
            _mat("hero_mat", "glossy", [0.75, 0.08, 0.12], roughness=0.1, clearcoat=0.6),
        ],
        "assignments": [
            {"group_index": 1, "material_name": "cyc_mat"},
            {"group_index": 2, "material_name": "hero_mat"},
        ],
        "camera": camera_for_bounds(obj.bounds(), view="iso", margin=1.5),
        "lighting": "soft_studio",
        "save": {"quality": "ultra", "width": 1280, "height": 1280},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white", "likely object too small"]},
            {"kind": "color_family", "target": [0.75, 0.08, 0.12], "hue_tol": 45, "min_fraction": 0.005},
        ],
    }


# ---------------------------------------------------------------------------
# Tier 4 — Multi-object scene graphs (6-12 meshes, hierarchy, flow)
# ---------------------------------------------------------------------------


def _t4_architecture_flow() -> dict[str, Any]:
    obj = CombinedObj("t4_arch")
    blocks = {
        "user": ([0, 0, 0], [1, 1, 1]),
        "agent": ([3.2, 0, 0], [1, 1, 1]),
        "queue": ([6.4, 0, 0], [1, 1, 1]),
        "octane": ([9.6, 0, 0], [1.4, 1.4, 1.4]),
    }
    mat_for = {"user": "user_mat", "agent": "agent_mat", "queue": "queue_mat", "octane": "octane_mat"}
    for name, (c, s) in blocks.items():
        b = ObjBuilder(name)
        b.add_box(center=(c[0], c[1], c[2]), size=(s[0], s[1], s[2]), material=mat_for[name])
        obj.add_group(name, mat_for[name], b)
    # arrows between blocks
    arrow_mat = "arrow_mat"
    a = ObjBuilder("arrow1")
    a.add_arrow(start_point=(0.6, 0, 0), end_point=(2.6, 0, 0), shaft_radius=0.08, head_radius=0.22)
    obj.add_group("arrow1", arrow_mat, a)
    a2 = ObjBuilder("arrow2")
    a2.add_arrow(start_point=(3.8, 0, 0), end_point=(5.8, 0, 0), shaft_radius=0.08, head_radius=0.22)
    obj.add_group("arrow2", arrow_mat, a2)
    a3 = ObjBuilder("arrow3")
    a3.add_arrow(start_point=(7.1, 0, 0), end_point=(8.8, 0, 0), shaft_radius=0.08, head_radius=0.22)
    obj.add_group("arrow3", arrow_mat, a3)
    materials = [
        _mat("user_mat", "glossy", [0.2, 0.6, 1.0], roughness=0.25),
        _mat("agent_mat", "glossy", [0.5, 0.9, 0.4], roughness=0.25),
        _mat("queue_mat", "glossy", [0.95, 0.8, 0.2], roughness=0.25),
        _mat("octane_mat", "metallic", [0.85, 0.85, 0.9], roughness=0.2, metallic=1.0),
        _mat(arrow_mat, "diffuse", [0.9, 0.9, 0.9], roughness=0.8),
    ]
    assignments = [
        {"group_index": i + 1, "material_name": mat_for[name]} for i, name in enumerate(blocks)
    ] + [
        {"group_index": len(blocks) + 1, "material_name": arrow_mat},
        {"group_index": len(blocks) + 2, "material_name": arrow_mat},
        {"group_index": len(blocks) + 3, "material_name": arrow_mat},
    ]
    return {
        "mesh_name": "t4_arch",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": materials,
        "assignments": assignments,
        "camera": camera_for_bounds(obj.bounds(), view="iso", margin=1.5),
        "lighting": "soft_studio",
        "save": {"quality": "high", "width": 1280, "height": 1280},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white", "likely object too small"]},
            {"kind": "color_family", "target": [0.2, 0.6, 1.0], "hue_tol": 45, "min_fraction": 0.005},
        ],
    }


def _t4_network_graph() -> dict[str, Any]:
    import random
    rng = random.Random(7)
    nodes = [(rng.uniform(-2.5, 2.5), rng.uniform(-2.0, 2.0), rng.uniform(-1.5, 1.5)) for _ in range(6)]
    obj = CombinedObj("t4_net")
    node_mat = "node_mat"
    for i, n in enumerate(nodes):
        b = ObjBuilder(f"n{i}")
        b.add_ellipsoid(center=n, radii=(0.35, 0.35, 0.35), material=node_mat)
        obj.add_group(f"n{i}", node_mat, b)
    edge_mat = "edge_mat"
    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), (0, 3), (1, 4)]
    gi = 6
    assignments = [{"group_index": i + 1, "material_name": node_mat} for i in range(len(nodes))]
    for (i, j) in edges:
        a = ObjBuilder(f"e{gi}")
        a.add_cylinder(center=((nodes[i][0] + nodes[j][0]) / 2,
                               (nodes[i][1] + nodes[j][1]) / 2,
                               (nodes[i][2] + nodes[j][2]) / 2),
                       radius=0.07, height=math.dist(nodes[i], nodes[j]),
                       segments=10, material=edge_mat)
        obj.add_group(f"e{gi}", edge_mat, a)
        assignments.append({"group_index": gi + 1, "material_name": edge_mat})
        gi += 1
    materials = [
        _mat(node_mat, "glossy", [0.95, 0.4, 0.12], roughness=0.2),
        _mat(edge_mat, "diffuse", [0.7, 0.7, 0.75], roughness=0.8),
    ]
    return {
        "mesh_name": "t4_net",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": materials,
        "assignments": assignments,
        "camera": camera_for_bounds(obj.bounds(), view="iso", margin=1.5),
        "lighting": "soft_studio",
        "save": {"quality": "high", "width": 1280, "height": 1280},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white", "likely object too small"]},
        ],
    }


def _t4_annotated_diagram() -> dict[str, Any]:
    obj = CombinedObj("t4_annot")
    label_mat = "label_mat"
    backing_mat = "backing_mat"
    callout_mat = "callout_mat"
    words = ["AGENT", "QUEUE", "RENDER"]
    assignments = []
    gi = 0
    # Build block-letter-ish bars spelling rough slabs (kept abstract: one slab per word)
    for i, w in enumerate(words):
        cx = (i - 1) * 3.0
        back = ObjBuilder(f"back{i}")
        back.add_box(center=(cx, 0, -0.1), size=(2.2, 0.9, 0.08), material=backing_mat)
        obj.add_group(f"back{i}", backing_mat, back)
        assignments.append({"group_index": gi + 1, "material_name": backing_mat})
        gi += 1
        slab = ObjBuilder(f"slab{i}")
        slab.add_box(center=(cx, 0, 0.05), size=(1.8, 0.5, 0.12), material=label_mat)
        obj.add_group(f"slab{i}", label_mat, slab)
        assignments.append({"group_index": gi + 1, "material_name": label_mat})
        gi += 1
        stem = ObjBuilder(f"stem{i}")
        stem.add_arrow(start_point=(cx, -0.6, 0), end_point=(cx, -1.8, 0),
                       shaft_radius=0.06, head_radius=0.18)
        obj.add_group(f"stem{i}", callout_mat, stem)
        assignments.append({"group_index": gi + 1, "material_name": callout_mat})
        gi += 1
    materials = [
        _mat(backing_mat, "diffuse", [0.1, 0.1, 0.12], roughness=0.9),
        _mat(label_mat, "glossy", [0.95, 0.95, 1.0], roughness=0.25),
        _mat(callout_mat, "diffuse", [0.95, 0.8, 0.2], roughness=0.7),
    ]
    return {
        "mesh_name": "t4_annot",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": materials,
        "assignments": assignments,
        "camera": camera_for_bounds(obj.bounds(), view="front", margin=1.3, fov=42),
        "lighting": "soft_studio",
        "save": {"quality": "high", "width": 1280, "height": 1280},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white", "likely object too small"]},
        ],
    }


# ---------------------------------------------------------------------------
# Tier 5 — Data & math: dense geometry, fields, surfaces
# ---------------------------------------------------------------------------


def _t5_math_surface_complex() -> dict[str, Any]:
    b = ObjBuilder("surface")
    xmin = ymin = -6.0
    xmax = ymax = 6.0
    steps = 60
    raw = []
    zs = []
    for iy in range(steps + 1):
        y = ymin + (ymax - ymin) * iy / steps
        row = []
        for ix in range(steps + 1):
            x = xmin + (xmax - xmin) * ix / steps
            r = math.hypot(x, y)
            z = math.sin(r) / max(r, 0.3) * (0.45 + 0.55 * math.cos(4 * math.atan2(y, x))) * 2.8
            z = max(min(z, 10.0), -10.0)
            zs.append(z)
            row.append((x, y, z))
        raw.append(row)
    mabs = max(abs(z) for z in zs) or 1.0
    scale = 1.6 / mabs
    verts = [[(x, y, z * scale) for x, y, z in row] for row in raw]
    b.add_box(center=(0, 0, -0.06), size=(12.4, 12.4, 0.04), material="base_mat")
    b.add_surface(vertices=verts, material="surface_mat")
    obj = CombinedObj("t5_surface")
    obj.add_group("surface", "surface_mat", b)
    return {
        "mesh_name": "t5_surface",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": [_mat("surface_mat", "glossy", [0.85, 0.55, 0.25], roughness=0.3)],
        "assignments": [{"group_index": 1, "material_name": "surface_mat"}],
        "camera": camera_for_bounds(obj.bounds(), view="iso", margin=1.25, fov=40),
        "lighting": "soft_studio",
        "save": {"quality": "ultra", "width": 1280, "height": 1280},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white", "likely object too small"]},
            {"kind": "shape_profile", "min_rows": 8},
        ],
    }


def _t5_wave_interference() -> dict[str, Any]:
    b = ObjBuilder("waves")
    xmin = ymin = -5.0
    xmax = ymax = 5.0
    steps = 56
    src_a = (-2.0, 0.0)
    src_b = (2.0, 0.0)
    raw = []
    zs = []
    for iy in range(steps + 1):
        y = ymin + (ymax - ymin) * iy / steps
        row = []
        for ix in range(steps + 1):
            x = xmin + (xmax - xmin) * ix / steps
            d1 = math.hypot(x - src_a[0], y - src_a[1])
            d2 = math.hypot(x - src_b[0], y - src_b[1])
            z = math.sin(d1) / max(d1, 0.5) + math.sin(d2) / max(d2, 0.5)
            z = max(min(z, 10.0), -10.0)
            zs.append(z)
            row.append((x, y, z))
        raw.append(row)
    mabs = max(abs(z) for z in zs) or 1.0
    scale = 1.4 / mabs
    verts = [[(x, y, z * scale) for x, y, z in row] for row in raw]
    b.add_box(center=(0, 0, -0.06), size=(10.4, 10.4, 0.04), material="base_mat")
    b.add_surface(vertices=verts, material="wave_mat")
    obj = CombinedObj("t5_waves")
    obj.add_group("waves", "wave_mat", b)
    return {
        "mesh_name": "t5_waves",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": [_mat("wave_mat", "glossy", [0.2, 0.8, 0.7], roughness=0.3)],
        "assignments": [{"group_index": 1, "material_name": "wave_mat"}],
        "camera": camera_for_bounds(obj.bounds(), view="top", margin=1.25, fov=40),
        "lighting": "soft_studio",
        "save": {"quality": "high", "width": 1280, "height": 1280},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white", "likely object too small"]},
            {"kind": "color_family", "target": [0.2, 0.8, 0.7], "hue_tol": 45, "min_fraction": 0.005},
        ],
    }


def _t5_vector_field() -> dict[str, Any]:
    import random
    rng = random.Random(11)
    obj = CombinedObj("t5_field")
    arrow_mat = "arrow_mat"
    positions = [(rng.uniform(-2.5, 2.5), rng.uniform(-2.5, 2.5), 0.0) for _ in range(10)]
    assignments = []
    gi = 0
    for p in positions:
        # rotational vector field v = (-y, x)
        vx, vy = -p[1], p[0]
        mag = math.hypot(vx, vy) or 1.0
        end = (p[0] + vx / mag * 0.9, p[1] + vy / mag * 0.9, 0.0)
        a = ObjBuilder(f"v{gi}")
        a.add_arrow(start_point=p, end_point=end, shaft_radius=0.06, head_radius=0.18)
        obj.add_group(f"v{gi}", arrow_mat, a)
        assignments.append({"group_index": gi + 1, "material_name": arrow_mat})
        gi += 1
    materials = [_mat(arrow_mat, "glossy", [0.95, 0.5, 0.1], roughness=0.25)]
    return {
        "mesh_name": "t5_field",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": materials,
        "assignments": assignments,
        "camera": camera_for_bounds(obj.bounds(), view="top", margin=1.4, fov=42),
        "lighting": "soft_studio",
        "save": {"quality": "high", "width": 1280, "height": 1280},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white", "likely object too small"]},
            {"kind": "color_family", "target": [0.95, 0.5, 0.1], "hue_tol": 45, "min_fraction": 0.005},
        ],
    }


# ---------------------------------------------------------------------------
# Tier 6 — Photoreal / stress: high face counts, multi-material families
# ---------------------------------------------------------------------------


def _t6_vase_studio() -> dict[str, Any]:
    obj = CombinedObj("t6_vases")
    materials = []
    assignments = []
    gi = 0

    def lathe_vase(center_x, radius, height, segs=40, profile=None):
        b = ObjBuilder(f"vase{gi}")
        if profile is None:
            profile = [0.2, 0.5, 0.7, 0.6, 0.35, 0.5, 0.45]
        rings = len(profile)
        pts = []
        for r in range(rings):
            yy = center_x  # placeholder; recomputed below
        # build as stacked rings (lathe approximation)
        vlines = []
        # simpler: stack scaled discs
        acc = 0.0
        for ri, pr in enumerate(profile):
            yy = (ri / (rings - 1) - 0.5) * height
            rr = pr * radius
            # a thin torus-ish ring via cylinder
            c = ObjBuilder(f"ring{gi}_{ri}")
            c.add_cylinder(center=(center_x, yy, 0), radius=rr, height=height / rings * 0.9,
                           segments=segs, material=f"vasemat{gi}")
            obj.add_group(f"ring{gi}_{ri}", f"vasemat{gi}", c)
        return

    # three vases with distinct silhouettes/materials
    vase_specs = [
        ("glass", [0.3, 0.55, 0.7, 0.5, 0.4, 0.55], [0.8, 0.9, 1.0], {"transmission": 1.0, "ior": 1.5, "opacity": 0.45, "roughness": 0.05}),
        ("ceramic", [0.35, 0.6, 0.5, 0.65, 0.45, 0.4], [0.1, 0.3, 0.85], {"roughness": 0.2, "clearcoat": 0.5}),
        ("metal", [0.25, 0.5, 0.75, 0.6, 0.35, 0.5], [0.8, 0.8, 0.85], {"roughness": 0.15, "metallic": 1.0}),
    ]
    xs = [-3.0, 0.0, 3.0]
    for (vi, (kind, profile, color, extra)) in enumerate(vase_specs):
        mat_name = f"vasemat{vi}"
        materials.append(_mat(mat_name, "glossy", color, **extra))
        rings = len(profile)
        for ri, pr in enumerate(profile):
            yy = (ri / (rings - 1) - 0.5) * 2.4
            rr = pr * 1.0
            c = ObjBuilder(f"ring{vi}_{ri}")
            c.add_cylinder(center=(xs[vi], yy, 0), radius=rr, height=2.4 / rings * 0.9,
                           segments=36, material=mat_name)
            obj.add_group(f"ring{vi}_{ri}", mat_name, c)
            assignments.append({"group_index": len(assignments) + 1, "material_name": mat_name})
    return {
        "mesh_name": "t6_vases",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": materials,
        "assignments": assignments,
        "camera": camera_for_bounds(obj.bounds(), view="iso", margin=1.4),
        "lighting": "soft_studio",
        "save": {"quality": "ultra", "width": 1280, "height": 1280},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white", "likely object too small"]},
        ],
    }


def _t6_earth_space() -> dict[str, Any]:
    obj = CombinedObj("t6_earth")
    # earth
    e = ObjBuilder("earth")
    e.add_ellipsoid(center=(0, 0, 0), radii=(1.4, 1.4, 1.4), material="earth_mat")
    obj.add_group("earth", "earth_mat", e)
    # atmosphere shell
    at = ObjBuilder("atmo")
    at.add_ellipsoid(center=(0, 0, 0), radii=(1.55, 1.55, 1.55), material="atmo_mat")
    obj.add_group("atmo", "atmo_mat", at)
    # moon
    m = ObjBuilder("moon")
    m.add_ellipsoid(center=(4.5, 1.0, -1.0), radii=(0.4, 0.4, 0.4), material="moon_mat")
    obj.add_group("moon", "moon_mat", m)
    materials = [
        _mat("earth_mat", "glossy", [0.15, 0.4, 0.85], roughness=0.4),
        _mat("atmo_mat", "glossy", [0.4, 0.7, 1.0], roughness=0.1, opacity=0.25),
        _mat("moon_mat", "diffuse", [0.8, 0.8, 0.78], roughness=0.9),
    ]
    assignments = [
        {"group_index": 1, "material_name": "earth_mat"},
        {"group_index": 2, "material_name": "atmo_mat"},
        {"group_index": 3, "material_name": "moon_mat"},
    ]
    return {
        "mesh_name": "t6_earth",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": materials,
        "assignments": assignments,
        "camera": camera_for_bounds(obj.bounds(), view="iso", margin=1.4),
        "lighting": "soft_studio",
        "save": {"quality": "ultra", "width": 1280, "height": 1280},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white", "likely object too small"]},
            {"kind": "color_family", "target": [0.15, 0.4, 0.85], "hue_tol": 45, "min_fraction": 0.01},
        ],
    }


def _t6_saturn_system() -> dict[str, Any]:
    obj = CombinedObj("t6_saturn")
    sat = ObjBuilder("saturn")
    sat.add_ellipsoid(center=(0, 0, 0), radii=(1.6, 1.6, 0.9), material="sat_mat")
    obj.add_group("saturn", "sat_mat", sat)
    materials = [_mat("sat_mat", "glossy", [0.9, 0.8, 0.55], roughness=0.35)]
    assignments = [{"group_index": 1, "material_name": "sat_mat"}]
    # rings as stacked thin cylinders (annulus approximation)
    ring_mat = "ring_mat"
    materials.append(_mat(ring_mat, "glossy", [0.85, 0.78, 0.6], roughness=0.3, opacity=0.6))
    for i, rr in enumerate([2.2, 2.5, 2.8, 3.1]):
        c = ObjBuilder(f"ring{i}")
        c.add_cylinder(center=(0, 0, 0), radius=rr, height=0.04, segments=48, material=ring_mat)
        obj.add_group(f"ring{i}", ring_mat, c)
        assignments.append({"group_index": i + 2, "material_name": ring_mat})
    # moons
    moon_mat = "moon_mat"
    materials.append(_mat(moon_mat, "diffuse", [0.75, 0.75, 0.72], roughness=0.9))
    for i, (mx, my) in enumerate([(4.5, 1.0), (-4.0, -1.5)]):
        c = ObjBuilder(f"moon{i}")
        c.add_ellipsoid(center=(mx, my, 0), radii=(0.4, 0.4, 0.4), material=moon_mat)
        obj.add_group(f"moon{i}", moon_mat, c)
        assignments.append({"group_index": len(assignments) + 1, "material_name": moon_mat})
    return {
        "mesh_name": "t6_saturn",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": materials,
        "assignments": assignments,
        "camera": camera_for_bounds(obj.bounds(), view="iso", margin=1.4),
        "lighting": "soft_studio",
        "save": {"quality": "ultra", "width": 1280, "height": 1280},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white", "likely object too small"]},
        ],
    }


# ---------------------------------------------------------------------------
# Tier 7 — Physical simulation fixtures: deterministic physics grammar
# ---------------------------------------------------------------------------


def _t7_advection_diffusion_panels() -> dict[str, Any]:
    """Four time panels of a Gaussian tracer advecting (+x) and diffusing.

    The physical claim is carried by geometry: each panel's peak height decays
    and its footprint broadens with time (diffusion), so the heightfield shape
    itself tells the story. No external simulator required.
    """
    steps = 20
    panels = 4
    xmin = ymin = -1.3
    xmax = ymax = 1.3
    xspan = xmax - xmin
    yspan = ymax - ymin
    gap = 0.5
    pitch = xspan + gap
    tracer_color = [0.1, 0.82, 0.7]

    base_b = ObjBuilder("base")
    base_b.add_box(center=(0, 0, -0.06),
                   size=(panels * pitch, yspan + 0.4, 0.04),
                   material="base_mat")
    obj = CombinedObj("t7_advect")
    obj.add_group("base", "base_mat", base_b)
    assignments = [{"group_index": 1, "material_name": "base_mat"}]
    for p in range(panels):
        t = float(p) * 1.2
        xoff = (p - (panels - 1) / 2) * pitch
        sigma = math.sqrt(0.25 + 0.12 * t)
        raw: list[list[tuple[float, float, float]]] = []
        zs: list[float] = []
        for iy in range(steps + 1):
            y = ymin + yspan * iy / steps
            row = []
            for ix in range(steps + 1):
                x = xmin + xspan * ix / steps
                xc = x - 0.7 * t  # advection toward +x
                h = math.exp(-(xc * xc + y * y) / (2 * sigma * sigma))
                zs.append(h)
                row.append((x + xoff, y, h))
            raw.append(row)
        mabs = max(zs) or 1.0
        scale = 1.3 / mabs
        verts = [[(x, y, z * scale) for x, y, z in row] for row in raw]
        surf = ObjBuilder(f"panel{p}")
        surf.add_surface(vertices=verts, material="tracer_mat")
        obj.add_group(f"panel{p}", "tracer_mat", surf)
        assignments.append({"group_index": len(assignments) + 1, "material_name": "tracer_mat"})
    return {
        "mesh_name": "t7_advect",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": [
            _mat("base_mat", "diffuse", [0.07, 0.09, 0.12], roughness=0.9),
            _mat("tracer_mat", "glossy", tracer_color, roughness=0.3),
        ],
        "assignments": assignments,
        "camera": camera_for_bounds(obj.bounds(), view="iso", margin=1.3, fov=42),
        "lighting": "soft_studio",
        "save": {"quality": "high", "width": 1024, "height": 1024},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white", "likely object too small"]},
            {"kind": "color_family", "target": tracer_color, "hue_tol": 45, "min_fraction": 0.01},
            {"kind": "shape_profile", "min_rows": 8},
        ],
    }


def _t7_cloth_drape_contact() -> dict[str, Any]:
    """PBD cloth sheet draping and tenting over a rigid sphere.

    A small Verlet/PBD solver embedded in the builder (deterministic, seeded
    only by geometry) produces emergent sag and a contact patch over the
    sphere — the same grammar as the `mass-spring-cloth-drape` recipe, here
    promoted to a harness task.
    """
    G = 28
    size = 6.0
    sphere_r = 1.9
    center = (0.0, 0.0, 0.0)
    rest = size / (G - 1)
    pinned = {(0, 0), (0, G - 1)}
    damping = 0.98
    gravity = -0.012
    dt = 0.6

    pos: list[list[list[float]]] = []
    prev: list[list[list[float]]] = []
    for i in range(G):
        row = []
        old = []
        for j in range(G):
            p = [-size / 2 + size * j / (G - 1), -size / 2 + size * i / (G - 1), sphere_r + 0.5]
            row.append(p[:])
            old.append(p[:])
        pos.append(row)
        prev.append(old)

    def _dist(a: list[float], b: list[float]) -> float:
        return math.sqrt(sum((a[k] - b[k]) ** 2 for k in range(3)))

    def _constrain(i: int, j: int, ni: int, nj: int, target: float, stiffness: float) -> None:
        a = pos[i][j]
        b = pos[ni][nj]
        cur = _dist(a, b) or 1e-6
        diff = (cur - target) / cur
        corr = min(max(diff, -0.5), 0.5) * 0.5 * stiffness
        ai = (i, j) not in pinned
        bi = (ni, nj) not in pinned
        if ai and bi:
            for k in range(3):
                off = (b[k] - a[k]) * corr
                a[k] += off
                b[k] -= off
        elif ai:
            for k in range(3):
                a[k] += (b[k] - a[k]) * 2 * corr
        elif bi:
            for k in range(3):
                b[k] -= (b[k] - a[k]) * 2 * corr

    for _ in range(90):
        for i in range(G):
            for j in range(G):
                if (i, j) in pinned:
                    continue
                p = pos[i][j]
                old = prev[i][j]
                nxt = [p[k] + (p[k] - old[k]) * damping + (gravity * dt * dt if k == 2 else 0.0) for k in range(3)]
                prev[i][j] = p[:]
                pos[i][j] = nxt
        for _ in range(8):
            for i in range(G):
                for j in range(G):
                    for di, dj in ((1, 0), (0, 1), (1, 1), (1, -1)):
                        ni, nj = i + di, j + dj
                        if not (0 <= ni < G and 0 <= nj < G):
                            continue
                        target = rest * (1.0 if di == 0 or dj == 0 else math.sqrt(2))
                        stiffness = 0.9 if (di == 0 or dj == 0) else 0.4
                        _constrain(i, j, ni, nj, target, stiffness)
        for i in range(G):
            for j in range(G):
                if (i, j) in pinned:
                    continue
                p = pos[i][j]
                v = [p[k] - center[k] for k in range(3)]
                r = math.sqrt(sum(x * x for x in v)) or 1e-6
                if r < sphere_r + 0.05:
                    s = (sphere_r + 0.05) / r
                    for k in range(3):
                        p[k] = center[k] + v[k] * s

    verts: list[list[tuple[float, float, float]]] = [
        [(float(pos[i][j][0]), float(pos[i][j][1]), float(pos[i][j][2])) for j in range(G)]
        for i in range(G)
    ]
    sphere_b = ObjBuilder("sphere")
    sphere_b.add_ellipsoid(center=center, radii=(sphere_r, sphere_r, sphere_r), segments_u=48, segments_v=24, material="sphere_mat")
    cloth_b = ObjBuilder("cloth")
    cloth_b.add_surface(vertices=verts, material="cloth_mat")
    obj = CombinedObj("t7_cloth_contact")
    obj.add_group("sphere", "sphere_mat", sphere_b)
    obj.add_group("cloth", "cloth_mat", cloth_b)
    return {
        "mesh_name": "t7_cloth_contact",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": [
            _mat("sphere_mat", "glossy", [0.3, 0.32, 0.36], roughness=0.5),
            _mat("cloth_mat", "glossy", [0.85, 0.3, 0.35], roughness=0.6),
        ],
        "assignments": [
            {"group_index": 1, "material_name": "sphere_mat"},
            {"group_index": 2, "material_name": "cloth_mat"},
        ],
        "camera": {
            "position": [8.60519, -14.715919, 7.709358],
            "target": [-0.740483, -3.553032, 0.180899],
            "fov": 35.0,
        },
        "lighting": "soft_studio",
        "save": {"quality": "high", "width": 1024, "height": 1024},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white", "likely object too small"]},
            {"kind": "color_family", "target": [0.85, 0.3, 0.35], "hue_tol": 45, "min_fraction": 0.01},
            {"kind": "shape_profile", "min_rows": 6},
        ],
    }


def _t7_particle_splash_fixture() -> dict[str, Any]:
    """Liquid + foam particle families from a deterministic dam-break splash.

    Particles are generated in-code (seeded) so the task is dependency-free and
    reproducible. Two material groups (liquid / foam) exercise the particle
    cloud + material-group grammar that Phase B SPlisHSPlasH adapters reuse.
    """
    import random
    rng = random.Random(20260715)
    liquid_b = ObjBuilder("liquid")
    foam_b = ObjBuilder("foam")
    for _ in range(180):
        gx = rng.random(); gy = rng.random()
        x = -3.0 + 2.8 * gx
        y = -2.0 + 4.0 * gy
        z = 0.1 + 1.6 * max(0.0, (x + 3.0) / 3.0) + 0.3 * rng.random()
        liquid_b.add_ellipsoid(center=(x, y, z), radii=(0.12, 0.12, 0.12), material="liquid_mat", segments_u=6, segments_v=4)
    for _ in range(60):
        x = rng.uniform(-3.0, 1.2)
        y = rng.uniform(-2.0, 2.0)
        z = rng.uniform(1.4, 2.6)
        foam_b.add_ellipsoid(center=(x, y, z), radii=(0.08, 0.08, 0.08), material="foam_mat", segments_u=6, segments_v=4)
    obj = CombinedObj("t7_splash")
    obj.add_group("liquid", "liquid_mat", liquid_b)
    obj.add_group("foam", "foam_mat", foam_b)
    return {
        "mesh_name": "t7_splash",
        "obj": obj.text(),
        "bounds": obj.bounds(),
        "materials": [
            _mat("liquid_mat", "glossy", [0.1, 0.7, 0.85], roughness=0.15, opacity=0.85),
            _mat("foam_mat", "diffuse", [0.9, 0.95, 1.0], roughness=0.7),
        ],
        "assignments": [
            {"group_index": 1, "material_name": "liquid_mat"},
            {"group_index": 2, "material_name": "foam_mat"},
        ],
        "camera": camera_for_bounds(obj.bounds(), view="iso", margin=1.4),
        "lighting": "soft_studio",
        "save": {"quality": "high", "width": 1024, "height": 1024},
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "mostly near-white", "likely object too small"]},
            {"kind": "color_family", "target": [0.1, 0.7, 0.85], "hue_tol": 45, "min_fraction": 0.01},
            {"kind": "color_family", "target": [0.9, 0.95, 1.0], "hue_tol": 45, "min_fraction": 0.005},
        ],
    }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

TIER_TITLES = {
    1: "Foundations — single primitive smoke tests",
    2: "Composition & camera framing — multi-object, per-group materials",
    3: "Lighting & materials — PBR fields, emissive, product studio",
    4: "Multi-object scene graphs — 6-12 meshes, hierarchy, flow",
    5: "Data & math — dense geometry, fields, surfaces",
    6: "Photoreal / stress — high face counts, multi-material families",
    7: "Physical simulation fixtures — deterministic physics grammar",
}

ALL_TASKS: list[BenchmarkTask] = [
    BenchmarkTask(1, "t1_glossy_cube", "Glossy blue cube", "primitive", "Single OBJ cube, blue glossy material, iso camera.", _t1_glossy_cube),
    BenchmarkTask(1, "t1_metallic_sphere", "Metallic gold sphere", "primitive", "Single OBJ sphere, metallic gold, iso camera.", _t1_metallic_sphere),
    BenchmarkTask(1, "t1_surface_field", "Radial math surface", "math-surface", "sin(r)/r height field, bronze glossy.", _t1_surface_field),
    BenchmarkTask(2, "t2_multi_material", "Green sphere on red cube", "multi-material", "Two meshes in one combined OBJ, per-group materials.", _t2_multi_material),
    BenchmarkTask(2, "t2_scatter", "3D scatter plot", "scatter", "8 xyz points, orange, iso camera.", _t2_scatter),
    BenchmarkTask(3, "t3_glass_like", "Glass-like sphere", "pbr-glass", "Transmission/ior/opacity sphere under studio.", _t3_glass_like),
    BenchmarkTask(3, "t3_emissive", "Emissive sphere", "pbr-emissive", "Emission-lit sphere glowing on studio backdrop.", _t3_emissive),
    BenchmarkTask(3, "t3_product_studio", "Product studio hero", "product-studio", "Cyclorama + clearcoat hero sphere.", _t3_product_studio),
    BenchmarkTask(4, "t4_network_graph", "Knowledge graph", "scene-graph", "6 nodes, 8 edges as spatial graph.", _t4_network_graph),
    BenchmarkTask(4, "t4_annotated_diagram", "Annotated diagram", "annotation", "Three labelled slabs with callout stems.", _t4_annotated_diagram),
    BenchmarkTask(5, "t5_vector_field", "Rotational vector field", "field", "10 rotational arrows, top view.", _t5_vector_field),
    BenchmarkTask(6, "t6_vase_studio", "Photoreal vase studio", "photoreal", "Three vases, glass/ceramic/metal families.", _t6_vase_studio),
    BenchmarkTask(7, "t7_advection_diffusion_panels", "Advection–diffusion panels", "physics-transport", "Four tiled Gaussians advecting + diffusing; peak decays, footprint broadens.", _t7_advection_diffusion_panels, True),
    BenchmarkTask(7, "t7_cloth_drape_contact", "Cloth drape contact", "physics-deformable", "PBD cloth draping over a rigid sphere with emergent contact patch.", _t7_cloth_drape_contact, True),
    BenchmarkTask(7, "t7_particle_splash_fixture", "Particle splash fixture", "physics-particles", "Seeded liquid + foam particle families (dam-break splash).", _t7_particle_splash_fixture, True),
]


def tasks_by_tier(tier: int) -> list[BenchmarkTask]:
    return [t for t in ALL_TASKS if t.tier == tier]


def get_task(slug: str) -> BenchmarkTask | None:
    for t in ALL_TASKS:
        if t.slug == slug:
            return t
    return None
