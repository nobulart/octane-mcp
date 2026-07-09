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

local function create_node(type_id, name, position)
    if not type_id then return nil, "missing node type for " .. tostring(name) end
    local ok, node_or_err = pcall(function()
        return octane.node.create{ type=type_id, name=name, position=position or {500, 500} }
    end)
    if ok then return node_or_err, nil end
    return nil, tostring(node_or_err)
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
    local material_pin_ix = 0
    for i = 1, pin_count do
        local ok_info, info = pcall(function() return mesh:getPinInfoIx(i) end)
        if not ok_info then ok_info, info = pcall(function() return mesh:getPinInfoIx(i - 1) end) end
        if ok_info and info then
            local is_material = (octane.PT_MATERIAL and info.type == octane.PT_MATERIAL) or info.label == "Material" or info.name == "Material"
            if is_material then
                material_pin_ix = material_pin_ix + 1
                if group_index and material_pin_ix ~= tonumber(group_index) then
                    append_log("skipping material pin #" .. tostring(material_pin_ix) .. " (group filter " .. tostring(group_index) .. ")")
                else
                    if info.name then connected = connect_to(mesh, info.name, mat) or connected end
                    if info.id then connected = connect_to(mesh, info.id, mat) or connected end
                end
            end
        end
    end
    if group_index then
        append_log("material pin #" .. tostring(group_index) .. " target on mesh (of " .. tostring(material_pin_ix) .. " material pins)")
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
    if activated then append_log("activated render target " .. tostring(rt)) end
    return activated
end

local function try_render_call(label, fn)
    local ok, result = pcall(fn)
    append_log("render attempt " .. tostring(label) .. " ok=" .. tostring(ok) .. " result=" .. tostring(result))
    return ok, result
end

local function request_render_restart(samples, width, height)
    if not (octane and octane.render) then return true, "Octane render API unavailable; acknowledged only" end
    local rt, rt_err = get_or_create_render_target()
    if not rt then return false, "render target failed: " .. tostring(rt_err) end
    ensure_render_target_defaults(rt)
    activate_render_target(rt)
    set_render_resolution(rt, width or DEFAULT_WIDTH, height or DEFAULT_HEIGHT)
    samples = samples or 64
    -- Octane X renders continuously on its own (default RT) once any scene
    -- exists, but saveImage() saves OUR render target's buffer -- so we MUST
    -- explicitly start OUR RT. A prior regression added an early-return that
    -- skipped start{rt} whenever Octane's default scene already reported
    -- beauty>0; that left our RT unrendered and forced a manual "render start"
    -- click. The correct behavior is to ALWAYS ensure OUR RT is rendering.
    -- CRITICAL: octane.render.start{renderTargetNode=rt} WEDGES (blocks
    -- forever) when Octane's render engine is already active -- which it is
    -- whenever Octane auto-renders the current scene. So we must NOT issue
    -- start{} while a render is live. Instead: probe render state; if a render
    -- is already running, just wait on it (it will populate our RT buffer).
    -- Only stop()+pause()+start{rt} when nothing is rendering.
    if octane.render.getRenderResultStatistics then
        local s_ok, stats = pcall(function() return octane.render.getRenderResultStatistics() end)
        if s_ok and type(stats) == "table" then
            local state = tostring(stats.renderState)
            local beauty = tonumber(stats.beautySamplesPerPixel) or 0
            -- renderState values observed: 0=idle, 1/2/3=queued/starting,
            -- 4=rendering. If already rendering (state>=1) or has samples,
            -- do NOT call start{} (it would wedge) -- just reuse the live run.
            if state ~= "0" or beauty > 0 then
                append_log("render already active (state=" .. state .. " beauty=" .. tostring(beauty) .. "); reusing live render, no start{}")
                return true, "render already active; reusing live render"
            end
        end
    end
    -- Stop any in-flight render before starting ours. Octane rejects a new
    -- start/restart while a previous render is still active
    -- ("Can't start a new render before finishing the previous render"), which
    -- left blank/black previews. stop() ends the current pass so the next
    -- start/restart is accepted. pause() alone is NOT enough (a paused render
    -- is still "in progress").
    pcall(function() if octane.render.stop then octane.render.stop() end end)
    pcall(function() octane.render.pause() end)
    -- Render the MAIN viewport (octane.render.start() with no args), NOT
    -- octane.render.start{renderTargetNode=rt}. saveImage() captures the main
    -- viewport buffer, so only the main-viewport render populates what saveImage
    -- can grab. Using start{rt} leaves the main viewport empty -> saveImage
    -- returns r1=false and writes nothing. Confirmed: the 19:06-20:34 working
    -- runs used main-viewport start; the regression appeared only after
    -- switching to start{rt}. The geometry is connected to our RT for the node
    -- graph, but the actual pixels we save come from the main viewport.
    -- NOTE: maxSamples is NOT a recognized key for octane.render.start on this
    -- Octane build, so it is intentionally NOT used; the render is instead
    -- bounded by wait_for_render_ready() polling the sample count to min_samples
    -- (with a wall-clock timeout), then the frame is grabbed. This avoids an
    -- unbounded render that would block every subsequent restart.
    -- Retry loop: Octane's stop() does not always halt the in-flight render
    -- synchronously, so the immediate start() can still raise "Can't start a
    -- new render before finishing the previous render". Yield briefly and
    -- retry so the prior pass has actually ended before we (re)start ours.
    local last_err = "no attempts made"
    for attempt = 1, 5 do
        local ok, result = try_render_call("start()", function() return octane.render.start() end)
        if ok then return true, "render start requested (main viewport; bounded by wait_for_render_ready)" end
        ok, result = try_render_call("restart()", function() return octane.render.restart() end)
        if ok then return true, "render restart requested" end
        ok, result = try_render_call("continue()", function() return octane.render.continue() end)
        if ok then return true, "render continue requested" end
        last_err = tostring(result)
        sleep_seconds(0.5)
    end
    return false, "render refresh failed after retries; last: " .. last_err
end

local function render_stat_number(stats, key)
    if type(stats) ~= "table" then return 0 end
    return tonumber(stats[key]) or 0
end

local function sleep_seconds(seconds)
    seconds = tonumber(seconds) or 0.25
    if octane and octane.sleep then
        local ok = pcall(function() octane.sleep(seconds) end)
        if ok then return end
    end
    os.execute("sleep " .. tostring(seconds))
end

local function wait_for_render_ready(min_samples, timeout_seconds)
    min_samples = tonumber(min_samples) or 16
    timeout_seconds = tonumber(timeout_seconds) or 10
    if not (octane and octane.render and octane.render.getRenderResultStatistics) then
        return true, "render statistics unavailable; continuing"
    end
    local last = "no statistics yet"
    local attempts = math.max(1, math.floor((timeout_seconds / 0.5) + 0.5))
    for _ = 1, attempts do
        local ok, stats = pcall(function() return octane.render.getRenderResultStatistics() end)
        if ok and type(stats) == "table" then
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
            last = tostring(stats)
        end
        sleep_seconds(0.5)
    end
    append_log("render preview readiness timeout: " .. tostring(last))
    return false, last
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
    local mesh = find_item_by_name(name)
    if not mesh then
        local err
        mesh, err = create_node(octane.NT_GEO_MESH, name, {500, 500})
        if not mesh then return false, "create mesh failed: " .. tostring(err) end
    end
    local loaded, load_err = pcall(function() mesh:setAttribute(octane.A_FILENAME, cmd.path, true) end)
    if not loaded then return false, "mesh load failed: " .. tostring(load_err) end
    maybe_connect_geometry_to_rt(mesh)
    local refreshed, refresh_msg = request_render_restart(64)
    append_log("post-import render refresh ok=" .. tostring(refreshed) .. " msg=" .. tostring(refresh_msg))
    return true, "imported geometry " .. tostring(name)
end

local function handle_create_material(cmd)
    local ok, msg = ensure_octane()
    if not ok then return true, msg end
    local name = cmd.name or "mcp_material"
    local existing = find_item_by_name(name)
    if existing then return true, "material exists " .. tostring(name) end
    local matType = octane.NT_MAT_DIFFUSE
    if cmd.kind == "glossy" and octane.NT_MAT_GLOSSY then matType = octane.NT_MAT_GLOSSY end
    if cmd.kind == "specular" and octane.NT_MAT_SPECULAR then matType = octane.NT_MAT_SPECULAR end
    if cmd.kind == "metallic" and octane.NT_MAT_METALLIC then matType = octane.NT_MAT_METALLIC end
    local mat, err = create_node(matType, name, {650, 500})
    if not mat then return false, "create material failed: " .. tostring(err) end
    local col = cmd.color or cmd.diffuse or cmd.albedo or {0.8, 0.8, 0.8}
    local function setdef(pin, val)
        if val ~= nil then
            local okp, w = pcall(set_pin_value, mat, pin, val)
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
    if cmd.texture_path then setdef(octane.P_DIFFUSE_TEXTURE or "diffuse_texture", cmd.texture_path) end
    if cmd.normal_path then setdef(octane.P_NORMAL_TEXTURE or "normal_texture", cmd.normal_path) end
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
        local env = find_item_by_name(name)
        if not env then
            local err
            env, err = create_node(env_type, name, {300, 680})
            if not env then return false, "environment create failed: " .. tostring(err) end
        end
        connect_to(rt, octane.P_ENVIRONMENT or "environment", env)
        local refreshed, refresh_msg = request_render_restart(64)
        append_log("post-light render refresh ok=" .. tostring(refreshed) .. " msg=" .. tostring(refresh_msg))
        return true, "created environment light " .. tostring(name) .. " (" .. tostring(light_type) .. ")"
    end
    -- emissive-material proxy for all other light types
    local existing = find_item_by_name(name)
    if existing then return true, "light/material exists " .. tostring(name) end
    local mat, err = create_node(octane.NT_MAT_EMISSIVE or octane.NT_MAT_DIFFUSE, name, {760, 500})
    if not mat then return false, "create light material failed: " .. tostring(err) end
    local function setdef(pin, val)
        if val ~= nil then
            local okp, w = pcall(set_pin_value, mat, pin, val)
            if not okp then append_log("light pin " .. tostring(pin) .. " unsupported: " .. tostring(w)) end
        end
    end
    local rgb = cmd.color or {1.0, 0.95, 0.85}
    setdef(octane.P_EMISSION or "emission", {rgb[1] or 1, rgb[2] or 1, rgb[3] or 1})
    setdef(octane.P_POWER or "power", intensity)
    return true, "created emissive light proxy " .. tostring(name) .. " (" .. tostring(light_type) .. ")"
end

local function handle_assign_material(cmd)
    local ok, msg = ensure_octane()
    if not ok then return true, msg end
    local mesh = find_item_by_name(cmd.object_name) or latest_imported_geometry_fallback()
    local mat = find_item_by_name(cmd.material_name)
    if not mesh then return false, "unknown object " .. tostring(cmd.object_name) end
    if not mat then return false, "unknown material " .. tostring(cmd.material_name) end
    local group_index = cmd.group_index or cmd.payload and cmd.payload.group_index
    local connected = connect_material_to_mesh_pins(mesh, mat, group_index)
    for _, pin in ipairs({"default", "Material", "material", "m1", "mat", octane.P_MATERIAL}) do
        if pin then connected = connect_to(mesh, pin, mat) or connected end
    end
    if connected then
        local refreshed, refresh_msg = request_render_restart(64)
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
    local cam = find_item_by_name("Hermes Camera")
    if not cam then
        local err
        cam, err = create_node(octane.NT_CAM_THINLENS or octane.NT_CAM_PANORAMIC, "Hermes Camera", {300, 520})
        if not cam then return false, "camera create failed: " .. tostring(err) end
    end
    if cmd.fov then set_pin_value(cam, octane.P_FOV or "fov", cmd.fov) end
    if cmd.position then set_pin_value(cam, octane.P_POSITION or "pos", cmd.position) end
    if cmd.target then set_pin_value(cam, octane.P_TARGET or "target", cmd.target) end
    connect_to(rt, octane.P_CAMERA or "camera", cam)
    local refreshed, refresh_msg = request_render_restart(64)
    append_log("post-camera render refresh ok=" .. tostring(refreshed) .. " msg=" .. tostring(refresh_msg))
    return true, "camera connected"
end

local function handle_set_lighting(cmd)
    local ok, msg = ensure_octane()
    if not ok then return true, msg end
    local rt, rt_err = get_or_create_render_target()
    if not rt then return false, "render target failed: " .. tostring(rt_err) end
    activate_render_target(rt)
    local env_type = octane.NT_ENV_DAYLIGHT or octane.NT_ENV_TEXTURE
    if not env_type then return true, "no known environment node type constant" end
    local env = find_item_by_name("Hermes Environment")
    if not env then
        local err
        env, err = create_node(env_type, "Hermes Environment", {300, 680})
        if not env then return false, "environment create failed: " .. tostring(err) end
    end
    connect_to(rt, octane.P_ENVIRONMENT or "environment", env)
    local refreshed, refresh_msg = request_render_restart(64)
    append_log("post-lighting render refresh ok=" .. tostring(refreshed) .. " msg=" .. tostring(refresh_msg))
    return true, "lighting preset " .. tostring(cmd.preset or "default") .. " connected"
end

local function handle_start_render(cmd)
    return request_render_restart(cmd.samples or 64, cmd.width or DEFAULT_WIDTH, cmd.height or DEFAULT_HEIGHT)
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

    local refreshed, refresh_msg = request_render_restart(cmd.samples or 64, cmd.width or DEFAULT_WIDTH, cmd.height or DEFAULT_HEIGHT)
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

local function handle_command(cmd)
    append_log("persistent command " .. tostring(cmd.id) .. " op=" .. tostring(cmd.op))
    if cmd.op == "ping" then return true, "pong " .. tostring(cmd.message or "") end
    if cmd.op == "import_geometry" then return handle_import_geometry(cmd) end
    if cmd.op == "create_material" then return handle_create_material(cmd) end
    if cmd.op == "create_light" then return handle_create_light(cmd) end
    if cmd.op == "assign_material" then return handle_assign_material(cmd) end
    if cmd.op == "set_camera" then return handle_set_camera(cmd) end
    if cmd.op == "set_lighting" then return handle_set_lighting(cmd) end
    if cmd.op == "start_render" then return handle_start_render(cmd) end
    if cmd.op == "save_preview" then return handle_save_preview(cmd) end
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
    local attempts = {
        function() return octane.timer.create{ interval=1.0, callback=timer_tick } end,
        function() return octane.timer.create{ time=1.0, callback=timer_tick } end,
        function() return octane.timer.create(1.0, timer_tick) end,
        function() return octane.timer.create(timer_tick) end,
    }
    for i, fn in ipairs(attempts) do
        local ok, timer_or_err = pcall(fn)
        if ok and timer_or_err then
            bridge_timer = timer_or_err
            local started = false
            local ok_start = pcall(function() bridge_timer:start() end)
            if ok_start then started = true end
            if not started then ok_start = pcall(function() octane.timer.start(bridge_timer) end); if ok_start then started = true end end
            if started then
                append_log("persistent timer started attempt=" .. tostring(i))
                return true
            end
            -- Octane X's timer.create(interval, callback) returns a timer object
            -- that can still fire during showWindow() even when explicit
            -- timer:start()/octane.timer.start(timer) reject the object. Treat a
            -- successful create as active; the runtime log confirms ticks by
            -- subsequent command processing.
            append_log("persistent timer created attempt=" .. tostring(i) .. "; explicit start unavailable, assuming active during showWindow")
            return true
        else
            append_log("timer create attempt " .. tostring(i) .. " failed: " .. tostring(timer_or_err))
        end
    end
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
