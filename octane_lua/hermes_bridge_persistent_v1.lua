-- Hermes / OctaneX MCP bridge persistent v1. Run inside Octane X.
--
-- Keeps a small Octane window open and processes Hermes command JSON files from
-- the Octane sandbox container queue. This avoids rerunning the one-shot script
-- for every command. If Octane's timer API signature differs, the window still
-- provides a safe "Process next" button.

local ROOT = os.getenv("OCTANEX_MCP_WORKSPACE") or ((os.getenv("HOME") or "/tmp") .. "/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP")
local QUEUE = ROOT .. "/queue"
local INBOX = ROOT .. "/inbox.json"
local PROCESSING = ROOT .. "/processing"
local PROCESSED = ROOT .. "/processed"
local FAILED = ROOT .. "/failed"
local RESULTS = ROOT .. "/results"
local STATUS = ROOT .. "/status.json"
local LOG = ROOT .. "/bridge.log"
local DEFAULT_PREVIEW = ROOT .. "/renders/preview.png"
local DEFAULT_WIDTH = 1280
local DEFAULT_HEIGHT = 1280
local LISTING = ROOT .. "/queue_listing.txt"
-- INLINE JSON DECODER (self-contained, no external file deps)
local JSON = {}
JSON.null = {}
local function _jerr(text, pos, msg)
    local near = text:sub(pos, pos + 32):gsub("\n", "\\n")
    return nil, msg .. " at byte " .. tostring(pos) .. " near '" .. near .. "'"
end
local function _skip_ws(text, pos)
    while true do
        local c = text:sub(pos, pos)
        if c == " " or c == "\t" or c == "\r" or c == "\n" then pos = pos + 1 else return pos end
    end
end
local _parse_value
local function _parse_string(text, pos)
    if text:sub(pos, pos) ~= '"' then return _jerr(text, pos, "expected string") end
    pos = pos + 1
    local out = {}
    while pos <= #text do
        local c = text:sub(pos, pos)
        if c == '"' then return table.concat(out), pos + 1 end
        if c == "\\" then
            local esc = text:sub(pos + 1, pos + 1)
            if esc == '"' or esc == "\\" or esc == "/" then table.insert(out, esc); pos = pos + 2
            elseif esc == "b" then table.insert(out, "\b"); pos = pos + 2
            elseif esc == "f" then table.insert(out, "\f"); pos = pos + 2
            elseif esc == "n" then table.insert(out, "\n"); pos = pos + 2
            elseif esc == "r" then table.insert(out, "\r"); pos = pos + 2
            elseif esc == "t" then table.insert(out, "\t"); pos = pos + 2
            elseif esc == "u" then
                local hex = text:sub(pos + 2, pos + 5)
                if not hex:match("^%x%x%x%x$") then return _jerr(text, pos, "invalid unicode escape") end
                local code = tonumber(hex, 16)
                if code and code < 128 then table.insert(out, string.char(code)) else table.insert(out, "?") end
                pos = pos + 6
            else return _jerr(text, pos, "invalid escape") end
        else table.insert(out, c); pos = pos + 1 end
    end
    return _jerr(text, pos, "unterminated string")
end
local function _parse_number(text, pos)
    local start = pos
    if text:sub(pos, pos) == "-" then pos = pos + 1 end
    if text:sub(pos, pos) == "0" then pos = pos + 1
    else
        if not text:sub(pos, pos):match("%d") then return _jerr(text, pos, "expected number") end
        while text:sub(pos, pos):match("%d") do pos = pos + 1 end
    end
    if text:sub(pos, pos) == "." then
        pos = pos + 1
        if not text:sub(pos, pos):match("%d") then return _jerr(text, pos, "invalid fraction") end
        while text:sub(pos, pos):match("%d") do pos = pos + 1 end
    end
    local e = text:sub(pos, pos)
    if e == "e" or e == "E" then
        pos = pos + 1
        local sign = text:sub(pos, pos)
        if sign == "+" or sign == "-" then pos = pos + 1 end
        if not text:sub(pos, pos):match("%d") then return _jerr(text, pos, "invalid exponent") end
        while text:sub(pos, pos):match("%d") do pos = pos + 1 end
    end
    return tonumber(text:sub(start, pos - 1)), pos
end
local function _parse_array(text, pos)
    pos = _skip_ws(text, pos + 1)
    local arr = {}
    if text:sub(pos, pos) == "]" then return arr, pos + 1 end
    while true do
        local value
        value, pos = _parse_value(text, pos)
        if value == nil then return nil, pos end
        table.insert(arr, value); pos = _skip_ws(text, pos)
        local c = text:sub(pos, pos)
        if c == "]" then return arr, pos + 1 end
        if c ~= "," then return _jerr(text, pos, "expected ',' or ']'") end
        pos = _skip_ws(text, pos + 1)
    end
end
local function _parse_object(text, pos)
    pos = _skip_ws(text, pos + 1)
    local obj = {}
    if text:sub(pos, pos) == "}" then return obj, pos + 1 end
    while true do
        local key
        key, pos = _parse_string(text, pos)
        if key == nil then return nil, pos end
        pos = _skip_ws(text, pos)
        if text:sub(pos, pos) ~= ":" then return _jerr(text, pos, "expected ':'") end
        local value
        value, pos = _parse_value(text, _skip_ws(text, pos + 1))
        if value == nil then return nil, pos end
        if value ~= JSON.null then obj[key] = value end
        pos = _skip_ws(text, pos)
        local c = text:sub(pos, pos)
        if c == "}" then return obj, pos + 1 end
        if c ~= "," then return _jerr(text, pos, "expected ',' or '}'") end
        pos = _skip_ws(text, pos + 1)
    end
end
function _parse_value(text, pos)
    pos = _skip_ws(text, pos)
    local c = text:sub(pos, pos)
    if c == '"' then return _parse_string(text, pos) end
    if c == "{" then return _parse_object(text, pos) end
    if c == "[" then return _parse_array(text, pos) end
    if c == "-" or c:match("%d") then return _parse_number(text, pos) end
    if text:sub(pos, pos + 3) == "true" then return true, pos + 4 end
    if text:sub(pos, pos + 4) == "false" then return false, pos + 5 end
    if text:sub(pos, pos + 3) == "null" then return JSON.null, pos + 4 end
    return _jerr(text, pos, "unexpected token")
end
function JSON.decode(text)
    if type(text) ~= "string" then return nil, "expected JSON string" end
    local value, pos = _parse_value(text, 1)
    if value == nil then return nil, pos end
    pos = _skip_ws(text, pos)
    if pos <= #text then return _jerr(text, pos, "trailing data") end
    return value, nil
end

local bridge_timer = nil
local status_label = nil
local count_label = nil
local bridge_window = nil
local processed_count = 0
local failed_count = 0
local running = true
local close_requested = false

local function append_log(message)
    local f = io.open(LOG, "a")
    if f then
        f:write(os.date("!%Y-%m-%dT%H:%M:%SZ"), " ", tostring(message), "\n")
        f:close()
    else
        print("Hermes persistent bridge could not open log: " .. LOG)
    end
end

local function write_file(path, text)
    local f, err = io.open(path, "w")
    if not f then
        print("Hermes persistent bridge write failed " .. tostring(path) .. ": " .. tostring(err))
        append_log("write_file failed: " .. tostring(path) .. " " .. tostring(err))
        return false, err
    end
    f:write(text)
    f:close()
    return true
end

local function read_file(path, quiet)
    local f, err = io.open(path, "r")
    if not f then
        if not quiet then print("Hermes persistent bridge read failed " .. tostring(path) .. ": " .. tostring(err)) end
        return nil, err
    end
    local data = f:read("*a")
    f:close()
    return data
end

local function file_exists(path)
    local f = io.open(path, "r")
    if f then f:close(); return true end
    return false
end

local function basename(path)
    return tostring(path):match("([^/]+)$") or tostring(path)
end

local function dirname(path)
    return tostring(path):match("^(.*)/[^/]+$") or "."
end

local function expand_path(path)
    path = tostring(path)
    if path:sub(1, 1) == "~" then
        local home = os.getenv("HOME") or "/Users/craig"
        path = home .. path:sub(2)
    end
    return path
end

local function json_escape(s)
    s = tostring(s or "")
    s = s:gsub('\\', '\\\\'):gsub('"', '\\"'):gsub('\n', '\\n'):gsub('\r', '\\r'):gsub('\t', '\\t')
    return s
end

local function json_encode(value)
    local value_type = type(value)
    if value_type == "nil" then return "null" end
    if value_type == "boolean" then return tostring(value) end
    if value_type == "number" then return tostring(value) end
    if value_type == "string" then return "\"" .. json_escape(value) .. "\"" end
    if value_type ~= "table" then return "\"" .. json_escape(tostring(value)) .. "\"" end

    local is_array = true
    local max_index = 0
    for k, _ in pairs(value) do
        if type(k) ~= "number" or k < 1 or math.floor(k) ~= k then
            is_array = false
            break
        end
        if k > max_index then max_index = k end
    end

    local parts = {}
    if is_array then
        for i = 1, max_index do
            parts[#parts + 1] = json_encode(value[i])
        end
        return "[" .. table.concat(parts, ",") .. "]"
    end

    local keys = {}
    for k, _ in pairs(value) do keys[#keys + 1] = tostring(k) end
    table.sort(keys)
    for _, k in ipairs(keys) do
        parts[#parts + 1] = "\"" .. json_escape(k) .. "\":" .. json_encode(value[k])
    end
    return "{" .. table.concat(parts, ",") .. "}"
end

local function update_label(text)
    if status_label then pcall(function() status_label:updateProperties{ text=tostring(text) } end) end
    if count_label then pcall(function() count_label:updateProperties{ text="processed=" .. tostring(processed_count) .. " failed=" .. tostring(failed_count) } end) end
end

local function write_status(state, extra, stage_info)
    -- stage_info (optional table) carries the dashboard's honest render pipeline
    -- state. Unknown numeric fields are emitted as JSON null (never a fake 0%).
    local stage = (stage_info and stage_info.render_stage) or (state or "ok")
    local text = "{\n" ..
        "  \"bridge_seen\": true,\n" ..
        "  \"bridge\": \"hermes_bridge_persistent_v1.lua\",\n" ..
        "  \"mode\": \"persistent_window\",\n" ..
        "  \"status\": \"" .. json_escape(state or "ok") .. "\",\n" ..
        "  \"render_stage\": \"" .. json_escape(stage) .. "\",\n" ..
        "  \"updated_at\": \"" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\",\n" ..
        "  \"octane_available\": " .. tostring(octane ~= nil) .. ",\n" ..
        "  \"octane_node_available\": " .. tostring(octane ~= nil and octane.node ~= nil) .. ",\n" ..
        "  \"samples_done\": " .. ((stage_info and stage_info.samples_done ~= nil) and tostring(stage_info.samples_done) or "null") .. ",\n" ..
        "  \"samples_target\": " .. ((stage_info and stage_info.samples_target ~= nil) and tostring(stage_info.samples_target) or "null") .. ",\n" ..
        "  \"last_preview_path\": " .. ((stage_info and stage_info.last_preview_path) and ("\"" .. json_escape(stage_info.last_preview_path) .. "\"") or "null") .. ",\n" ..
        "  \"processed_count\": " .. tostring(processed_count) .. ",\n" ..
        "  \"failed_count\": " .. tostring(failed_count) .. ",\n" ..
        "  \"root\": \"" .. json_escape(ROOT) .. "\""
    if extra then text = text .. ",\n  \"last_event\": \"" .. json_escape(extra) .. "\"" end
    text = text .. "\n}\n"
    write_file(STATUS, text)
    update_label(state .. (extra and (": " .. tostring(extra)) or ""))
end

local function write_result(cmd, success, message, source_path, command_path, duration_ms)
    local output_paths = "[]"
    if cmd and cmd.op == "save_preview" then
        local preview_path = cmd.path or DEFAULT_PREVIEW
        output_paths = "[\"" .. json_escape(preview_path) .. "\"]"
    end
    local path = RESULTS .. "/" .. tostring(cmd and cmd.id or "unknown") .. ".json"
    local text = "{\n" ..
        "  \"schema_version\": \"1.0\",\n" ..
        "  \"command_id\": \"" .. json_escape(cmd and cmd.id or "unknown") .. "\",\n" ..
        "  \"op\": \"" .. json_escape(cmd and cmd.op or "unknown") .. "\",\n" ..
        "  \"success\": " .. tostring(success == true) .. ",\n" ..
        "  \"message\": \"" .. json_escape(message or "") .. "\",\n" ..
        "  \"processed_at\": \"" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\",\n" ..
        "  \"duration_ms\": " .. tostring(math.floor((duration_ms or 0) + 0.5)) .. ",\n" ..
        "  \"source_path\": \"" .. json_escape(source_path or "") .. "\",\n" ..
        "  \"command_path\": \"" .. json_escape(command_path or "") .. "\",\n" ..
        "  \"output_paths\": " .. output_paths .. "\n" ..
        "}\n"
    write_file(path, text)
    return path
end

local function request_bridge_close(reason)
    reason = reason or "releasing bridge window"
    if close_requested then
        append_log("bridge release already requested; ignoring duplicate: " .. tostring(reason))
        return
    end
    close_requested = true
    running = false
    append_log("bridge release requested: " .. tostring(reason))
    if bridge_timer then pcall(function() bridge_timer:stop() end); pcall(function() octane.timer.stop(bridge_timer) end) end
    write_status("releasing", reason)
    if bridge_window then
        local closed = false
        local ok = pcall(function() octane.gui.closeWindow(bridge_window) end)
        closed = closed or ok
        ok = pcall(function() bridge_window:closeWindow() end)
        closed = closed or ok
        append_log("bridge release close attempted closed=" .. tostring(closed))
    end
end

local function parse_command(raw)
    local decoded, err = JSON.decode(raw)
    if not decoded then return nil, err end
    local payload = decoded.payload or {}
    return {
        id = decoded.id or "unknown",
        op = decoded.op or "unknown",
        payload = payload,
        path = payload.path,
        name = payload.name,
        kind = payload.kind,
        preset = payload.preset,
        message = payload.message,
        object_name = payload.object_name,
        material_name = payload.material_name,
        fov = payload.fov,
        samples = payload.samples,
        width = payload.width,
        height = payload.height,
        color = payload.color,
        position = payload.position,
        target = payload.target,
    }
end

local function ensure_octane()
    if not (octane and octane.node and octane.project) then
        return false, "Octane node/project API unavailable; acknowledged only"
    end
    return true, nil
end

local function scene_graph()
    if not octane then return nil end
    if octane.project and octane.project.getSceneGraph then return octane.project.getSceneGraph() end
    if octane.nodegraph and octane.nodegraph.getRootGraph then return octane.nodegraph.getRootGraph() end
    return nil
end

local function find_item_by_name(name)
    if not name or name == "" then return nil end
    local graph = scene_graph()
    if not graph then return nil end
    local ok, items = pcall(function() return graph:findItemsByName(name) end)
    if ok and items and #items > 0 then return items[1] end
    ok, items = pcall(function() return graph:getOwnedItems() end)
    if ok and items then
        for _, item in ipairs(items) do
            local okp, props = pcall(function() return item:getProperties() end)
            if okp and props and props.name == name then return item end
        end
    end
    return nil
end

-- Return ALL nodes whose name matches (orphan-aware variant of find_item_by_name).
local function find_items_by_name(name)
    local out = {}
    if not name or name == "" then return out end
    local graph = scene_graph()
    if not graph then return out end
    local ok, items = pcall(function() return graph:findItemsByName(name) end)
    if ok and items then
        for _, it in ipairs(items) do out[#out + 1] = it end
    end
    ok, items = pcall(function() return graph:getOwnedItems() end)
    if ok and items then
        for _, item in ipairs(items) do
            local okp, props = pcall(function() return item:getProperties() end)
            if okp and props and props.name == name then out[#out + 1] = item end
        end
    end
    return out
end

-- Delete every node matching `name` except the first `keep_first`. Returns the
-- count deleted. Prevents the scene graph from accumulating duplicate Hermes_*
-- nodes that stale find_item_by_name would otherwise re-bind to. This is the
-- root-cause fix for "several geometry nodes not wired to anything": each
-- repeated render used to leave an orphaned mesh/camera/env that the RT then
-- failed to use, while the canonical node sat unused.
local function delete_items_by_name(name, keep_first)
    keep_first = keep_first or 0
    local items = find_items_by_name(name)
    local deleted = 0
    for i, item in ipairs(items) do
        if i > keep_first then
            local ok = pcall(function() octane.project.deleteItems({item}) end)
            if not ok then pcall(function() item:delete() end) end
            deleted = deleted + 1
        end
    end
    if deleted > 0 then append_log("delete_items_by_name: removed " .. tostring(deleted) .. " orphan node(s) named " .. tostring(name)) end
    return deleted
end

local function create_node(type_id, name, position)
    if not type_id then return nil, "missing node type for " .. tostring(name) end
    -- FIX (2026-07-12): target the MAIN scene graph explicitly via
    -- graphOwner=octane.project.getSceneGraph() (or nodegraph.getRootGraph()).
    -- Without this, octane.node.create lands nodes in the SCRIPT-local
    -- graph: they render (RT references them) but are NOT visible/editable
    -- in Octane's main outliner, so manual env/light edits in the UI
    -- hit a different graph and the scene looks like "only the RT node".
    -- The API export (octane_lua_api.txt line ~638) confirms node.create
    -- accepts a graphOwner field.
    -- NOTE: defined BEFORE ensure_canonical so the local is in scope
    -- at the call site (Lua local-forward-reference would be nil).
    local g = nil
    pcall(function()
        if octane.project and octane.project.getSceneGraph then g = octane.project.getSceneGraph() end
    end)
    if not g then pcall(function()
        if octane.nodegraph and octane.nodegraph.getRootGraph then g = octane.nodegraph.getRootGraph() end
    end) end
    local ok, node_or_err = pcall(function()
        if g then
            return octane.node.create{ type=type_id, name=name, position=position or {500, 500}, graphOwner=g }
        else
            return octane.node.create{ type=type_id, name=name, position=position or {500, 500} }
        end
    end)
    if ok then return node_or_err, nil end
    return nil, tostring(node_or_err)
end

-- Ensure exactly one canonical node of (type, name): delete duplicate orphans,
-- reuse the first if present, else create it. Then run setup(node). Returns the
-- canonical node (or nil).
local function ensure_canonical(type_id, name, position, setup)
    delete_items_by_name(name, 1)
    local node = find_item_by_name(name)
    if not node and type_id then
        local err
        node, err = create_node(type_id, name, position or {500, 500})
        if not node then append_log("ensure_canonical create failed " .. tostring(name) .. " err=" .. tostring(err)); return nil end
    end
    if node and setup then
        local ok, em = pcall(setup, node)
        if not ok then append_log("ensure_canonical setup failed " .. tostring(name) .. " err=" .. tostring(em)) end
    end
    return node
end

local function set_pin_value(node, pin, value)
    if not node or not pin then return false end
    local ok, err = pcall(function() node:setPinValue(pin, value) end)
    if not ok then append_log("setPinValue failed pin=" .. tostring(pin) .. " err=" .. tostring(err)) end
    return ok
end

local function connect_to(node, pin, src)
    if not node or not pin or not src then return false end
    local ok, err = pcall(function() node:connectTo(pin, src) end)
    if not ok then append_log("connectTo failed pin=" .. tostring(pin) .. " err=" .. tostring(err)) end
    return ok
end

local function disconnect_pin(node, pin)
    if not node or not pin then return false end
    local ok, err = pcall(function() node:disconnect(pin) end)
    if not ok then append_log("disconnect failed pin=" .. tostring(pin) .. " err=" .. tostring(err)) end
    return ok
end

local function connected_node_label(node, pin)
    if not node or not pin then return "nil" end
    local ok, connected = pcall(function() return node:getConnectedNode(pin) end)
    if ok then return tostring(connected) end
    ok, connected = pcall(function() return node:getConnectedNodeIx(pin) end)
    if ok then return tostring(connected) end
    return "<unknown>"
end

local function connected_node(node, pin)
    if not node or not pin then return nil end
    local ok, connected = pcall(function() return node:getConnectedNode(pin) end)
    if ok and connected then return connected end
    ok, connected = pcall(function() return node:getConnectedNodeIx(pin) end)
    if ok and connected then return connected end
    return nil
end

local function ensure_film_settings(rt)
    if not rt then return nil, "missing render target" end
    local pin = octane.P_FILM_SETTINGS or "filmSettings"
    local film = connected_node(rt, pin) or connected_node(rt, "filmSettings")
    if film then return film, nil end
    local film_type = octane.NT_FILM_SETTINGS
    if not film_type then return nil, "octane.NT_FILM_SETTINGS unavailable" end
    local created, err = create_node(film_type, "Hermes Film Settings", {520, 300})
    if not created then return nil, err end
    connect_to(rt, pin, created)
    return created, nil
end

local function set_render_resolution(rt, width, height)
    width = tonumber(width) or DEFAULT_WIDTH
    height = tonumber(height) or DEFAULT_HEIGHT
    local film, err = ensure_film_settings(rt)
    if not film then
        append_log("film resolution failed: " .. tostring(err))
        return false
    end
    local resolution = {width, height}
    local ok_any = false
    for _, pin in ipairs({octane.P_RESOLUTION, "resolution", "filmResolution", "res", "size"}) do
        if pin then ok_any = set_pin_value(film, pin, resolution) or ok_any end
    end
    for _, pin in ipairs({"width", "x", "filmWidth"}) do
        ok_any = set_pin_value(film, pin, width) or ok_any
    end
    for _, pin in ipairs({"height", "y", "filmHeight"}) do
        ok_any = set_pin_value(film, pin, height) or ok_any
    end
    append_log("film resolution requested " .. tostring(width) .. "x" .. tostring(height) .. " ok=" .. tostring(ok_any) .. " film=" .. tostring(film))
    return ok_any
end

-- Assign a material to a mesh's material pin(s). If group_index is provided,
-- only the Nth material pin (ordered by pin index) is wired; otherwise all
-- material pins are wired to the same material. This enables a single combined
-- OBJ with multiple usemtl groups (e.g. red cube group + green sphere group)
-- to receive distinct materials.
local function connect_material_to_mesh_pins(mesh, mat, group_index)
    local connected = false
    if not mesh or not mat then return connected end
    local ok_count, pin_count = pcall(function() return mesh:getPinCount() end)
    if not (ok_count and pin_count) then return connected end
    -- Each usemtl group becomes a material INPUT pin named after the group.
    -- This build does NOT expose octane.PT_MATERIAL (the pins report type=7),
    -- and connectTo by numeric index fails -- the pin must be addressed by its
    -- NAME (e.g. "earth_ice"). Record both index and name; connect by name.
    local material_pins = {}  -- list of {index, name}
    local NON_MATERIAL = {
        position = true, rotation = true, scale = true, transform = true,
        geometry = true, ["imported mesh"] = true, mesh = true,
        ["object layer"] = true, visibility = true, ["medium"] = true,
        displacement = true, ["hdr tail"] = true,
    }
    for i = 1, pin_count do
        local ok_info, info = pcall(function() return mesh:getPinInfoIx(i) end)
        if not ok_info then ok_info, info = pcall(function() return mesh:getPinInfoIx(i - 1) end) end
        if ok_info and info then
            local nm = tostring(info.name or "")
            local lbl = string.lower(tostring(info.label or ""))
            local is_material = (octane.PT_MATERIAL and info.type == octane.PT_MATERIAL)
                or (lbl == "material")
                or (nm ~= "" and not NON_MATERIAL[string.lower(nm)] and not NON_MATERIAL[lbl])
            if is_material then
                material_pins[#material_pins + 1] = { index = i, name = nm }
            end
        end
    end
    local n_pins = #material_pins
    if group_index then
        local target = tonumber(group_index)
        local p = material_pins[target]
        append_log("material group #" .. tostring(target) .. " -> pin " .. tostring(p and p.name) .. " (of " .. tostring(n_pins) .. " material pins)")
        if p and p.name then
            connected = connect_to(mesh, p.name, mat) or connected
        end
    else
        for _, p in ipairs(material_pins) do
            if p.name then connected = connect_to(mesh, p.name, mat) or connected end
        end
    end
    return connected
end

local function connect_material_to_all_mesh_pins(mesh, mat)
    return connect_material_to_mesh_pins(mesh, mat, nil)
end

local function get_or_create_render_target()
    local rt = find_item_by_name("Hermes Render Target") or find_item_by_name("Hermes_RT")
    if rt then return rt end
    local node, err = create_node(octane.NT_RENDERTARGET, "Hermes Render Target", {300, 300})
    if not node then return nil, err end
    return node, nil
end

local function ensure_connected_node(node, pin, type_id, name, position)
    if not node or not pin or not type_id then return nil end
    local existing = connected_node(node, pin)
    if existing then return existing end
    local item = find_item_by_name(name)
    if not item then item = create_node(type_id, name, position) end
    if item then connect_to(node, pin, item) end
    return item
end

local function ensure_render_target_defaults(rt)
    if not rt then return false end
    ensure_connected_node(rt, octane.P_KERNEL or "kernel", octane.NT_KERN_DIRECTLIGHTING, "Hermes Direct Lighting Kernel", {520, 160})
    ensure_connected_node(rt, octane.P_ANIMATION or "animation", octane.NT_ANIMATION_SETTINGS, "Hermes Animation Settings", {520, 220})
    ensure_connected_node(rt, octane.P_RENDER_LAYER or "renderLayer", octane.NT_RENDER_LAYER, "Hermes Render Layer", {520, 360})
    ensure_connected_node(rt, octane.P_RENDER_PASSES or "renderPasses", octane.NT_RENDER_AOV_GROUP, "Hermes Render AOV Group", {520, 420})
    ensure_connected_node(rt, octane.P_OUTPUT_AOVS or "compositeAovs", octane.NT_OUTPUT_AOV_GROUP, "Hermes Output AOV Group", {520, 480})
    ensure_connected_node(rt, octane.P_IMAGER or "imager", octane.NT_IMAGER_CAMERA, "Hermes Imager", {520, 540})
    ensure_connected_node(rt, octane.P_POST_PROCESSING or "postproc", octane.NT_POSTPROCESSING, "Hermes Post Processing", {520, 600})
    ensure_film_settings(rt)
    return true
end

local function activate_render_target(rt)
    if not rt then return false end
    local activated = false
    if octane and octane.project then
        local ok = pcall(function() octane.project.setSelection{rt} end)
        activated = activated or ok
        ok = pcall(function() octane.project.setSelection({rt}) end)
        activated = activated or ok
        ok = pcall(function() octane.project.select(rt) end)
        activated = activated or ok
    end
    -- Selecting the RT node in the graph is NOT sufficient on this Octane build:
    -- the engine renders whatever RT is *active in the main viewport*, and
    -- setSelection alone does not switch that. The user previously had to
    -- manually re-select the RT node in the UI before the engine would render
    -- it. There is no documented public setter for the active RT, so we probe
    -- the most likely setter names (each pcall-wrapped, non-fatal) and log
    -- which one actually switches the active target. This is how we learn the
    -- working API without risking the render-wedge that start{rt} causes.
    local setter_candidates = {
        { "octane.render.setRenderTargetNode(rt)", function() return octane.render.setRenderTargetNode(rt) end },
        { "octane.project.setRenderTargetNode(rt)", function() return octane.project.setRenderTargetNode(rt) end },
        { "octane.project.setActiveRenderTarget(rt)", function() return octane.project.setActiveRenderTarget(rt) end },
        { "octane.render.setRenderTarget(rt)", function() return octane.render.setRenderTarget(rt) end },
        { "octane.project.setRenderTarget(rt)", function() return octane.project.setRenderTarget(rt) end },
    }
    for _, cand in ipairs(setter_candidates) do
        local ok, result = pcall(cand[2])
        if ok and result ~= false then
            activated = true
            append_log("activated render target via " .. cand[1] .. " result=" .. tostring(result))
            break
        end
    end
    if activated then append_log("activated render target " .. tostring(rt)) end
    return activated
end

local function try_render_call(label, fn)
    local ok, result = pcall(fn)
    append_log("render attempt " .. tostring(label) .. " ok=" .. tostring(ok) .. " result=" .. tostring(result))
    return ok, result
end

-- Defined before request_render_restart so the `local` is bound at call time
-- (a `local function` is only visible after its declaration line).
local function sleep_seconds(seconds)
    seconds = tonumber(seconds) or 0.25
    if octane and octane.sleep then
        local ok = pcall(function() octane.sleep(seconds) end)
        if ok then return end
    end
    os.execute("sleep " .. tostring(seconds))
end

local function request_render_restart(samples, width, height, do_start, max_render_time)
    -- Bulletproof: called from EVERY scene-assembly handler (import_geometry,
    -- create_material, set_camera, set_lighting, save_preview). A hard error
    -- here would abort the whole drain script and strand the rest of the queue,
    -- so the ENTIRE body runs inside one pcall. Any internal failure returns
    -- (false, err) so callers log an honest failure instead of dropping the cmd.
    --
    -- do_start (default true): whether to actually call octane.render.start{}.
    -- Scene-assembly handlers pass do_start=false so they only WIRE the scene
    -- (RT/camera/materials) and return immediately. This is critical for batch
    -- drains: octane.render.start{} BLOCKS for the render duration on this build,
    -- so calling it per-command wedges the drain script (a re-click is ignored
    -- while the script is busy, and the queue never fully empties). Only
    -- handle_save_preview passes do_start=true, performing the single real
    -- render + wait + save at the end.
    do_start = (do_start ~= false)  -- only explicit false skips the start
    local ok, a, b = pcall(function()
        if not (octane and octane.render) then return true, "Octane render API unavailable; acknowledged only" end
        append_log("request_render_restart: entered samples=" .. tostring(samples) .. " do_start=" .. tostring(do_start))
        local rt, rt_err = get_or_create_render_target()
        if not rt then return false, "render target failed: " .. tostring(rt_err) end
        pcall(ensure_render_target_defaults, rt)
        pcall(activate_render_target, rt)
        pcall(set_render_resolution, rt, width or DEFAULT_WIDTH, height or DEFAULT_HEIGHT)
        samples = samples or 64
        -- Bound the actual render to the requested convergence ceiling. Without
        -- this, octane.render.start{} runs to the RT film's pre-existing
        -- maxSamples (e.g. 5000) and ignores cmd.samples/timeout entirely.
        local film = ensure_film_settings(rt)
        if film then
            -- Best-effort cap. NOTE (2026-07-12): this Octane X build's
            -- Lua API does NOT expose film attribute constants (octane.A_*)
            -- nor enumerable attributes (getAttributeCount()==0). The bridge
            -- CANNOT set maxSamples/maxRenderTime programmatically; the
            -- reliable fast-preview path is to set Kernel>Max samples in
            -- Octane X's UI once (persists in the RT). This attempt is a
            -- no-op on this build but harmless and documents intent.
            local max_spp = tonumber(samples) or 64
            pcall(function() film:setAttribute("maxSamples", max_spp, true) end)
            local mrt = tonumber(max_render_time)
            if mrt and mrt > 0 then pcall(function() film:setAttribute("maxRenderTime", mrt, true) end) end
            append_log("film cap set maxSamples=" .. tostring(max_spp) .. " maxRenderTime=" .. tostring(mrt or "unset"))
        end
        -- Camera guard: octane.render.start{} must NOT run until a camera is
        -- connected to the RT. During scene assembly the camera is not wired
        -- yet, and start{} with no camera aborts the script. Defer the start to
        -- save_preview, where set_camera has connected the camera.
        local cam_pin = octane.P_CAMERA or "camera"
        local cam_label = nil
        pcall(function() cam_label = connected_node_label(rt, cam_pin) end)
        local cam_connected = cam_label ~= nil and cam_label ~= ""
        if not cam_connected then
            append_log("request_render_restart: no camera on RT; deferring start{} to save_preview")
            return true, "render start deferred (no camera yet; will start at save_preview)"
        end
        -- Deferred-start path: scene-assembly handlers (import/material/camera/
        -- lighting) only WIRE the scene and return. They must NOT call
        -- octane.render.start{} here because start{} blocks for the render
        -- duration and wedges the batch drain (a re-click is ignored while the
        -- script is busy). Only save_preview (do_start=true) performs the real
        -- render. The camera is connected now, so the deferred start at
        -- save_preview will have a valid RT+camera to begin from.
        if not do_start then
            append_log("request_render_restart: do_start=false; scene wired, start deferred to save_preview")
            return true, "scene wired; render start deferred (do_start=false)"
        end
        pcall(function() if octane.render.stop then octane.render.stop() end end)
        pcall(function() octane.render.pause() end)
        local last_err = "no attempts made"
        local started = false
        local function engine_running()
            if not (octane and octane.render and octane.render.getRenderResultStatistics) then return false end
            local ok_s, stats = pcall(function() return octane.render.getRenderResultStatistics() end)
            if not (ok_s and type(stats) == "table") then return false end
            if stats.hasPendingUpdates == true then return true end
            if tostring(stats.renderState) == "4" then return true end
            return false
        end
        for attempt = 1, 5 do
            local ok1, result = try_render_call("start{renderTargetNode=rt}", function() return octane.render.start{ renderTargetNode = rt } end)
            if ok1 and engine_running() then started = true; break end
            ok1, result = try_render_call("restart()", function() return octane.render.restart() end)
            if ok1 and engine_running() then started = true; break end
            ok1, result = try_render_call("continue()", function() return octane.render.continue() end)
            if ok1 and engine_running() then started = true; break end
            last_err = tostring(result)
            sleep_seconds(0.5)
        end
        if not started then
            return false, "render engine did not start running after retries (stale-frame risk); last: " .. last_err
        end
        return true, "render start requested (RT " .. tostring(rt) .. "; engine running; bounded by wait_for_render_ready)"
    end)
    if not ok then
        append_log("request_render_restart: HARD ERROR caught: " .. tostring(a))
        return false, "request_render_restart crashed: " .. tostring(a)
    end
    return a, b
end


local function render_stat_number(stats, key)
    if type(stats) ~= "table" then return 0 end
    return tonumber(stats[key]) or 0
end

local function wait_for_render_ready(min_samples, timeout_seconds)
    min_samples = tonumber(min_samples) or 16
    timeout_seconds = tonumber(timeout_seconds) or 10
    if not (octane and octane.render and octane.render.getRenderResultStatistics) then
        return true, "render statistics unavailable; continuing"
    end
    local last = "no statistics yet"
    local got_stats = false
    local attempts = math.max(1, math.floor((timeout_seconds / 0.5) + 0.5))
    for _ = 1, attempts do
        local ok, stats = pcall(function() return octane.render.getRenderResultStatistics() end)
        if ok and type(stats) == "table" then
            got_stats = true
            local beauty = render_stat_number(stats, "beautySamplesPerPixel")
            local info = render_stat_number(stats, "infoSamplesPerPixel")
            local pending = stats.hasPendingUpdates == true
            local state = tostring(stats.renderState)
            last = "beauty=" .. tostring(beauty) .. " info=" .. tostring(info) .. " pending=" .. tostring(pending) .. " state=" .. state
            if (beauty >= min_samples or info >= min_samples) and not pending then
                append_log("render ready for preview: " .. last)
                return true, last
            end
        else
            last = "stats err/nil: " .. tostring(stats)
        end
        sleep_seconds(0.5)
    end
    -- If we never got valid stats, the render loop may still be producing a
    -- frame; don't block the capture on a polling API that returned nil.
    append_log("render preview readiness: got_stats=" .. tostring(got_stats) .. " last=" .. last)
    if got_stats then
        return false, last
    end
    return true, "stats unavailable after polling; attempting save anyway"
end

local function latest_imported_geometry_fallback()
    local graph = scene_graph()
    if graph then
        local ok, nodes = pcall(function() return graph:findNodes(octane.NT_GEO_MESH, true) end)
        if ok and nodes and #nodes > 0 then return nodes[#nodes] end
    end
    return find_item_by_name("octane_live_cube") or find_item_by_name("concept_anchor_cube") or find_item_by_name("hermes_mcp_cube")
end

local function maybe_connect_geometry_to_rt(mesh)
    local rt = get_or_create_render_target()
    if not rt or not mesh then return false end
    activate_render_target(rt)
    local mesh_pin = octane.P_MESH or "mesh"
    disconnect_pin(rt, mesh_pin)
    disconnect_pin(rt, "mesh")
    local connected = connect_to(rt, mesh_pin, mesh) or connect_to(rt, "mesh", mesh)
    append_log("render target mesh connection requested mesh=" .. tostring(mesh) .. " connected=" .. tostring(connected) .. " now=" .. connected_node_label(rt, mesh_pin))
    return connected
end

local function handle_import_geometry(cmd)
    local ok, msg = ensure_octane()
    if not ok then return true, msg end
    if not cmd.path then return false, "import_geometry missing path" end
    local name = cmd.name or basename(cmd.path)
    -- Canonical mesh: delete duplicate orphans, keep/create ONE mesh node, then
    -- wire it to the RT so the geometry is actually in the scene graph (no
    -- orphaned meshes left unwired).
    local mesh = ensure_canonical(octane.NT_GEO_MESH, name, {500, 500}, function(m)
        pcall(function() m:setAttribute(octane.A_FILENAME, cmd.path, true) end)
    end)
    if not mesh then return false, "create mesh failed: " .. tostring(name) end
    maybe_connect_geometry_to_rt(mesh)
    local refreshed, refresh_msg = request_render_restart(64, nil, nil, false)
    append_log("post-import render refresh ok=" .. tostring(refreshed) .. " msg=" .. tostring(refresh_msg))
    return true, "imported geometry " .. tostring(name)
end

local function handle_create_material(cmd)
    local ok, msg = ensure_octane()
    if not ok then return true, msg end
    local name = cmd.name or "mcp_material"
    -- Canonical material: delete duplicate orphans, then create fresh so the
    -- CURRENT spec (color/kind/roughness/...) is actually applied. The old
    -- "if existing then return" silently kept a stale material.
    local matType = octane.NT_MAT_DIFFUSE
    if cmd.kind == "glossy" and octane.NT_MAT_GLOSSY then matType = octane.NT_MAT_GLOSSY end
    if cmd.kind == "specular" and octane.NT_MAT_SPECULAR then matType = octane.NT_MAT_SPECULAR end
    if cmd.kind == "metallic" and octane.NT_MAT_METALLIC then matType = octane.NT_MAT_METALLIC end
    local mat = ensure_canonical(matType, name, {650, 500}, function(m)
        local col = cmd.color or cmd.diffuse or cmd.albedo or {0.8, 0.8, 0.8}
        local function setdef(pin, val)
            if val ~= nil then
                local okp, w = pcall(set_pin_value, m, pin, val)
                if not okp then append_log("material pin " .. tostring(pin) .. " unsupported: " .. tostring(w)) end
            end
        end
        setdef(octane.P_DIFFUSE or "diffuse", {col[1] or 0.8, col[2] or 0.8, col[3] or 0.8})
        setdef(octane.P_ROUGHNESS or "roughness", cmd.roughness)
        setdef(octane.P_SPECULAR or "specular", cmd.specular)
        setdef(octane.P_METALLIC or "metallic", cmd.metallic)
        setdef(octane.P_TRANSMISSION or "transmission", cmd.transmission)
        setdef(octane.P_INDEX or "ior", cmd.ior)
        setdef(octane.P_OPACITY or "opacity", cmd.opacity)
        setdef(octane.P_CLEARCOAT or "clearcoat", cmd.clearcoat)
        setdef(octane.P_ANISOTROPY or "anisotropy", cmd.anisotropy)
        setdef(octane.P_EMISSION or "emission", cmd.emission)
        -- File paths are not valid scalar values for material texture pins.
        -- Build an image-texture node, load its filename attribute, then wire
        -- the node into the material's first texture-type pin.  We do NOT
        -- hardcode the pin name (P_DIFFUSE / P_ALBEDO / etc.) because the
        -- exported API corpus does not enumerate per-build pin constants;
        -- instead we scan the material node's pins for one whose value type
        -- is PT_TEXTURE and connect there.  The earlier direct
        -- set_pin_value(path) silently produced a white material.
        --
        -- The image node type may be octane.NT_TEX_IMAGE in this build, or it
        -- may be absent.  We resolve it at runtime: try NT_TEX_IMAGE; if that
        -- global is nil or node.create fails, fall back to NT_TEX_RGB (which
        -- the corpus confirms exists) and log which type actually worked.
        local function make_image_node(node_name, file_path)
            local tried, made, errmsg = nil, nil, nil
            for _, t in ipairs({octane.NT_TEX_IMAGE, octane.NT_TEX_RGB}) do
                if t then
                    tried = tostring(t)
                    local n, e = create_node(t, node_name, {600, 560})
                    if n then
                        local loaded = pcall(function() n:setAttribute(octane.A_FILENAME, file_path, true) end)
                        return n, tried, loaded
                    else
                        errmsg = tostring(e)
                    end
                end
            end
            return nil, tried, false, errmsg
        end
        if cmd.texture_path then
            local tex, ntype, loaded = make_image_node(name .. "_albedo", cmd.texture_path)
            if tex then
                local wired_pin = nil
                pcall(function()
                    local count = m:getPinCount()
                    for i = 0, count - 1 do
                        local info = m:getPinInfoIx(i)
                        if info and (info.type == 4 or info.type == "PT_TEXTURE") then
                            if connect_to(m, i, tex) then wired_pin = tostring(info.name or i); break end
                        end
                    end
                end)
                append_log("image texture albedo node=" .. tostring(ntype)
                    .. " path=" .. tostring(cmd.texture_path)
                    .. " loaded=" .. tostring(loaded) .. " wired_pin=" .. tostring(wired_pin))
            else
                append_log("image texture albedo FAILED node=" .. tostring(ntype) .. " path=" .. tostring(cmd.texture_path))
            end
        end
        if cmd.normal_path then
            local normal, ntype, loaded = make_image_node(name .. "_normal", cmd.normal_path)
            if normal then
                local wired_pin = nil
                pcall(function()
                    local count = m:getPinCount()
                    for i = 0, count - 1 do
                        local info = m:getPinInfoIx(i)
                        if info and (info.type == 4 or info.type == "PT_TEXTURE") then
                            if connect_to(m, i, normal) then wired_pin = tostring(info.name or i); break end
                        end
                    end
                end)
                append_log("image texture normal node=" .. tostring(ntype)
                    .. " path=" .. tostring(cmd.normal_path)
                    .. " loaded=" .. tostring(loaded) .. " wired_pin=" .. tostring(wired_pin))
            else
                append_log("image texture normal FAILED node=" .. tostring(ntype) .. " path=" .. tostring(cmd.normal_path))
            end
        end
    end)
    if not mat then return false, "create material failed: " .. tostring(name) end
    return true, "created material " .. tostring(name)
end

local function handle_create_light(cmd)
    local ok, msg = ensure_octane()
    if not ok then return true, msg end
    local name = cmd.name or "mcp_light"
    local light_type = cmd.light_type or "emissive"
    local intensity = cmd.intensity or 10
    -- NOTE: native NT_LIGHT_* node types are NOT scripting-exposed on this
    -- Octane X build (octane.NT_LIGHT_AREA / NT_LIGHT_SUN are nil). The only
    -- scene-lightable primitives are environment nodes (NT_ENV_DAYLIGHT) and
    -- emissive materials (NT_MAT_EMISSIVE, applied to geometry). We map:
    --   sun_light / environment / daylight -> daylight environment node
    --   area/point/spot/directional/emissive -> emissive material proxy
    if light_type == "sun_light" or light_type == "environment" or light_type == "daylight" then
        local rt, rt_err = get_or_create_render_target()
        if not rt then return false, "render target failed: " .. tostring(rt_err) end
        activate_render_target(rt)
        local env_type = octane.NT_ENV_DAYLIGHT or octane.NT_ENV_TEXTURE
        if not env_type then return true, "no known environment node type constant" end
        -- Canonical environment: delete orphan nodes, keep one.
        local env = ensure_canonical(env_type, name, {300, 680})
        if not env then return false, "environment create failed" end
        connect_to(rt, octane.P_ENVIRONMENT or "environment", env)
        local refreshed, refresh_msg = request_render_restart(64, nil, nil, false)
        append_log("post-light render refresh ok=" .. tostring(refreshed) .. " msg=" .. tostring(refresh_msg))
        return true, "created environment light " .. tostring(name) .. " (" .. tostring(light_type) .. ")"
    end
    -- emissive-material proxy: build a small sphere/box mesh at cmd.position
    -- (default above the scene) with an emissive material, so it actually
    -- emits light into the scene (a material-only node is an orphan with no
    -- geometry to glow from). Native NT_LIGHT_* node types are nil on this
    -- build, so this is the only scriptable local-light path.
    local existing = find_item_by_name(name)
    if existing then return true, "light/material exists " .. tostring(name) end
    local pos = cmd.position or {0, 8, 6}
    local geo_type = octane.NT_GEO_SPHERE or octane.NT_GEO_BOX or octane.NT_GEO_PLANE
    if not geo_type then
        return true, "no primitive geometry node type available for light proxy"
    end
    local mesh, merr = create_node(geo_type, name, {760, 500})
    if not mesh then return false, "create light mesh failed: " .. tostring(merr) end
    -- shrink the proxy so it reads as a light, not a boulder
    pcall(function() set_pin_value(mesh, octane.P_SCALE or "scale", {1.2, 1.2, 1.2}) end)
    pcall(function() set_pin_value(mesh, "position", pos) end)
    local mat, err = create_node(octane.NT_MAT_EMISSIVE or octane.NT_MAT_DIFFUSE, name .. "_mat", {820, 500})
    if not mat then return false, "create light material failed: " .. tostring(err) end
    local rgb = cmd.color or {1.0, 0.95, 0.85}
    pcall(set_pin_value, mat, octane.P_EMISSION or "emission", {rgb[1] or 1, rgb[2] or 1, rgb[3] or 1})
    pcall(set_pin_value, mat, octane.P_POWER or "power", intensity)
    connect_to(mesh, octane.P_MATERIAL or "material", mat)
    return true, "created emissive light proxy " .. tostring(name) .. " (" .. tostring(light_type) .. ") at " .. tostring(pos[1]) .. "," .. tostring(pos[2]) .. "," .. tostring(pos[3])
end

local function handle_assign_material(cmd)
    local ok, msg = ensure_octane()
    if not ok then return true, msg end
    local mesh = find_item_by_name(cmd.object_name) or latest_imported_geometry_fallback()
    local mat = find_item_by_name(cmd.material_name)
    if not mesh then return false, "unknown object " .. tostring(cmd.object_name) end
    if not mat then return false, "unknown material " .. tostring(cmd.material_name) end
    local group_index = cmd.group_index or cmd.payload and cmd.payload.group_index
    -- DIAGNOSTIC (2026-07-12): dump the mesh's pin structure so we learn the
    -- real material-pin identifier on this build (octane.PT_MATERIAL appears
    -- nil, and no pin is literally named "Material"). Remove once wired.
    pcall(function()
        local okc, pc = pcall(function() return mesh:getPinCount() end)
        if okc and pc then
            local parts = {}
            for i = 1, pc do
                local oki, info = pcall(function() return mesh:getPinInfoIx(i) end)
                if oki and info then
                    parts[#parts + 1] = string.format("#%d name=%s type=%s label=%s", i,
                        tostring(info.name), tostring(info.type), tostring(info.label))
                end
            end
            append_log("MESH_PINS(" .. tostring(pc) .. "): " .. table.concat(parts, " | "))
        end
    end)
    local connected = connect_material_to_mesh_pins(mesh, mat, group_index)
    if connected then
        local refreshed, refresh_msg = request_render_restart(64, nil, nil, false)
        append_log("post-material render refresh ok=" .. tostring(refreshed) .. " msg=" .. tostring(refresh_msg))
        return true, "assigned material " .. tostring(cmd.material_name) .. (group_index and (" to group #" .. tostring(group_index)) or "")
    end
    return true, "material exists; no known material pin accepted on mesh"
end

local function handle_set_camera(cmd)
    local ok, msg = ensure_octane()
    if not ok then return true, msg end
    local rt, rt_err = get_or_create_render_target()
    if not rt then return false, "render target failed: " .. tostring(rt_err) end
    activate_render_target(rt)
    -- Canonical camera: delete orphan Hermes Camera nodes, keep one, reconnect.
    local cam = ensure_canonical(octane.NT_CAM_THINLENS or octane.NT_CAM_PANORAMIC, "Hermes Camera", {300, 520}, function(c)
        if cmd.fov then set_pin_value(c, octane.P_FOV or "fov", cmd.fov) end
        if cmd.position then set_pin_value(c, octane.P_POSITION or "pos", cmd.position) end
        if cmd.target then set_pin_value(c, octane.P_TARGET or "target", cmd.target) end
        if cmd.up then set_pin_value(c, octane.P_UP or "up", cmd.up) end
        -- FOCUS FIX: honour recipe aperture when provided (user-set in viewport),
        -- else force near-pinhole (0.0) for a sharp subject.
        local ap_val = cmd.aperture ~= nil and cmd.aperture or 0.0
        for _, ap in ipairs({octane.P_APERTURE or "aperture", "aperture", "fstop", "fStop", "lensRadius", "apertureRadius"}) do
            set_pin_value(c, ap, ap_val)
        end
        local dist = 10.0
        if cmd.position and cmd.target then
            local dx = (cmd.position[1] or 0) - (cmd.target[1] or 0)
            local dy = (cmd.position[2] or 0) - (cmd.target[2] or 0)
            local dz = (cmd.position[3] or 0) - (cmd.target[3] or 0)
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        end
        if cmd.focus_distance then dist = cmd.focus_distance end
        for _, fd in ipairs({octane.P_FOCUSDISTANCE or "focusDistance", "focusDistance", "focusDist", "focalDepth", "focus"}) do
            set_pin_value(c, fd, dist)
        end
        append_log("camera focus dist=" .. tostring(dist) .. " aperture=" .. tostring(ap_val))
    end)
    if not cam then return false, "camera create failed" end
    connect_to(rt, octane.P_CAMERA or "camera", cam)
    local refreshed, refresh_msg = request_render_restart(64, nil, nil, false)
    append_log("post-camera render refresh ok=" .. tostring(refreshed) .. " msg=" .. tostring(refresh_msg))
    return true, "camera connected"
end

-- Read the LIVE camera pose so a user-set viewport angle can be captured and
-- re-applied exactly. Writes the resolved pose to RESULTS/get_camera.json.
local function read_camera_pin(cam, keys)
    for _, k in ipairs(keys) do
        local ok, v = pcall(function() return cam:getPinValue(k) end)
        if ok and v ~= nil then return v end
    end
    return nil
end

local function handle_get_camera(cmd)
    local ok, msg = ensure_octane()
    if not ok then return true, msg end
    local cam = find_item_by_name("Hermes Camera")
    if not cam then
        local rt = get_or_create_render_target()
        if rt then
            local okc, cnode = pcall(function() return rt:getConnectedNodes(octane.P_CAMERA or "camera") end)
            if okc and cnode then cam = cnode end
        end
    end
    if not cam then return false, "no camera node found" end
    local result = { timestamp = os.date("!%Y-%m-%dT%H:%M:%SZ") }
    local pos = read_camera_pin(cam, { octane.P_POSITION or "pos", "position", "pos" })
    local tgt = read_camera_pin(cam, { octane.P_TARGET or "target", "target" })
    local fov = read_camera_pin(cam, { octane.P_FOV or "fov", "fov", "fieldOfView" })
    local up  = read_camera_pin(cam, { octane.P_UP or "up", "up" })
    if pos then
        if type(pos) == "userdata" then
            pcall(function() result.position = { pos[1], pos[2], pos[3] } end)
        elseif type(pos) == "table" then
            result.position = { pos[1], pos[2], pos[3] }
        end
    end
    if tgt then
        if type(tgt) == "userdata" then
            pcall(function() result.target = { tgt[1], tgt[2], tgt[3] } end)
        elseif type(tgt) == "table" then
            result.target = { tgt[1], tgt[2], tgt[3] }
        end
    end
    if fov ~= nil then
        if type(fov) == "userdata" then pcall(function() result.fov = fov[1] end)
        else result.fov = tonumber(fov) end
    end
    if up then
        if type(up) == "userdata" then
            pcall(function() result.up = { up[1], up[2], up[3] } end)
        elseif type(up) == "table" then
            result.up = { up[1], up[2], up[3] }
        end
    end
    local path = RESULTS .. "/get_camera.json"
    write_file(path, json_encode(result) .. "\n")
    local summary = string.format("position=%s target=%s fov=%s up=%s",
        result.position and table.concat(result.position, ",") or "nil",
        result.target and table.concat(result.target, ",") or "nil",
        result.fov or "nil",
        result.up and table.concat(result.up, ",") or "nil")
    append_log("get_camera " .. summary)
    return true, "camera pose written: " .. path .. " | " .. summary
end

local function handle_set_lighting(cmd)
    local ok, msg = ensure_octane()
    if not ok then return true, msg end
    -- TEMP INTROSPECTION: enumerate the octane module's attribute/node
    -- constants so we learn the EXACT A_* names this build exposes
    -- (GetPinInfo returns non-iterable cdata, so node-pin dumps fail).
    -- Guarded; remove once dark_studio + film cap are bound correctly.
    pcall(function()
        local want = {"SKY","SUN","HORIZON","RENDER","SAMPLE","ENV","MAX","DAYLIGHT","POWER","INTENSITY","TEXTURE","GROUND","TURBIDITY","NORTH"}
        local found = {}
        local okp, t = pcall(function() return octane and pairs(octane) end)
        if okp and t then
            for k, v in t do
                local ks = tostring(k)
                for _, w in ipairs(want) do
                    if string.find(ks:upper(), w) then found[#found+1] = ks .. "=" .. tostring(v); break end
                end
            end
        end
        table.sort(found)
        append_log("OCTANE_CONSTANTS count=" .. tostring(#found) .. " " .. table.concat(found, " "))
    end)
    local rt, rt_err = get_or_create_render_target()
    if not rt then return false, "render target failed: " .. tostring(rt_err) end
    activate_render_target(rt)
    local preset = cmd.preset or "default"
    if preset == "planetary" then
        -- User-selected Planetary environment (switched live in the viewport).
        -- This build's Lua constants may not expose NT_ENV_PLANETARY by name,
        -- so probe it defensively and fall back to daylight if unavailable.
        local env_type = octane.NT_ENV_PLANETARY or octane.NT_ENV_DAYLIGHT or octane.NT_ENV_TEXTURE
        if not env_type then return true, "no known environment node type constant" end
        local env = ensure_canonical(env_type, "Hermes Environment", {300, 680})
        if not env then return false, "planetary environment create failed" end
        connect_to(rt, octane.P_ENVIRONMENT or "environment", env)
        local pp = cmd.planetary or {}
        for _, pin in ipairs({
            "latitude", "longitude", "month", "day", "localTime", "gmtOffset",
            "skyTurbidity", "power", "sunIntensity", "sunSize", "northOffset",
        }) do
            if pp[pin] ~= nil then
                set_pin_value(env, pin, pp[pin])
            end
        end
        local refreshed, refresh_msg = request_render_restart(64, nil, nil, false)
        append_log("post-lighting(planetary) render refresh ok=" .. tostring(refreshed) .. " msg=" .. tostring(refresh_msg))
        return true, "lighting preset planetary connected"
    end
    if preset == "dark_studio" then
        -- True dark studio (VERIFIED 2026-07-12): build an NT_ENV_TEXTURE
        -- fed by a near-black NT_TEX_RGB. Both node types exist + are
        -- creatable on this build (probe DARK_ENV.built=true). This gives
        -- a real dark background (no blue daylight sky) and replaces the
        -- earlier no-op daylight-env darkening (env attrs are opaque:
        -- getAttributeCount()==1, no settable sun/sky pins).
        -- Native NT_LIGHT_* node types are nil on this build, so local
        -- illumination comes from emissive-material proxies (see
        -- handle_create_light), positioned at the subject.
        local tex = create_node(octane.NT_TEX_RGB, "Hermes Dark Color", {200, 700})
        if not tex then return false, "dark studio color texture failed" end
        set_pin_value(tex, octane.P_COLOR or "color", {0.015, 0.015, 0.02})
        local env = create_node(octane.NT_ENV_TEXTURE, "Hermes Environment", {300, 680})
        if not env then return false, "dark studio environment create failed" end
        connect_to(env, octane.P_TEXTURE or "texture", tex)
        connect_to(rt, octane.P_ENVIRONMENT or "environment", env)
        local refreshed, refresh_msg = request_render_restart(64, nil, nil, false)
        append_log("post-lighting(dark_studio) render refresh ok=" .. tostring(refreshed) .. " msg=" .. tostring(refresh_msg))
        return true, "dark studio environment connected"
    end
    local env_type = octane.NT_ENV_DAYLIGHT or octane.NT_ENV_TEXTURE
    if not env_type then return true, "no known environment node type constant" end
    -- Canonical environment: delete orphan Hermes Environment nodes, keep one.
    local env = ensure_canonical(env_type, "Hermes Environment", {300, 680})
    if not env then return false, "environment create failed" end
    connect_to(rt, octane.P_ENVIRONMENT or "environment", env)
    local refreshed, refresh_msg = request_render_restart(64, nil, nil, false)
    append_log("post-lighting render refresh ok=" .. tostring(refreshed) .. " msg=" .. tostring(refresh_msg))
    return true, "lighting preset " .. tostring(preset) .. " connected"
end

local function handle_set_object_transform(cmd)
    local ok, msg = ensure_octane()
    if not ok then return true, msg end
    if not cmd.object_name then return false, "set_object_transform missing object_name" end
    local node = find_item_by_name(cmd.object_name)
    if not node then return false, "unknown object " .. tostring(cmd.object_name) end
    local P_TRANSLATION = octane.P_TRANSFORM_TRANSLATION or "translation"
    local P_ROTATION    = octane.P_TRANSFORM_ROTATION or "rotation"
    local P_SCALE       = octane.P_TRANSFORM_SCALE or "scale"
    if cmd.translation then set_pin_value(node, P_TRANSLATION, cmd.translation) end
    if cmd.rotation_euler then set_pin_value(node, P_ROTATION, cmd.rotation_euler) end
    if cmd.scale then set_pin_value(node, P_SCALE, cmd.scale) end
    local refreshed, refresh_msg = request_render_restart(64, nil, nil, false)
    append_log("post-transform refresh ok=" .. tostring(refreshed) .. " msg=" .. tostring(refresh_msg))
    return true, "set transform on " .. tostring(cmd.object_name)
end

local function handle_start_render(cmd)
    return request_render_restart(cmd.samples or 64, cmd.width or DEFAULT_WIDTH, cmd.height or DEFAULT_HEIGHT, true, cmd.max_render_time)
end

local function candidates_png_type()
    -- First available PNG save-type constant, for the progressive pre-grab.
    if octane.imageSaveType then
        if octane.imageSaveType.PNG8 ~= nil then return octane.imageSaveType.PNG8 end
        if octane.imageSaveType.PNG16 ~= nil then return octane.imageSaveType.PNG16 end
    end
    if octane.imageSaveFormat then
        if octane.imageSaveFormat.PNG_8 ~= nil then return octane.imageSaveFormat.PNG_8 end
        if octane.imageSaveFormat.PNG_16 ~= nil then return octane.imageSaveFormat.PNG_16 end
    end
    return nil
end

local function handle_save_preview(cmd)
    if not (octane and octane.render) then return true, "Octane render API unavailable; acknowledged only" end
    local path = expand_path(cmd.path or DEFAULT_PREVIEW)
    local rt = get_or_create_render_target()
    activate_render_target(rt)
    set_render_resolution(rt, cmd.width or DEFAULT_WIDTH, cmd.height or DEFAULT_HEIGHT)
    os.execute("mkdir -p '" .. dirname(path):gsub("'", "'\\''") .. "'")

    local refreshed, refresh_msg = request_render_restart(cmd.samples or 64, cmd.width or DEFAULT_WIDTH, cmd.height or DEFAULT_HEIGHT, true, cmd.max_render_time)
    append_log("pre-save render refresh ok=" .. tostring(refreshed) .. " msg=" .. tostring(refresh_msg))
    if not refreshed then return false, tostring(refresh_msg) end
    local ready, ready_msg = wait_for_render_ready(cmd.min_samples or 16, cmd.timeout_seconds or 10)
    append_log("pre-save render readiness ok=" .. tostring(ready) .. " msg=" .. tostring(ready_msg))
    write_status("processing", "rendering preview", { render_stage = "rendering", samples_target = cmd.samples or 64 })

    -- Optional progressive preview: grab a low-SPP frame IMMEDIATELY from the
    -- already-live render (no extra request_render_restart, which would wedge a
    -- running engine) so the dashboard can show motion early. The full pass
    -- below then lands the final frame. Honesty: progressive_path is only
    -- emitted when the caller actually requested progressive mode.
    if cmd.progressive then
        local prog_path = expand_path(cmd.progressive_path or (dirname(path) .. "/preview_progressive.png"))
        os.execute("mkdir -p '" .. dirname(prog_path):gsub("'", "'\\''") .. "'")
        local prog_ok, prog_err = pcall(function() return octane.render.saveImage(prog_path, candidates_png_type()) end)
        if prog_ok then
            write_status("processing", "progressive frame saved", { render_stage = "rendering", samples_target = cmd.samples or 64, last_preview_path = prog_path })
            append_log("progressive preview saved " .. tostring(prog_path))
        else
            append_log("progressive preview skipped: " .. tostring(prog_err))
        end
    end

    local candidates = {}
    if octane.imageSaveType then
        if octane.imageSaveType.PNG8 ~= nil then table.insert(candidates, {"imageSaveType.PNG8", octane.imageSaveType.PNG8}) end
        if octane.imageSaveType.PNG16 ~= nil then table.insert(candidates, {"imageSaveType.PNG16", octane.imageSaveType.PNG16}) end
    end
    if octane.imageSaveFormat then
        if octane.imageSaveFormat.PNG_8 ~= nil then table.insert(candidates, {"imageSaveFormat.PNG_8", octane.imageSaveFormat.PNG_8}) end
        if octane.imageSaveFormat.PNG_16 ~= nil then table.insert(candidates, {"imageSaveFormat.PNG_16", octane.imageSaveFormat.PNG_16}) end
    end

    local last_err = "no PNG save constants found"
    local function attempt(label, fn)
        local ok, r1, r2, r3 = pcall(fn)
        append_log("save attempt " .. tostring(label) .. " ok=" .. tostring(ok) .. " r1=" .. tostring(r1) .. " r2=" .. tostring(r2) .. " r3=" .. tostring(r3) .. " exists=" .. tostring(file_exists(path)))
        if ok and r1 ~= false and file_exists(path) then return true, nil end
        if ok and r1 == false then return false, "returned false" end
        if ok then return false, "reported success but file missing" end
        return false, tostring(r1)
    end

    for _, candidate in ipairs(candidates) do
        local cname, cvalue = candidate[1], candidate[2]
        local ok, err = attempt("saveImage path," .. cname, function() return octane.render.saveImage(path, cvalue) end)
        if ok then return true, "preview saved " .. tostring(path) end
        last_err = err
        ok, err = attempt("saveImage2 filename,saveType " .. cname, function() return octane.render.saveImage2(path, cvalue) end)
        if ok then return true, "preview saved " .. tostring(path) end
        last_err = err
        ok, err = attempt("saveImage3 filename,saveType " .. cname, function() return octane.render.saveImage3(path, cvalue) end)
        if ok then return true, "preview saved " .. tostring(path) end
        last_err = err
        ok, err = attempt("saveRenderPass beauty,path,type " .. cname, function() return octane.render.saveRenderPass(0, path, cvalue) end)
        if ok then return true, "preview saved " .. tostring(path) end
        last_err = err
    end
    return false, "save preview failed: " .. tostring(last_err)
end

-- Deep pin read for the harvest API. Walks every pin on a node and captures
-- name + value for scalar/vec/text pins so the agent can read back live
-- camera/light/environment tweaks made in the Octane viewport. Connection
-- pins (PT_UNKNOWN/PT_*_LINK) are skipped to avoid dumping node refs.
local HARVEST_PIN_WANT = {
    ["pos"]=true, ["position"]=true, ["target"]=true, ["up"]=true, ["upVector"]=true,
    ["fov"]=true, ["aperture"]=true, ["focusDistance"]=true, ["focusDist"]=true,
    ["focalDepth"]=true, ["lensRadius"]=true, ["fStop"]=true, ["fstop"]=true,
    ["power"]=true, ["intensity"]=true, ["exposure"]=true, ["gamma"]=true,
    ["sun"]=true, ["sky"]=true, ["daylight"]=true, ["turbidity"]=true,
    ["north"]=true, ["ground"]=true, ["medium"]=true, ["backplate"]=true,
    ["env"]=true, ["environment"]=true, ["thin"]=true, ["importance"]=true,
    ["name"]=true, ["visible"]=true,
}
local function pin_value_str(v)
    if type(v) == "table" then
        local ok, s = pcall(function()
            local parts = {}
            for i = 1, #v do parts[#parts+1] = tostring(v[i]) end
            return table.concat(parts, ",")
        end)
        return ok and ("[" .. s .. "]") or tostring(v)
    end
    return tostring(v)
end

local function serialize_node(node)
    if not node or type(node) ~= "table" then
        return { type = type(node) or "nil" }
    end
    local result = { type = node._type or tostring(node) }
    local props = node:getProperties()
    if props then
        result.name = props.name or ""
        result.id = props.id or ""
        if props.position then result.position = props.position end
        if props.scale then result.scale = props.scale end
        if props.rotation then result.rotation = props.rotation end
    end
    -- Walk pins: capture name + value for camera / light / environment nodes
    -- so live viewport edits are readable by the agent (deep harvest fix).
    -- This build's Lua API is inconsistent about pin getters (getPinInfoIx vs
    -- GetPinInfo, getPinValue vs GetPinValue), so try both spellings and use
    -- whichever returns a usable value.
    local ok_count, pin_count = pcall(function() return node:getPinCount() end)
    if not (ok_count and pin_count and pin_count > 0) then
        ok_count, pin_count = pcall(function() return node:GetPinCount() end)
    end
    if ok_count and pin_count and pin_count > 0 then
        local pins = {}
        for i = 1, pin_count do
            local ok_info, info = pcall(function() return node:getPinInfoIx(i) end)
            if not ok_info then ok_info, info = pcall(function() return node:GetPinInfo(i) end) end
            if not ok_info then ok_info, info = pcall(function() return node:getPinInfoIx(i - 1) end) end
            if ok_info and info then
                local pname = tostring(info.name or info[3] or "")
                local plabel = tostring(info.label or info[2] or pname)
                local key = pname ~= "" and pname or plabel
                local lkey = key:lower()
                local tname = tostring(node._type or ""):upper()
                local capture = HARVEST_PIN_WANT[lkey] or
                    (string.find(tname, "CAM") or string.find(tname, "LIGHT") or string.find(tname, "ENV")) ~= nil
                if capture and key ~= "" then
                    local ok_v, val = pcall(function() return node:getPinValue(key) end)
                    if not (ok_v and val ~= nil) then
                        ok_v, val = pcall(function() return node:GetPinValue(key) end)
                    end
                    if not (ok_v and val ~= nil) then
                        ok_v, val = pcall(function() return node:GetPinValue(i) end)
                    end
                    if ok_v and val ~= nil then
                        pins[key] = pin_value_str(val)
                    end
                end
            end
        end
        if next(pins) then result.pins = pins end
    end
    result.has_geometry = node.getGeometry and (pcall(function() return node:getGeometry() end) and true or false)
    result.has_material = node.getMaterial and (pcall(function() return node:getMaterial() end) and true or false)
    return result
end

local function harvest_scene_graph()
    local graph = scene_graph()
    if not graph then return { nodes = {}, count = 0, timestamp = os.date("!%Y-%m-%dT%H:%M:%SZ") } end
    local items = {}
    local ok, all_items = pcall(function() return graph:getOwnedItems() end)
    if not ok or not all_items then return { nodes = {}, count = 0, timestamp = os.date("!%Y-%m-%dT%H:%M:%SZ") } end
    for _, node in ipairs(all_items) do
        local node_data = serialize_node(node)
        node_data.visible = node.isVisible and node:isVisible() or true
        if node.getConnectedNodes then
            local connected = {}
            local ok2, pins = pcall(function() return node:getConnectedNodes() end)
            if ok2 and pins then
                for _, cn in ipairs(pins) do
                    table.insert(connected, cn.name or tostring(cn))
                end
            end
            node_data.connected = connected
        end
        items[#items + 1] = node_data
    end
    return { nodes = items, count = #items, timestamp = os.date("!%Y-%m-%dT%H:%M:%SZ") }
end

local function handle_scene_harvest(cmd)
    local result = harvest_scene_graph()
    local path = RESULTS .. "/scene_harvest.json"
    result.dry_run = (cmd and (cmd.dry_run or (cmd.payload and cmd.payload.dry_run))) == true
    write_file(path, json_encode(result) .. "\n")
    return true, "scene harvested: " .. tostring(result.count or 0) .. " nodes"
end

local function handle_probe_types(cmd)
    local ok, msg = ensure_octane()
    if not ok then return true, msg end
    local out = {}
    local function test(t)
        local exists = (octane[t] ~= nil)
        local created, cerr = nil, "not tried"
        if exists then
            created, cerr = create_node(octane[t], "probe_" .. t, {500, 500})
        end
        out[t] = string.format("exists=%s created=%s err=%s", tostring(exists), tostring(created ~= nil), tostring(cerr))
    end
    test("NT_LIGHT_AREA")
    test("NT_LIGHT_SUN")
    test("NT_LIGHT_DAYLIGHT")
    test("NT_ENV_DAYLIGHT")
    test("NT_ENV_TEXTURE")
    test("NT_TEX_RGB")
    test("NT_ENV_THIN")
    test("NT_GEO_SPHERE")
    test("NT_GEO_BOX")
    test("NT_GEO_PLANE")
    -- Enumerate daylight env node's real attribute pin names so we can
    -- bind sun/sky intensity for a true dark studio.
    local env_probe = {}
    pcall(function()
        local env = octane.node.create{ type=octane.NT_ENV_DAYLIGHT, name="probe_env_attrs", graphOwner=octane.project.getSceneGraph() }
        if env then
            local n = 0
            pcall(function() n = env:getAttributeCount() end)
            for i = 0, (n > 0 and n - 1 or 0) do
                local info = nil
                pcall(function() info = env:getAttributeInfo(i) end)
                if info and info.name then
                    env_probe[info.name] = info.type or "?"
                end
            end
            env_probe["_attrCount"] = n
        end
    end)
    out["ENV_ATTRS"] = env_probe
    -- Test dark environment via NT_ENV_TEXTURE + NT_TEX_RGB (both exist).
    local dark = {}
    pcall(function()
        local tex = octane.node.create{ type=octane.NT_TEX_RGB, name="probe_dark_tex", graphOwner=octane.project.getSceneGraph() }
        if tex then
            set_pin_value(tex, octane.P_COLOR or "color", {0.02, 0.02, 0.03})
            local envt = octane.node.create{ type=octane.NT_ENV_TEXTURE, name="probe_dark_env", graphOwner=octane.project.getSceneGraph() }
            if envt then
                connect_to(envt, octane.P_TEXTURE or "texture", tex)
                dark["built"] = true
                dark["tex_node"] = tostring(tex)
                dark["env_node"] = tostring(envt)
            else
                dark["built"] = false
                dark["env_err"] = "NT_ENV_TEXTURE create failed"
            end
        else
            dark["built"] = false
            dark["tex_err"] = "NT_TEX_RGB create failed"
        end
    end)
    out["DARK_ENV"] = dark
    -- Test scene reset API.
    local reset = {}
    pcall(function()
        if octane.project and octane.project.newScene then
            reset["newScene"] = "exists"
        else
            reset["newScene"] = "nil"
        end
        if octane.nodegraph and octane.nodegraph.getRootGraph then
            reset["getRootGraph"] = "exists"
        else
            reset["getRootGraph"] = "nil"
        end
    end)
    out["RESET"] = reset
    append_log("PROBE_TYPES " .. json_encode(out))
    return true, "probe logged"
end

local function handle_command(cmd)
    append_log("persistent command " .. tostring(cmd.id) .. " op=" .. tostring(cmd.op))
    if cmd.op == "ping" then return true, "pong " .. tostring(cmd.message or "") end
    if cmd.op == "import_geometry" then return handle_import_geometry(cmd) end
    if cmd.op == "create_material" then return handle_create_material(cmd) end
    if cmd.op == "create_light" then return handle_create_light(cmd) end
    if cmd.op == "assign_material" then return handle_assign_material(cmd) end
    if cmd.op == "set_camera" then return handle_set_camera(cmd) end
    if cmd.op == "get_camera" then return handle_get_camera(cmd) end
    if cmd.op == "set_lighting" then return handle_set_lighting(cmd) end
    if cmd.op == "set_object_transform" then return handle_set_object_transform(cmd) end
    if cmd.op == "start_render" then return handle_start_render(cmd) end
    if cmd.op == "save_preview" then return handle_save_preview(cmd) end
    if cmd.op == "scene_harvest" then return handle_scene_harvest(cmd) end
    if cmd.op == "probe_types" then return handle_probe_types(cmd) end
    return true, "acknowledged " .. tostring(cmd.op)
end

local function processed_or_failed_exists(id)
    return file_exists(PROCESSED .. "/" .. tostring(id) .. ".json") or file_exists(FAILED .. "/" .. tostring(id) .. ".json")
end

local function list_queue_files()
    local files = {}
    if octane and octane.file and octane.file.listDirectory then
        local ok, entries = pcall(function() return octane.file.listDirectory(QUEUE) end)
        if ok and entries then
            for _, e in ipairs(entries) do
                local name = type(e) == "table" and (e.name or e.path or e.filename) or tostring(e)
                if name and name:match("%.json$") then
                    if name:sub(1,1) == "/" then table.insert(files, name) else table.insert(files, QUEUE .. "/" .. basename(name)) end
                end
            end
        end
    end
    if #files == 0 then
        os.execute("ls -1 '" .. QUEUE:gsub("'", "'\\''") .. "'/*.json 2>/dev/null > '" .. LISTING:gsub("'", "'\\''") .. "'")
        local listing = read_file(LISTING, true)
        if listing then for line in listing:gmatch("[^\r\n]+") do table.insert(files, line) end end
    end
    table.sort(files)
    return files
end

local function next_queue_file()
    local files = list_queue_files()
    for _, path in ipairs(files) do
        local id = basename(path):gsub("%.json$", "")
        if not processed_or_failed_exists(id) then return path, id end
    end
    return nil, nil
end

local function process_file(path, id)
    local raw = read_file(path)
    if not raw or raw == "" then return false, "empty command file" end
    local cmd, parse_err = parse_command(raw)
    if not cmd then cmd = {id = id or basename(path):gsub("%.json$", ""), op = "invalid_json"} end
    if not cmd.id or cmd.id == "unknown" then cmd.id = id or "unknown" end
    local started = os.clock()
    local active_path = path
    if path ~= INBOX then
        local processing_path = PROCESSING .. "/" .. tostring(cmd.id) .. ".json"
        local moved_to_processing = os.rename(path, processing_path)
        if moved_to_processing then active_path = processing_path end
    end
    local ok, handled, message
    if parse_err then
        ok, handled, message = true, false, "invalid JSON: " .. tostring(parse_err)
    else
        ok, handled, message = pcall(function()
            local success, msg = handle_command(cmd)
            return success, msg
        end)
    end
    local dst_dir = (ok and handled) and PROCESSED or FAILED
    local dst = dst_dir .. "/" .. tostring(cmd.id) .. ".json"
    os.rename(active_path, dst)
    if file_exists(INBOX) then
        local inbox_raw = read_file(INBOX, true)
        if inbox_raw and inbox_raw:find('"id"%s*:%s*"' .. tostring(cmd.id) .. '"') then os.remove(INBOX) end
    end
    if ok and handled then
        processed_count = processed_count + 1
        write_result(cmd, true, message, path, dst, (os.clock() - started) * 1000)
        append_log("persistent processed id=" .. tostring(cmd.id) .. " message=" .. tostring(message))
        local preview_path = (cmd.op == "save_preview") and (cmd.path or DEFAULT_PREVIEW) or nil
        local spp = (cmd.op == "save_preview") and (cmd.samples or 64) or nil
        write_status("processed", tostring(cmd.op) .. " " .. tostring(message), { render_stage = "ready", samples_done = spp, samples_target = spp, last_preview_path = preview_path })
        if cmd.op == "start_render" then
            request_bridge_close("render restarted; bridge released intentionally so Octane can continue rendering the updated scene")
        end
        return true, message
    else
        failed_count = failed_count + 1
        local err = ok and message or handled
        write_result(cmd, false, err, path, dst, (os.clock() - started) * 1000)
        append_log("persistent failed id=" .. tostring(cmd.id) .. " error=" .. tostring(err))
        write_status("failed", tostring(err), { render_stage = "error" })
        return false, err
    end
end

local function process_next_command()
    local path, id = next_queue_file()
    if not path then
        write_status("idle", "no queued command", { render_stage = "idle" })
        return false, "no queued command"
    end
    return process_file(path, id)
end

local function drain_some(limit)
    limit = limit or 3
    local did = 0
    for _ = 1, limit do
        if close_requested then break end
        local path, id = next_queue_file()
        if not path then break end
        process_file(path, id)
        did = did + 1
    end
    if did == 0 then write_status("idle", "waiting for commands", { render_stage = "idle" }) end
    return did
end

local function timer_tick()
    if not running then return end
    drain_some(2)
end

local function start_timer()
    if not (octane and octane.timer and octane.timer.create) then
        append_log("persistent timer API unavailable; manual button only")
        return false
    end
    -- Octane X build (2026-07-12): octane.timer.create takes
    -- POSITIONAL (interval:number, callback:function). Table-form
    -- calls (create{interval=..,callback=..}) error with
    -- "bad argument #1 to 'create' (number expected, got table)".
    local ok, timer_or_err = pcall(function() return octane.timer.create(1.0, timer_tick) end)
    if ok and timer_or_err then
        bridge_timer = timer_or_err
        append_log("persistent timer created (interval=1.0, callback=timer_tick)")
        return true
    end
    append_log("persistent timer create failed: " .. tostring(timer_or_err))
    append_log("persistent timer not started; manual button only")
    return false
end

append_log("persistent bridge starting")
write_status("starting", "creating bridge window", { render_stage = "queued" })

local timer_started = start_timer()
local process_button = octane.gui.create{ type=octane.gui.componentType.BUTTON, text="Process next", width=140, height=24, callback=function() process_next_command() end }
local drain_button = octane.gui.create{ type=octane.gui.componentType.BUTTON, text="Drain queue", width=140, height=24, callback=function() drain_some(20) end }
local close_button = octane.gui.create{ type=octane.gui.componentType.BUTTON, text="Stop bridge", width=140, height=24, callback=function()
    request_bridge_close("bridge stopped by user")
end }
status_label = octane.gui.create{ type=octane.gui.componentType.LABEL, text="Hermes bridge starting", width=360, height=24 }
count_label = octane.gui.create{ type=octane.gui.componentType.LABEL, text="processed=0 failed=0", width=360, height=24 }
local mode_label = octane.gui.create{ type=octane.gui.componentType.LABEL, text=(timer_started and "Auto-poll timer active" or "Timer unavailable: use Process next / Drain queue"), width=360, height=24 }
local group = octane.gui.create{ type=octane.gui.componentType.GROUP, children={ mode_label, status_label, count_label, process_button, drain_button, close_button }, rows=6, cols=1, padding={12}, border=false }
local window = octane.gui.create{ type=octane.gui.componentType.WINDOW, width=420, height=220, children={group}, text="Hermes Octane MCP Bridge" }
bridge_window = window
write_status("running", timer_started and "persistent timer active" or "manual bridge window active", { render_stage = "queued" })
window:showWindow()
running = false
if bridge_timer then pcall(function() bridge_timer:stop() end); pcall(function() octane.timer.stop(bridge_timer) end) end
if close_requested then
    write_status("released", "render started; bridge intentionally exited so Octane can render the updated scene", { render_stage = "rendering" })
    append_log("persistent bridge released after render start")
else
    write_status("closed", "bridge window closed", { render_stage = "idle" })
    append_log("persistent bridge closed")
end
