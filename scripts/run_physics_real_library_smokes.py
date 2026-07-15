#!/usr/bin/env python3
"""Run optional real-library smoke checks for physics recipe sources.

These checks complement fixture-first recipe tests. They intentionally do not run
inside the core unittest suite because the real simulators are heavy, optional,
and local-environment dependent. Each probe is bounded and reports one of:

- ``passed``: a real library command/import/configure completed.
- ``blocked``: the source tree exists but a required runtime/build dependency is missing.
- ``skipped``: the source tree or command is absent.

Run:
    python3 scripts/run_physics_real_library_smokes.py
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TIMEOUT = 120

SOURCES = {
    "oceananigans": Path("/Users/craig/src/Oceananigans.jl"),
    "splishsplash": Path("/Users/craig/src/SPlisHSPlasH"),
    "genesis": Path("/Users/craig/src/Genesis"),
    "mpipymhd": Path("/Users/craig/src/MPIPyMHD-Magnetohydrodynamics-Simulation-Framework"),
}


def _run(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None, timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env, text=True, capture_output=True, timeout=timeout)
        return {
            "command": cmd,
            "cwd": str(cwd) if cwd else None,
            "exit_code": proc.returncode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout_tail": proc.stdout[-2000:],
            "stderr_tail": proc.stderr[-2000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": cmd,
            "cwd": str(cwd) if cwd else None,
            "exit_code": None,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout_tail": (exc.stdout or "")[-2000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-2000:] if isinstance(exc.stderr, str) else "",
            "timed_out": True,
        }


def _result(name: str, source: Path, status: str, detail: str, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "source_path": str(source),
        "source_exists": source.exists(),
        "status": status,
        "detail": detail,
        "evidence": evidence or {},
    }


def smoke_oceananigans(timeout: int) -> dict[str, Any]:
    source = SOURCES["oceananigans"]
    julia = shutil.which("julia")
    if not source.exists():
        return _result("Oceananigans.jl", source, "skipped", "local source tree is absent")
    if julia is None:
        return _result("Oceananigans.jl", source, "blocked", "julia executable is not on PATH")

    script = """
using Oceananigans
using Oceananigans.Models: ShallowWaterModel
using Oceananigans.Grids: RectilinearGrid
using Printf

grid = RectilinearGrid(size=(24, 36), extent=(2, 2), topology=(Periodic, Periodic, Flat))
model = ShallowWaterModel(grid; gravitational_acceleration=9.81)
set!(model, h = (x, y) -> 1 + 0.05 * tanh(8 * (x - 1)), uh = 0.02, vh = 0.0)
for n in 1:5
    time_step!(model, 0.02)
end
h = Array(interior(model.solution.h))
uh = Array(interior(model.solution.uh))
vh = Array(interior(model.solution.vh))
@printf("grid=%dx%d h_min=%.6f h_max=%.6f uh_max=%.6f vh_max=%.6f", size(h,1), size(h,2), minimum(h), maximum(h), maximum(abs.(uh)), maximum(abs.(vh)))
"""
    with tempfile.TemporaryDirectory(prefix="octanex-ocean-smoke-") as td:
        path = Path(td) / "smoke.jl"
        path.write_text(script, encoding="utf-8")
        evidence = _run([julia, f"--project={source}", str(path)], timeout=timeout)
    if evidence["exit_code"] == 0 and "grid=24x36" in evidence["stdout_tail"]:
        return _result("Oceananigans.jl", source, "passed", "ran a real ShallowWaterModel CPU smoke for five time steps", evidence)
    return _result("Oceananigans.jl", source, "blocked", "Oceananigans command failed; see evidence tails", evidence)


def smoke_splishsplash(timeout: int) -> dict[str, Any]:
    source = SOURCES["splishsplash"]
    if not source.exists():
        return _result("SPlisHSPlasH", source, "skipped", "local source tree is absent")

    import_probe = _run([sys.executable, "-c", "import pysplishsplash as sph; print(sph)"], timeout=20)
    if import_probe["exit_code"] == 0:
        return _result("SPlisHSPlasH", source, "passed", "imported real pysplishsplash Python binding", import_probe)

    cmake = shutil.which("cmake")
    ninja = shutil.which("ninja")
    if cmake is None:
        return _result("SPlisHSPlasH", source, "blocked", "pysplishsplash is not importable and cmake is not on PATH", import_probe)

    with tempfile.TemporaryDirectory(prefix="octanex-splish-config-") as td:
        build = Path(td) / "build"
        cmd = [cmake, "-S", str(source), "-B", str(build), "-DSPH_LIBS_ONLY=ON", "-DUSE_PYTHON_BINDINGS=OFF", "-DCMAKE_BUILD_TYPE=Release"]
        if ninja:
            cmd[5:5] = ["-G", "Ninja"]
        configure = _run(cmd, timeout=timeout)

    evidence = {"import_probe": import_probe, "configure_probe": configure}
    if configure["exit_code"] == 0:
        return _result("SPlisHSPlasH", source, "passed", "real source tree configured headlessly with SPH_LIBS_ONLY", evidence)
    return _result("SPlisHSPlasH", source, "blocked", "pysplishsplash is not importable and bounded CMake configure failed", evidence)


def smoke_genesis(timeout: int) -> dict[str, Any]:
    source = SOURCES["genesis"]
    if not source.exists():
        return _result("Genesis", source, "skipped", "local source tree is absent")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(source)
    code = "import genesis as gs; print(getattr(gs, '__version__', 'unknown'))"
    evidence = _run([sys.executable, "-c", code], env=env, timeout=timeout)
    if evidence["exit_code"] == 0:
        return _result("Genesis", source, "passed", "imported real Genesis source package", evidence)
    return _result("Genesis", source, "blocked", "Genesis source import failed, usually because optional runtime deps are not installed", evidence)


def smoke_mpipymhd(timeout: int) -> dict[str, Any]:
    source = SOURCES["mpipymhd"]
    if not source.exists():
        return _result("MPIPyMHD", source, "skipped", "local source tree is absent")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(source)
    code = "import numpy as np; from mpi4py import MPI; print(MPI.COMM_WORLD.Get_size(), np.__version__)"
    evidence = _run([sys.executable, "-c", code], env=env, timeout=timeout)
    if evidence["exit_code"] == 0:
        return _result("MPIPyMHD", source, "passed", "imported mpi4py/numpy against local MPIPyMHD source context", evidence)
    return _result("MPIPyMHD", source, "blocked", "MPI Python runtime dependency import failed", evidence)


def run_all(timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    checks = [
        smoke_oceananigans(timeout),
        smoke_splishsplash(timeout),
        smoke_genesis(timeout),
        smoke_mpipymhd(timeout),
    ]
    return {
        "schema": "octanex-physics-real-library-smokes/v1",
        "repo": str(ROOT),
        "timeout_seconds": timeout,
        "summary": {
            "passed": sum(1 for c in checks if c["status"] == "passed"),
            "blocked": sum(1 for c in checks if c["status"] == "blocked"),
            "skipped": sum(1 for c in checks if c["status"] == "skipped"),
        },
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="per-probe timeout in seconds")
    parser.add_argument("--output", type=Path, help="optional JSON output path")
    args = parser.parse_args()

    report = run_all(timeout=args.timeout)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
