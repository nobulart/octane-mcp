#!/usr/bin/env python3
"""Generate the Genesis `cloth-on-rigid` fixture (Phase B5).

The fixture is a deterministic, committed snapshot of a cloth sheet draping over
a moving rigid body. It follows the same fixture-first boundary as the other
Phase B adapters (mhd-orszag-tang-vortex, oceananigans-shallow-water-front,
dam-break-splash): no runtime Genesis dependency is required to BUILD or TEST the
recipe; the committed fixture is the boundary.

Provenance records the exact Genesis call sequence used to regenerate the fixture
from a real simulation (run inside the Genesis `.venv` with PYTHONPATH stripped),
so the adapter is honest about being fixture-first until the local Genesis source
exposes a stable cloth/rigid entity API.

Run:
    PYTHONPATH=scripts:. uv run python scripts/export_genesis_cloth_on_rigid_fixture.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "examples" / "fixtures" / "genesis" / "cloth-on-rigid"
FIXTURE_FILE = "cloth-on-rigid.json"

# Deterministic cloth grid: NxN vertices, draped over a rigid sphere that
# translates along +x. Cloth sags under gravity; vertices near the sphere
# contact point are pinned to the surface (contact markers).
N = 24
CLOTH_HALF = 3.0          # cloth spans [-3, 3] in x and y
SPHERE_CENTER0 = (-1.0, 0.0, 1.0)
SPHERE_R = 1.0
SPHERE_DX = 2.0           # rigid body translates +x by this over the sim
CLOTH_Z0 = 1.7            # cloth starts just above the sphere top (z=2.0) so it drapes over


def _genesis_regen_script() -> str:
    """Exact Genesis call sequence to regenerate this fixture from a real sim.

    Documented (not executed here) because the local Genesis build does not yet
    expose a stable CLOTH/RIGID entity surface in its Python API; the fixture is
    the committed boundary so the recipe builds/tests without a GPU solve.
    """
    return (
        "import genesis as gs\n"
        "gs.init(backend=gs.cpu, logging_level='error')\n"
        "scene = gs.Scene(show_viewer=False)\n"
        "rigid = scene.add_entity(\n"
        "    gs.RIGID,  # when available\n"
        "    morph=gs.morphs.Sphere(pos=SPHERE_CENTER0, radius=SPHERE_R),\n"
        "    surface=gs.surfaces.Sphere(),\n"
        ")\n"
        "cloth = scene.add_entity(\n"
        "    gs.CLOTH,  # when available\n"
        "    morph=gs.morphs.Surface(\n"
        "        mesh=gs.Mesh(verts=initial_verts, faces=initial_faces),\n"
        "        pos=(0, 0, 2.4),\n"
        "    ),\n"
        "    material=gs.materials.Cloth(),\n"
        ")\n"
        "scene.build()\n"
        "for i in range(steps):\n"
        "    rigid.set_pos(SPHERE_CENTER0 + (i/steps)*SPHERE_DX, 0, 0)\n"
        "    scene.step()\n"
        "    # sample cloth verts + rigid transform + contact markers -> fixture\n"
    )


def _build_fixture(steps: int = 12) -> dict:
    from genesis_cloth_drape import build_draped_vertices, contact_indices

    cloth_z0 = CLOTH_Z0
    # Rigid body final transform (translate +x by SPHERE_DX)
    sphere_center = [SPHERE_CENTER0[0] + SPHERE_DX, SPHERE_CENTER0[1], SPHERE_CENTER0[2]]
    # Draped cloth vertices (single source of truth shared with the recipe renderer)
    verts = build_draped_vertices(N, CLOTH_HALF, cloth_z0, sphere_center, SPHERE_R)
    contact = contact_indices(verts, sphere_center, SPHERE_R)
    return {
        "schema": "octanex-genesis-cloth-on-rigid/v1",
        "grid": [N, N],
        "cloth_half_extent": CLOTH_HALF,
        "cloth_z0": cloth_z0,
        "sphere": {"center0": list(SPHERE_CENTER0), "center": sphere_center, "radius": SPHERE_R},
        "rigid_displacement": [SPHERE_DX, 0.0, 0.0],
        "steps": steps,
        "vertices": verts,
        "contact_vertex_indices": contact,
        "contact_count": len(contact),
    }


def _sha256_of(obj: dict) -> str:
    import hashlib

    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode("utf-8")).hexdigest()


def main_to(out_path: Path) -> dict:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fixture = _build_fixture()
    fixture["fixture_sha256"] = _sha256_of(fixture)
    fixture["regeneration"] = _genesis_regen_script()
    provenance = {
        "schema": fixture["schema"],
        "source_library": "Genesis",
        "source_path": "/Users/craig/src/Genesis",
        "generator": "scripts/export_genesis_cloth_on_rigid_fixture.py",
        "fixture": f"examples/fixtures/genesis/cloth-on-rigid/{FIXTURE_FILE}",
        "fixture_sha256": fixture["fixture_sha256"],
        "physical_variables": ["cloth_vertex_positions", "rigid_body_transform", "contact_markers"],
        "units": {"length": "scene units", "time": "steps"},
        "null_model": "flat cloth sheet at rest; rigid sphere absent",
        "limitations": [
            "fixture is a deterministic analytic drape snapshot, not a real Genesis cloth solve",
            "local Genesis build does not yet expose a stable CLOTH/RIGID Python entity API; "
            "regeneration script documents the call sequence for when it does",
        ],
        "model": "analytic drape (fixture-first boundary; real Genesis sim regenerates the fixture)",
    }
    out_path.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    sidecar = {
        "source_library": "Genesis",
        "source_path": "/Users/craig/src/Genesis",
        "fixture": f"examples/fixtures/genesis/cloth-on-rigid/{FIXTURE_FILE}",
        "fixture_sha256": fixture["fixture_sha256"],
        "physical_variables": provenance["physical_variables"],
        "units": provenance["units"],
        "null_model": provenance["null_model"],
        "limitations": provenance["limitations"],
        "model": provenance["model"],
    }
    sidecar_path = out_path.with_suffix(".prov.json")
    sidecar_path.write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")
    return {"fixture": str(out_path), "grid": fixture["grid"], "contact_count": fixture["contact_count"], "vertices": len(fixture["vertices"]), "sha256": fixture["fixture_sha256"][:16], "fixture_sha256": fixture["fixture_sha256"]}


def main() -> dict:
    return main_to(FIXTURE_DIR / FIXTURE_FILE)


if __name__ == "__main__":
    import sys

    print(json.dumps(main(), indent=2))
