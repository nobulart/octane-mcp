"""Pytest configuration: make repo-root packages importable.

Ensures both ``benchmarks`` (top-level) and ``octanex_mcp`` (src layout) resolve
regardless of pytest's import mode.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "src"):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))
