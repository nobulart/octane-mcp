"""WP8 — Animation DSL (camera-orbit keyframe manifest).

Defines a small, dependency-free animation grammar for the bridge:

- ``CameraKeyframe`` / ``AnimationManifest`` — the declarative scene description
  (stable node names + replaceable asset paths, per the north-star protocol).
- ``sample_camera`` / ``camera_command`` — interpolate a camera pose at any time
  and emit an Octane ``set_camera`` command envelope.
- ``build_bake_plan`` — the per-frame render schedule the bridge can queue.
- ``build_animation_commands`` — turn the bake plan into queue-ready
  ``set_camera`` + ``save_preview`` command envelopes (one per frame, zero-padded
  ``frame_XXXX.png``). Used by the ``octane_build_animation`` MCP tool / gateway.
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
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


__all__ = [
    "CameraKeyframe",
    "AnimationManifest",
    "AnimationEncodeError",
    "sample_camera",
    "camera_command",
    "build_bake_plan",
    "build_animation_commands",
    "orbit_manifest",
    "frame_paths",
    "encode_frames",
    # Phase 4: object animation
    "EASING",
    "ease",
    "ObjectKeyframe",
    "ObjectAnimationManifest",
    "sample_object",
    "object_transform_command",
    "build_object_animation_commands",
    "object_rotate_manifest",
    "object_translate_manifest",
]


# Stable tuple alias for a 3D point.
Vec3 = Tuple[float, float, float]


def _v3(x: Sequence[float]) -> Vec3:
    """Coerce any 3-sequence into a fixed-arity ``Vec3`` tuple."""
    return (float(x[0]), float(x[1]), float(x[2]))


# ---------------------------------------------------------------------------
# Phase 4: easing functions (normalized t in [0,1] -> eased [0,1])
# ---------------------------------------------------------------------------

EASING: Dict[str, Callable[[float], float]] = {
    "linear": lambda t: t,
    "ease_in_out_quad": lambda t: 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2,
    "ease_in_quad": lambda t: t * t,
    "ease_out_quad": lambda t: 1 - (1 - t) ** 2,
    "ease_in_out_cubic": lambda t: 3 * t**2 - 2 * t**3 if False else (4 * t**3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2),
}


def ease(name: str, t: float) -> float:
    """Apply a named easing to normalized time ``t`` in [0,1]."""
    fn = EASING.get(name or "linear") or EASING["linear"]
    return max(0.0, min(1.0, fn(max(0.0, min(1.0, t)))))


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


def build_animation_commands(
    manifest: AnimationManifest,
    *,
    width: int = 1280,
    height: int = 1280,
    samples: int = 64,
    min_samples: int = 16,
    timeout_seconds: int = 10,
    quality: Optional[str] = None,
    max_render_time: Optional[int] = None,
    output_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Queue-ready per-frame command envelopes for the full bake plan.

    Each frame emits a ``set_camera`` command followed by a ``save_preview``
    command writing a zero-padded ``frame_XXXX.png`` into the manifest's
    ``output_dir`` (via ``frame_paths``). The returned list is exactly what the
    MCP tool / gateway dispatch hands to ``write_command`` — no Octane session,
    no Lua edit, no heavy dependency required.

    ``quality`` maps through the shared ``QUALITY_TIERS`` resolution used by the
    other preview tools (see ``server._build_save_preview_envelope``), so callers
    can request ``"high"`` / ``"ultra"`` convergence tiers uniformly. The
    resolution is done by the *caller* (the tool passes the resolved envelope),
    keeping this helper free of the models import and server-boot layering clean.

    ``output_dir`` overrides ``manifest.output_dir``. **Use a *relative* path
    such as ``"renders"``** — that is what the Octane Lua bridge's ``saveImage``
    resolves correctly under the workspace ``OctaneMCP/renders`` dir (proven live:
    the ``octane_save_preview`` tool writes ``octane-preview.png`` this way). An
    *absolute* ``/…/OctaneMCP/renders/…`` path is re-based by Octane's ``saveImage``
    to the sandbox ``Data/renders/``, dropping the ``OctaneMCP`` segment and losing
    the frames. The MCP tools intentionally leave this as the relative default.
    """
    if output_dir is not None:
        manifest = replace(manifest, output_dir=output_dir)
    paths = frame_paths(manifest, count=max(1, int(round(manifest.duration * manifest.fps))))
    commands: List[Dict[str, object]] = []
    for (i, _t, cam_cmd), path in zip(build_bake_plan(manifest), paths):
        commands.append({"op": "set_camera", "payload": dict(cam_cmd)})
        commands.append(
            {
                "op": "save_preview",
                "payload": {
                    "path": path,
                    "width": width,
                    "height": height,
                    "samples": samples,
                    "min_samples": min_samples,
                    "timeout_seconds": timeout_seconds,
                    "quality": quality,
                    "max_render_time": max_render_time,
                },
            }
        )
    return commands


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


# ---------------------------------------------------------------------------
# Phase 4: object animation (rotate/translate/scale a node over frames)
# ---------------------------------------------------------------------------

# A common standard frame rate when the user does not specify one.
DEFAULT_FPS = 24


@dataclass(frozen=True)
class ObjectKeyframe:
    """An object transform state at frame ``frame`` (absolute frame index)."""

    frame: int
    translation: Optional[Vec3] = None
    rotation_euler: Optional[Vec3] = None
    scale: Optional[Vec3] = None


@dataclass(frozen=True)
class ObjectAnimationManifest:
    """Declarative per-object transform animation.

    ``object_name`` is the stable node name (``Hermes::<scene>::<uid>``). Frames
    span ``start_frame``..``end_frame`` inclusive; if either is given as a
    timecode string (``"00:00:16:08"``) it is converted at ``fps``. ``easing``
    is applied per-segment so motion like "quadratic in-out" accelerates then
    decelerates within each keyframe span.
    """

    object_name: str
    start_frame: int
    end_frame: int
    keyframes: Tuple[ObjectKeyframe, ...]
    fps: int = DEFAULT_FPS
    width: int = 1280
    height: int = 1280
    output_dir: str = "renders"
    basename: str = "frame"
    # Render convergence per frame (mirrors build_animation_commands).
    samples: int = 64
    min_samples: int = 16
    timeout_seconds: int = 10
    quality: Optional[str] = None
    max_render_time: Optional[int] = None
    easing: str = "ease_in_out_quad"


def _parse_frame(value: Any, fps: int) -> int:
    """Coerce a frame spec to an int.

    Accepts an int, or a timecode string ``"HH:MM:SS:FF"`` (SMPTE) / ``"SS.FFF"``
    (seconds.frames) resolved against ``fps``. Unknown forms raise ValueError.
    """
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value * fps))
    if isinstance(value, str):
        s = value.strip()
        if ":" in s:
            parts = s.split(":")
            if len(parts) == 4:  # HH:MM:SS:FF
                h, m, sec, ff = (int(p) for p in parts)
                return int((h * 3600 + m * 60 + sec) * fps + ff)
            if len(parts) == 2:  # SS.FFF -> seconds.frames-ish; treat as SS.frac
                sec, frac = int(parts[0]), int(parts[1])
                return int(sec * fps + frac)
        if s.replace(".", "", 1).isdigit():
            return int(round(float(s) * fps))
    raise ValueError(f"cannot parse frame spec: {value!r}")


def sample_object(manifest: ObjectAnimationManifest, frame: int) -> ObjectKeyframe:
    """Interpolate an object's transform at an absolute ``frame``.

    Easing is applied to the normalized segment position *before* lerp, so the
    motion eases within each keyframe span (e.g. quadratic in-out). Frames
    outside the span hold the nearest endpoint.
    """
    kfs = manifest.keyframes
    if not kfs:
        raise ValueError("ObjectAnimationManifest needs at least one keyframe")
    if frame <= kfs[0].frame:
        return kfs[0]
    if frame >= kfs[-1].frame:
        return kfs[-1]
    for a, b in zip(kfs, kfs[1:]):
        if a.frame <= frame <= b.frame:
            span = (b.frame - a.frame) or 1
            r = ease(manifest.easing, (frame - a.frame) / span)
            return ObjectKeyframe(
                frame=frame,
                translation=_v3(_lerp3(a.translation, b.translation, r)) if (a.translation and b.translation) else (a.translation or b.translation),
                rotation_euler=_v3(_lerp3(a.rotation_euler, b.rotation_euler, r)) if (a.rotation_euler and b.rotation_euler) else (a.rotation_euler or b.rotation_euler),
                scale=_v3(_lerp3(a.scale, b.scale, r)) if (a.scale and b.scale) else (a.scale or b.scale),
            )
    return kfs[-1]


def object_transform_command(obj_kf: ObjectKeyframe, object_name: str) -> dict:
    """Octane ``set_object_transform`` envelope for a sampled object keyframe."""
    payload: dict[str, Any] = {"object_name": object_name}
    if obj_kf.translation is not None:
        payload["translation"] = list(obj_kf.translation)
    if obj_kf.rotation_euler is not None:
        payload["rotation_euler"] = list(obj_kf.rotation_euler)
    if obj_kf.scale is not None:
        payload["scale"] = list(obj_kf.scale)
    return {"op": "set_object_transform", "payload": payload}


def build_object_animation_commands(
    manifest: ObjectAnimationManifest,
    *,
    width: int | None = None,
    height: int | None = None,
    samples: int | None = None,
    min_samples: int | None = None,
    timeout_seconds: int | None = None,
    quality: Optional[str] = None,
    max_render_time: Optional[int] = None,
    output_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Queue-ready per-frame command envelopes: ``set_object_transform`` + ``save_preview``.

    One entry per frame in ``start_frame..end_frame``; frame paths preserve the
    absolute frame index (``frame_0400.png``) so a sub-range composes with a
    longer sequence. Mirrors ``build_animation_commands`` for cameras.
    """
    if output_dir is not None:
        manifest = replace(manifest, output_dir=output_dir)
    w = width or manifest.width
    h = height or manifest.height
    sp = samples or manifest.samples
    ms = min_samples or manifest.min_samples
    to = timeout_seconds or manifest.timeout_seconds
    q = quality if quality is not None else manifest.quality
    mr = max_render_time if max_render_time is not None else manifest.max_render_time

    commands: List[Dict[str, Any]] = []
    for frame in range(manifest.start_frame, manifest.end_frame + 1):
        obj_kf = sample_object(manifest, frame)
        commands.append(object_transform_command(obj_kf, manifest.object_name))
        commands.append(
            {
                "op": "save_preview",
                "payload": {
                    "path": f"{manifest.output_dir}/{manifest.basename}_{frame:04d}.png",
                    "width": w,
                    "height": h,
                    "samples": sp,
                    "min_samples": ms,
                    "timeout_seconds": to,
                    "quality": q,
                    "max_render_time": mr,
                },
            }
        )
    return commands


def object_rotate_manifest(
    object_name: str,
    *,
    axis: str = "y",
    degrees: float = 0.0,
    start_frame: Any = 0,
    end_frame: Any = 24,
    fps: int = DEFAULT_FPS,
    easing: str = "ease_in_out_quad",
    **kw,
) -> ObjectAnimationManifest:
    """Rotate ``object_name`` by ``degrees`` about ``axis`` over a frame range.

    The node starts at rotation 0 on ``axis`` and ends at ``degrees`` (other
    axes held at 0). ``start_frame``/``end_frame`` accept ints or timecode
    strings. This is the grammar behind "rotate #54 by 104 degrees over frames
    400-1000 with quadratic in-out".
    """
    ax = axis.lower()
    if ax not in ("x", "y", "z"):
        raise ValueError(f"rotate axis must be x/y/z, got {axis!r}")
    idx = {"x": 0, "y": 1, "z": 2}[ax]
    sf = _parse_frame(start_frame, fps)
    ef = _parse_frame(end_frame, fps)
    start_rot = [0.0, 0.0, 0.0]
    end_rot = [0.0, 0.0, 0.0]
    end_rot[idx] = float(degrees)
    keyframes = (
        ObjectKeyframe(frame=sf, rotation_euler=_v3(start_rot)),
        ObjectKeyframe(frame=ef, rotation_euler=_v3(end_rot)),
    )
    return ObjectAnimationManifest(
        object_name=object_name,
        start_frame=sf,
        end_frame=ef,
        keyframes=keyframes,
        fps=fps,
        easing=easing,
        **kw,
    )


def object_translate_manifest(
    object_name: str,
    *,
    offset: Vec3 = (0.0, 0.0, 0.0),
    start_frame: Any = 0,
    end_frame: Any = 24,
    fps: int = DEFAULT_FPS,
    easing: str = "ease_in_out_quad",
    **kw,
) -> ObjectAnimationManifest:
    """Translate ``object_name`` by ``offset`` over a frame range (eases in-out)."""
    sf = _parse_frame(start_frame, fps)
    ef = _parse_frame(end_frame, fps)
    keyframes = (
        ObjectKeyframe(frame=sf, translation=(0.0, 0.0, 0.0)),
        ObjectKeyframe(frame=ef, translation=_v3(offset)),
    )
    return ObjectAnimationManifest(
        object_name=object_name,
        start_frame=sf,
        end_frame=ef,
        keyframes=keyframes,
        fps=fps,
        easing=easing,
        **kw,
    )
