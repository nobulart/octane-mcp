"""Tests for Phase 3 grouping + mesh modifiers.

Asset-level ops (meshmod) run against real trimesh (the ``science`` extra).
If the extra is missing the module raises MeshDependencyError with a hint
rather than crashing at import, so the test skips cleanly instead of failing.
"""

import unittest
from pathlib import Path

from octanex_mcp.bridge import Workspace
from octanex_mcp.scene import (
    group_objects,
    load_scene_manifest,
    modify_objects,
    normalize_scene_plan,
    save_scene_manifest,
)
from octanex_mcp.visuals import create_primitive_obj
from octanex_mcp.meshmod import (
    MeshDependencyError,
    is_mesh_available,
    merge_objs,
    smooth_obj,
    subdivide_obj,
)


class MeshModTests(unittest.TestCase):
    def setUp(self):
        self.ws = Workspace(Path.home() / "tmp" / "octanex_phase3_ws")
        self.ws.ensure()
        self.box = create_primitive_obj(
            {"id": "b", "type": "box", "size": [2, 2, 2]}, scene_id="t", workspace=self.ws
        )["path"]
        self.sphere = create_primitive_obj(
            {"id": "s", "type": "sphere", "radius": 1}, scene_id="t", workspace=self.ws
        )["path"]

    def test_subdivide_increases_faces(self):
        if not is_mesh_available():
            self.skipTest("science extra (trimesh) not installed")
        out = subdivide_obj(self.box, iterations=1, workspace=self.ws)
        self.assertGreater(out["face_count"], 12)  # box = 12 tris -> 48 after 1 subdiv
        self.assertTrue(Path(out["path"]).exists())

    def test_subdivide_respects_max_faces(self):
        if not is_mesh_available():
            self.skipTest("science extra (trimesh) not installed")
        # cap is a guard checked before subdividing, so the result may slightly
        # exceed 100 in one step but must never explode toward the default 200k.
        out = subdivide_obj(self.box, iterations=5, max_faces=100, workspace=self.ws)
        self.assertLessEqual(out["face_count"], 12 * 4 * 4 * 4)  # <= 3 subdivision steps

    def test_smooth_runs(self):
        if not is_mesh_available():
            self.skipTest("science extra (trimesh) not installed")
        out = smooth_obj(self.sphere, iterations=1, workspace=self.ws)
        self.assertTrue(Path(out["path"]).exists())
        self.assertGreater(out["vertex_count"], 0)

    def test_merge_combines_two_meshes(self):
        if not is_mesh_available():
            self.skipTest("science extra (trimesh) not installed")
        out = merge_objs([self.box, self.sphere], out_name="twomesh", workspace=self.ws)
        self.assertEqual(out["part_count"], 2)
        self.assertTrue(Path(out["path"]).exists())

    def test_missing_dep_raises_hint(self):
        # Force the unavailable path without actually uninstalling trimesh.
        import octanex_mcp.meshmod as mm

        real = mm.is_mesh_available
        mm.is_mesh_available = lambda: False  # type: ignore
        try:
            with self.assertRaises(MeshDependencyError) as ctx:
                subdivide_obj(self.box, workspace=self.ws)
            self.assertIn("science", str(ctx.exception))
        finally:
            mm.is_mesh_available = real  # type: ignore


def _make_scene(ws, n=12):
    objs = [
        {"id": f"o{i}", "type": "box", "size": [1, 1, 1], "transform": {"translate": [i, 0, 0]}}
        for i in range(1, n + 1)
    ]
    return save_scene_manifest({"scene_id": "ph3", "objects": objs}, ws)


class SceneGroupModifyTests(unittest.TestCase):
    def setUp(self):
        self.ws = Workspace(Path.home() / "tmp" / "octanex_phase3_scene_ws")
        self.ws.ensure()
        _make_scene(self.ws)

    def test_modify_resolution_subdivides_each_ref(self):
        if not is_mesh_available():
            self.skipTest("science extra (trimesh) not installed")
        res = modify_objects("ph3", "#1 and #3", "resolution", iterations=1, workspace=self.ws)
        self.assertEqual(res["modifier"], "resolution")
        self.assertIn("o1", res["results"])
        self.assertIn("o3", res["results"])
        self.assertGreater(res["results"]["o1"]["face_count"], 12)
        # node name preserved (stable)
        self.assertEqual(res["results"]["o1"]["node_name"], "Hermes::ph3::o1")

    def test_group_merges_and_records_group(self):
        if not is_mesh_available():
            self.skipTest("science extra (trimesh) not installed")
        res = group_objects("ph3", "#6 through #10 and #54", workspace=self.ws)
        self.assertGreaterEqual(res["member_count"], 2)
        self.assertTrue(Path(res["merged_path"]).exists())
        # Members removed, merged node present
        loaded = load_scene_manifest("ph3", self.ws)["scene"]
        uids = [o.get("uid") for o in loaded["objects"]]
        self.assertNotIn("o6", uids)
        self.assertIn(res["group_guid"], [g["guid"] for g in loaded["groups"]])

    def test_modify_unknown_modifier_raises(self):
        with self.assertRaises(ValueError):
            modify_objects("ph3", "#1", "explode", workspace=self.ws)

    def test_modify_no_refs_raises(self):
        with self.assertRaises(ValueError):
            modify_objects("ph3", "#999", "smooth", workspace=self.ws)


if __name__ == "__main__":
    unittest.main()
