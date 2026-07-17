"""LuisaRender quality backend — offline path-traced PNG from ``canvas.scene.v1``.

This is the *quality tier* backend in the two-tier model (WebGL realtime,
LuisaRender offline quality; see ``docs/luisa-render-backend-investigation.md``
and ``docs/canvas-web-ui-build-plan.md``). Unlike ``WebGLBackend`` (pure
conversion, browser renders), this backend produces real pixels server-side by:

1. ``build(scene)``        → compile ``canvas.scene.v1`` to ``.luisa`` + sidecar
                            OBJ meshes in a workspace directory.
2. ``render_preview``      → run ``luisa-render-cli -b metal`` and convert the
                            resulting EXR to PNG (in-memory path).
3. ``save_png(scene,path)`` → same as render_preview, persisted to ``path``.

No Octane, no AppleScript, no TCC — a clean local CLI with a Metal backend.
Pixel QA uses the same stdlib PNG stats discipline as
``scripts/spike_luisa_scene.py`` so a blank/flat frame fails loudly.
"""

from __future__ import annotations

import os
import struct
import subprocess
import tempfile
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

from octanex_mcp.backends.base import Backend
from octanex_mcp.backends.luisa import compile_scene
from octanex_mcp.canvas_scene import validate_scene

_DEFAULT_LUISA_ROOT = Path("/Users/craig/src/LuisaRender")


# ---------------------------------------------------------------------------
# Pixel stats (stdlib only — same discipline as scripts/spike_luisa_scene.py)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PngStats:
    width: int
    height: int
    stddev: float
    min_value: int
    max_value: int
    unique_sample: int

    @property
    def nonblank(self) -> bool:
        return (
            self.stddev > 3.0
            and self.max_value > self.min_value
            and self.unique_sample > 10
        )


def read_png_stats(path: Path) -> PngStats:
    """Decode an 8-bit RGB/RGBA PNG and return enough stats to detect blank frames."""
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"not a PNG: {path}")
    pos = 8
    width = height = bit_depth = color_type = None
    idat: list[bytes] = []
    while pos < len(data):
        size = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        payload = data[pos + 8 : pos + 8 + size]
        pos += 12 + size
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", payload[:10])
        elif chunk_type == b"IDAT":
            idat.append(payload)
        elif chunk_type == b"IEND":
            break
    if bit_depth != 8 or color_type not in (2, 6) or width is None or height is None:
        raise ValueError(
            f"unsupported PNG encoding bit_depth={bit_depth} color_type={color_type}"
        )
    channels = 3 if color_type == 2 else 4
    raw = zlib.decompress(b"".join(idat))
    stride = width * channels
    prior = [0] * stride
    pixels: list[Tuple[int, int, int]] = []
    offset = 0
    for _ in range(height):
        filt = raw[offset]
        offset += 1
        encoded = list(raw[offset : offset + stride])
        offset += stride
        row = [0] * stride
        for i, value in enumerate(encoded):
            left = row[i - channels] if i >= channels else 0
            up = prior[i]
            up_left = prior[i - channels] if i >= channels else 0
            if filt == 0:
                pred = 0
            elif filt == 1:
                pred = left
            elif filt == 2:
                pred = up
            elif filt == 3:
                pred = (left + up) // 2
            elif filt == 4:
                p = left + up - up_left
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - up_left)
                pred = left if pa <= pb and pa <= pc else up if pb <= pc else up_left
            else:
                raise ValueError(f"unsupported PNG filter: {filt}")
            row[i] = (value + pred) & 255
        for i in range(0, stride, channels):
            pixels.append((row[i], row[i + 1], row[i + 2]))
        prior = row
    values = [c for px in pixels for c in px]
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    step = max(1, len(pixels) // 1000)
    return PngStats(
        width=int(width),
        height=int(height),
        stddev=variance ** 0.5,
        min_value=min(values),
        max_value=max(values),
        unique_sample=len(set(pixels[::step])),
    )


# ---------------------------------------------------------------------------
# Backend
# ---------------------------------------------------------------------------

class LuisaBackend(Backend):
    """Offline quality backend driving ``luisa-render-cli -b metal``.

    Parameters are environment-overridable so the same code works on the Mac
    Studio and a future thin client:

    - ``luisa_root``: checkout containing ``build/bin/luisa-render-cli``.
    - ``backend``:    Luisa compute backend (``metal`` on Apple Silicon).
    - ``spp``:        samples per pixel (low for smoke, high for finals).
    - ``resolution``: ``(width, height)``.
    """

    name = "luisa"

    def __init__(
        self,
        *,
        luisa_root: Optional[Path] = None,
        backend: Optional[str] = None,
        spp: Optional[int] = None,
        resolution: Optional[Tuple[int, int]] = None,
        workdir: Optional[Path] = None,
        timeout: int = 300,
        converter_python: Optional[str] = None,
    ) -> None:
        self.luisa_root = Path(
            luisa_root or os.environ.get("LUISA_ROOT", _DEFAULT_LUISA_ROOT)
        )
        self.backend = backend or os.environ.get("LUISA_BACKEND", "metal")
        self.spp = int(spp or os.environ.get("LUISA_SPP", "64"))
        res = resolution or (960, 540)
        env_res = os.environ.get("LUISA_RESOLUTION")
        if env_res and "x" in env_res:
            w, h = env_res.lower().split("x", 1)
            res = (int(w), int(h))
        self.resolution: Tuple[int, int] = res
        self.timeout = timeout
        self.workdir = Path(workdir) if workdir else None
        # EXR→PNG conversion needs cv2+OpenEXR, which the repo .venv lacks but
        # the macOS system python3 has. Default to the system python, not the
        # interpreter running this code (which may be the cv2-less .venv).
        self.converter_python = (
            converter_python
            or os.environ.get("LUISA_CONVERTER_PYTHON")
            or "/usr/bin/python3"
        )

    # -- protocol ----------------------------------------------------------

    def build(self, scene: Mapping[str, Any]) -> Dict[str, Any]:
        """Compile ``canvas.scene.v1`` to a ``.luisa`` file + sidecar OBJs.

        Returns a build manifest describing the emitted artifacts. The heavy
        lifting (CLI run) only happens in ``render_preview`` / ``save_png``.
        """
        built = self._normalise(scene)
        out_dir = self._scene_dir(built)
        out_dir.mkdir(parents=True, exist_ok=True)

        scene_text, sidecars = compile_scene(
            built, spp=self.spp, resolution=self.resolution
        )
        scene_path = out_dir / "scene.luisa"
        scene_path.write_text(scene_text)
        for fname, obj_text in sidecars:
            (out_dir / fname).write_text(obj_text)

        return {
            "ok": True,
            "backend": self.name,
            "scene_id": built.get("scene_id"),
            "workdir": str(out_dir),
            "scene_file": str(scene_path),
            "sidecar_count": len(sidecars),
            "spp": self.spp,
            "resolution": list(self.resolution),
        }

    def render_preview(self, scene: Mapping[str, Any]) -> Dict[str, Any]:
        manifest = self.build(scene)
        if not manifest.get("ok"):
            return manifest
        result = self._render_and_convert(Path(manifest["workdir"]))
        manifest.update(result)
        return manifest

    def save_png(self, scene: Mapping[str, Any], path: Optional[str] = None) -> Dict[str, Any]:
        manifest = self.render_preview(scene)
        if not manifest.get("ok"):
            return manifest
        src_png = Path(manifest["png"])
        if path:
            dest = Path(path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(src_png.read_bytes())
            manifest["saved_png"] = str(dest)
        return manifest

    # -- internals ----------------------------------------------------------

    def _normalise(self, scene: Mapping[str, Any]) -> Mapping[str, Any]:
        ok, errors = validate_scene(scene)
        if not ok:
            raise ValueError(f"LuisaBackend received invalid canvas.scene.v1: {errors}")
        return scene

    def _scene_dir(self, scene: Mapping[str, Any]) -> Path:
        base = self.workdir or Path(tempfile.gettempdir()) / "luisa-backend"
        sid = str(scene.get("scene_id") or "scene")
        safe = "".join(ch if (ch.isalnum() or ch in "_-") else "_" for ch in sid)
        return base / safe

    def _cli(self) -> Path:
        cli = self.luisa_root / "build" / "bin" / "luisa-render-cli"
        if not cli.exists():
            raise FileNotFoundError(
                f"luisa-render-cli not found at {cli}. "
                f"Build hint: cmake --build {self.luisa_root}/build "
                "--target luisa-render-cli -j 4"
            )
        return cli

    def _render_and_convert(self, workdir: Path) -> Dict[str, Any]:
        scene_file = workdir / "scene.luisa"
        exr_path = workdir / "render.exr"
        png_path = workdir / "render.png"
        for p in (exr_path, png_path):
            if p.exists():
                p.unlink()

        proc = subprocess.run(
            [str(self._cli()), "-b", self.backend, str(scene_file)],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )
        if proc.returncode != 0:
            return {
                "ok": False,
                "backend": self.name,
                "error": f"luisa-render-cli exited {proc.returncode}",
                "stderr_tail": (proc.stderr or "")[-2000:],
                "stdout_tail": (proc.stdout or "")[-2000:],
            }
        if not exr_path.exists() or exr_path.stat().st_size <= 1000:
            return {
                "ok": False,
                "backend": self.name,
                "error": f"expected non-trivial EXR at {exr_path}",
            }

        converter = self.luisa_root / "tools" / "hdr2srgb.py"
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env["OPENCV_IO_ENABLE_OPENEXR"] = "1"
        conv = subprocess.run(
            [self.converter_python, str(converter), str(exr_path)],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        if conv.returncode != 0 or not png_path.exists():
            return {
                "ok": False,
                "backend": self.name,
                "error": f"EXR→PNG conversion failed ({conv.returncode})",
                "stderr_tail": (conv.stderr or "")[-2000:],
            }

        stats = read_png_stats(png_path)
        return {
            "ok": True,
            "backend": self.name,
            "supported": True,
            "exr": str(exr_path),
            "png": str(png_path),
            "png_bytes": png_path.stat().st_size,
            "png_stats": {
                "width": stats.width,
                "height": stats.height,
                "stddev": round(stats.stddev, 3),
                "min": stats.min_value,
                "max": stats.max_value,
                "unique_sample": stats.unique_sample,
                "nonblank": stats.nonblank,
            },
            "render_log_tail": (proc.stdout or "")[-1000:],
        }


__all__ = ["LuisaBackend", "PngStats", "read_png_stats"]
