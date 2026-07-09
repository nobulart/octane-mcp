"""WP8 — Animation DSL (camera-orbit keyframe manifest).

Defines a small, dependency-free animation grammar for the bridge:

- ``CameraKeyframe`` / ``AnimationManifest`` — the declarative scene description
  (stable node names + replaceable asset paths, per the north-star protocol).
- ``sample_camera`` / ``camera_command`` — interpolate a camera pose at any time
  and emit an Octane ``set_camera`` command envelope.
- ``build_bake_plan`` — the per-frame render schedule the bridge can queue.
- ``orbit_manifest`` — convenience builder for a circular camera orbit (the
  most common agent-requested motion).
- ``encode_frames`` — optional video encode via an *injected* encoder callable,
  so the module stays free of heavy/non-optional dependencies (ffmpeg is an
  external tool, not a project dependency).

Layering rule (skill §6): this module imports only stdlib + ``octanex_mcp``
dataclasses. It MUST NOT import ``benchmarks`` / ``scripts`` / ``tests`` — the
console-script server launches with repo root off ``sys.path``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Tuple

__all__ = [
    "CameraKeyframe",
    "AnimationManifest",
    "AnimationEncodeError",
    "sample_camera",
    "camera_command",
    "build_bake_plan",
    "orbit_manifest",
    "frame_paths",
    "encode_frames",
]


# Stable tuple alias for a 3D point.
Vec3 = Tuple[float, float, float]


@dataclass(frozen=True)
class CameraKeyframe:
    """A camera pose at time ``t`` (seconds from clip start)."""

    t: float
    position: Vec3
    target: Vec3
    fov: float = 45.0


@dataclass(frozen=True)
class AnimationManifest:
    """Declarative animation description.

    ``encoder`` is an optional callable ``(frame_paths, out_path) -> None``.
    Inject it for offline tests or to wire ffmpeg without adding a hard dep.
    """

    fps: int
    duration: float  # seconds
    keyframes: Tuple[CameraKeyframe, ...]  # sorted by t; first t == 0
    width: int = 1280
    height: int = 1280
    output_dir: str = "renders"
    basename: str = "frame"
    encoder: Optional[Callable[[Sequence[str], str], None]] = None


class AnimationEncodeError(RuntimeError):
    """Raised when ``encode_frames`` is called without an injected encoder."""


def _lerp(a: float, b: float, r: float) -> float:
    return a + (b - a) * r


def _lerp3(a: Vec3, b: Vec3, r: float) -> Vec3:
    return (_lerp(a[0], b[0], r), _lerp(a[1], b[1], r), _lerp(a[2], b[2], r))


def sample_camera(manifest: AnimationManifest, t: float) -> CameraKeyframe:
    """Linearly interpolate position/target/fov at time ``t`` (seconds).

    Clamps to the first keyframe before the clip start and to the last
    keyframe after the clip end (hold-last behaviour).
    """
    kfs = manifest.keyframes
    if not kfs:
        raise ValueError("AnimationManifest must contain at least one keyframe")
    if t <= kfs[0].t:
        return kfs[0]
    if t >= kfs[-1].t:
        return kfs[-1]
    for a, b in zip(kfs, kfs[1:]):
        if a.t <= t <= b.t:
            span = (b.t - a.t) or 1.0
            r = (t - a.t) / span
            return CameraKeyframe(
                t=t,
                position=_lerp3(a.position, b.position, r),
                target=_lerp3(a.target, b.target, r),
                fov=_lerp(a.fov, b.fov, r),
            )
    return kfs[-1]


def camera_command(kf: CameraKeyframe) -> dict:
    """Octane ``set_camera`` command envelope for a sampled keyframe."""
    return {
        "op": "set_camera",
        "position": list(kf.position),
        "target": list(kf.target),
        "fov": kf.fov,
    }


def build_bake_plan(manifest: AnimationManifest) -> list[Tuple[int, float, dict]]:
    """Per-frame render schedule: ``(frame_index, time, camera_command)``.

    Frame count is ``round(duration * fps)``; frame 0 sits at t=0.
    """
    if manifest.fps <= 0:
        return [(0, 0.0, camera_command(manifest.keyframes[0]))]
    n = max(1, int(round(manifest.duration * manifest.fps)))
    plan: list[Tuple[int, float, dict]] = []
    for i in range(n):
        t = i / manifest.fps
        kf = sample_camera(manifest, t)
        plan.append((i, t, camera_command(kf)))
    return plan


def frame_paths(manifest: AnimationManifest, count: int) -> list[str]:
    """Render-output paths for ``count`` frames (zero-padded)."""
    return [
        f"{manifest.output_dir}/{manifest.basename}_{i:04d}.png"
        for i in range(count)
    ]


def encode_frames(
    manifest: AnimationManifest, frame_paths: Sequence[str], out_path: str
) -> str:
    """Encode rendered frames to ``out_path``.

    Uses ``manifest.encoder`` if injected (keeps the offline/test path free of
    ffmpeg). Raises ``AnimationEncodeError`` when no encoder is configured,
    directing the caller to inject one or wire ffmpeg externally.
    """
    if manifest.encoder is not None:
        manifest.encoder(frame_paths, out_path)
        return out_path
    raise AnimationEncodeError(
        "no encoder configured; inject AnimationManifest.encoder="
        "(frame_paths, out_path) -> None, or wire ffmpeg externally. "
        "ffmpeg is an optional external tool, not a project dependency."
    )


def orbit_manifest(
    center: Vec3 = (0.0, 0.0, 0.0),
    radius: float = 8.0,
    height: float = 2.0,
    fps: int = 24,
    duration: float = 6.0,
    start_deg: float = 0.0,
    end_deg: float = 360.0,
    fov: float = 45.0,
    segments: int = 24,
    **kw,
) -> AnimationManifest:
    """Build a circular camera orbit around ``center``.

    Emits ``segments + 1`` keyframes evenly spaced in angle so linear
    interpolation between them approximates the arc (a 2-keyframe full orbit
    would interpolate a straight chord, not a circle). ``segments`` defaults to
    24 (~15 degrees of arc per segment at 360 deg).
    """
    if segments < 2:
        raise ValueError("orbit_manifest requires segments >= 2")
    a0 = math.radians(start_deg)
    a1 = math.radians(end_deg)
    keyframes = []
    for i in range(segments + 1):
        f = i / segments
        ang = a0 + (a1 - a0) * f
        pos: Vec3 = (
            center[0] + radius * math.cos(ang),
            center[1] + height,
            center[2] + radius * math.sin(ang),
        )
        keyframes.append(
            CameraKeyframe(
                t=f * duration,
                position=pos,
                target=(center[0], center[1], center[2]),
                fov=fov,
            )
        )
    return AnimationManifest(
        fps=fps, duration=duration, keyframes=tuple(keyframes), **kw
    )
