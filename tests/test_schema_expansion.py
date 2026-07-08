from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from octanex_mcp import schema
from octanex_mcp.schema import (
    ALLOWED_CREATION_KINDS,
    ALLOWED_CREATION_MATERIAL_TYPES,
    ALLOWED_LIGHT_TYPES,
    ALLOWED_MATERIAL_SHADERS,
    ALLOWED_MATERIAL_TYPES,
    ALLOWED_LIGHT_MODE_TYPES,
    ALLOWED_LIGHT_TYPE,
    SCHEMA_VERSION,
    create_material_schema,
    create_light_schema,
    validate_command,
)


class ExpandedSchemaTests(unittest.TestCase):
    """Tests for material/light schema expansion."""

    def test_all_allowed_creation_kinds_registered(self) -> None:
        """All kinds used in the schema are in ALLOWED_CREATION_KINDS."""
        for kind in create_material_schema()["material_kinds"]:
            with self.subTest(kind=kind):
                self.assertIn(kind, ALLOWED_CREATION_KINDS)

    def test_all_allowed_material_shaders(self) -> None:
        """All material shaders are in ALLOWED_MATERIAL_SHADERS."""
        for shader in ALLOWED_CREATION_MATERIAL_TYPES:
            with self.subTest(shader=shader):
                self.assertIn(shader, ALLOWED_MATERIAL_SHADERS)

    def test_all_allowed_light_types(self) -> None:
        """All light types are in ALLOWED_LIGHT_TYPES."""
        for lt in ALLOWED_LIGHT_TYPES:
            with self.subTest(lt=lt):
                self.assertIn(lt, ALLOWED_LIGHT_MODE_TYPES)

    def test_allowed_material_kinds_comprehensive(self) -> None:
        """Material kinds include new and legacy entries."""
        expected_kinds = {
            "glossy", "diffuse", "specular", "metallic",
            "glass", "ceramic", "atmosphere",
            "prismatic", "translucent", "fabric",
        }
        self.assertEqual(ALLOWED_CREATION_KINDS, expected_kinds)

    def test_allowed_light_types_comprehensive(self) -> None:
        """Light types include area, sun, and standard types."""
        expected_lights = {
            "area_light", "sun_light",
            "point_light", "spot_light", "directional_light",
            "environment", "emissive",
        }
        self.assertEqual(ALLOWED_LIGHT_TYPES, expected_lights)

    def test_allowed_light_modes_comprehensive(self) -> None:
        """Light modes cover the full set of lighting modes (modes + physical types)."""
        expected_modes = {
            "default", "key", "fill", "rim", "accent",
            "environment", "emissive", "area_light",
            "spot_light", "point_light", "sun_light", "directional_light",
        }
        self.assertEqual(ALLOWED_LIGHT_TYPE, expected_modes)

    def test_create_material_schema_includes_new_kinds(self) -> None:
        """create_material_schema() returns material kinds for new types."""
        schema_data = create_material_schema()
        kinds = schema_data["material_kinds"]
        self.assertIn("glass", kinds)
        self.assertIn("ceramic", kinds)
        self.assertIn("atmosphere", kinds)

    def test_create_material_schema_includes_prismatic_and_translucent(self) -> None:
        """create_material_schema() returns prismatic and translucent."""
        schema_data = create_material_schema()
        kinds = schema_data["material_kinds"]
        self.assertIn("prismatic", kinds)
        self.assertIn("translucent", kinds)

    def test_create_light_schema_includes_area_and_sun_types(self) -> None:
        """create_light_schema() returns area_light and sun_light."""
        schema_data = create_light_schema()
        light_types = set(schema_data["light_types"])
        self.assertIn("area_light", light_types)
        self.assertIn("sun_light", light_types)

    def test_create_material_schema_has_new_material_types(self) -> None:
        """create_material_schema() returns new material types."""
        schema_data = create_material_schema()
        material_types = schema_data["material_types"]
        # check new entries are listed
        self.assertIsInstance(material_types, list)
        # at least the known ones
        new_types = {"glass", "ceramic", "atmosphere", "prismatic", "translucent"}
        for t in new_types:
            with self.subTest(t=t):
                self.assertIn(t, material_types)

    def test_allowed_material_types_comprehensive(self) -> None:
        """ALLOWED_MATERIAL_TYPES includes all expected material types."""
        expected = {
            "diffuse", "glossy", "specular", "metallic",
            "glass", "ceramic", "atmosphere",
            "prismatic", "translucent", "fabric",
        }
        for t in expected:
            with self.subTest(t=t):
                self.assertIn(t, ALLOWED_MATERIAL_TYPES)

    def test_validate_command_for_glass_material(self) -> None:
        """validate_command works with a glass material."""
        command = {
            "id": "cmd-glass",
            "op": "create_material",
            "payload": {
                "name": "my_glass",
                "kind": "glass",
                "color": [0.1, 0.5, 0.8],
                "opacity": 0.7,
                "ior": 1.52,
            },
            "schema_version": SCHEMA_VERSION,
            "created_at": "2026-01-01T00:00:00Z",
            "source": "octanex-mcp",
        }
        result = validate_command(command)
        self.assertTrue(result.ok)

    def test_validate_command_for_ceramic_material(self) -> None:
        """validate_command works with a ceramic material."""
        command = {
            "id": "cmd-ceramic",
            "op": "create_material",
            "payload": {
                "name": "my_ceramic",
                "kind": "ceramic",
                "color": [0.9, 0.85, 0.7],
                "roughness": 0.6,
            },
            "schema_version": SCHEMA_VERSION,
            "created_at": "2026-01-01T00:00:00Z",
            "source": "octanex-mcp",
        }
        result = validate_command(command)
        self.assertTrue(result.ok)

    def test_validate_command_for_atmosphere_material(self) -> None:
        """validate_command works with an atmosphere material."""
        command = {
            "id": "cmd-atmo",
            "op": "create_material",
            "payload": {
                "name": "my_atmo",
                "kind": "atmosphere",
                "color": [0.8, 0.9, 1.0],
                "density": 0.5,
            },
            "schema_version": SCHEMA_VERSION,
            "created_at": "2026-01-01T00:00:00Z",
            "source": "octanex-mcp",
        }
        result = validate_command(command)
        self.assertTrue(result.ok)

    def test_validate_command_for_area_light_preset(self) -> None:
        """validate_command works with an area_light preset."""
        command = {
            "id": "cmd-area",
            "op": "set_lighting",
            "payload": {
                "preset": "area_light",
            },
            "schema_version": SCHEMA_VERSION,
            "created_at": "2026-01-01T00:00:00Z",
            "source": "octanex-mcp",
        }
        result = validate_command(command)
        self.assertTrue(result.ok)

    def test_validate_command_for_sun_light_preset(self) -> None:
        """validate_command works with a sun_light preset."""
        command = {
            "id": "cmd-sun",
            "op": "set_lighting",
            "payload": {
                "preset": "sun_light",
            },
            "schema_version": SCHEMA_VERSION,
            "created_at": "2026-01-01T00:00:00Z",
            "source": "octanex-mcp",
        }
        result = validate_command(command)
        self.assertTrue(result.ok)

    def test_create_material_schema_has_valid_ranges_for_ior(self) -> None:
        """create_material_schema() validates IOR for glass."""
        schema_data = create_material_schema()
        fields = schema_data.get("material_fields", {})
        glass_fields = fields.get("glass", {})
        self.assertIn("ior", glass_fields)

    def test_create_light_schema_has_valid_ranges(self) -> None:
        """create_light_schema() validates light field ranges."""
        schema_data = create_light_schema()
        fields = schema_data.get("light_fields", {})
        self.assertIn("area_intensity", fields)


if __name__ == "__main__":
    unittest.main()
