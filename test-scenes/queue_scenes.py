"""Generate test scenes and queue commands to the Octane MCP bridge."""
from pathlib import Path
import json

OUT_DIR = Path('test-scenes')
OUT_DIR.mkdir(exist_ok=True)

from octanex_mcp.bridge import write_command

def queue(op, payload):
    """Queue a command through the bridge."""
    cmd = {
        'schema_version': '2.0',
        'op': op,
        'payload': payload or {},
        'created_at': str(OUT_DIR),
        'source': 'test-viz',
    }
    write_command(op, payload)
    return cmd


# ---------- Scene 1: BOX (blue glossy) ----------
print('Scene 1: BOX - Blue glossy')

box_obj_path = OUT_DIR / 'box.obj'
queue('import_geometry', {'path': str(box_obj_path), 'format': 'obj', 'name': 'box'})
queue('create_material', {'name': 'box_material', 'kind': 'glossy', 'color': [0.1, 0.1, 1.0], 'roughness': 0.3})
queue('assign_material', {'object_name': 'box', 'material_name': 'box_material'})
queue('set_camera', {'position': [3.0, 3.0, 4.0], 'target': [0.0, 0.0, 0.0], 'fov': 45})
queue('set_lighting', {'preset': 'soft_studio'})
queue('start_render', {'samples': 256, 'width': 1280, 'height': 1280})
queue('save_preview', {'path': str(OUT_DIR / 'preview-box.png'), 'width': 1280, 'height': 1280})
print(f'  Queued 7 commands for BOX')
print(f'  OBJ: {box_obj_path.stat().st_size} bytes')


# ---------- Scene 2: PYRAMID (gold) ----------
print('\nScene 2: PYRAMID - Gold')

pyramid_obj_path = OUT_DIR / 'pyramid.obj'
queue('import_geometry', {'path': str(pyramid_obj_path), 'format': 'obj', 'name': 'pyramid'})
queue('create_material', {'name': 'pyramid_material', 'kind': 'gold', 'color': [1.0, 0.8, 0.1], 'roughness': 0.15})
queue('assign_material', {'object_name': 'pyramid', 'material_name': 'pyramid_material'})
queue('set_camera', {'position': [2.0, 4.0, 3.0], 'target': [0.0, 1.5, 0.0], 'fov': 60})
queue('set_lighting', {'preset': 'soft_studio'})
queue('start_render', {'samples': 256, 'width': 1280, 'height': 1280})
queue('save_preview', {'path': str(OUT_DIR / 'preview-pyramid.png'), 'width': 1280, 'height': 1280})
print(f'  Queued 7 commands for PYRAMID')
print(f'  OBJ: {pyramid_obj_path.stat().st_size} bytes')


# ---------- Scene 3: TORUS (green) ----------
print('\nScene 3: TORUS - Green')

from octanex_mcp.visuals import ObjBuilder

torus_builder = ObjBuilder('torus')
torus_builder.add_ellipsoid(center=(0, 0, 0), radii=(1.75, 1.75, 1.0), segments_u=42, segments_v=22, material='green')
torus_obj_path = OUT_DIR / 'torus.obj'
torus_obj_path.write_text(torus_builder.text())
with open(torus_obj_path, 'a') as f:
    f.write('\n# Material: torus_material\n# Color: [0.1, 0.8, 0.1] (green)\n# Roughness: 0.2\n')

queue('import_geometry', {'path': str(torus_obj_path), 'format': 'obj', 'name': 'torus'})
queue('create_material', {'name': 'torus_material', 'kind': 'glossy', 'color': [0.1, 0.8, 0.1], 'roughness': 0.2})
queue('assign_material', {'object_name': 'torus', 'material_name': 'torus_material'})
queue('set_camera', {'position': [4.0, 2.5, 4.0], 'target': [0.0, 0.0, 0.0], 'fov': 50})
queue('set_lighting', {'preset': 'soft_studio'})
queue('start_render', {'samples': 256, 'width': 1280, 'height': 1280})
queue('save_preview', {'path': str(OUT_DIR / 'preview-torus.png'), 'width': 1280, 'height': 1280})
print(f'  Queued 7 commands for TORUS')
print(f'  OBJ: {torus_obj_path.stat().st_size} bytes')


# ---------- Scene 4: CYLINDER (magenta) ----------
print('\nScene 4: CYLINDER - Magenta')

cylinder_builder = ObjBuilder('cylinder')
cylinder_builder.add_cylinder(center=(0, 0, 0), radius=1.0, height=3.5, segments=32, material='magenta')
cylinder_obj_path = OUT_DIR / 'cylinder.obj'
cylinder_obj_path.write_text(cylinder_builder.text())
with open(cylinder_obj_path, 'a') as f:
    f.write('\n# Material: cylinder_material\n# Color: [0.9, 0.1, 0.8] (magenta)\n# Roughness: 0.25\n')

queue('import_geometry', {'path': str(cylinder_obj_path), 'format': 'obj', 'name': 'cylinder'})
queue('create_material', {'name': 'cylinder_material', 'kind': 'glossy', 'color': [0.9, 0.1, 0.8], 'roughness': 0.25})
queue('assign_material', {'object_name': 'cylinder', 'material_name': 'cylinder_material'})
queue('set_camera', {'position': [3.0, 4.0, 4.0], 'target': [0.0, 0.0, 0.0], 'fov': 40})
queue('set_lighting', {'preset': 'soft_studio'})
queue('start_render', {'samples': 256, 'width': 1280, 'height': 1280})
queue('save_preview', {'path': str(OUT_DIR / 'preview-cylinder.png'), 'width': 1280, 'height': 1280})
print(f'  Queued 7 commands for CYLINDER')
print(f'  OBJ: {cylinder_obj_path.stat().st_size} bytes')


# ---------- Scene summary ----------
print('\n' + '=' * 60)
print('Scene summary:')
print('  1. BOX       → blue    [0.1, 0.1, 1.0]  glossy  → preview-box.png')
print('  2. PYRAMID   → gold    [1.0, 0.8, 0.1]  glossy  → preview-pyramid.png')
print('  3. TORUS     → green   [0.1, 0.8, 0.1]  glossy  → preview-torus.png')
print('  4. CYLINDER  → magenta [0.9, 0.1, 0.8]  glossy  → preview-cylinder.png')
print('\nOutput directory:', OUT_DIR)
print(f'Total OBJ files: {len(list(OUT_DIR.glob("*.obj")))}')
print('All 4 test scenes are queued (28 commands total).')
print('\nLaunch Octane bridge from Script menu to render!')

# Print all OBJ files
print('\nOBJ files:')
for obj_file in sorted(OUT_DIR.glob('*.obj')):
    print(f'  {obj_file.name}: {obj_file.stat().st_size} bytes')
