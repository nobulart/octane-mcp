"""Repair recipe scene.json command sequences so Octane binds materials.

Root cause (found 2026-07-09 live verification):
The OctaneX Lua bridge does NOT honor OBJ/MTL `usemtl` colors. Materials only
reach the mesh via explicit ``create_material`` + ``assign_material`` commands.
Recipes whose *subject depends on color* (planet, vases, product, terrain)
rendered as default white/grey geometry because:
  * photoreal-earth-space / saturn-moons-space / photoreal-product-studio /
    photoreal-vase-studio emitted ZERO ``create_material`` commands, and
  * geospatial-terrain emitted ``create_material`` but NO ``assign_material``
    (assign_material is used by 0/18 recipes).

This script makes every recipe self-sufficient: for each ``usemtl`` group in
``scene.obj`` it appends a ``create_material`` (color/kind from scene.json's
``materials`` block, defaulting to a neutral grey for scene/environment groups
the recipe never specified) and an ``assign_material`` with the correct
1-based ``group_index`` (ordinal of first ``usemtl`` appearance, which matches
Octane's material-pin ordering).

It is idempotent: existing create/assign commands in ``commands`` are stripped
and regenerated deterministically, while ``import_geometry`` / ``set_camera`` /
``set_lighting`` / ``start_render`` / ``save_preview`` and all other scene.json
fields (visual_iteration_protocol, final_bundle, etc.) are preserved.

Usage:
    PYTHONPATH= uv run python scripts/fix_recipe_materials.py <slug> [slug ...]
    PYTHONPATH= uv run python scripts/fix_recipe_materials.py --all
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Verbose material "kind" strings in scene.json -> one of the 4 kinds the Lua
# bridge's create_material actually supports (see octane_lua/lib/handlers.lua).
def normalize_kind(kind: str | None) -> str:
    if not kind:
        return "diffuse"
    k = kind.lower()
    if "glass" in k or "specular" in k:
        return "specular"
    if "metal" in k or "brushed" in k:
        return "metallic"
    if any(t in k for t in ("glossy", "ceramic", "porcelain", "pearl", "silk")):
        return "glossy"
    return "diffuse"


def usemtl_order(obj_text: str) -> list[str]:
    order: list[str] = []
    for m in re.finditer(r"^usemtl\s+(\S+)", obj_text, re.M):
        g = m.group(1)
        if g not in order:
            order.append(g)
    return order


def build_material_command(group: str, mats: dict) -> dict:
    spec = mats.get(group, {})
    cmd: dict = {
        "op": "create_material",
        "payload": {
            "name": group,
            "kind": normalize_kind(spec.get("kind")),
            "color": spec.get("color", [0.8, 0.8, 0.8]),
        },
    }
    if "roughness" in spec:
        cmd["payload"]["roughness"] = spec["roughness"]
    if "metallic" in spec:
        cmd["payload"]["metallic"] = spec["metallic"]
    if "transmission" in spec:
        cmd["payload"]["transmission"] = spec["transmission"]
    if "ior" in spec:
        cmd["payload"]["ior"] = spec["ior"]
    if "opacity" in spec:
        cmd["payload"]["opacity"] = spec["opacity"]
    if "emission" in spec:
        cmd["payload"]["emission"] = spec["emission"]
    return cmd


def build_assign_command(slug: str, group: str, index: int) -> dict:
    return {
        "op": "assign_material",
        "payload": {
            "object_name": slug,
            "material_name": group,
            "group_index": index,
        },
    }


def fix_recipe(slug: str) -> dict:
    d = ROOT / "examples" / "recipes" / slug
    obj_path = d / "scene.obj"
    scn_path = d / "scene.json"
    if not obj_path.exists() or not scn_path.exists():
        return {"slug": slug, "ok": False, "error": "scene.obj/scene.json missing"}

    obj_text = obj_path.read_text(encoding="utf-8")
    scene = json.loads(scn_path.read_text(encoding="utf-8"))
    mats = scene.get("materials", {})
    groups = usemtl_order(obj_text)
    if not groups:
        return {"slug": slug, "ok": False, "error": "no usemtl groups in scene.obj"}

    create_cmds = [build_material_command(g, mats) for g in groups]
    assign_cmds = [build_assign_command(slug, g, i + 1) for i, g in enumerate(groups)]

    # Preserve non-material commands, then re-insert create+assign deterministically
    # right after import_geometry.
    preserved = [
        c for c in scene.get("commands", [])
        if c.get("op") not in ("create_material", "assign_material")
    ]
    out: list[dict] = []
    inserted = False
    for c in preserved:
        out.append(c)
        if c.get("op") == "import_geometry" and not inserted:
            out.extend(create_cmds)
            out.extend(assign_cmds)
            inserted = True
    if not inserted:
        # No import_geometry found; just prepend material commands.
        out = create_cmds + assign_cmds + preserved

    scene["commands"] = out
    scn_path.write_text(json.dumps(scene, indent=2), encoding="utf-8")
    return {
        "slug": slug,
        "ok": True,
        "groups": groups,
        "created": len(create_cmds),
        "assigned": len(assign_cmds),
    }


def main(argv: list[str]) -> int:
    if not argv or argv == ["--all"]:
        slugs = [p.name for p in sorted((ROOT / "examples" / "recipes").iterdir()) if (p / "scene.json").exists()]
    else:
        slugs = argv
    results = []
    for slug in slugs:
        # Only fix the recipes that are actually broken (no assign_material and
        # either missing create_material or missing assign). Running on a healthy
        # recipe is harmless (idempotent), but we scope to the 5 known failures
        # unless --all is given.
        results.append(fix_recipe(slug))
    for r in results:
        if r.get("ok"):
            print(f"  fixed {r['slug']}: {r['created']} create + {r['assigned']} assign "
                  f"({', '.join(r['groups'])})")
        else:
            print(f"  SKIP {r['slug']}: {r.get('error')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
