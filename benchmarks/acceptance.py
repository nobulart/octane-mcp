"""Backward-compatible re-export of the pixel-QA core.

The acceptance logic now lives in the library module
``octanex_mcp.acceptance`` so the MCP server (a console script with the repo
root off ``sys.path``) can import it without dragging in ``benchmarks``. This
shim keeps ``import benchmarks.acceptance`` working for the test suite, harness,
and verify scripts.

``benchmarks`` stays a *consumer* of ``octanex_mcp``; it must never be imported
by anything under ``src/octanex_mcp`` (that breaks the server's stdio launch).
"""

from octanex_mcp.acceptance import (  # noqa: F401
    _DISQUALIFYING,
    _hue_families,
    _hue_to_rgb,
    evaluate_acceptance,
    filter_reference,
    reference_to_acceptance,
    summarize,
)

__all__ = [
    "evaluate_acceptance",
    "reference_to_acceptance",
    "filter_reference",
    "summarize",
    "_hue_families",
    "_hue_to_rgb",
    "_DISQUALIFYING",
]
