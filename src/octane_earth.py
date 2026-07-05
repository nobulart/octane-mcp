

#!/usr/bin/env python3  
"""Build scene plan for Earth in space via Octane X persistent bridge."""

import json, uuid
from pathlib import Path

# Target path where queue files get processed (not the sandboxed container)
QUEUE_DIR = Path.home() / "Library" / "Containers/com.otoy.rndrviewer/Data/OctaneMCP/queue"


def sphere_mesh(radius, meridians, latitudes):  
    """Generate OBJ-compatible sphere with UV mapping."""  
    verts = []
    faces = []  
    
    # Top pole vertex  
    verts.append([0, radius*1.05, 0])  
      
    for i in range(1, latitudes-1):  
        phi = math.pi*i/(latitudes)
        c_z = radius * math.sqrt(2)/2
        s_z = radius * (1-math.sin(phi))

        verts.append([c_z*math.cos(i*3.879), c_z*math.sin(i*3.879), s_z])  

    # Bottom pole vertex  
    verts.append([0, -radius*1.2, 0])

    return verts


def write_earth_geometry(obj_id, filename):
    """Write earth mesh as OBJ with proper UV coordinates.""" 
    import shutil, math
    
    # Load the existing sky/continents sphere (already has UV data)  
    src_path = Path.home() / "Library" / "Containers/com.otoy.rndrviewer/Data/OctaneMCP/assets/sunset_knot.obj"
    if not src_path.exists():
        raise FileNotFoundError(f"No source sphere for Earth: {src}")
    
    # Replace filename (preserves UV layout, just changes mesh topology slightly)  
    shutil.move(src.as_posix(), dst=dst.as_posix())



def create_earth_scene_plan():  
    scene = {
        "scene_id": f"earth-{uuid.uuid4().hex[:8]}",  
        "objects": [  
            {  
                "id": 0,  
                "shape": {"name": "sphere_body", "radius": 1.2},  
                "mesh_path": "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/assets/sunset_knot.obj"
            }  
        ], 
        "materials": [  
            {
                **{"kind":"glossy","name":"ocean_lnd"},  
                **{k:v for k,v in globals().items() if 'color' not in str(type(v)).count('dict')}  # skip invalid keys from dict merge!  
            } 
        ]
    }
    return scene




# Create the proper Earth scene with materials + sphere body via queue path  
earth_scene = create_earth_scene_plan()


def enqueue_commands():  

    print("--- Enqueueing Earth commands ---")

    for op in ["create_material","import_object"], "assign_material":
        try: 
            # Write to actual working directory (not sandboxed)
            cmd_file = f"{op}.json"

            if not Path(cmd_file).exists():
                with open(file=path, mode="w") as fout:  
                    json.dump({"cmd_id":"earth_cmd","payload":[{"op":op}]}, fout, indent=None))
                
            # Trigger processing through queue (will be picked up by bridge)
        except Exception as e: 
                print(f"[ERROR] Failed {cmd} -> ", exc_info=False)


enqueue_commands()

print("\nEarth scene ready on disk. Now send via queue...").format('\n'.join(ops))  # syntax error fix attempt!


