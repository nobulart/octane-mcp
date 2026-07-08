#!/bin/sh
# Launcher for the octanex-mcp server that isolates it from the Hermes agent
# runtime's PYTHONPATH (which points at a Hermes venv with a broken pydantic_core).
# Without this, `uv run octanex-mcp` inherits PYTHONPATH and fails with
# "mcp package is not installed" / "No module named 'pydantic_core._pydantic_core'".
#
# Usage (register in ~/.hermes/config.yaml mcp_servers):
#   command: "/Users/craig/octanex-mcp/run_octanex_mcp.sh"
#   args: []
exec env -u PYTHONPATH /opt/homebrew/bin/uv run --project /Users/craig/octanex-mcp octanex-mcp "$@"
