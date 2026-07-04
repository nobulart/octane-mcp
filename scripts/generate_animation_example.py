from __future__ import annotations

import json
import math
import shutil
import struct
import subprocess
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "examples" / "animations" / "orbit-reveal"
FRAMES = OUT / "frames"
OBJ_FRAMES = OUT / "obj_frames"
WIDTH = 960
HEIGHT = 640
FRAME_COUNT = 32
FPS = 12

Color = tuple[int, int, int]
Point3 = tuple[float, float, float]
Point2 = tuple[float, float]

BG_TOP = (18, 26, 54)
BG_BOTTOM = (8, 12, 26)
CYAN = (18, 197, 255)
GOLD = (255, 181, 61)
VIOLET = (166, 109, 255)
GREEN = (75, 220, 140)
GRAY = (112, 128, 160)
BASE = (35, 45, 75)
WHITE = (230, 238, 255)


def shade(color: Color, factor: float) -> Color:
    return tuple(max(0, min(255, int(c * factor))) for c in color)  # type: ignore[return-value]


def blend(a: Color, b: Color, t: float) -> Color:
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))  # type: ignore[return-value]


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


def project(p: Point3, scale: float = 82.0, cx: float = WIDTH / 2, cy: float = HEIGHT / 2 + 72) -> Point2:
    x, y, z = p
    u = (x - y) * 0.866
    v = (x + y) * 0.33 - z * 0.92
    return (cx + u * scale, cy + v * scale)


def blank() -> list[list[Color]]:
    pixels: list[list[Color]] = []
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        pixels.append([blend(BG_TOP, BG_BOTTOM, t) for _ in range(WIDTH)])
    return pixels


def set_px(pixels: list[list[Color]], x: int, y: int, color: Color) -> None:
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        pixels[y][x] = color


def line(pixels: list[list[Color]], p1: Point2, p2: Point2, color: Color, width: int = 2) -> None:
    x1, y1 = p1
    x2, y2 = p2
    steps = max(1, int(max(abs(x2 - x1), abs(y2 - y1))))
    radius = max(0, width // 2)
    for i in range(steps + 1):
        t = i / steps
        x = int(round(x1 + (x2 - x1) * t))
        y = int(round(y1 + (y2 - y1) * t))
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                set_px(pixels, x + dx, y + dy, color)


def circle(pixels: list[list[Color]], center: Point2, radius: int, color: Color) -> None:
    cx, cy = center
    for y in range(int(cy - radius), int(cy + radius) + 1):
        for x in range(int(cx - radius), int(cx + radius) + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius * radius:
                set_px(pixels, x, y, color)


def rect(pixels: list[list[Color]], center: Point2, size: tuple[int, int], color: Color) -> None:
    cx, cy = center
    sx, sy = size[0] // 2, size[1] // 2
    for y in range(int(cy - sy), int(cy + sy) + 1):
        for x in range(int(cx - sx), int(cx + sx) + 1):
            set_px(pixels, x, y, color)


def orbit_points(radius: float, zoff: float, phase: float, count: int = 120) -> list[Point3]:
    pts = []
    for k in range(count):
        a = 2 * math.pi * k / (count - 1)
        pts.append((math.cos(a) * radius, math.sin(a) * radius * 0.72, zoff + 0.20 * math.sin(a + phase)))
    return pts


def draw_frame(frame: int) -> list[list[Color]]:
    t = frame / FRAME_COUNT
    pixels = blank()

    # Ground/reference plane.
    plane = [project((-3.4, -3.4, -0.08)), project((3.4, -3.4, -0.08)), project((3.4, 3.4, -0.08)), project((-3.4, 3.4, -0.08))]
    for a, b in zip(plane, plane[1:] + plane[:1]):
        line(pixels, a, b, shade(BASE, 1.2), 2)

    # Orbit paths revealed over time.
    configs = [(1.15, 0.26, 0.0, CYAN), (2.0, 0.45, 1.3, VIOLET), (2.75, 0.62, 2.0, GREEN)]
    for idx, (radius, zoff, phase, color) in enumerate(configs):
        pts = orbit_points(radius, zoff, phase)
        visible = max(4, int(len(pts) * min(1.0, (t * 1.2) - idx * 0.10)))
        for p1, p2 in zip(pts[:visible], pts[1:visible]):
            line(pixels, project(p1), project(p2), shade(color, 0.92), 2)
        angle = 2 * math.pi * (t + idx * 0.21)
        body = (math.cos(angle) * radius, math.sin(angle) * radius * 0.72, zoff + 0.20 * math.sin(angle + phase))
        circle(pixels, project(body), 8, color)

    # Central body and pulsing highlight.
    pulse = 10 + int(4 * math.sin(2 * math.pi * t))
    circle(pixels, project((0, 0, 0.35)), 18 + pulse // 3, shade(GOLD, 0.45))
    circle(pixels, project((0, 0, 0.35)), 17, GOLD)

    # Timeline blocks at bottom: frames as product/storyboard cue.
    for k in range(FRAME_COUNT):
        x = 190 + k * 18
        color = GOLD if k <= frame else shade(GRAY, 0.55)
        rect(pixels, (x, HEIGHT - 70), (10, 20), color)
    line(pixels, (180, HEIGHT - 42), (780, HEIGHT - 42), shade(WHITE, 0.45), 1)
    return pixels


def obj_for_frame(frame: int) -> str:
    t = frame / FRAME_COUNT
    vertices: list[Point3] = []
    edges: list[tuple[int, int, str]] = []
    faces_by_material: list[tuple[str, tuple[int, ...]]] = []

    def v(p: Point3) -> int:
        vertices.append(p)
        return len(vertices)

    def polyline(points: list[Point3], mat: str) -> None:
        ids = [v(p) for p in points]
        for a, b in zip(ids, ids[1:]):
            edges.append((a, b, mat))

    configs = [(1.15, 0.26, 0.0, "cyan"), (2.0, 0.45, 1.3, "violet"), (2.75, 0.62, 2.0, "green")]
    for idx, (radius, zoff, phase, mat) in enumerate(configs):
        pts = orbit_points(radius, zoff, phase, 64)
        visible = max(4, int(len(pts) * min(1.0, (t * 1.2) - idx * 0.10)))
        polyline(pts[:visible], mat)
        angle = 2 * math.pi * (t + idx * 0.21)
        body = (math.cos(angle) * radius, math.sin(angle) * radius * 0.72, zoff + 0.20 * math.sin(angle + phase))
        s = 0.09
        cx, cy, cz = body
        base = len(vertices)
        for dx, dy, dz in [(-s, -s, -s), (s, -s, -s), (s, s, -s), (-s, s, -s), (-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s)]:
            v((cx + dx, cy + dy, cz + dz))
        for face in ((1, 2, 3, 4), (5, 8, 7, 6), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 8, 4), (5, 1, 4, 8)):
            faces_by_material.append((mat, tuple(base + i for i in face)))

    lines = ["# Animated recipe frame for OctaneX MCP", f"o orbit_reveal_frame_{frame:03d}"]
    for p in vertices:
        lines.append(f"v {p[0]:.5f} {p[1]:.5f} {p[2]:.5f}")
    current = None
    for mat, face in faces_by_material:
        if mat != current:
            lines.append(f"usemtl {mat}")
            current = mat
        lines.append("f " + " ".join(str(i) for i in face))
    for a, b, mat in edges:
        if mat != current:
            lines.append(f"usemtl {mat}")
            current = mat
        lines.append(f"l {a} {b}")
    return "\n".join(lines) + "\n"


def run_ffmpeg() -> dict[str, str | bool]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return {"ffmpeg_found": False, "animation_gif": False, "animation_mp4": False}
    palette = OUT / "palette.png"
    subprocess.run([ffmpeg, "-y", "-framerate", str(FPS), "-i", str(FRAMES / "frame_%03d.png"), "-vf", "palettegen", str(palette)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run([ffmpeg, "-y", "-framerate", str(FPS), "-i", str(FRAMES / "frame_%03d.png"), "-i", str(palette), "-lavfi", "paletteuse", str(OUT / "animation.gif")], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run([ffmpeg, "-y", "-framerate", str(FPS), "-i", str(FRAMES / "frame_%03d.png"), "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT / "animation.mp4")], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {"ffmpeg_found": True, "animation_gif": True, "animation_mp4": True}


def main() -> None:
    FRAMES.mkdir(parents=True, exist_ok=True)
    OBJ_FRAMES.mkdir(parents=True, exist_ok=True)
    for frame in range(FRAME_COUNT):
        write_png(FRAMES / f"frame_{frame:03d}.png", WIDTH, HEIGHT, draw_frame(frame))
        (OBJ_FRAMES / f"scene_{frame:03d}.obj").write_text(obj_for_frame(frame), encoding="utf-8")
    ffmpeg_result = run_ffmpeg()
    storyboard = {
        "slug": "orbit-reveal",
        "title": "Animated Orbit Reveal",
        "purpose": "Demonstrate an animated product: a short explainer loop built from generated scene states.",
        "fps": FPS,
        "frames": FRAME_COUNT,
        "products": ["animation.gif", "animation.mp4", "frames/frame_000.png", "obj_frames/scene_000.obj"],
        "mcp_pattern": [
            "Generate a series of OBJ frame states under obj_frames/.",
            "For a true Octane render, import each OBJ state, render/save a PNG, then encode the PNG sequence with ffmpeg.",
            "If the native OBJ importer drops line primitives, convert orbit/path lines to thin cylinders or tubes before final rendering.",
            "For fast docs, use the lightweight preview frames and animation.gif included here."
        ],
        "ffmpeg": ffmpeg_result,
    }
    (OUT / "storyboard.json").write_text(json.dumps(storyboard, indent=2), encoding="utf-8")
    (OUT / "README.md").write_text(f"""# Animated Orbit Reveal

![Animated preview](animation.gif)

This is a minimal animated product example for OctaneX MCP. It demonstrates the practical pattern before native Octane animation controls exist in the MCP surface:

1. Generate a sequence of scene states (`obj_frames/scene_000.obj` ...).
2. Render or preview each state as a PNG frame (`frames/frame_000.png` ...).
3. Encode the frames into a reviewable artifact (`animation.gif` and `animation.mp4`).

## Files

- `animation.gif` — GitHub-friendly animated preview.
- `animation.mp4` — video product encoded with ffmpeg.
- `frames/` — deterministic lightweight PNG frames.
- `obj_frames/` — reusable OBJ scene states for Octane re-rendering. These use line primitives for orbit paths; convert paths to thin cylinders/tubes if the native importer drops lines.
- `storyboard.json` — metadata, FPS, product list, and agent pattern.

## Why this matters

Animated products are useful for:

- temporal data stories;
- orbit/trajectory/physics explanations;
- architecture flows and command lifecycle diagrams;
- optimization progress over time;
- before/after or step-by-step debugging explanations.

## Re-rendering in Octane

For final-quality native renders, process each OBJ frame through the Octane bridge:

1. Import `obj_frames/scene_000.obj` with `octane_import_geometry(...)`.
2. Apply a stable camera and lighting preset.
3. Save a PNG preview for that frame.
4. Repeat for each frame, then encode the saved PNG sequence with:

```bash
ffmpeg -y -framerate {FPS} -i frame_%03d.png -pix_fmt yuv420p animation.mp4
```

The repo-generated preview keeps the learning artifact available even when Octane is not running.
""", encoding="utf-8")
    print(json.dumps({"out": str(OUT), "frames": FRAME_COUNT, **ffmpeg_result}, indent=2))


if __name__ == "__main__":
    main()
