"""Tests for stable #N ids, never-renumbering labels, and ref resolution.

These lock in the contract: uids are fixed for a scene's lifetime, the human
"#N" badge never shifts when an object is removed, and resolve_label_refs turns
"#6 through #10 and #54" into the right uid set (with groups expanding to members).
"""

import unittest

from octanex_mcp.scene import (
    normalize_scene_plan,
    resolve_label_refs,
)


def _plan(objects, groups=None):
    return {"scene_id": "labeltest", "objects": objects, "groups": groups or []}


class TestStableIds(unittest.TestCase):
    def test_uids_assigned_and_seeded_from_id(self):
        scene = normalize_scene_plan(_plan([{"id": "a"}, {"id": "b"}]))
        uids = [o["uid"] for o in scene["objects"]]
        self.assertEqual(uids, ["a", "b"])

    def test_labels_mapped_and_stable(self):
        scene = normalize_scene_plan(_plan([{"id": "a"}, {"id": "b"}, {"id": "c"}]))
        self.assertEqual(scene["labels"], {"#1": "a", "#2": "b", "#3": "c"})

    def test_missing_id_mints_stable_uid(self):
        scene = normalize_scene_plan(_plan([{"type": "box"}, {"id": "b"}]))
        self.assertEqual(scene["objects"][0]["uid"], "o0001")
        self.assertEqual(scene["labels"]["#1"], "o0001")

    def test_removal_leaves_gap_not_renumber(self):
        scene = normalize_scene_plan(_plan([{"id": "a"}, {"id": "b"}, {"id": "c"}]))
        # Drop the middle object, then re-normalize (simulates a load+save).
        scene["objects"] = [o for o in scene["objects"] if o["id"] != "b"]
        reloaded = normalize_scene_plan(scene)
        labels = reloaded["labels"]
        # #2 (was b) is GONE; #1 and #3 are preserved, not shifted.
        self.assertNotIn("#2", labels)
        self.assertEqual(labels["#1"], "a")
        self.assertEqual(labels["#3"], "c")

    def test_new_object_gets_next_badge(self):
        scene = normalize_scene_plan(_plan([{"id": "a"}, {"id": "b"}, {"id": "c"}]))
        scene["objects"].append({"id": "d"})
        reloaded = normalize_scene_plan(scene)
        self.assertEqual(reloaded["labels"]["#4"], "d")


class TestRefResolution(unittest.TestCase):
    def setUp(self):
        # uids seeded from id: #1->a, #2->b, ... #11->k
        self.scene = normalize_scene_plan(_plan(
            [{"id": f"a{i}"} for i in range(1, 12)],  # #1..#11 -> a1..a11
        ))
        self.assertEqual(self.scene["labels"]["#10"], "a10")
        self.assertEqual(self.scene["labels"]["#11"], "a11")

    def test_single(self):
        self.assertEqual(resolve_label_refs(self.scene, "#10"), ["a10"])

    def test_and_list(self):
        self.assertEqual(resolve_label_refs(self.scene, "#1 and #3"), ["a1", "a3"])

    def test_through_range(self):
        uids = resolve_label_refs(self.scene, "#6 through #10")
        self.assertEqual(uids, [f"a{i}" for i in range(6, 11)])

    def test_mixed_range_and_singleton(self):
        uids = resolve_label_refs(self.scene, "#6 through #10 and #1")
        self.assertEqual(uids, [f"a{i}" for i in range(6, 11)] + ["a1"])

    def test_unknown_badge_dropped(self):
        self.assertEqual(resolve_label_refs(self.scene, "#999"), [])

    def test_dash_range(self):
        uids = resolve_label_refs(self.scene, "#1-#3")
        self.assertEqual(uids, ["a1", "a2", "a3"])


class TestGroupRefs(unittest.TestCase):
    def setUp(self):
        # 11 objects id a1..a11 -> #1..#11; group g1 lists real uids.
        self.scene = normalize_scene_plan(_plan(
            [{"id": f"a{i}"} for i in range(1, 12)],  # #1..#11
            groups=[{"id": "g1", "members": ["a6", "a7", "a8", "a10", "a11"]}],
        ))

    def test_group_expands_to_members(self):
        # #G1 -> a6,a7,a8,a10,a11
        uids = resolve_label_refs(self.scene, "#G1")
        self.assertEqual(
            sorted(uids),
            sorted(["a6", "a7", "a8", "a10", "a11"]),
        )

    def test_group_prefix_only(self):
        # "g" prefix must not collide with object #1
        self.assertNotIn("a1", resolve_label_refs(self.scene, "#G1"))


if __name__ == "__main__":
    unittest.main()
