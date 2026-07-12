"""Phase-1 API corpus pipeline — offline tests (no Octane, no network).

These validate the Python side of the capability registry:
  - corpus ingest coerces the Lua exporter's JSON shape
  - capability_report flags the build's lighting strategy / save signature
  - validate_corpus fails clearly when required probes/constants are absent
  - a synthetic corpus fixture exercises the happy path
The Lua exporter (octane_lua/export_api_docs_v3.lua) is only
exercised live inside Octane X; these tests guard the contract it
must satisfy.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from octanex_mcp.api_corpus import (
    ApiCorpus,
    DEFAULT_REQUIRED_CONSTANTS,
    DEFAULT_REQUIRED_PROBES,
    load_corpus,
    validate_corpus,
)


def _synthetic_corpus(lighting: str = "proxy") -> dict:
    """Build a corpus JSON dict that mimics export_api_docs_v3.lua output."""
    native_light = lighting == "native"
    constants = {
        "NT_GEO_MESH": True,
        "NT_RENDERTARGET": True,
        "NT_ENV_DAYLIGHT": True,
        "NT_ENV_TEXTURE": True,
        "NT_MAT_DIFFUSE": True,
        "NT_MAT_EMISSIVE": True,
        "NT_LIGHT_AREA": native_light,
        "NT_LIGHT_SUN": native_light,
        "NT_CAM_THINLENS": True,
        "NT_CAM_PANORAMIC": True,
        "NT_FILM_SETTINGS": True,
        "P_MESH": True,
        "P_CAMERA": True,
        "P_ENVIRONMENT": True,
        "P_FOV": True,
        "P_POSITION": True,
        "P_TARGET": True,
        "P_DIFFUSE": True,
        "P_ROUGHNESS": True,
        "P_EMISSION": True,
        "P_MATERIAL": True,
        "P_MAX_SAMPLES": True,
        "P_MAX_RENDER_TIME": False,  # this build ignores maxRenderTime
        "A_FILENAME": True,
        "A_MAX_SAMPLES": True,
        "A_MAX_RENDER_TIME": False,
    }
    probes = {
        "project.getSceneGraph": {"available": True},
        "nodegraph.getRootGraph": {"available": True},
        "node.create": {"available": True},
        "render.start": {"available": True},
        "render.restart": {"available": True},
        "render.saveImage": {"available": True},
        "render.getRenderResultStatistics": {"available": True},
        "file.listDirectory": {"available": True},
        "json.encode": {"available": True},
        "timer.create": {"available": True},
        "gui.create": {"available": True},
        "apiinfo.getNodeTypeName": {"available": True},
    }
    return {
        "schema": "octanex-api-corpus/v1",
        "exported_at": "2026-07-12T00:00:00Z",
        "octane_available": True,
        "octane_help_available": True,
        "build": {"octane_version": "2023.1", "octane_build": "12.3.4-mac"},
        "modules": {"project": {"functions": ["getSceneGraph"], "properties": [], "constants": []}},
        "constants_by_prefix": {"NT_": {k: v for k, v in constants.items() if k.startswith("NT_")}},
        "feature_probes": probes,
        "constant_probes": {k: {"exists": v, "value": "nil" if not v else "1"} for k, v in constants.items()},
    }


class ApiCorpusIngestTests(unittest.TestCase):
    def test_coerce_preserves_shape(self) -> None:
        corpus = ApiCorpus(**_synthetic_corpus())
        self.assertEqual(corpus.schema, "octanex-api-corpus/v1")
        self.assertTrue(corpus.octane_available)
        self.assertEqual(corpus.build["octane_build"], "12.3.4-mac")
        self.assertIn("project.getSceneGraph", corpus.feature_probes)
        self.assertIn("P_MAX_SAMPLES", corpus.constant_probes)

    def test_build_tag_from_build(self) -> None:
        corpus = ApiCorpus(**_synthetic_corpus())
        self.assertEqual(corpus.build_tag, "12.3.4-mac")

    def test_build_tag_falls_back_to_version(self) -> None:
        data = _synthetic_corpus()
        data["build"] = {"octane_version": "2023.1"}
        corpus = ApiCorpus(**data)
        self.assertEqual(corpus.build_tag, "2023.1")

    def test_probe_available_helper(self) -> None:
        corpus = ApiCorpus(**_synthetic_corpus())
        self.assertTrue(corpus.probe_available("render.start"))
        self.assertFalse(corpus.probe_available("nonexistent.probe"))

    def test_constant_exists_helper_via_constant_probes(self) -> None:
        corpus = ApiCorpus(**_synthetic_corpus())
        self.assertTrue(corpus.constant_exists("NT_GEO_MESH"))
        self.assertFalse(corpus.constant_exists("NT_LIGHT_AREA"))


class ApiCorpusCapabilityTests(unittest.TestCase):
    def test_lighting_strategy_native_when_light_constants_present(self) -> None:
        corpus = ApiCorpus(**_synthetic_corpus(lighting="native"))
        report = corpus.capability_report()
        self.assertEqual(report["lighting_strategy"], "native_light")

    def test_lighting_strategy_proxy_when_light_constants_absent(self) -> None:
        corpus = ApiCorpus(**_synthetic_corpus(lighting="proxy"))
        report = corpus.capability_report()
        self.assertEqual(report["lighting_strategy"], "daylight_env_or_emissive_proxy")

    def test_save_preview_signature_known_when_save_and_maxsamples(self) -> None:
        corpus = ApiCorpus(**_synthetic_corpus())
        report = corpus.capability_report()
        # saveImage + P_MAX_SAMPLES are the two things the bridge needs
        # to emit a guaranteed-good preview path.
        self.assertTrue(report["save_preview_signature_known"])

    def test_all_required_probes_present_on_full_corpus(self) -> None:
        corpus = ApiCorpus(**_synthetic_corpus())
        report = corpus.capability_report()
        for name in DEFAULT_REQUIRED_PROBES:
            self.assertTrue(report["required_probes"][name], f"probe {name} should be present")
        self.assertTrue(report["all_required_probes_present"])

    def test_missing_required_constant_reported_as_gap(self) -> None:
        data = _synthetic_corpus()
        data["constant_probes"]["P_MAX_SAMPLES"] = {"exists": False, "value": "nil"}
        corpus = ApiCorpus(**data)
        report = corpus.capability_report()
        self.assertFalse(report["required_constants"]["P_MAX_SAMPLES"])
        self.assertFalse(report["all_required_constants_present"])


class ApiCorpusValidationTests(unittest.TestCase):
    def test_validate_ok_on_full_corpus(self) -> None:
        corpus = ApiCorpus(**_synthetic_corpus())
        result = validate_corpus(corpus)
        self.assertTrue(result["ok"])
        self.assertEqual(result["errors"], [])

    def test_validate_fails_when_octane_absent(self) -> None:
        data = _synthetic_corpus()
        data["octane_available"] = False
        corpus = ApiCorpus(**data)
        result = validate_corpus(corpus)
        self.assertFalse(result["ok"])
        self.assertTrue(any("octane" in e.lower() for e in result["errors"]))

    def test_validate_warns_on_missing_required_probe(self) -> None:
        data = _synthetic_corpus()
        data["feature_probes"]["node.create"] = {"available": False, "error": "nil"}
        corpus = ApiCorpus(**data)
        result = validate_corpus(corpus)
        # Missing probe -> warning, and all_required_probes_present False,
        # but octane_available True so ok stays True (partial export still usable).
        self.assertFalse(result["capabilities"]["all_required_probes_present"])
        self.assertTrue(any("node.create" in w for w in result["warnings"]))


class ApiCorpusLoadTests(unittest.TestCase):
    def test_load_corpus_from_file(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "octane_lua_api.12.3.4-mac.json"
            p.write_text(json.dumps(_synthetic_corpus()), encoding="utf-8")
            corpus = load_corpus(path=p)
            self.assertIsNotNone(corpus)
            self.assertEqual(corpus.build_tag, "12.3.4-mac")
            self.assertEqual(corpus.source_path, str(p))

    def test_load_corpus_returns_none_when_missing(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            corpus = load_corpus(path=Path(tmp))
            self.assertIsNone(corpus)

    def test_latest_corpus_path_picks_newest(self) -> None:
        import os
        import tempfile
        from octanex_mcp.api_corpus import latest_corpus_path
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            older = root / "octane_lua_api.old.json"
            newer = root / "octane_lua_api.new.json"
            older.write_text("{}", encoding="utf-8")
            newer.write_text("{}", encoding="utf-8")
            # Make newer actually newer.
            os.utime(newer, (1_000_000_000, 2_000_000_000))
            os.utime(older, (1_000_000_000, 1_000_000_000))
            self.assertEqual(latest_corpus_path(workspace=root), newer)


if __name__ == "__main__":
    unittest.main()
