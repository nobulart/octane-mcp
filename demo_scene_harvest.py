#!/usr/bin/env python3
"""Demonstrate real-time OctaneX scene graph harvest.

This writes a scene_harvest command to the queue, triggers the Lua bridge,
and reads the harvest result to show the live scene state.
"""

import json
import os
import time
from pathlib import Path

OCTANE_MCP_STATUS = Path("/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/status.json")
OCTANE_MCP_QUEUE = Path("/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/queue")
OCTANE_MCP_RESULTS = Path("/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/results")

def main():
    """Read the live scene graph via the OctaneX bridge."""
    # Read current status to verify bridge is live
    if not OCTANE_MCP_STATUS.exists():
        print("ERROR: status.json not found — bridge may not be active")
        return
    
    status = json.loads(OCTANE_MCP_STATUS.read_text())
    print(f"Bridge status: {status['status']}")
    print(f"Render stage: {status['render_stage']}")
    print(f"Octane available: {status['octane_available']}")
    print(f"Processed commands: {status['processed_count']}")
    print()
    
    # Write a scene_harvest command to the queue
    harvest_cmd = {
        "schema_version": "1.0",
        "id": time.strftime("%Y%m%d%H%M%S"),
        "op": "scene_harvest",
        "payload": {"dry_run": True},
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "octanex-mcp-scene-harvest-demo",
    }
    
    cmd_path = OCTANE_MCP_QUEUE / "scene_harvest.json"
    cmd_path.write_text(json.dumps(harvest_cmd, indent=2))
    print(f"Written scene_harvest command to queue: {cmd_path}")
    
    # Wait for the bridge to process it
    print("\nWaiting for the bridge to process the harvest command...")
    for i in range(10):
        try:
            result_path = OCTANE_MCP_RESULTS / f"{harvest_cmd['id']}.json"
            if result_path.exists():
                raw = result_path.read_text()
                print(f"\nHarvest result ({len(raw)} bytes):")
                print(raw[:500])
                break
        except Exception as exc:
            print(f"  Check {i+1}/10: {exc}")
        
        time.sleep(0.5)
    
    # Also read the latest status to see what the bridge reported
    print("\n" + "="*60)
    print("Current OctaneX scene state (from status.json):")
    print("="*60)
    for key, val in status.items():
        if key not in ("bridge_status_path", "bridge_status_age_seconds"):
            print(f"  {key}: {val}")
    
    # Read all queue files to see what's there
    print(f"\nQueue files ({len(list(OCTANE_MCP_QUEUE.glob('*.json')))} total):")
    for qf in sorted(OCTANE_MCP_QUEUE.glob('*.json'))[:5]:
        print(f"  - {qf.name}")
    
    # Read the scene_harvest command content
    if cmd_path.exists():
        cmd_content = json.loads(cmd_path.read_text())
        print(f"\nsend_scene_harvest command:")
        print(f"  op: {cmd_content['op']}")
        print(f"  id: {cmd_content['id']}")
        print(f"  source: {cmd_content['source']}")

if __name__ == "__main__":
    main()
