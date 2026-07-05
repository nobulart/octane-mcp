#!/usr/bin/env python3
"""Generate Earth + Moon OBJ/MTL scene for Octane X MCP rendering."""

import math
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Scale: we work in arbitrary 3D units. Earth radius = 1.0, Moon orbital distance = ~60x
# For rendering, this makes both bodies visible in a single camera view.
EARTH_RADIUS = 1.0
MOON_RADIUS = 1.0 / 3.67  # ~0.2725
MOON_DISTANCE = 60.0       # scaled orbital distance (proportional to real ~60x)

def generate_sphere(obj_path, mtl_path, name, radius, pos, color, roughness=0.15, specular=0.5):
    """Generate a subdivided sphere OBJ with UVs."""
    lines = []
    lines.append(f"# {name}")
    lines.append(f"mtllib {os.path.basename(mtl_path)}")
    lines.append(f"o {name}")
    
    # Subdivisions for sphere (detail level)
    u_seg = 64
    v_seg = 32
    
    # Generate vertices
    vertices = []
    uvs = []
    
    for v in range(v_seg + 1):
        theta = math.pi * v / v_seg
        sin_theta = math.sin(theta)
        cos_theta = math.cos(theta)
        for u in range(u_seg + 1):
            phi = 2 * math.pi * u / u_seg
            x = radius * sin_theta * math.cos(phi) + pos[0]
            y = radius * sin_theta * math.sin(phi) + pos[1]
            z = radius * cos_theta + pos[2]
            vertices.append((x, y, z))
            uvs.append((u / u_seg, v / v_seg))
    
    # Write vertices and UVs
    for i, (vx, vy, vz) in enumerate(vertices):
        lines.append(f"v {vx:.6f} {vy:.6f} {vz:.6f}")
    for uv in uvs:
        lines.append(f"vt {uv[0]:.6f} {uv[1]:.6f}")
    
    # Write faces (triangle strip)
    face_idx = 0
    for v in range(v_seg):
        for u in range(u_seg):
            a = v * (u_seg + 1) + u
            b = a + 1
            c = (v + 1) * (u_seg + 1) + u
            d = c + 1
            # Two triangles
            lines.append(f"usemtl {name}_surface")
            lines.append(f"f {a+1}//{a+1} {b+1}//{b+1} {c+1}//{c+1}")
            lines.append(f"f {b+1}//{b+1} {d+1}//{d+1} {c+1}//{c+1}")
            face_idx += 2
    
    with open(obj_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    
    # Write MTL
    r, g, b = color
    mtlines = []
    mtlines.append(f"# {name} material")
    mtlines.append(f"newmtl {name}_surface")
    mtlines.append(f"Ka 1.0 1.0 1.0")  # ambient
    mtlines.append(f"Kd {r*0.3:.4f} {g*0.3:.4f} {b*0.3:.4f}")  # diffuse
    mtlines.append(f"Ks {specular:.4f} {specular:.4f} {specular:.4f}")  # specular
    mtlines.append(f"Ns {(1-roughness)*64:.1f}")  # shininess
    mtlines.append(f"d 1.0")
    
    with open(mtl_path, 'w') as f:
        f.write('\n'.join(mtlines) + '\n')

def main():
    base = OUTPUT_DIR
    
    # Earth - slightly blue-green (simplified, real Earth would need texture maps)
    # Using a blue-green color for now - real texture would need image maps
    earth_color = (0.1, 0.3, 0.6)  # blue ocean base
    generate_sphere(
        f"{base}/earth.obj", os.path.join(base, "earth.mtl"),
        "earth", EARTH_RADIUS, [0.0, 0.0, 0.0],
        earth_color, roughness=0.08, specular=0.7
    )
    
    # Moon - gray, rough, no specular
    moon_color = (0.65, 0.65, 0.63)  # lunar gray
    generate_sphere(
        f"{base}/moon.obj", os.path.join(base, "moon.mtl"),
        "moon", MOON_RADIUS, [MOON_DISTANCE, 5.0, 0.0],
        moon_color, roughness=0.8, specular=0.05
    )
    
    print(f"Generated: {base}/earth.obj, {base}/earth.mtl")
    print(f"Generated: {base}/moon.obj, {base}/moon.mtl")
    print(f"Earth radius: {EARTH_RADIUS}, Moon radius: {MOON_RADIUS}")
    print(f"Earth-Moon distance: {MOON_DISTANCE} (scaled)")

if __name__ == '__main__':
    main()
