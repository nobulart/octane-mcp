"""Generate test scenes and queue them to the Octane MCP bridge."""
from pathlib import Path

OUT_DIR = Path.cwd() / 'test-scenes'
OUT_DIR.mkdir(exist_ok=True)

from octanex_mcp.bridge import write_command
from octanex_mcp.schema import validate_command
from octanex_mcp.visuals import ObjBuilder


def queue(op, payload):
    """Queue a command through the bridge."""
    cmd = {
        'schema_version': '2.0',
        'op': op,
        'payload': payload or {},
        'created_at': str(OUT_DIR),
        'source': 'test-viz',
    }
    validate_command(cmd)
    result = write_command(op, payload)
    return result


# ---------- Scene 1: BOX (blue glossy) ----------
print('Scene 1: BOX - Blue glossy')

box_builder = ObjBuilder('box')
box_builder.add_box(center=(0, 0, 0), size=(3, 3, 4), material='glossy')

box_obj_path = OUT_DIR / 'box.obj'
box_obj_path.write_text(box_builder.text())

with open(box_obj_path, 'a') as f:
    f.write('\n# Material: box_material\n')
    f.write('# Color: [0.1, 0.1, 1.0] (blue)\n')
    f.write('# Roughness: 0.3\n')

print(f'  Generated OBJ: {box_obj_path}')
print(f'  OBJ lines: {len(box_builder.lines)}')

queue('import_geometry', {'path': str(box_obj_path), 'format': 'obj', 'name': 'box'})
queue('create_material', {'name': 'box_material', 'kind': 'glossy', 'color': [0.1, 0.1, 1.0], 'roughness': 0.3})
queue('assign_material', {'object_name': 'box', 'material_name': 'box_material'})
queue('set_camera', {'position': [3.0, 3.0, 4.0], 'target': [0.0, 0.0, 0.0], 'fov': 45})
queue('set_lighting', {'preset': 'soft_studio'})
queue('start_render', {'samples': 256, 'width': 1280, 'height': 1280})
queue('save_preview', {'path': str(OUT_DIR / 'preview-box.png'), 'width': 1280, 'height': 1280, 'samples': 256, 'min_samples': 1, 'timeout_seconds': 10})
print('  Queued 7 bridge commands')


# ---------- Scene 2: PYRAMID (gold) ----------
print('\nScene 2: PYRAMID - Gold')

pyramid_builder = ObjBuilder('pyramid')
pyramid_builder.add_box(center=(0, 1.5, 0), size=(2.5, 2.5, 3), material='gold')

pyramid_obj_path = OUT_DIR / 'pyramid.obj'
pyramid_obj_path.write_text(pyramid_builder.text())

with open(pyramid_obj_path, 'a') as f:
    f.write('\n# Material: pyramid_material\n')
    f.write('# Color: [1.0, 0.8, 0.1] (gold)\n')
    f.write('# Roughness: 0.15\n')

print(f'  Generated OBJ: {pyramid_obj_path}')
print(f'  OBJ lines: {len(pyramid_builder.lines)}')

queue('import_geometry', {'path': str(pyramid_obj_path), 'format': 'obj', 'name': 'pyramid'})
queue('create_material', {'name': 'pyramid_material', 'kind': 'gold', 'color': [1.0, 0.8, 0.1], 'roughness': 0.15})
queue('assign_material', {'object_name': 'pyramid', 'material_name': 'pyramid_material'})
queue('set_camera', {'position': [2.0, 4.0, 3.0], 'target': [0.0, 1.5, 0.0], 'fov': 60})
queue('set_lighting', {'preset': 'soft_studio'})
queue('start_render', {'samples': 256, 'width': 1280, 'height': 1280})
queue('save_preview', {'path': str(OUT_DIR / 'preview-pyramid.png'), 'width': 1280, 'height': 1280, 'samples': 256, 'min_samples': 1, 'timeout_seconds': 10})
print('  Queued 7 bridge commands')


# ---------- Scene 3: TORUS (green) ----------
print('\nScene 3: TORUS - Green')

torus_builder = ObjBuilder('torus')
torus_builder.add_ellipsoid(center=(0, 0, 0), radii=(1.75, 1.75, 1.0), segments_u=42, segments_v=22, material='green')

torus_obj_path = OUT_DIR / 'torus.obj'
torus_obj_path.write_text(torus_builder.text())

with open(torus_obj_path, 'a') as f:
    f.write('\n# Material: torus_material\n')
    f.write('# Color: [0.1, 0.8, 0.1] (green)\n')
    f.write('# Roughness: 0.2\n')

print(f'  Generated OBJ: {torus_obj_path}')
print(f'  OBJ lines: {len(torus_builder.lines)}')

queue('import_geometry', {'path': str(torus_obj_path), 'format': 'obj', 'name': 'torus'})
queue('create_material', {'name': 'torus_material', 'kind': 'glossy', 'color': [0.1, 0.8, 0.1], 'roughness': 0.2})
queue('assign_material', {'object_name': 'torus', 'material_name': 'torus_material'})
queue('set_camera', {'position': [4.0, 2.5, 4.0], 'target': [0.0, 0.0, 0.0], 'fov': 50})
queue('set_lighting', {'preset': 'soft_studio'})
queue('start_render', {'samples': 256, 'width': 1280, 'height': 1280})
queue('save_preview', {'path': str(OUT_DIR / 'preview-torus.png'), 'width': 1280, 'height': 1280, 'samples': 256, 'min_samples': 1, 'timeout_seconds': 10})
print('  Queued 7 bridge commands')


# ---------- Scene 4: CYLINDER (magenta) ----------
print('\nScene 4: CYLINDER - Magenta')

cylinder_builder = ObjBuilder('cylinder')
cylinder_builder.add_cylinder(center=(0, 0, 0), radius=1.0, height=3.5, segments=32, material='magenta')

cylinder_obj_path = OUT_DIR / 'cylinder.obj'
cylinder_obj_path.write_text(cylinder_builder.text())

with open(cylinder_obj_path, 'a') as f:
    f.write('\n# Material: cylinder_material\n')
    f.write('# Color: [0.9, 0.1, 0.8] (magenta)\n')
    f.write('# Roughness: 0.25\n')

print(f'  Generated OBJ: {cylinder_obj_path}')
print(f'  OBJ lines: {len(cylinder_builder.lines)}')

queue('import_geometry', {'path': str(cylinder_obj_path), 'format': 'obj', 'name': 'cylinder'})
queue('create_material', {'name': 'cylinder_material', 'kind': 'glossy', 'color': [0.9, 0.1, 0.8], 'roughness': 0.25})
queue('assign_material', {'object_name': 'cylinder', 'material_name': 'cylinder_material'})
queue('set_camera', {'position': [3.0, 4.0, 4.0], 'target': [0.0, 0.0, 0.0], 'fov': 40})
queue('set_lighting', {'preset': 'soft_studio'})
queue('start_render', {'samples': 256, 'width': 1280, 'height': 1280})
queue('save_preview', {'path': str(OUT_DIR / 'preview-cylinder.png'), 'width': 1280, 'height': 1280, 'samples': 256, 'min_samples': 1, 'timeout_seconds': 10})
print('  Queued 7 bridge commands')


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
print('Launch Octane bridge from Script menu to render!')
