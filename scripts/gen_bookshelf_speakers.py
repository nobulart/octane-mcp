#!/usr/bin/env python3
"""Generate a pair of bookshelf speakers as a combined Octane-visible OBJ.

Design notes (matches the proven-visible path used by octane_visualize_bars):
  * One combined OBJ (single `o` object, many `usemtl` groups) so it maps to ONE
    mesh node in the Octane scene graph. Imported OBJs bind a material per
    `usemtl` group via assign_material(group_index) -- the per-group material
    pin works; binding to the whole mesh does not faithfully colour a combined
    subject on this Octane build.
  * Each speaker = cabinet (box) + woofer cone (cylinder) + tweeter dome
    (ellipsoid) + trim ring (thin cylinder). Two speakers -> 8 groups.
  * After writing the OBJ, the script queues the full command sequence through
    the project's write_command() (so it lands in the container queue the
    oneshot bridge drains): import -> 8x create_material -> 8x assign_material
    (group_index) -> set_camera (framed from bounds) -> set_lighting
    (soft_studio) -> save_preview. No standalone start_render (save_preview
    restarts + renders + saves inline).

Usage:
    PYTHONPATH= uv run python scripts/gen_bookshelf_speakers.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from octanex_mcp.bridge import Workspace, write_command  # noqa: E402
from octanex_mcp.visuals import ObjBuilder, camera_for_bounds  # noqa: E402

OUT = Path.home() / "Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/assets/bookshelf_speakers.obj"
OBJECT_NAME = "bookshelf_speakers"

# speaker cabinet footprint (decimetre-ish units)
CAB_W, CAB_H, CAB_D = 2.2, 4.0, 2.6
SPACING = 5.2  # center-to-center along X (pair sits side by side)

MATERIALS: dict[str, dict] = {
    # walnut cabinet (warm wood, semi-gloss)
    "mat_cabinet": {"kind": "glossy", "color": [0.33, 0.18, 0.10], "roughness": 0.45},
    # woofer paper cone (near-black, matte)
    "mat_cone": {"kind": "glossy", "color": [0.07, 0.07, 0.08], "roughness": 0.6},
    # tweeter dome (brushed aluminium)
    "mat_dome": {"kind": "metallic", "color": [0.82, 0.84, 0.87], "roughness": 0.28},
    # trim ring (matte black plastic)
    "mat_trim": {"kind": "glossy", "color": [0.04, 0.04, 0.05], "roughness": 0.5},
}


def add_speaker(b: ObjBuilder, *, cx: float, side: str) -> None:
    cab_mat = f"mat_cabinet_{side}"
    cone_mat = f"mat_cone_{side}"
    dome_mat = f"mat_dome_{side}"
    trim_mat = f"mat_trim_{side}"

    # cabinet (sits on the floor: y center = CAB_H/2)
    b.add_box(center=(cx, CAB_H / 2.0, 0.0), size=(CAB_W, CAB_H, CAB_D), material=cab_mat)

    front_z = CAB_D / 2.0  # +1.3
    # woofer: lower third, protrudes slightly
    b.add_cylinder(
        center=(cx, 1.5, front_z - 0.10),
        radius=0.72, height=0.24, segments=48, material=cone_mat,
    )
    # trim ring around the woofer (thin disc, just behind the cone front)
    b.add_cylinder(
        center=(cx, 1.5, front_z - 0.14),
        radius=0.84, height=0.08, segments=48, material=trim_mat,
    )
    # tweeter dome: upper area
    b.add_ellipsoid(
        center=(cx, 3.05, front_z + 0.02),
        radii=(0.34, 0.34, 0.22), segments_u=40, segments_v=22, material=dome_mat,
    )
    # small trim ring around the tweeter
    b.add_cylinder(
        center=(cx, 3.05, front_z - 0.04),
        radius=0.42, height=0.06, segments=36, material=trim_mat,
    )


def main() -> int:
    b = ObjBuilder(OBJECT_NAME)
    # group order = cabinet_l, cone_l, dome_l, trim_l, cabinet_r, cone_r, dome_r, trim_r
    add_speaker(b, cx=-SPACING / 2.0, side="l")
    add_speaker(b, cx=+SPACING / 2.0, side="r")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OBJ_TEXT = b.text()
    OUT.write_text(OBJ_TEXT, encoding="utf-8")

    # validate face indices are in range
    verts = [ln for ln in OBJ_TEXT.splitlines() if ln.startswith("v ")]
    vcount = len(verts)
    max_idx = 0
    for ln in OBJ_TEXT.splitlines():
        if ln.startswith("f "):
            for tok in ln.split()[1:]:
                max_idx = max(max_idx, int(tok.split("/")[0]))
    if max_idx > vcount:
        print(f"OBJ INVALID: max face index {max_idx} > vertex count {vcount}")
        return 1
    print(f"wrote {OUT} ({vcount} verts; face-index max {max_idx} ok)")

    bounds = b.bounds()
    camera = camera_for_bounds(bounds, view="iso", margin=1.5, fov=42.0)
    print(f"bounds={bounds}")
    print(f"camera={camera}")

    # queue the full scene
    ws = Workspace()
    ws.ensure()
    preview_path = ws.renders_dir / "bookshelf_speakers_octane-preview.png"

    write_command("import_geometry", {"path": str(OUT), "format": "obj", "name": OBJECT_NAME})

    # groups in first-appearance order
    groups: list[str] = []
    for ln in OBJ_TEXT.splitlines():
        if ln.startswith("usemtl "):
            g = ln.split()[1]
            if g not in groups:
                groups.append(g)

    for g in groups:
        spec = MATERIALS.get(g.rsplit("_", 1)[0], {"kind": "diffuse", "color": [0.8, 0.8, 0.8]})
        payload = {"name": g, "kind": spec["kind"], "color": spec["color"]}
        if "roughness" in spec:
            payload["roughness"] = spec["roughness"]
        write_command("create_material", payload)

    for idx, g in enumerate(groups, start=1):
        write_command(
            "assign_material",
            {"object_name": OBJECT_NAME, "material_name": g, "group_index": idx},
        )

    write_command("set_camera", camera)
    write_command("set_lighting", {"preset": "soft_studio"})
    write_command(
        "save_preview",
        {
            "path": str(preview_path),
            "width": 1280,
            "height": 1280,
            "quality": "standard",
            "samples": 96,
            "min_samples": 32,
            "timeout_seconds": 90,
        },
    )
    print(f"queued {2 + 2 * len(groups)} commands (import + {len(groups)}x create + "
          f"{len(groups)}x assign + camera + lighting + save_preview)")
    print(f"preview -> {preview_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
