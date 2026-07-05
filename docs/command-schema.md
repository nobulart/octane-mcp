# Command schema and lifecycle

OctaneX MCP uses versioned JSON command envelopes. Hermes/Python writes these files; Octane Lua reads and handles only allowlisted operations.

## Envelope

```json
{
  "schema_version": "1.0",
  "id": "176...-abcd1234",
  "op": "import_geometry",
  "payload": {
    "path": "/absolute/path/to/asset.obj",
    "format": "obj",
    "name": "asset_name"
  },
  "created_at": "2026-01-01T00:00:00Z",
  "source": "octanex-mcp"
}
```

Required envelope fields:

| Field | Purpose |
| --- | --- |
| `schema_version` | Current schema version, currently `1.0`. |
| `id` | Unique command id; also used for command/result filenames. |
| `op` | Allowlisted command operation. |
| `payload` | Operation-specific object. Nested metadata is preserved by the Lua bridge. |
| `created_at` | UTC ISO timestamp ending in `Z`. |
| `source` | Producer marker, normally `octanex-mcp`. |

## Lifecycle

```text
queue/<id>.json
  -> processing/<id>.json
  -> processed/<id>.json or failed/<id>.json
  -> results/<id>.json
```

`inbox.json` remains as a one-shot compatibility fallback for GUI runtimes that cannot safely enumerate directories.

## Result file

After Lua handles a command, it writes:

```json
{
  "schema_version": "1.0",
  "command_id": "176...-abcd1234",
  "op": "save_preview",
  "success": true,
  "message": "saved preview /.../renders/preview.png",
  "processed_at": "2026-01-01T00:00:05Z",
  "duration_ms": 123,
  "source_path": "/.../queue/<id>.json",
  "command_path": "/.../processed/<id>.json",
  "output_paths": ["/.../renders/preview.png"]
}
```

## Validation

Python validates commands before writing them. Agents can also call:

- `octane_validate_command(command)` — validate one command envelope.
- `octane_schema()` — return supported operations, field limits, path rules, and examples.
- `octane_validate_queue()` — validate all queued command JSON files.

CLI/automation can inspect validation through `octane_status()`, whose `commands.validation` field reports queue validity.

## Current validation scope

The validator is intentionally lightweight and dependency-free. It checks:

- allowed operation names;
- required envelope fields;
- required payload fields for core operations;
- common scalar/vector field types;
- stable structured error codes in `error_details`;
- render/camera/material ranges;
- generated path traversal safety.

It does not yet validate every Octane API-specific semantic constraint. Those should be added incrementally as command payloads stabilize.
