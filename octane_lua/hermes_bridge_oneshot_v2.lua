-- Hermes / OctaneX MCP bridge one-shot v2. Run inside Octane X.
-- Processes one command from the Octane X sandbox container inbox and exits.
--
-- Octane X from the Mac App Store is sandboxed. Hermes writes commands into
-- the real container path below, which Octane Lua can read/write directly.

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
local BRIDGE_DIR = (debug and debug.getinfo and debug.getinfo(1, "S").source:match("@?(.*[/\\])")) or ""
local JSON = dofile(BRIDGE_DIR .. "lib/json.lua")

local function append_log(message)
    local f = io.open(LOG, "a")
    if f then
        f:write(os.date("!%Y-%m-%dT%H:%M:%SZ"), " ", tostring(message), "\n")
        f:close()
    else
        print("Hermes bridge v2 could not open log: " .. LOG)
    end
end

local function write_file(path, text)
    local f, err = io.open(path, "w")
    if not f then
        print("Hermes bridge v2 write failed " .. tostring(path) .. ": " .. tostring(err))
        append_log("write_file failed: " .. tostring(path) .. " " .. tostring(err))
        return false, err
    end
    f:write(text)
    f:close()
    return true
end

local function read_file(path)
    local f, err = io.open(path, "r")
    if not f then
        print("Hermes bridge v2 read failed " .. tostring(path) .. ": " .. tostring(err))
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

local function json_escape(s)
    s = tostring(s or "")
    s = s:gsub('\\', '\\\\'):gsub('"', '\\"'):gsub('\n', '\\n'):gsub('\r', '\\r'):gsub('\t', '\\t')
    return s
end

local function write_status(state, extra)
    local text = "{\n" ..
        "  \"bridge_seen\": true,\n" ..
        "  \"bridge\": \"hermes_bridge_oneshot_v2.lua\",\n" ..
        "  \"mode\": \"one_shot\",\n" ..
        "  \"status\": \"" .. json_escape(state or "ok") .. "\",\n" ..
        "  \"updated_at\": \"" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\",\n" ..
        "  \"octane_available\": " .. tostring(octane ~= nil) .. ",\n" ..
        "  \"octane_node_available\": " .. tostring(octane and octane.node ~= nil) .. ",\n" ..
        "  \"root\": \"" .. json_escape(ROOT) .. "\""
    if extra then text = text .. ",\n  \"last_event\": \"" .. json_escape(extra) .. "\"" end
    text = text .. "\n}\n"
    write_file(STATUS, text)
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
    if octane.project and octane.project.getSceneGraph then
        return octane.project.getSceneGraph()
    end
    if octane.nodegraph and octane.nodegraph.getRootGraph then
        return octane.nodegraph.getRootGraph()
    end
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

local function connect_material_to_all_mesh_pins(mesh, mat)
    local connected = false
    if not mesh or not mat then return connected end
    local ok_count, pin_count = pcall(function() return mesh:getPinCount() end)
    if ok_count and pin_count then
        for i = 1, pin_count do
            local ok_info, info = pcall(function() return mesh:getPinInfoIx(i) end)
            if not ok_info then ok_info, info = pcall(function() return mesh:getPinInfoIx(i - 1) end) end
            if ok_info and info then
                local is_material = (octane.PT_MATERIAL and info.type == octane.PT_MATERIAL) or info.label == "Material" or info.name == "Material"
                if is_material then
                    if info.name then connected = connect_to(mesh, info.name, mat) or connected end
                    if info.id then connected = connect_to(mesh, info.id, mat) or connected end
                end
            end
        end
    end
    return connected
end

local function get_or_create_render_target()
    local rt = find_item_by_name("Hermes Render Target") or find_item_by_name("Hermes_RT")
    if rt then return rt end
    local node, err = create_node(octane.NT_RENDERTARGET, "Hermes Render Target", {300, 300})
    if not node then return nil, err end
    return node, nil
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
    activate_render_target(rt)
    set_render_resolution(rt, width or DEFAULT_WIDTH, height or DEFAULT_HEIGHT)
    samples = samples or 64
    local ok, result = try_render_call("restart()", function() return octane.render.restart() end)
    if ok then return true, "render restart requested" end
    ok, result = try_render_call("start{renderTargetNode=rt,maxSamples=samples}", function() return octane.render.start{ renderTargetNode=rt, maxSamples=samples } end)
    if ok then return true, "render start requested" end
    ok, result = try_render_call("start({renderTargetNode=rt,maxSamples=samples})", function() return octane.render.start({ renderTargetNode=rt, maxSamples=samples }) end)
    if ok then return true, "render start requested" end
    ok, result = try_render_call("start{renderTargetNode=rt}", function() return octane.render.start{ renderTargetNode=rt } end)
    if ok then return true, "render start requested" end
    ok, result = try_render_call("continue()", function() return octane.render.continue() end)
    if ok then return true, "render continue requested" end
    return false, "render refresh failed; see bridge.log for attempted signatures"
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
    if cmd.color then set_pin_value(mat, octane.P_DIFFUSE or "diffuse", {cmd.color[1] or 0.8, cmd.color[2] or 0.8, cmd.color[3] or 0.8}) end
    return true, "created material " .. tostring(name)
end

local function handle_assign_material(cmd)
    local ok, msg = ensure_octane()
    if not ok then return true, msg end
    local mesh = find_item_by_name(cmd.object_name) or latest_imported_geometry_fallback()
    local mat = find_item_by_name(cmd.material_name)
    if not mesh then return false, "unknown object " .. tostring(cmd.object_name) end
    if not mat then return false, "unknown material " .. tostring(cmd.material_name) end
    local connected = connect_material_to_all_mesh_pins(mesh, mat)
    for _, pin in ipairs({"default", "Material", "material", "m1", "mat", octane.P_MATERIAL}) do
        if pin then connected = connect_to(mesh, pin, mat) or connected end
    end
    if connected then
        local refreshed, refresh_msg = request_render_restart(64)
        append_log("post-material render refresh ok=" .. tostring(refreshed) .. " msg=" .. tostring(refresh_msg))
        return true, "assigned material " .. tostring(cmd.material_name)
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

local function handle_save_preview(cmd)
    if not (octane and octane.render) then return true, "Octane render API unavailable; acknowledged only" end
    local path = cmd.path or DEFAULT_PREVIEW
    local rt = get_or_create_render_target()
    activate_render_target(rt)
    set_render_resolution(rt, cmd.width or DEFAULT_WIDTH, cmd.height or DEFAULT_HEIGHT)
    os.execute("mkdir -p '" .. dirname(path):gsub("'", "'\\''") .. "'")

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
        ok, err = attempt("saveImage2 table path/saveType " .. cname, function() return octane.render.saveImage2{ path=path, saveType=cvalue, type=cvalue, renderTargetNode=rt } end)
        if ok then return true, "preview saved " .. tostring(path) end
        last_err = err
        ok, err = attempt("saveImage2 filename,props saveType " .. cname, function() return octane.render.saveImage2(path, { saveType=cvalue, type=cvalue, renderTargetNode=rt }) end)
        if ok then return true, "preview saved " .. tostring(path) end
        last_err = err
        ok, err = attempt("saveImage2 filename,props imageSaveType " .. cname, function() return octane.render.saveImage2(path, { imageSaveType=cvalue, imageSaveFormat=cvalue, renderTargetNode=rt }) end)
        if ok then return true, "preview saved " .. tostring(path) end
        last_err = err
        ok, err = attempt("saveImage3 filename,props saveType " .. cname, function() return octane.render.saveImage3(path, { saveType=cvalue, type=cvalue, renderTargetNode=rt }) end)
        if ok then return true, "preview saved " .. tostring(path) end
        last_err = err
        ok, err = attempt("saveImage3 filename,props imageSaveType " .. cname, function() return octane.render.saveImage3(path, { imageSaveType=cvalue, imageSaveFormat=cvalue, renderTargetNode=rt }) end)
        if ok then return true, "preview saved " .. tostring(path) end
        last_err = err
        ok, err = attempt("saveRenderPass beauty,path,type " .. cname, function() return octane.render.saveRenderPass(0, path, cvalue) end)
        if ok then return true, "preview saved " .. tostring(path) end
        last_err = err
        ok, err = attempt("saveRenderPass beauty,path,props " .. cname, function() return octane.render.saveRenderPass(0, path, { saveType=cvalue, type=cvalue }) end)
        if ok then return true, "preview saved " .. tostring(path) end
        last_err = err
    end
    return false, "save preview failed: " .. tostring(last_err)
end

local function handle_command(cmd)
    append_log("v2 command " .. tostring(cmd.id) .. " op=" .. tostring(cmd.op))
    if cmd.op == "ping" then return true, "pong " .. tostring(cmd.message or "") end
    if cmd.op == "import_geometry" then return handle_import_geometry(cmd) end
    if cmd.op == "create_material" then return handle_create_material(cmd) end
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
    os.execute("ls -1 '" .. QUEUE:gsub("'", "'\\''") .. "'/*.json 2>/dev/null > '" .. LISTING:gsub("'", "'\\''") .. "'")
    local listing = read_file(LISTING)
    if listing then
        for line in listing:gmatch("[^\r\n]+") do table.insert(files, line) end
    end
    table.sort(files)
    return files
end

local function process_raw_command(raw, source_path, source_label)
    local cmd, parse_err = parse_command(raw)
    if not cmd then cmd = {id = basename(source_path):gsub("%.json$", ""), op = "invalid_json"} end
    local started = os.clock()
    local active_path = source_path
    if source_path ~= INBOX then
        local processing_path = PROCESSING .. "/" .. tostring(cmd.id) .. ".json"
        local moved_to_processing = os.rename(source_path, processing_path)
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
    local moved, move_err = os.rename(active_path, dst)
    if source_path ~= INBOX and file_exists(INBOX) then
        local inbox_raw = read_file(INBOX)
        if inbox_raw and inbox_raw:find('"id"%s*:%s*"' .. tostring(cmd.id) .. '"') then os.remove(INBOX) end
    end
    if ok and handled then
        write_result(cmd, true, message, source_path, dst, (os.clock() - started) * 1000)
        append_log("v2 processed " .. tostring(source_label) .. " id=" .. tostring(cmd.id) .. " moved=" .. tostring(moved) .. " err=" .. tostring(move_err) .. " message=" .. tostring(message))
        write_status("processed", tostring(cmd.op) .. " " .. tostring(message))
        print("Hermes bridge v2 processed " .. tostring(cmd.op) .. ": " .. tostring(message))
        return true
    else
        local err = ok and message or handled
        write_result(cmd, false, err, source_path, dst, (os.clock() - started) * 1000)
        append_log("v2 failed " .. tostring(source_label) .. " id=" .. tostring(cmd.id) .. " error=" .. tostring(err))
        write_status("failed", tostring(err))
        print("Hermes bridge v2 failed: " .. tostring(err))
        return false
    end
end

append_log("v2 bridge starting")
write_status("running", "draining queue")
local processed = 0
for _, path in ipairs(list_queue_files()) do
    local id = basename(path):gsub("%.json$", "")
    if not processed_or_failed_exists(id) then
        local raw = read_file(path)
        if raw and raw ~= "" then
            process_raw_command(raw, path, "queue")
            processed = processed + 1
        end
    end
end

if processed == 0 then
    local raw = read_file(INBOX)
    if raw and raw ~= "" then
        process_raw_command(raw, INBOX, "inbox")
        processed = processed + 1
    end
end

if processed == 0 then
    append_log("v2 no queued or inbox command")
    write_status("idle", "no queued command")
    print("Hermes bridge v2: no queued command at " .. QUEUE .. " or " .. INBOX)
else
    append_log("v2 drained commands count=" .. tostring(processed))
end
