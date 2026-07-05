#!/usr/bin/env python3
"""Generate a parametric helicoid spiral surface in OBJ and queue it to Octane X."""
from __future__ import annotations

import math
import json
import sys
from pathlib import Path

# Add local src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from octanex_mcp.bridge import Workspace, write_command
from octanex_mcp.schema import validate_command


def helicoid_obj(rows: int = 40, cols: int = 64, radius: float = 1.8, width: float = 1.4, turns: float = 2.0) -> str:
    """Generate an OBJ for a helicoid surface:
    
    x = u * cos(v)
    y = u * sin(v)
    z = k * v        (where k controls twist)
    
    where u ∈ [-width, width] and v ∈ [0, 2π·turns].
    
    Also adds edge rings (rims) at inner and outer radii.
    """
    lines = ["# Parametric helicoid surface", "o helicoid_spiral"]
    
    half_w = width / 2.0
    k = radius / (math.tau * turns)  # twist rate so outer edge = radius
    
    verts: list[tuple[float, float, float]] = []
    
    # Build surface vertices
    for ir in range(rows + 1):
        r = ir / rows  # u parameter from 0..1
        for ic in range(cols + 1):
            v = math.tau * turns * ic / cols  # v parameter from 0..2π·turns
            u = radius * r  # radial parameter
            x = u * math.cos(v)
            y = u * math.sin(v)
            z = k * v - k * math.tau * turns / 2  # center vertically
            # Offset by half-width perpendicular to surface normal for thickness
            verts.append((x, y, z))
    
    # Write vertices
    for x, y, z in verts:
        lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
    
    start = 1
    # Create quads, one per row-cell
    for r in range(rows):
        for c in range(cols):
            a = start + r * (cols + 1) + c
            b = start + r * (cols + 1) + c + 1
            d = start + (r + 1) * (cols + 1) + c
            e = start + (r + 1) * (cols + 1) + c + 1
            lines.append(f"f {a} {b} {e} {d}")
    
    # Outer rim ring (circle at u = radius, z = constant at each turn boundary)
    rim_verts_start = len(verts) + 1
    rim_segments = max(cols, 64)
    for ic in range(rim_segments + 1):
        v = math.tau * ic / rim_segments
        x = radius * math.cos(v)
        y = radius * math.sin(v)
        z = 0.0
        verts.append((x, y, z))
        lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
    
    # Outer ring quad strip (thin ribbon)
    for ic in range(rim_segments):
        a = rim_verts_start + ic
        b = rim_verts_start + ic + 1
        d = rim_verts_start + ic + cols + 1
        e = rim_verts_start + ic + cols + 2
        lines.append(f"f {a} {b} {e} {d}")
    
    # Write material
    lines.append("usemtl helicoid_surface")
    
    return "\n".join(lines) + "\n"


def torus_knot_obj(p: int = 2, q: int = 3, radius: float = 1.2, tube: float = 0.25, steps: int = 200, tube_steps: int = 24) -> str:
    """Generate a torus knot OBJ using the parametric torus knot equations:
    
    x = R*cos(q*t) + r*cos(p*t)*cos(q*t)
    y = R*sin(q*t) + r*cos(p*t)*sin(q*t)
    z = r*sin(p*t)
    
    This creates a beautiful knotted toroidal shape.
    """
    lines = ["# Parametric torus knot", "o torus_knot"]
    
    verts: list[tuple[float, float, float]] = []
    
    R = radius  # major radius
    r = tube    # minor radius
    
    for it in range(steps + 1):
        t = math.tau * it / steps
        for ij in range(tube_steps + 1):
            phi = math.tau * ij / tube_steps
            
            # Torus knot center line
            cx = R * math.cos(q * t) + r * math.cos(p * t)
            cy = R * math.sin(q * t) + r * math.cos(p * t)
            cz = r * math.sin(p * t)
            
            # Tube offset (simplified torus tube cross-section)
            tx = r * math.cos(phi) * math.cos(q * t)
            ty = r * math.cos(phi) * math.sin(q * t)
            tz = r * math.sin(phi)
            
            x = cx + tx
            y = cy + ty
            z = cz + tz
            
            verts.append((x, y, z))
            lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
    
    start = 1
    for it in range(steps):
        for ij in range(tube_steps):
            a = start + it * (tube_steps + 1) + ij
            b = start + it * (tube_steps + 1) + ij + 1
            d = start + (it + 1) * (tube_steps + 1) + ij
            e = start + (it + 1) * (tube_steps + 1) + ij + 1
            lines.append(f"f {a} {b} {e} {d}")
    
    lines.append("usemtl torus_knot_surface")
    return "\n".join(lines) + "\n"


def compute_bounds(vertices: list[tuple[float, float, float]]) -> dict:
    if not vertices:
        return {"center": [0, 0, 0], "radius": 1}
    mins = [min(v[i] for v in vertices) for i in range(3)]
    maxs = [max(v[i] for v in vertices) for i in range(3)]
    center = [(mins[i] + maxs[i]) / 2 for i in range(3)]
    radius = max(math.dist(center, v) for v in vertices) or 1.0
    return {"center": [round(c, 4) for c in center], "radius": round(radius, 4)}


def main():
    workspace = Workspace()
    workspace.ensure()
    assets_dir = workspace.assets_dir
    scripts_dir = Path(__file__).resolve().parent
    
    # Generate the two parametric surfaces
    print("Generating helicoid spiral...")
    helicoid = helicoid_obj(rows=48, cols=80, radius=1.5, width=1.2, turns=2.5)
    helicoid_path = assets_dir / "helicoid_spiral.obj"
    helicoid_path.write_text(helicoid)
    
    print("Generating torus knot (2,3)...")
    torus_knot = torus_knot_obj(p=2, q=3, radius=1.0, tube=0.22, steps=300, tube_steps=32)
    torus_knot_path = assets_dir / "torus_knot.obj"
    torus_knot_path.write_text(torus_knot)
    
    # Verify bounds
    h_lines = helicoid.split("\n")
    h_verts = [(float(l.split()[1]), float(l.split()[2]), float(l.split()[3])) 
               for l in h_lines if l.startswith("v")]
    t_lines = torus_knot.split("\n")
    t_verts = [(float(l.split()[1]), float(l.split()[2]), float(l.split()[3])) 
               for l in t_lines if l.startswith("v")]
    
    h_bounds = compute_bounds(h_verts)
    t_bounds = compute_bounds(t_verts)
    
    print(f"  Helicoid bounds: center={h_bounds['center']}, radius={h_bounds['radius']}")
    print(f"  Torus knot bounds: center={t_bounds['center']}, radius={t_bounds['radius']}")
    
    # --- Queue commands ---
    import os
    
    def queue(op, payload):
        """Queue with schema validation."""
        cmd = {
            "schema_version": "2.0",
            "op": op,
            "payload": payload or {},
            "created_at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "octanex-mcp-generate",
        }
        # Validate
        from octanex_mcp.schema import validate_command
        v = validate_command(cmd)
        if not v.ok:
            print(f"VALIDATION WARNING: {v.errors}")
        
        return write_command(op, payload)
    
    print("\nClearing scene (flush node tree)...")
    # We need to import geometry into specific named objects.
    # First, clear existing geometry by using the scene import pattern.
    
    print("\n=== QUEING SCENE COMMANDS ===\n")
    
    # 1. Import helicoid
    print("1. Importing helicoid surface...")
    queue("import_geometry", {
        "path": str(helicoid_path),
        "format": "obj",
        "name": "helicoid_spiral",
    })
    
    # 2. Create material for helicoid (iridescent blue-purple)
    print("2. Creating helicoid material...")
    queue("create_material", {
        "name": "helicoid_mat",
        "kind": "glossy",
        "color": [0.1, 0.4, 1.0],
        "roughness": 0.15,
        "metallic": 0.3,
    })
    queue("assign_material", {
        "object_name": "helicoid_spiral",
        "material_name": "helicoid_mat",
    })
    
    # 3. Import torus knot
    print("3. Importing torus knot...")
    queue("import_geometry", {
        "path": str(torus_knot_path),
        "format": "obj",
        "name": "torus_knot_2_3",
    })
    
    # 4. Create material for torus knot (warm gold-orange)
    print("4. Creating torus knot material...")
    queue("create_material", {
        "name": "torus_knot_mat",
        "kind": "metallic",
        "color": [1.0, 0.65, 0.15],
        "roughness": 0.12,
        "metallic": 1.0,
    })
    queue("assign_material", {
        "object_name": "torus_knot_2_3",
        "material_name": "torus_knot_mat",
    })
    
    # 5. Set camera — angled elevated view of both objects
    print("5. Setting camera...")
    queue("set_camera", {
        "position": [4.5, 3.5, 5.0],
        "target": [0.0, 0.0, 0.0],
        "fov": 50,
    })
    
    # 6. Set lighting
    print("6. Setting lighting...")
    queue("set_lighting", {
        "preset": "soft_studio",
    })
    
    # 7. Start render
    print("7. Starting render (512 samples)...")
    queue("start_render", {
        "samples": 512,
        "width": 1280,
        "height": 1280,
    })
    
    print("\n✅ All commands queued! Run the persistent bridge in Octane X to render.")
    print(f"   Workspace: {workspace.root}")
    print(f"   Helicoid OBJ: {helicoid_path}")
    print(f"   Torus knot OBJ: {torus_knot_path}")


if __name__ == "__main__":
    main()
