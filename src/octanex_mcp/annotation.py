"""Dev-only label overlay for rendered Octane scenes.

Goal (project idea, 2026-07-10): let the human talk about the scene by a
stable per-object badge ("change object #43", "group #6 through #10") by
drawing "#N" markers onto the rendered preview.

Approach B from the design brainstorm: render the clean scene -> PNG, then
project each object's ``bounds.center`` through the camera that produced the
frame and draw the badge in 2D. No Lua changes, no scene pollution, crisp
text, trivially toggleable. (Approach A -- in-scene camera-facing billboards
-- is a possible future opt-in for recorded walkthroughs; B is the default.)

Dependency policy (matches the rest of the repo): the projection math is
pure stdlib (no numpy). The final raster step uses Pillow *if available*
(``harvest`` extra); if it is missing we raise a precise install hint rather
than an import traceback, so the offline test suite never needs Pillow.

Two pieces of ground truth are required and must live in the manifest:
  * ``camera``: {position:[x,y,z], target:[x,y,z], fov:deg}
  * per-object ``bounds.center`` (already produced by create_primitive_obj;
    callers supplying external meshes must provide it).

Without the camera you cannot project; without bounds.center you cannot place
the badge. Both are surfaced as clear errors, not silent wrong output.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

__all__ = [
    "CameraView",
    "project_world_to_screen",
    "compute_label_layout",
    "draw_label_overlay",
    "LabelPlacement",
]

Vec3 = Tuple[float, float, float]


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(a: Vec3) -> Vec3:
    m = math.sqrt(_dot(a, a)) or 1e-9
    return (a[0] / m, a[1] / m, a[2] / m)


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


@dataclass(frozen=True)
class CameraView:
    """A minimal perspective camera (right-handed, look-at)."""

    position: Vec3
    target: Vec3
    fov_deg: float = 45.0
    up: Vec3 = (0.0, 1.0, 0.0)

    def forward(self) -> Vec3:
        # Direction the camera looks (target - position, normalized).
        return _norm(_sub(self.target, self.position))


def _basis(cam: CameraView) -> Tuple[Vec3, Vec3, Vec3]:
    """Return camera basis (right, true_up, forward) as orthonormal vectors."""
    fwd = cam.forward()
    right = _norm(_cross(fwd, cam.up))
    true_up = _cross(right, fwd)
    return right, true_up, fwd


def project_world_to_screen(
    point: Vec3,
    cam: CameraView,
    width: int,
    height: int,
) -> Optional[Tuple[float, float, float]]:
    """Project a world point to screen space.

    Returns ``(x, y, depth)`` in pixels with origin top-left, or ``None``
    if the point is behind the camera. ``depth`` is the view-space distance
    (positive in front); callers can use it for occlusion ordering / culling.

    Pure stdlib; verified against a hand-computed look-at in the tests.
    """
    if width <= 0 or height <= 0:
        raise ValueError("width/height must be positive")
    rel = _sub(point, cam.position)
    right, up, fwd = _basis(cam)
    # View-space coordinates (camera looks down +fwd).
    x_c = _dot(rel, right)
    y_c = _dot(rel, up)
    z_c = _dot(rel, fwd)
    if z_c <= 1e-9:
        return None  # behind / on the camera plane
    # Perspective: half-height at unit depth = tan(fov/2).
    tan_half = math.tan(math.radians(cam.fov_deg) / 2.0)
    ndc_x = (x_c / z_c) / tan_half
    # Aspect correction: divide by (width/height) so x uses the wider axis.
    ndc_x /= (width / height)
    ndc_y = (y_c / z_c) / tan_half
    # NDC [-1,1] -> screen pixels (y flipped: +up is -y in pixel space).
    sx = (ndc_x * 0.5 + 0.5) * width
    sy = (0.5 - ndc_y * 0.5) * height
    return (sx, sy, z_c)


@dataclass
class LabelPlacement:
    badge: str
    uid: str
    screen: Tuple[float, float]
    depth: float
    visible: bool


def _bounds_center(obj: Mapping[str, Any]) -> Optional[Vec3]:
    b = obj.get("bounds")
    if isinstance(b, Mapping) and isinstance(b.get("center"), (list, tuple)):
        c = b["center"]
        if len(c) == 3 and all(isinstance(v, (int, float)) for v in c):
            return (float(c[0]), float(c[1]), float(c[2]))
    # geometry center fallback (some generators store geometry.center)
    g = obj.get("geometry")
    if isinstance(g, Mapping) and isinstance(g.get("center"), (list, tuple)):
        c = g["center"]
        if len(c) == 3:
            return (float(c[0]), float(c[1]), float(c[2]))
    return None


@dataclass
class _LabelInput:
    badge: str
    uid: str
    center: Vec3


def compute_label_layout(
    scene: Mapping[str, Any],
    camera: Optional[CameraView] = None,
    width: int = 1280,
    height: int = 1280,
    *,
    cull_behind: bool = True,
) -> List[LabelPlacement]:
    """Project every labelled object's center to screen space.

    Uses the supplied ``camera`` or the scene manifest's ``camera`` block
    (position/target/fov). Raises a clear error when neither exists, since
    projection is impossible without it.
    """
    cam = camera
    if cam is None:
        cam_block = scene.get("camera") or {}
        pos = cam_block.get("position")
        tgt = cam_block.get("target")
        fov = cam_block.get("fov", 45.0)
        if not (isinstance(pos, (list, tuple)) and isinstance(tgt, (list, tuple))):
            raise ValueError(
                "no camera available: pass CameraView or set scene['camera']"
                " = {position:[x,y,z], target:[x,y,z], fov:deg}"
            )
        cam = CameraView(
            position=(float(pos[0]), float(pos[1]), float(pos[2])),
            target=(float(tgt[0]), float(tgt[1]), float(tgt[2])),
            fov_deg=float(fov),
        )

    labels: Mapping[str, str] = scene.get("labels") or {}
    uid_to_badge: Dict[str, str] = {v: k for k, v in labels.items()}

    placements: List[LabelPlacement] = []
    for obj in scene.get("objects", []):
        if not isinstance(obj, Mapping):
            continue
        uid = str(obj.get("uid") or obj.get("id") or "")
        badge = uid_to_badge.get(uid)
        if not badge:
            continue
        center = _bounds_center(obj)
        if center is None:
            # No center -> cannot place; skip with a non-visible marker so the
            # caller can still report "object #N has no bounds".
            placements.append(LabelPlacement(badge, uid, (0.0, 0.0), 0.0, False))
            continue
        proj = project_world_to_screen(center, cam, width, height)
        if proj is None:
            if cull_behind:
                continue
            placements.append(LabelPlacement(badge, uid, (0.0, 0.0), 0.0, False))
            continue
        sx, sy, depth = proj
        on_screen = (-20 <= sx <= width + 20) and (-20 <= sy <= height + 20)
        placements.append(
            LabelPlacement(badge, uid, (sx, sy), depth, on_screen)
        )
    # Sort far-to-near so nearer badges draw last (on top).
    placements.sort(key=lambda p: p.depth, reverse=True)
    return placements


def draw_label_overlay(
    source_png: str,
    placements: Sequence[LabelPlacement],
    out_png: str,
    *,
    background: Tuple[int, int, int, int] = (20, 20, 24, 200),
    text_color: Tuple[int, int, int, int] = (240, 240, 245, 255),
    font_size: int = 22,
) -> str:
    """Raster the badges onto ``source_png`` -> ``out_png``.

    Requires Pillow (the ``harvest`` extra). Raises a precise install hint
    instead of an import traceback when it is absent, so offline environments
    can still run the projection/layout logic in tests.
    """
    try:
        from PIL import Image, ImageDraw
    except Exception as exc:  # pragma: no cover - exercised when Pillow missing
        raise RuntimeError(
            "Pillow is required to draw the label overlay. Install it with: "
            "uv sync --extra harvest   (or: pip install pillow)"
        ) from exc

    if not Path(source_png).exists():
        raise ValueError(f"label overlay: source preview not found: {source_png}")

    img = Image.open(source_png).convert("RGBA")
    draw = ImageDraw.Draw(img)
    try:
        from PIL import ImageFont

        font = ImageFont.load_default()
        # Prefer a scalable font if the platform has one; fall back silently.
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", font_size)
        except Exception:
            pass
    except Exception:
        font = None

    for p in placements:
        if not p.visible:
            continue
        x, y = p.screen
        label = p.badge
        # Measure text box for the label background.
        if font is not None:
            bbox = draw.textbbox((0, 0), label, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        else:
            tw, th = len(label) * 11, 16
        pad = 5
        bx0, by0 = x + 6, y - th - pad
        bx1, by1 = bx0 + tw + pad * 2, by0 + th + pad * 2
        draw.rectangle([bx0, by0, bx1, by1], fill=background)
        draw.text((bx0 + pad, by0 + pad), label, fill=text_color, font=font)

    img.convert("RGB").save(out_png)
    return out_png
