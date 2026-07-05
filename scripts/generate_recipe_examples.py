from __future__ import annotations

import json
import math
import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "examples" / "recipes"
DOCS = ROOT / "docs"

Color = tuple[int, int, int]
Point3 = tuple[float, float, float]
Point2 = tuple[float, float]

PALETTE: dict[str, Color] = {
    "cyan": (18, 197, 255),
    "blue": (53, 117, 255),
    "navy": (22, 34, 66),
    "gold": (255, 181, 61),
    "orange": (255, 116, 50),
    "red": (255, 68, 96),
    "green": (75, 220, 140),
    "violet": (166, 109, 255),
    "magenta": (255, 79, 190),
    "white": (230, 238, 255),
    "gray": (112, 128, 160),
    "dark": (8, 13, 28),
    "base": (35, 45, 75),
    "earth": (88, 156, 114),
    "water": (42, 107, 205),
}


def shade(color: Color, factor: float) -> Color:
    return tuple(max(0, min(255, int(c * factor))) for c in color)  # type: ignore[return-value]


def write_png(path: Path, width: int, height: int, pixels: list[list[Color]]) -> None:
    raw = b"".join(b"\x00" + b"".join(bytes(px) for px in row) for row in pixels)
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


@dataclass
class Mesh:
    vertices: list[Point3] = field(default_factory=list)
    faces: list[tuple[list[int], str]] = field(default_factory=list)
    lines: list[tuple[int, int, str]] = field(default_factory=list)

    def add_vertex(self, p: Point3) -> int:
        self.vertices.append(p)
        return len(self.vertices)

    def add_face(self, indices: list[int], mat: str) -> None:
        self.faces.append((indices, mat))

    def add_line(self, a: int, b: int, mat: str) -> None:
        self.lines.append((a, b, mat))

    def add_box(self, center: Point3, size: Point3, mat: str) -> None:
        cx, cy, cz = center
        sx, sy, sz = (size[0] / 2, size[1] / 2, size[2] / 2)
        pts = [
            (cx - sx, cy - sy, cz - sz), (cx + sx, cy - sy, cz - sz),
            (cx + sx, cy + sy, cz - sz), (cx - sx, cy + sy, cz - sz),
            (cx - sx, cy - sy, cz + sz), (cx + sx, cy - sy, cz + sz),
            (cx + sx, cy + sy, cz + sz), (cx - sx, cy + sy, cz + sz),
        ]
        i = [self.add_vertex(p) for p in pts]
        for face in ([0, 1, 2, 3], [4, 7, 6, 5], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [4, 0, 3, 7]):
            self.add_face([i[k] for k in face], mat)

    def add_surface(self, rows: list[list[Point3]], mat: str) -> None:
        if not rows:
            return
        ids = [[self.add_vertex(p) for p in row] for row in rows]
        for r in range(len(rows) - 1):
            for c in range(len(rows[0]) - 1):
                self.add_face([ids[r][c], ids[r][c + 1], ids[r + 1][c + 1], ids[r + 1][c]], mat)

    def add_cylinder(self, center: Point3, radius: float, height: float, mat: str, segments: int = 18) -> None:
        cx, cy, cz = center
        bottom = []
        top = []
        for k in range(segments):
            a = 2 * math.pi * k / segments
            bottom.append(self.add_vertex((cx + radius * math.cos(a), cy + radius * math.sin(a), cz - height / 2)))
            top.append(self.add_vertex((cx + radius * math.cos(a), cy + radius * math.sin(a), cz + height / 2)))
        for k in range(segments):
            self.add_face([bottom[k], bottom[(k + 1) % segments], top[(k + 1) % segments], top[k]], mat)
        self.add_face(list(reversed(bottom)), mat)
        self.add_face(top, mat)

    def add_polyline(self, pts: list[Point3], mat: str) -> None:
        ids = [self.add_vertex(p) for p in pts]
        for a, b in zip(ids, ids[1:]):
            self.add_line(a, b, mat)

    def to_obj(self, name: str) -> str:
        lines = ["# Generated sample scene for OctaneX MCP recipes", "mtllib scene.mtl", f"o {name}"]
        for x, y, z in self.vertices:
            lines.append(f"v {x:.5f} {y:.5f} {z:.5f}")
        current = None
        for indices, mat in self.faces:
            if mat != current:
                lines.append(f"usemtl {mat}")
                current = mat
            lines.append("f " + " ".join(str(i) for i in indices))
        for a, b, mat in self.lines:
            if mat != current:
                lines.append(f"usemtl {mat}")
                current = mat
            lines.append(f"l {a} {b}")
        return "\n".join(lines) + "\n"


class Preview:
    def __init__(self, width: int = 960, height: int = 640) -> None:
        self.width = width
        self.height = height
        self.pixels = [[(8, 12, 26) for _ in range(width)] for _ in range(height)]
        for y in range(height):
            t = y / max(1, height - 1)
            row = shade((18, 26, 54), 1 - 0.35 * t)
            for x in range(width):
                self.pixels[y][x] = row

    def project(self, p: Point3, scale: float, cx: float, cy: float) -> Point2:
        x, y, z = p
        # Isometric-ish camera looking from front-right-above.
        u = (x - y) * 0.866
        v = (x + y) * 0.33 - z * 0.92
        return (cx + u * scale, cy + v * scale)

    def bounds(self, mesh: Mesh) -> tuple[float, float, float, float]:
        pts = [self.project(p, 1, 0, 0) for p in mesh.vertices]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return min(xs), max(xs), min(ys), max(ys)

    def draw_mesh(self, mesh: Mesh, colors: dict[str, Color]) -> None:
        if not mesh.vertices:
            return
        minx, maxx, miny, maxy = self.bounds(mesh)
        span = max(maxx - minx, maxy - miny, 1e-6)
        scale = min(self.width * 0.72, self.height * 0.72) / span
        cx = self.width / 2 - (minx + maxx) * scale / 2
        cy = self.height / 2 - (miny + maxy) * scale / 2 + self.height * 0.05
        face_items = []
        for indices, mat in mesh.faces:
            poly3 = [mesh.vertices[i - 1] for i in indices]
            depth = sum(p[0] + p[1] + p[2] * 0.2 for p in poly3) / len(poly3)
            poly2 = [self.project(p, scale, cx, cy) for p in poly3]
            # crude face normal brightness in view coordinates
            bright = 0.78 + 0.22 * ((sum(p[2] for p in poly3) / len(poly3)) >= 0)
            face_items.append((depth, poly2, shade(colors.get(mat, PALETTE.get(mat, PALETTE["white"])), bright)))
        for _, poly, color in sorted(face_items, key=lambda item: item[0]):
            self.fill_poly(poly, color)
            self.stroke_poly(poly, shade(color, 0.55))
        for a, b, mat in mesh.lines:
            p1 = self.project(mesh.vertices[a - 1], scale, cx, cy)
            p2 = self.project(mesh.vertices[b - 1], scale, cx, cy)
            self.line(p1, p2, colors.get(mat, PALETTE.get(mat, PALETTE["white"])), width=3)

    def fill_poly(self, poly: list[Point2], color: Color) -> None:
        if len(poly) < 3:
            return
        miny = max(0, int(math.floor(min(y for _, y in poly))))
        maxy = min(self.height - 1, int(math.ceil(max(y for _, y in poly))))
        for y in range(miny, maxy + 1):
            xs = []
            for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
                if (y1 <= y < y2) or (y2 <= y < y1):
                    if y2 != y1:
                        xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for x1, x2 in zip(xs[0::2], xs[1::2]):
                a = max(0, int(math.floor(x1)))
                b = min(self.width - 1, int(math.ceil(x2)))
                for x in range(a, b + 1):
                    self.pixels[y][x] = color

    def stroke_poly(self, poly: list[Point2], color: Color) -> None:
        for p1, p2 in zip(poly, poly[1:] + poly[:1]):
            self.line(p1, p2, color, width=1)

    def line(self, p1: Point2, p2: Point2, color: Color, width: int = 1) -> None:
        x1, y1 = p1
        x2, y2 = p2
        steps = max(1, int(max(abs(x2 - x1), abs(y2 - y1))))
        r = max(0, width // 2)
        for i in range(steps + 1):
            t = i / steps
            x = int(round(x1 + (x2 - x1) * t))
            y = int(round(y1 + (y2 - y1) * t))
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < self.width and 0 <= yy < self.height:
                        self.pixels[yy][xx] = color

    def save(self, path: Path) -> None:
        write_png(path, self.width, self.height, self.pixels)


@dataclass
class Recipe:
    slug: str
    title: str
    category: str
    purpose: str
    prompt: str
    tools: list[str]
    steps: list[str]
    variations: list[str]
    mesh: Mesh
    colors: dict[str, Color]
    camera: dict[str, object]


def color_to_float(color: Color) -> list[float]:
    return [round(c / 255, 4) for c in color]


def material_kind(name: str) -> str:
    if name in {"base", "navy", "earth", "water"}:
        return "diffuse"
    return "glossy"


def material_roughness(name: str) -> float:
    if name == "gold":
        return 0.18
    if name in {"base", "navy", "earth", "water"}:
        return 0.55
    return 0.25


def write_mtl(path: Path, colors: dict[str, Color]) -> None:
    lines = ["# Generated material hints for OctaneX MCP recipe assets"]
    for name, color in colors.items():
        r, g, b = color_to_float(color)
        lines.extend([
            f"newmtl {name}",
            f"Kd {r:.4f} {g:.4f} {b:.4f}",
            f"Ks {min(1.0, r + 0.15):.4f} {min(1.0, g + 0.15):.4f} {min(1.0, b + 0.15):.4f}",
            f"Ns {max(20, int(500 * (1 - material_roughness(name))))}",
            "",
        ])
    path.write_text("\n".join(lines), encoding="utf-8")


def bars_recipe() -> Recipe:
    mesh = Mesh()
    vals = [4, 9, 2, 7, 5, 11, 3, 8]
    mesh.add_box((0, 0, -0.06), (7.2, 1.2, 0.08), "base")
    for i, v in enumerate(vals):
        x = (i - (len(vals) - 1) / 2) * 0.82
        h = v * 0.22
        mesh.add_box((x, 0, h / 2), (0.52, 0.62, h), "cyan" if v < 8 else "gold")
    mesh.add_box((0, -0.72, 0.03), (7.4, 0.05, 0.06), "white")
    return Recipe("data-bars", "3D KPI Bar Chart", "Data visualization", "Compare a short numeric sequence as spatial bars with a clear baseline and highlight bars above threshold.", "Visualize quarterly or experiment metrics as a 3D bar chart, highlighting unusually high values.", ["octane_visualize_bars", "octane_save_preview"], ["Call octane_visualize_bars(values=[4,9,2,7,5,11,3,8], name='kpi_bars').", "Drain the queue with the one-shot Lua bridge.", "Save a preview and inspect framing/contrast."], ["Use negative values to show below-baseline bars.", "Map categories to materials once multi-material assignment is richer."], mesh, {k: PALETTE[k] for k in ["base", "cyan", "gold", "white"]}, {"position": [4.2, -5.0, 3.0], "target": [0, 0, 0.8], "fov": 45})


def surface_recipe() -> Recipe:
    mesh = Mesh()
    rows = []
    for iy in range(32):
        y = -3 + 6 * iy / 31
        row = []
        for ix in range(32):
            x = -3 + 6 * ix / 31
            r = math.sqrt(x * x + y * y)
            z = math.sin(r * 2.2) / max(r, 0.45)
            row.append((x, y, z * 1.1))
        rows.append(row)
    mesh.add_box((0, 0, -0.18), (6.7, 6.7, 0.06), "base")
    mesh.add_surface(rows, "gold")
    return Recipe("math-surface", "Radial Math Surface", "Mathematics", "Render a height field for z = sin(r*2.2)/max(r, 0.45) to explain radial damping and singularity protection.", "Show a damped radial wave surface for a math explanation.", ["octane_visualize_surface", "octane_save_preview"], ["Call octane_visualize_surface(expression='sin(r*2.2) / max(r, 0.45)', steps=32).", "Use one-shot bridge to drain the generated scene sequence.", "Inspect whether peaks are clipped; reduce expression amplitude if needed."], ["Overlay sample points or gradient vectors.", "Use surfaces for loss landscapes or potential fields."], mesh, {"base": PALETTE["base"], "gold": PALETTE["gold"]}, {"position": [4.5, -5.5, 3.2], "target": [0, 0, 0.1], "fov": 42})


def vector_field_recipe() -> Recipe:
    mesh = Mesh()
    mesh.add_box((0, 0, -0.04), (6.5, 6.5, 0.05), "base")
    for ix in range(-3, 4):
        for iy in range(-3, 4):
            x, y = ix * 0.85, iy * 0.85
            angle = math.atan2(y, x) + math.pi / 2
            length = 0.38 + 0.05 * math.sqrt(ix * ix + iy * iy)
            x2 = x + math.cos(angle) * length
            y2 = y + math.sin(angle) * length
            mesh.add_polyline([(x, y, 0.05), (x2, y2, 0.28)], "cyan")
            mesh.add_box((x2, y2, 0.28), (0.12, 0.12, 0.12), "gold")
    return Recipe("vector-field", "Rotating Vector Field", "Math/physics", "Show a 2D rotational vector field lifted into 3D with arrow tips to explain flow direction.", "Render a rotational field around the origin for a dynamics lesson.", ["octane_import_geometry", "octane_create_material", "octane_set_camera"], ["Generate arrows as line segments plus small cubes/cones.", "Import geometry and assign bright cyan/gold materials.", "Frame from above to emphasize vector direction."], ["Use colors for magnitude.", "Animate successive field snapshots as separate OBJ imports."], mesh, {"base": PALETTE["base"], "cyan": PALETTE["cyan"], "gold": PALETTE["gold"]}, {"position": [0, -7, 5], "target": [0, 0, 0], "fov": 38})


def network_recipe() -> Recipe:
    mesh = Mesh()
    pts = []
    for k in range(10):
        a = 2 * math.pi * k / 10
        pts.append((math.cos(a) * (2.4 + 0.35 * (k % 2)), math.sin(a) * (2.0 + 0.25 * ((k + 1) % 2)), 0.25 + 0.08 * k))
    edges = [(0, 1), (1, 3), (3, 5), (5, 7), (7, 9), (9, 0), (2, 4), (4, 6), (6, 8), (8, 2), (0, 5), (1, 6), (3, 8)]
    for a, b in edges:
        mesh.add_polyline([pts[a], pts[b]], "gray")
    for i, p in enumerate(pts):
        mesh.add_box(p, (0.28, 0.28, 0.28), "violet" if i in {0, 5} else "cyan")
    mesh.add_box((0, 0, -0.05), (6.5, 5.5, 0.05), "base")
    return Recipe("network-graph", "Knowledge Graph Topology", "Graphs/knowledge", "Render nodes and links as spatial graph geometry to discuss hubs, bridges, and communities.", "Turn a dependency or knowledge graph into a spatial scene with highlighted hubs.", ["octane_import_geometry", "octane_create_material"], ["Generate node cubes and edge polylines from graph layout coordinates.", "Highlight hub/bridge nodes with a separate material.", "Use camera angle that separates edge crossings."], ["Add labels as future billboard/text geometry.", "Use animation to show graph traversal or diffusion."], mesh, {"base": PALETTE["base"], "gray": PALETTE["gray"], "cyan": PALETTE["cyan"], "violet": PALETTE["violet"]}, {"position": [4.8, -5.4, 4.1], "target": [0, 0, 0.4], "fov": 40})


def geospatial_recipe() -> Recipe:
    mesh = Mesh()
    rows = []
    for iy in range(28):
        y = -3 + 6 * iy / 27
        row = []
        for ix in range(34):
            x = -4 + 8 * ix / 33
            z = 0.22 * math.sin(x * 1.7) * math.cos(y * 1.3) + 0.18 * math.exp(-((x - 1.1) ** 2 + (y + 0.7) ** 2) / 1.3)
            row.append((x, y, z))
        rows.append(row)
    mesh.add_surface(rows, "earth")
    mesh.add_box((0, 0, -0.22), (8.5, 6.5, 0.04), "water")
    for x, y in [(-2.5, -0.6), (-0.3, 1.2), (1.8, -1.0), (2.8, 1.1)]:
        mesh.add_cylinder((x, y, 0.35), 0.12, 0.7, "gold", 14)
    return Recipe("geospatial-terrain", "Terrain and Site Markers", "Geospatial/science", "Represent a small terrain tile with highlighted points of interest, suitable for GIS-to-Octane experiments.", "Show terrain relief with several site markers for a geospatial explanation.", ["octane_import_geometry", "octane_set_camera", "octane_save_preview"], ["Generate terrain mesh from height data or a formula.", "Add marker cylinders for sites/events.", "Use a wide camera and verify scale/readability."], ["Replace synthetic terrain with DEM or GeoJSON-derived geometry.", "Encode uncertainty with marker height or color."], mesh, {"earth": PALETTE["earth"], "water": PALETTE["water"], "gold": PALETTE["gold"]}, {"position": [5.5, -6.5, 4.2], "target": [0, 0, 0], "fov": 46})


def orbit_recipe() -> Recipe:
    mesh = Mesh()
    mesh.add_box((0, 0, -0.05), (6.5, 6.5, 0.04), "base")
    mesh.add_cylinder((0, 0, 0.35), 0.32, 0.7, "gold", 32)
    for radius, mat, zoff in [(1.2, "cyan", 0.28), (2.1, "violet", 0.45), (2.8, "green", 0.62)]:
        pts = []
        for k in range(80):
            a = 2 * math.pi * k / 79
            pts.append((math.cos(a) * radius, math.sin(a) * radius * 0.75, zoff + 0.2 * math.sin(a + radius)))
        mesh.add_polyline(pts, mat)
        mesh.add_box(pts[13], (0.22, 0.22, 0.22), mat)
    return Recipe("physics-orbits", "Orbital Trajectories", "Physics/simulation", "Show several trajectories around a central body to explain orbital state, phase, or simulation snapshots.", "Visualize N-body or orbit paths with current particle positions.", ["octane_import_geometry", "octane_start_render"], ["Generate trajectory polylines from simulation points.", "Add small bodies at current timestep.", "Render with strong depth cues."], ["Use colors for object classes or energy.", "Export a sequence of OBJ frames for animation."], mesh, {"base": PALETTE["base"], "gold": PALETTE["gold"], "cyan": PALETTE["cyan"], "violet": PALETTE["violet"], "green": PALETTE["green"]}, {"position": [4.8, -6.0, 3.7], "target": [0, 0, 0.3], "fov": 42})


def architecture_recipe() -> Recipe:
    mesh = Mesh()
    xs = [-3, -1, 1, 3]
    names = ["user", "agent", "queue", "octane"]
    for i, x in enumerate(xs):
        mesh.add_box((x, 0, 0.45), (0.9, 0.65, 0.9), "cyan" if i < 2 else "gold")
        mesh.add_box((x, 0, 1.05), (1.05, 0.75, 0.08), "white")
    for a, b in zip(xs, xs[1:]):
        mesh.add_polyline([(a + 0.55, 0, 0.75), (b - 0.55, 0, 0.75)], "green")
    mesh.add_box((0, 0, -0.05), (7.2, 1.7, 0.06), "base")
    return Recipe("architecture-flow", "MCP Architecture Flow", "Architecture/explanation", "Turn an architecture diagram into geometry: user, agent, queue, and Octane as spatial blocks connected by flow lines.", "Explain how Hermes MCP commands become Octane scene updates.", ["octane_import_geometry", "octane_set_camera"], ["Use boxes for system components and lines for command flow.", "Color active or risky steps differently.", "Add future labels/billboards once text support exists."], ["Use this as a debugging state diagram.", "Animate command movement by moving small cubes along the flow."], mesh, {"base": PALETTE["base"], "cyan": PALETTE["cyan"], "gold": PALETTE["gold"], "white": PALETTE["white"], "green": PALETTE["green"]}, {"position": [2.8, -5.2, 2.6], "target": [0, 0, 0.5], "fov": 36})


def avatar_recipe() -> Recipe:
    mesh = Mesh()
    # Simple avatar face: plate, eyes, mouth, halo, pointer.
    mesh.add_box((0, 0, 1.1), (1.8, 0.28, 2.0), "navy")
    mesh.add_box((-0.42, -0.22, 1.45), (0.34, 0.08, 0.16), "cyan")
    mesh.add_box((0.42, -0.22, 1.45), (0.34, 0.08, 0.16), "cyan")
    for x in [-0.35, -0.17, 0, 0.17, 0.35]:
        mesh.add_box((x, -0.24, 0.75 + 0.14 * (1 - abs(x))), (0.12, 0.08, 0.08), "gold")
    pts = []
    for k in range(72):
        a = 2 * math.pi * k / 71
        pts.append((1.35 * math.cos(a), 0.05, 1.55 + 1.2 * math.sin(a)))
    mesh.add_polyline(pts, "violet")
    mesh.add_polyline([(1.1, -0.05, 0.9), (2.6, -0.15, 0.5), (3.1, -0.15, 0.5)], "gold")
    mesh.add_box((3.25, -0.15, 0.5), (0.28, 0.12, 0.18), "gold")
    mesh.add_box((0, 0, -0.08), (4.8, 1.2, 0.08), "base")
    return Recipe("avatar-guide", "Hermes Avatar Guide", "Agent communication", "Place a geometric Hermes guide in a scene with a pointer so agents can direct attention visually.", "Render Hermes as a non-human guide pointing at an object or idea.", ["octane_show_avatar", "octane_import_geometry"], ["Call octane_show_avatar for the standard avatar.", "Add target geometry and pointer/callout blocks.", "Use color states: cyan helpful, gold insight, amber warning, red error."], ["Add emotion-state variants.", "Use pointer geometry to highlight data points or errors."], mesh, {"base": PALETTE["base"], "navy": PALETTE["navy"], "cyan": PALETTE["cyan"], "gold": PALETTE["gold"], "violet": PALETTE["violet"]}, {"position": [0, -4.5, 2.0], "target": [0, 0, 1.2], "fov": 38})


def wave_interference_recipe() -> Recipe:
    mesh = Mesh()
    rows = []
    sources = [(-1.35, -0.35), (1.35, 0.45)]
    for iy in range(36):
        y = -3 + 6 * iy / 35
        row = []
        for ix in range(36):
            x = -3 + 6 * ix / 35
            z = 0.0
            for sx, sy in sources:
                r = math.hypot(x - sx, y - sy)
                z += math.cos(r * 4.2) / (1.0 + r * 0.7)
            row.append((x, y, z * 0.55))
        rows.append(row)
    mesh.add_box((0, 0, -0.42), (6.8, 6.8, 0.05), "base")
    mesh.add_surface(rows, "cyan")
    for sx, sy in sources:
        mesh.add_cylinder((sx, sy, 0.35), 0.15, 0.7, "gold", 24)
    return Recipe("wave-interference-field", "Wave Interference Field", "Math/physics", "Show constructive and destructive interference from two point sources as a height field with source markers.", "Explain two-source wave interference as a rendered surface with highlighted emitters.", ["octane_visualize_surface", "octane_import_geometry", "octane_save_preview"], ["Generate a height field from two damped radial cosine sources.", "Import the scene and use the camera metadata from scene.json.", "Save and review a PNG preview; the ripple extrema should remain visible without clipping."], ["Animate phase offsets as frame sequences.", "Map amplitude sign to separate materials once per-face material assignment is richer."], mesh, {"base": PALETTE["base"], "cyan": PALETTE["cyan"], "gold": PALETTE["gold"]}, {"position": [4.6, -5.6, 3.6], "target": [0, 0, 0.0], "fov": 42})


def vision_feedback_loop_recipe() -> Recipe:
    mesh = Mesh()
    xs = [-3.2, -1.05, 1.05, 3.2]
    mats = ["cyan", "gold", "violet", "green"]
    for i, x in enumerate(xs):
        mesh.add_box((x, 0, 0.48), (1.0, 0.72, 0.82), mats[i])
        mesh.add_box((x, 0, 1.02), (1.08, 0.8, 0.08), "white")
    for a, b in zip(xs, xs[1:]):
        mesh.add_box(((a + b) / 2, 0, 0.66), (abs(b - a) - 1.1, 0.10, 0.10), "white")
    mesh.add_polyline([(3.2, 0.55, 0.95), (1.05, 1.35, 1.2), (-1.05, 1.35, 1.2), (-3.2, 0.55, 0.95)], "magenta")
    mesh.add_box((0, 0, -0.06), (7.7, 2.5, 0.06), "base")
    return Recipe("vision-feedback-loop", "Render/Vision Feedback Loop", "Agent workflow", "Represent the closed loop where an agent queues geometry, Octane saves a PNG, local vision reviews it, and the next scene patch is chosen.", "Show the OctaneX MCP visual feedback loop as spatial process blocks.", ["octane_build_scene", "octane_save_preview", "octane_review_preview", "octane_suggest_camera_fix"], ["Build or import scene geometry with the MCP tools.", "Run the bridge and call octane_save_preview so Octane writes a PNG.", "Call octane_review_preview and feed warnings into the next camera/material patch."], ["Use block color to show pass/fail state.", "Animate the magenta return path as a correction pulse in future frame-sequence examples."], mesh, {"base": PALETTE["base"], "cyan": PALETTE["cyan"], "gold": PALETTE["gold"], "violet": PALETTE["violet"], "green": PALETTE["green"], "white": PALETTE["white"], "magenta": PALETTE["magenta"]}, {"position": [3.6, -5.8, 3.0], "target": [0, 0, 0.65], "fov": 38})


RECIPES = [bars_recipe(), surface_recipe(), vector_field_recipe(), network_recipe(), geospatial_recipe(), orbit_recipe(), architecture_recipe(), avatar_recipe(), wave_interference_recipe(), vision_feedback_loop_recipe()]


def command_sequence(recipe: Recipe) -> list[dict[str, object]]:
    material_commands = [
        {
            "op": "create_material",
            "payload": {
                "name": name,
                "kind": material_kind(name),
                "color": color_to_float(color),
                "roughness": material_roughness(name),
            },
        }
        for name, color in recipe.colors.items()
    ]
    return [
        {"op": "import_geometry", "payload": {"path": f"examples/recipes/{recipe.slug}/scene.obj", "format": "obj", "name": recipe.slug}},
        *material_commands,
        {"op": "set_camera", "payload": recipe.camera},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "start_render", "payload": {"samples": 128, "width": 1280, "height": 1280}},
        {"op": "save_preview", "payload": {"path": f"examples/recipes/{recipe.slug}/octane-preview.png", "width": 1280, "height": 1280}},
    ]


def write_recipe(recipe: Recipe) -> None:
    d = OUT / recipe.slug
    d.mkdir(parents=True, exist_ok=True)
    (d / "scene.obj").write_text(recipe.mesh.to_obj(recipe.slug), encoding="utf-8")
    write_mtl(d / "scene.mtl", recipe.colors)
    (d / "scene.json").write_text(json.dumps({
        "slug": recipe.slug,
        "title": recipe.title,
        "category": recipe.category,
        "purpose": recipe.purpose,
        "prompt": recipe.prompt,
        "camera": recipe.camera,
        "materials": {
            name: {"kind": material_kind(name), "color": color_to_float(color), "roughness": material_roughness(name)}
            for name, color in recipe.colors.items()
        },
        "commands": command_sequence(recipe),
        "preview_note": "preview.png is a lightweight repo-generated raster preview; re-render in Octane for final quality.",
        "native_render_note": "Some teaching assets use OBJ line primitives for paths/arrows. If the Octane OBJ importer drops lines, convert those paths to thin cylinders/tubes before final native rendering.",
        "quality_checklist": [
            "Preview is non-blank and the central idea is recognizable at thumbnail size.",
            "Scene imports the local scene.obj path listed in commands[].",
            "Camera frames the entire subject with margin.",
            "Materials named in OBJ usemtl statements are documented in scene.mtl and scene.json.",
            "If native Octane output differs from preview.png, record the lesson in docs/recipe-book.md."
        ],
    }, indent=2), encoding="utf-8")
    preview = Preview()
    preview.draw_mesh(recipe.mesh, recipe.colors)
    preview.save(d / "preview.png")
    (d / "README.md").write_text(f"""# {recipe.title}

![Preview render](preview.png)

- **Category:** {recipe.category}
- **Purpose:** {recipe.purpose}
- **Starter prompt:** {recipe.prompt}

## Files

- `scene.obj` — reusable geometry scene.
- `scene.mtl` — material color/roughness hints matching the OBJ `usemtl` names.
- `scene.json` — command sequence and camera metadata for agents.
- `preview.png` — lightweight generated preview for quick review in GitHub/docs.

## MCP tools to use

{chr(10).join(f"- `{tool}`" for tool in recipe.tools)}

## Steps

{chr(10).join(f"{idx + 1}. {step}" for idx, step in enumerate(recipe.steps))}

## Variations to explore

{chr(10).join(f"- {item}" for item in recipe.variations)}

## Quality checklist

- Preview is non-blank and recognizable at thumbnail size.
- Camera frames the entire subject with clear margins.
- Materials in `scene.obj` match `scene.mtl` and `scene.json`.
- If Octane drops OBJ line primitives, convert paths/arrows to thin cylinders or tubes for final native renders.
- Record any useful native-render success or failure in `docs/recipe-book.md`.

## Re-render in Octane

1. Import `scene.obj` with `octane_import_geometry(path=\"{d.relative_to(ROOT) / 'scene.obj'}\", name=\"{recipe.slug}\")`.
2. Apply camera from `scene.json`.
3. Drain the queue with `octane_lua/hermes_bridge_oneshot_v2.lua`.
4. Save an Octane preview and replace/add it alongside `preview.png` if it teaches a useful lesson.
""", encoding="utf-8")


def write_index() -> None:
    rows = []
    for r in RECIPES:
        rows.append(f"| [{r.title}](../examples/recipes/{r.slug}/README.md) | {r.category} | `{r.slug}` | {r.purpose} |")
    (DOCS / "recipe-library.md").write_text(f"""# Example Recipe Library

This library gives agents copyable scenes, preview renders, and operational recipes for exploring OctaneX MCP applications. Each recipe includes:

- `scene.obj` reusable geometry;
- `scene.mtl` material hints for OBJ import;
- `scene.json` MCP command/camera metadata;
- `preview.png` or `photoreal-preview.png` generated preview/target render for quick review;
- `README.md` with prompts, steps, variations, and quality checklist.

The previews are intentionally small, deterministic repo-generated renders so they can be reviewed on GitHub and reused without launching Octane. For final quality, run the listed command sequence through the Octane Lua bridge and save an Octane preview next to the sample.

Photoreal target examples may include an external target/reference image. These are visual quality bars, not claims of native Octane success until an `octane-preview.png` is saved and inspected.

Animated products are also possible by generating frame-by-frame scene states. See [`examples/animations/orbit-reveal/`](../examples/animations/orbit-reveal/README.md) for a checked-in GIF/MP4 example with PNG frames and OBJ frame states.

| Recipe | Application area | Slug | Why it matters |
| --- | --- | --- | --- |
{chr(10).join(rows)}
| [Photoreal Product Studio](../examples/recipes/photoreal-product-studio/README.md) | Photoreal/PBR rendering | `photoreal-product-studio` | Set a quality target for glass, metal, softbox lighting, camera, and native-render validation. |

## Recommended agent loop

1. Read the recipe README and inspect `preview.png` or the recipe-specific target preview.
2. Reuse or modify `scene.obj` / the generator pattern.
3. Queue import/camera/render commands through MCP.
4. Drain the queue with `octane_lua/hermes_bridge_oneshot_v2.lua`.
5. Save an Octane preview.
6. If the result teaches anything reusable, call `octane_record_recipe(...)` or edit `docs/recipe-book.md`.

## Coverage map

- **Data:** KPI bars.
- **Math:** radial surface and vector field.
- **Graphs:** knowledge/dependency graph.
- **Geospatial:** terrain tile and site markers.
- **Physics:** orbital trajectories.
- **Systems:** MCP architecture flow.
- **Agent communication:** Hermes avatar guide.
- **Feedback loops:** render/vision review loop and corrective camera/material iteration.
- **Photoreal:** product-studio scene with PBR material intent and target render.

## Animation pattern

Current reliable animation flow:

```text
Python generator -> obj_frames/scene_000.obj ... -> frame PNGs -> animation.gif / animation.mp4
```

Native Octane timeline controls are not yet exposed by the MCP. For now, generate one OBJ scene state per frame, render or preview each frame, then encode with `ffmpeg`. This is enough for data stories, trajectory reveals, system-flow explainers, and parameter sweeps.
""", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    for recipe in RECIPES:
        write_recipe(recipe)
    write_index()
    print(json.dumps({"recipes": [r.slug for r in RECIPES], "root": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
