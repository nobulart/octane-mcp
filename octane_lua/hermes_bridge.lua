-- Hermes / OctaneX MCP bridge prototype: one-shot in-app command runner
--
-- IMPORTANT: Octane X runs Lua on the UI/message thread. A persistent polling
-- loop or os.execute sleep will freeze the app. This script processes exactly
-- one command from /Users/craig/OctaneMCP/inbox.json and exits.
--
-- Workflow:
--   1. Hermes/MCP queues a command (also writes inbox.json).
--   2. Run this script inside Octane X.
--   3. The script mutates/acknowledges one command and returns control to UI.

local ROOT = "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
local INBOX = ROOT .. "/inbox.json"
local PROCESSED = ROOT .. "/processed"
local FAILED = ROOT .. "/failed"
local STATUS = ROOT .. "/status.json"
local LOG = ROOT .. "/bridge.log"

local function append_log(message)
    local f = io.open(LOG, "a")
    if f then
        f:write(os.date("!%Y-%m-%dT%H:%M:%SZ"), " ", tostring(message), "\n")
        f:close()
    end
end

local function write_file(path, text)
    local f, err = io.open(path, "w")
    if not f then
        append_log("write_file failed: " .. tostring(path) .. " " .. tostring(err))
        return false, err
    end
    f:write(text)
    f:close()
    return true
end

local function read_file(path)
    local f = io.open(path, "r")
    if not f then return nil end
    local data = f:read("*a")
    f:close()
    return data
end

local function basename(path)
    return tostring(path):match("([^/]+)$") or tostring(path)
end

local function json_escape(s)
    s = tostring(s or "")
    s = s:gsub('\\', '\\\\'):gsub('"', '\\"'):gsub('\n', '\\n'):gsub('\r', '\\r'):gsub('\t', '\\t')
    return s
end

local function write_status(state, extra)
    local text = "{\n" ..
        "  \"bridge_seen\": true,\n" ..
        "  \"bridge\": \"hermes_bridge.lua\",\n" ..
        "  \"mode\": \"one_shot\",\n" ..
        "  \"status\": \"" .. json_escape(state or "ok") .. "\",\n" ..
        "  \"updated_at\": \"" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\",\n" ..
        "  \"root\": \"" .. json_escape(ROOT) .. "\""
    if extra then
        text = text .. ",\n  \"last_event\": \"" .. json_escape(extra) .. "\""
    end
    text = text .. "\n}\n"
    write_file(STATUS, text)
end

local function extract_string(raw, key)
    return raw:match('"' .. key .. '"%s*:%s*"([^"]+)"')
end

local function extract_number(raw, key)
    local value = raw:match('"' .. key .. '"%s*:%s*([%-%d%.]+)')
    if value then return tonumber(value) end
    return nil
end

local function parse_command(raw)
    local id = extract_string(raw, "id") or "unknown"
    local op = extract_string(raw, "op") or "unknown"
    return {
        id = id,
        op = op,
        raw = raw,
        path = extract_string(raw, "path"),
        name = extract_string(raw, "name"),
        kind = extract_string(raw, "kind"),
        preset = extract_string(raw, "preset"),
        message = extract_string(raw, "message"),
        object_name = extract_string(raw, "object_name"),
        material_name = extract_string(raw, "material_name"),
        fov = extract_number(raw, "fov"),
        samples = extract_number(raw, "samples"),
    }
end

local created_nodes = {}
local created_materials = {}

local function octane_available()
    return octane ~= nil and octane.node ~= nil
end

local function ensure_octane()
    if not octane_available() then
        return false, "Octane Lua API is not available in this interpreter; command acknowledged only"
    end
    return true
end

local function handle_import_geometry(cmd)
    local ok, msg = ensure_octane()
    if not ok then return true, msg end
    if not cmd.path then return false, "import_geometry missing path" end
    local name = cmd.name or basename(cmd.path)
    local mesh = octane.node.create{ type=octane.NT_GEO_MESH, name=name, position={500, 500} }
    mesh:setAttribute(octane.A_FILENAME, cmd.path, true)
    created_nodes[name] = mesh
    return true, "imported geometry " .. tostring(name)
end

local function handle_create_material(cmd)
    local ok, msg = ensure_octane()
    if not ok then return true, msg end
    local name = cmd.name or "mcp_material"
    local matType = octane.NT_MAT_DIFFUSE
    if cmd.kind == "glossy" and octane.NT_MAT_GLOSSY then matType = octane.NT_MAT_GLOSSY end
    if cmd.kind == "specular" and octane.NT_MAT_SPECULAR then matType = octane.NT_MAT_SPECULAR end
    local mat = octane.node.create{ type=matType, name=name, position={650, 500} }
    created_materials[name] = mat
    return true, "created material " .. tostring(name)
end

local function handle_command(cmd)
    append_log("one-shot command " .. tostring(cmd.id) .. " op=" .. tostring(cmd.op))

    if cmd.op == "ping" then
        return true, "pong " .. tostring(cmd.message or "")
    elseif cmd.op == "import_geometry" then
        return handle_import_geometry(cmd)
    elseif cmd.op == "create_material" then
        return handle_create_material(cmd)
    elseif cmd.op == "open_or_create_project" then
        return true, "project command acknowledged; reset intentionally not automatic"
    elseif cmd.op == "assign_material" or cmd.op == "set_camera" or cmd.op == "set_lighting" or cmd.op == "start_render" or cmd.op == "save_preview" or cmd.op == "build_concept" then
        return true, "acknowledged " .. tostring(cmd.op) .. "; exact handler pending API export/mapping"
    end

    return true, "acknowledged unknown op " .. tostring(cmd.op)
end

append_log("one-shot bridge starting")
write_status("running", "start")

local raw = read_file(INBOX)
if not raw or raw == "" then
    append_log("no inbox command")
    write_status("idle", "no inbox command")
    print("Hermes bridge: no inbox command at " .. INBOX)
    return
end

local cmd = parse_command(raw)
local ok, handled, message = pcall(function()
    local success, msg = handle_command(cmd)
    return success, msg
end)

if ok and handled then
    local dst = PROCESSED .. "/" .. tostring(cmd.id) .. ".json"
    local moved = os.rename(INBOX, dst)
    append_log("processed inbox id=" .. tostring(cmd.id) .. " moved=" .. tostring(moved) .. " message=" .. tostring(message))
    write_status("processed", tostring(cmd.op) .. " " .. tostring(message))
    print("Hermes bridge processed " .. tostring(cmd.op) .. ": " .. tostring(message))
else
    local err = ok and message or handled
    local dst = FAILED .. "/" .. tostring(cmd.id) .. ".json"
    os.rename(INBOX, dst)
    append_log("failed inbox id=" .. tostring(cmd.id) .. " error=" .. tostring(err))
    write_status("failed", tostring(err))
    print("Hermes bridge failed: " .. tostring(err))
end
