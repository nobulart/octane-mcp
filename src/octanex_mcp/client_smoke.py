from __future__ import annotations

import json

from .bridge import create_simple_obj, list_commands, read_status, write_command


def main() -> None:
    asset = create_simple_obj("client_smoke_cube", 0.75)
    results = [
        write_command("ping", {"message": "client smoke"}),
        write_command("import_geometry", {"path": asset["path"], "format": "obj", "name": asset["name"]}),
        write_command("create_material", {"name": "smoke_blue", "kind": "glossy", "color": [0.1, 0.3, 1.0], "roughness": 0.2}),
        write_command("assign_material", {"object_name": asset["name"], "material_name": "smoke_blue"}),
        write_command("set_camera", {"position": [2.5, 1.5, 4.0], "target": [0, 0, 0], "fov": 45}),
    ]
    print(json.dumps({"asset": asset, "queued": results, "status": read_status(), "commands": list_commands()}, indent=2))


if __name__ == "__main__":
    main()
