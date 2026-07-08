from __future__ import annotations
import json, time, uuid
from pathlib import Path

WS = (
    Path.home() / "Library" / "Containers/com.otoy.rndrviewer/Data/OctaneMCP"
)
QDIR = WS / "queue"

def qf(op, pl):
    cid = f"{time.time_ns()}-{uuid.uuid4().hex[:8]}"
    txt = json.dumps({"id":cid,"op":op,"payload":pl or {}},indent=2)
    path = QDIR / f"{cid}.json"
    path.write_text(txt)
    print(f"QUEUED: {cid} -> {op}")

# Build cube OBJ
ad = WS/"assets"
ad.mkdir(parents=True,exist_ok=True)
s = 0.5
verts=[(-s,-s,-s),(s,-s,-s),(s,s,-s),(-s,s,-s),(-s,-s,s),(s,-s,s),(s,s,s),(-s,s,s)]
lines=["# showcase cube"]
for v in verts:
    lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
faces=[(1,5,8),(1,8,4),(2,3,7),(2,7,6),(3,4,8),(3,8,7),(1,2,6),(1,6,5),(4,3,7),(5,6,7),(5,7,8)]
for f in faces:
    lines.append(f"f {f[0]} {f[1]} {f[2]}")
cf = ad/"showcase_cube.obj"
cf.write_text("\n".join(lines))
print("CUBE WRITTEN:"+str(cf))

qf("import_geometry",{"path":str(cf),"format":"obj","name":"showcase_cube"})
qf("create_material",{"name":"golden_metal","kind":"metallic","color":[1.0,0.75,0.15],"roughness":0.25,"metallic":1.0})
qf("assign_material",{"object_name":"showcase_cube","material_name":"golden_metal"})
qf("set_camera",{"position":[2.5,2.0,3.0],"target":[0.0,0.0,0.0],"fov":45})
qf("start_render",{"samples":256})
