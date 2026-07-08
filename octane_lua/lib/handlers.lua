-- Hermes / OctaneX MCP shared command handlers.
-- Each handler accepts a parsed command table and returns (ok, handled, message).
--
-- These are the *single-source-of-truth* handlers for both the one-shot and
-- persistent bridge bridges. The generated entry-point scripts simply dofile
-- runtime.lua and handlers.lua, then call handle_command(cmd).

local runtime = require("lib.runtime")
local handlers = {}

-- Command dispatch table -- each key is an op (string) -> handler function.
handlers.dispatch = {}

-- ---------------------------------------------------------------------------
-- parse_command (used by both bridges before reaching handlers)
-- ---------------------------------------------------------------------------

function handlers.parse_command(raw)
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
        group_index = payload.group_index,
        fov = payload.fov,
        samples = payload.samples,
        width = payload.width,
        height = payload.height,
        color = payload.color,
        position = payload.position,
        target = payload.target,
    }, nil
end

-- ---------------------------------------------------------------------------
-- Handlers (return ok, handled, message)
-- ---------------------------------------------------------------------------

function handlers.handle_ping(cmd)
    return true, true, "pong " .. tostring(cmd.message or "")
end

function handlers.handle_import_geometry(cmd)
    local ok, msg = runtime.ensure_octane()
    if not ok then return true, msg, nil end
    if not cmd.path then return false, "import_geometry missing path", nil end
    local name = cmd.name or runtime.basename(cmd.path)
    local mesh = runtime.find_item_by_name(name)
    if not mesh then
        local err
        mesh, err = runtime.create_node(octane.NT_GEO_MESH, name, {500, 500})
        if not mesh then return false, "create mesh failed: " .. tostring(err), nil end
    end
    local loaded, load_err = pcall(function() mesh:setAttribute(octane.A_FILENAME, cmd.path, true) end)
    if not loaded then return false, "mesh load failed: " .. tostring(load_err), nil end
    local rt = runtime.get_or_create_render_target()
    if rt and mesh then
        runtime.activate_render_target(rt)
        local mesh_pin = octane.P_MESH or "mesh"
        runtime.disconnect_pin(rt, mesh_pin)
        runtime.disconnect_pin(rt, "mesh")
        runtime.connect_to(rt, mesh_pin, mesh)
    end
    local refreshed, refresh_msg = runtime.request_render_restart(64)
    return true, "imported geometry " .. name, refresh_msg
end

function handlers.handle_create_material(cmd)
    local ok, msg = runtime.ensure_octane()
    if not ok then return true, msg, nil end
    local name = cmd.name or "mcp_material"
    local existing = runtime.find_item_by_name(name)
    if existing then return true, "material exists " .. name, nil end
    local matType = octane.NT_MAT_DIFFUSE
    if cmd.kind == "glossy" and octane.NT_MAT_GLOSSY then matType = octane.NT_MAT_GLOSSY end
    if cmd.kind == "specular" and octane.NT_MAT_SPECULAR then matType = octane.NT_MAT_SPECULAR end
    if cmd.kind == "metallic" and octane.NT_MAT_METALLIC then matType = octane.NT_MAT_METALLIC end
    local mat, err = runtime.create_node(matType, name, {650, 500})
    if not mat then return false, "create material failed: " .. tostring(err), nil end
    if cmd.color then
        runtime.set_pin_value(mat, octane.P_DIFFUSE or "diffuse", {cmd.color[1] or 0.8, cmd.color[2] or 0.8, cmd.color[3] or 0.8})
    end
    return true, "created material " .. name, nil
end

function handlers.handle_assign_material(cmd)
    local ok, msg = runtime.ensure_octane()
    if not ok then return true, msg, nil end
    local mesh = runtime.find_item_by_name(cmd.object_name) or runtime.find_item_by_name("octane_live_cube")
    local mat = runtime.find_item_by_name(cmd.material_name)
    if not mesh then return false, "unknown object " .. tostring(cmd.object_name), nil end
    if not mat then return false, "unknown material " .. tostring(cmd.material_name), nil end
    local group_index = cmd.group_index or (cmd.payload and cmd.payload.group_index)
    local connected = runtime.connect_material_to_mesh_pins(mesh, mat, group_index)
    for _, pin in ipairs({"default", "Material", "material", "m1", "mat", octane.P_MATERIAL}) do
        if pin then connected = runtime.connect_to(mesh, pin, mat) or connected end
    end
    if connected then
        local refreshed, refresh_msg = runtime.request_render_restart(64)
        return true, "assigned material " .. cmd.material_name .. (group_index and (" to group #" .. tostring(group_index)) or ""), refresh_msg
    end
    return true, "material exists; no known material pin accepted on mesh", nil
end

function handlers.handle_set_camera(cmd)
    local ok, msg = runtime.ensure_octane()
    if not ok then return true, msg, nil end
    local rt, rt_err = runtime.get_or_create_render_target()
    if not rt then return false, "render target failed: " .. tostring(rt_err), nil end
    runtime.activate_render_target(rt)
    local cam = runtime.find_item_by_name("Hermes Camera")
    if not cam then
        local err
        cam, err = runtime.create_node(octane.NT_CAM_THINLENS or octane.NT_CAM_PANORAMIC, "Hermes Camera", {300, 520})
        if not cam then return false, "camera create failed: " .. tostring(err), nil end
    end
    if cmd.fov then runtime.set_pin_value(cam, octane.P_FOV or "fov", cmd.fov) end
    if cmd.position then runtime.set_pin_value(cam, octane.P_POSITION or "pos", cmd.position) end
    if cmd.target then runtime.set_pin_value(cam, octane.P_TARGET or "target", cmd.target) end
    runtime.connect_to(rt, octane.P_CAMERA or "camera", cam)
    local refreshed, refresh_msg = runtime.request_render_restart(64)
    return true, "camera connected", refresh_msg
end

function handlers.handle_set_lighting(cmd)
    local ok, msg = runtime.ensure_octane()
    if not ok then return true, msg, nil end
    local rt, rt_err = runtime.get_or_create_render_target()
    if not rt then return false, "render target failed: " .. tostring(rt_err), nil end
    runtime.activate_render_target(rt)
    local env_type = octane.NT_ENV_DAYLIGHT or octane.NT_ENV_TEXTURE
    if not env_type then return true, "no known environment node type constant", nil end
    local env = runtime.find_item_by_name("Hermes Environment")
    if not env then
        local err
        env, err = runtime.create_node(env_type, "Hermes Environment", {300, 680})
        if not env then return false, "environment create failed: " .. tostring(err), nil end
    end
    runtime.connect_to(rt, octane.P_ENVIRONMENT or "environment", env)
    local refreshed, refresh_msg = runtime.request_render_restart(64)
    return true, "lighting preset " .. tostring(cmd.preset or "default") .. " connected", refresh_msg
end

function handlers.handle_start_render(cmd)
    return runtime.request_render_restart(cmd.samples or 64, cmd.width or 1280, cmd.height or 1280)
end

function handlers.handle_save_preview(cmd)
    if not (octane and octane.render) then return true, "Octane render API unavailable; acknowledged only", nil end
    local path = cmd.path or "/OctaneMCP/renders/preview.png"
    local rt = runtime.get_or_create_render_target()
    runtime.activate_render_target(rt)
    os.execute("mkdir -p '" .. path:gsub("'", "'\\''") .. "'")

    local refreshed, refresh_msg = runtime.request_render_restart(cmd.samples or 64, cmd.width or 1280, cmd.height or 1280, cmd.max_render_time)
    if not refreshed then return false, refresh_msg, nil end
    -- Wait until min_samples reached OR the time cap (timeout_seconds) elapses.
    -- On timeout we still SAVE the best-effort frame (do not abort) so a
    -- user-requested convergence ceiling actually yields an image.
    local ready, ready_msg = runtime.wait_for_render_ready(cmd.min_samples or 16, cmd.timeout_seconds or 10)
    if not ready then
        runtime.append_log(LOG, "save_preview: timeout reached, saving best-effort frame (" .. tostring(ready_msg) .. ")")
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
        if ok and r1 ~= false and runtime.file_exists(path) then return true, nil end
        if ok and r1 == false then return false, "returned false" end
        if ok then return false, "reported success but file missing" end
        return false, tostring(r1)
    end

    for _, candidate in ipairs(candidates) do
        local cname, cvalue = candidate[1], candidate[2]
        local ok, err = attempt("saveImage", function() return octane.render.saveImage(path, cvalue) end)
        if ok then return true, "preview saved " .. path, err end
        last_err = err
        ok, err = attempt("saveImage2", function() return octane.render.saveImage2{ path=path, saveType=cvalue, type=cvalue, renderTargetNode=rt } end)
        if ok then return true, "preview saved " .. path, err end
        ok, err = attempt("saveImage2(filename,props)", function() return octane.render.saveImage2(path, { saveType=cvalue, type=cvalue, renderTargetNode=rt }) end)
        if ok then return true, "preview saved " .. path, err end
    end
    return false, "save preview failed: " .. last_err, nil
end

handlers.dispatch["ping"] = handlers.handle_ping
handlers.dispatch["import_geometry"] = handlers.handle_import_geometry
handlers.dispatch["create_material"] = handlers.handle_create_material
handlers.dispatch["assign_material"] = handlers.handle_assign_material
handlers.dispatch["set_camera"] = handlers.handle_set_camera
handlers.dispatch["set_lighting"] = handlers.handle_set_lighting
handlers.dispatch["start_render"] = handlers.handle_start_render
handlers.dispatch["save_preview"] = handlers.handle_save_preview

-- ---------------------------------------------------------------------------
-- handle_command dispatcher (called by both bridges)
-- ---------------------------------------------------------------------------

function handlers.handle_command(cmd)
    local handler = handlers.dispatch[cmd.op]
    if handler then
        local ok, handled, message = handler(cmd)
        return ok, handled, message or tostring(cmd.op)
    end
    return true, true, "acknowledged " .. tostring(cmd.op)
end

return handlers
