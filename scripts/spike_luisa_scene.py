#!/usr/bin/env python3
"""WP15 LuisaRender QualityBackend smoke spike.

This is intentionally a spike script, not production backend code. It proves the
minimum offline quality-backend path:

    .luisa scene -> luisa-render-cli -b metal -> EXR -> PNG -> pixel stats

The default paths match Craig's local setup, but all paths are configurable so the
script remains useful as LuisaRender moves.
"""

from __future__ import annotations

import argparse
import os
import struct
import subprocess
import sys
import tempfile
import textwrap
import zlib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_LUISA_ROOT = Path("/Users/craig/src/LuisaRender")
DEFAULT_OUTPUT_DIR = Path(tempfile.gettempdir()) / "luisa-smoke"


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
        return self.stddev > 3.0 and self.max_value > self.min_value and self.unique_sample > 10


@dataclass(frozen=True)
class SmokeResult:
    scene_path: Path
    exr_path: Path
    png_path: Path
    stats: PngStats
    render_log_tail: str


def build_scene_text(*, resolution: int, spp: int, exr_name: str) -> str:
    """Return a tiny, deterministic Luisa scene with a lit subject and floor."""
    return textwrap.dedent(
        f"""
        Surface mat_subject : Matte {{
          Kd : Constant {{
            v {{ 0.9, 0.22, 0.08 }}
          }}
        }}

        Surface mat_floor : Matte {{
          Kd : Constant {{
            v {{ 0.45, 0.45, 0.48 }}
          }}
        }}

        Shape subject : InlineMesh {{
          positions {{ -0.7, -0.5, 0, 0.7, -0.5, 0, 0.0, 0.7, 0 }}
          indices {{ 0, 1, 2 }}
          surface {{ @mat_subject }}
        }}

        Shape floor : InlineMesh {{
          positions {{ -2, -0.7, 0.4, 2, -0.7, 0.4, 2, -0.7, -1.8, -2, -0.7, -1.8 }}
          indices {{ 0, 1, 2, 0, 2, 3 }}
          surface {{ @mat_floor }}
        }}

        Shape key_light : InlineMesh {{
          positions {{ -1, 1.8, -1, 1, 1.8, -1, 1, 1.8, 1, -1, 1.8, 1 }}
          indices {{ 0, 1, 2, 0, 2, 3 }}
          surface {{ @mat_floor }}
          light : Diffuse {{
            emission : Constant {{
              v {{ 6, 6, 6 }}
            }}
          }}
        }}

        Camera camera : Pinhole {{
          fov {{ 45 }}
          spp {{ {spp} }}
          filter : Gaussian {{
            radius {{ 1 }}
          }}
          film : Color {{
            resolution {{ {resolution}, {resolution} }}
          }}
          file {{ "{exr_name}" }}
          transform : View {{
            position {{ 0, 0, 3 }}
            front {{ 0, 0, -1 }}
            up {{ 0, 1, 0 }}
          }}
        }}

        render {{
          cameras {{ @camera }}
          integrator : MegaPath {{
            sampler : PMJ02BN {{}}
          }}
          shapes {{
            @subject,
            @floor,
            @key_light
          }}
          environment : Null {{}}
        }}
        """
    ).strip() + "\n"


def resolve_luisa_cli(luisa_root: Path, explicit_cli: Path | None) -> Path:
    cli = explicit_cli or luisa_root / "build" / "bin" / "luisa-render-cli"
    if not cli.exists():
        raise SystemExit(
            f"luisa-render-cli not found at {cli}\n"
            "Build hint:\n"
            f"  cd {luisa_root}\n"
            "  cmake -S . -B build -D CMAKE_BUILD_TYPE=Release \\\n"
            "    -D CMAKE_CXX_FLAGS=\"-I/opt/homebrew/opt/minizip/include/minizip\"\n"
            "  cmake --build build --target luisa-render-cli -j 4"
        )
    return cli


def run_checked(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout)
    if proc.returncode != 0:
        combined = (proc.stdout or "") + (proc.stderr or "")
        raise SystemExit(f"command failed ({proc.returncode}): {' '.join(cmd)}\n{combined[-4000:]}")
    return proc


def render_scene(*, cli: Path, backend: str, scene_path: Path, timeout: int) -> str:
    proc = run_checked([str(cli), "-b", backend, str(scene_path)], cwd=scene_path.parent, timeout=timeout)
    combined = (proc.stdout or "") + (proc.stderr or "")
    return combined[-2000:]


def convert_exr_to_png(*, luisa_root: Path, exr_path: Path, python: str) -> Path:
    converter = luisa_root / "tools" / "hdr2srgb.py"
    if not converter.exists():
        raise SystemExit(f"missing Luisa EXR converter: {converter}")
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["OPENCV_IO_ENABLE_OPENEXR"] = "1"
    run_checked([python, str(converter), str(exr_path)], cwd=exr_path.parent, env=env, timeout=60)
    png_path = exr_path.with_suffix(".png")
    if not png_path.exists():
        raise SystemExit(f"EXR converter did not create {png_path}")
    return png_path


def read_png_stats(path: Path) -> PngStats:
    """Decode enough 8-bit RGB/RGBA PNG to detect blank/flat frames.

    This avoids depending on Pillow/OpenCV inside the octanex-mcp uv environment.
    """
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

    if bit_depth != 8 or color_type not in (2, 6):
        raise ValueError(f"unsupported PNG encoding bit_depth={bit_depth} color_type={color_type}")
    if width is None or height is None:
        raise ValueError(f"PNG missing IHDR size: {path}")
    channels = 3 if color_type == 2 else 4
    raw = zlib.decompress(b"".join(idat))
    stride = width * channels  # type: ignore[operator]
    prior = [0] * stride
    pixels: list[tuple[int, int, int]] = []
    offset = 0

    for _ in range(height):  # type: ignore[arg-type]
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
            pixels.append(tuple(row[i : i + 3]))  # type: ignore[arg-type]
        prior = row

    values = [channel for pixel in pixels for channel in pixel]
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    sample_step = max(1, len(pixels) // 1000)
    return PngStats(
        width=int(width),
        height=int(height),
        stddev=variance**0.5,
        min_value=min(values),
        max_value=max(values),
        unique_sample=len(set(pixels[::sample_step])),
    )


def run_smoke(args: argparse.Namespace) -> SmokeResult:
    luisa_root = args.luisa_root.expanduser().resolve()
    cli = resolve_luisa_cli(luisa_root, args.luisa_cli.expanduser().resolve() if args.luisa_cli else None)
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    scene_path = output_dir / "smoke.luisa"
    exr_path = output_dir / "smoke.exr"
    scene_path.write_text(build_scene_text(resolution=args.resolution, spp=args.spp, exr_name=exr_path.name))

    render_log_tail = render_scene(cli=cli, backend=args.backend, scene_path=scene_path, timeout=args.timeout)
    if not exr_path.exists() or exr_path.stat().st_size <= 1000:
        raise SystemExit(f"expected non-trivial EXR at {exr_path}")

    png_path = convert_exr_to_png(luisa_root=luisa_root, exr_path=exr_path, python=args.python)
    stats = read_png_stats(png_path)
    if not stats.nonblank:
        raise SystemExit(
            "render appears blank/flat: "
            f"stddev={stats.stddev:.3f} min={stats.min_value} max={stats.max_value} unique_sample={stats.unique_sample}"
        )
    return SmokeResult(scene_path=scene_path, exr_path=exr_path, png_path=png_path, stats=stats, render_log_tail=render_log_tail)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--luisa-root", type=Path, default=DEFAULT_LUISA_ROOT)
    parser.add_argument("--luisa-cli", type=Path, default=None, help="Override luisa-render-cli path")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--backend", default="metal")
    parser.add_argument("--resolution", type=int, default=96)
    parser.add_argument("--spp", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--python", default="python3", help="Python with cv2/OpenEXR support for Luisa tools/hdr2srgb.py")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = run_smoke(args)
    stats = result.stats
    print("LUISA_SMOKE_OK")
    print(f"scene={result.scene_path}")
    print(f"exr={result.exr_path} bytes={result.exr_path.stat().st_size}")
    print(f"png={result.png_path} bytes={result.png_path.stat().st_size}")
    print(
        "stats="
        f"{stats.width}x{stats.height} stddev={stats.stddev:.3f} "
        f"min={stats.min_value} max={stats.max_value} unique_sample={stats.unique_sample}"
    )
    print("render_log_tail:")
    print(result.render_log_tail.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
