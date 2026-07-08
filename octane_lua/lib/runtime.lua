-- Hermes / OctaneX MCP shared runtime.
-- Self-contained Lua library: file I/O, JSON (uses dofile json.lua or inline decoder),
-- status/result writing, logging, and queue lifecycle helpers (queue -> processing -> processed|failed).
--
-- Both one-shot and persistent bridges can require or dofile this file.
-- If Octane cannot reliably require repo-local modules, the init scripts
-- inline the contents; the source-of-truth code lives here.

local runtime = {}

-- ---------------------------------------------------------------------------
-- JSON loader (tries dofile, falls back to inline)
-- ---------------------------------------------------------------------------

local function load_json_decoder()
    if not pcall(function() require("lib.json") end) then
        -- Fallback to inline (the one-shot and persistent generated copies
        -- ship with a self-contained JSON decoder). We create a global JSON
        -- table if one does not already exist.
        if not _G.JSON then
            local json = {}
            -- We leave `_parse_value`, `JSON.decode`, etc. in global scope
            -- where the generated bridges already installed them.
            if type(JSON) == "table" then
                json = JSON
            end
            _G.JSON = json
        end
        return _G.JSON
    end
    return require("lib.json")
end

-- ---------------------------------------------------------------------------
-- File helpers
-- ---------------------------------------------------------------------------

function runtime.write_file(path, text)
    local f, err = io.open(path, "w")
    if not f then
        return false, err
    end
    f:write(text)
    f:close()
    return true
end

function runtime.read_file(path, quiet)
    local f, err = io.open(path, "r")
    if not f then
        if not quiet then
        end
        return nil, err
    end
    local data = f:read("*a")
    f:close()
    return data
end

function runtime.file_exists(path)
    local f = io.open(path, "r")
    if f then f:close(); return true end
    return false
end

function runtime.remove_file(path)
    os.remove(path)
end

-- ---------------------------------------------------------------------------
-- Logging and directory helpers
-- ---------------------------------------------------------------------------

function runtime.basename(path)
    return tostring(path):match("([^/]+)$") or tostring(path)
end

function runtime.dirname(path)
    return tostring(path):match("^(.*/)[^/]+$") or (tostring(path):match("^(.+)/[^/]+$") or ".")
end

function runtime.json_escape(s)
    s = tostring(s or "")
    s = s:gsub('\\', '\\\\'):gsub('"', '\\"'):gsub('\n', '\\n'):gsub('\r', '\\r'):gsub('\t', '\\t')
    return s
end

function runtime.append_log(log_path, message)
    local f = io.open(log_path, "a")
    if f then
        f:write(os.date("!%Y-%m-%dT%H:%M:%SZ"), " ", tostring(message), "\n")
        f:close()
    end
end

-- ---------------------------------------------------------------------------
-- Status and result writers (shared between oneshot and persistent)
-- ---------------------------------------------------------------------------

function runtime.write_status(status_path, bridge_name, mode, state, extra)
    local text = "{\n" ..
        "  \"bridge_seen\": true,\n" ..
        "  \"bridge\": \"" .. runtime.json_escape(bridge_name) .. "\",\n" ..
        "  \"mode\": \"" .. runtime.json_escape(mode) .. "\",\n" ..
        "  \"status\": \"" .. runtime.json_escape(state or "ok") .. "\",\n" ..
        "  \"updated_at\": \"" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\",\n" ..
        "  \"octane_available\": " .. tostring(octane ~= nil) .. ",\n" ..
        "  \"octane_node_available\": " .. tostring(octane ~= nil and octane.node ~= nil)
    if extra then
        text = text .. ",\n  \"last_event\": \"" .. runtime.json_escape(extra) .. "\""
    end
    text = text .. "\n}\n"
    runtime.write_file(status_path, text)
end

function runtime.write_result(results_path, cmd, success, message, source_path, command_path, duration_ms)
    local output_paths = "[]"
    if cmd and cmd.op == "save_preview" then
        local preview_path = cmd.path or ""
        output_paths = "[\"" .. runtime.json_escape(preview_path) .. "\"]"
    end
    local path = results_path .. "/" .. tostring(cmd and cmd.id or "unknown") .. ".json"
    local text = "{\n" ..
        "  \"schema_version\": \"1.0\",\n" ..
        "  \"command_id\": \"" .. runtime.json_escape(cmd and cmd.id or "unknown") .. "\",\n" ..
        "  \"op\": \"" .. runtime.json_escape(cmd and cmd.op or "unknown") .. "\",\n" ..
        "  \"success\": " .. tostring(success == true) .. ",\n" ..
        "  \"message\": \"" .. runtime.json_escape(message or "") .. "\",\n" ..
        "  \"processed_at\": \"" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\",\n" ..
        "  \"duration_ms\": " .. tostring(math.floor((duration_ms or 0) + 0.5)) .. ",\n" ..
        "  \"source_path\": \"" .. runtime.json_escape(source_path or "") .. "\",\n" ..
        "  \"command_path\": \"" .. runtime.json_escape(command_path or "") .. "\",\n" ..
        "  \"output_paths\": " .. output_paths .. "\n" ..
        "}\n"
    runtime.write_file(path, text)
    return path
end

-- ---------------------------------------------------------------------------
-- Queue lifecycle helpers
-- ---------------------------------------------------------------------------

function runtime.moved_to_processing(queue_path, processing_path, cmd)
    active_path = queue_path
    local moved = os.rename(queue_path, processing_path)
    if moved then
        active_path = processing_path
    end
    return moved, active_path
end

function runtime.move_to_dir(source_path, dir, cmd, label)
    local id = cmd and cmd.id or runtime.basename(source_path):gsub("%.json$", "")
    local dst = dir .. "/" .. id .. ".json"
    local moved, err = os.rename(source_path, dst)
    if not moved and label then
        runtime.append_log(label, "move " .. source_path .. " -> " .. dir .. " err=" .. tostring(err))
    end
    return moved, dst
end

-- ---------------------------------------------------------------------------
-- Octane bridge helpers (shared by both modes)
-- ---------------------------------------------------------------------------

function runtime.ensure_octane()
    if not (octane and octane.node and octane.project) then
        return false, "Octane node/project API unavailable; acknowledged only"
    end
    return true, nil
end

function runtime.scene_graph()
    if octane.project and octane.project.getSceneGraph then
        return octane.project.getSceneGraph()
    end
    if octane.nodegraph and octane.nodegraph.getRootGraph then
        return octane.nodegraph.getRootGraph()
    end
    return nil
end

function runtime.find_item_by_name(name)
    if not name or name == "" then return nil end
    local graph = runtime.scene_graph()
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

function runtime.create_node(type_id, name, position)
    if not type_id then return nil, "missing node type for " .. tostring(name) end
    local ok, node_or_err = pcall(function()
        return octane.node.create{ type=type_id, name=name, position=position or {500, 500} }
    end)
    if ok then return node_or_err, nil end
    return nil, tostring(node_or_err)
end

function runtime.set_pin_value(node, pin, value)
    if not node or not pin then return false end
    local ok, err = pcall(function() node:setPinValue(pin, value) end)
    if not ok then runtime.append_log(LOG, "setPinValue failed pin=" .. tostring(pin) .. " err=" .. tostring(err)) end
    return ok
end

function runtime.connect_to(node, pin, src)
    if not node or not pin or not src then return false end
    local ok, err = pcall(function() node:connectTo(pin, src) end)
    if not ok then runtime.append_log(LOG, "connectTo failed pin=" .. tostring(pin) .. " err=" .. tostring(err)) end
    return ok
end

function runtime.disconnect_pin(node, pin)
    if not node or not pin then return false end
    local ok, err = pcall(function() node:disconnect(pin) end)
    if not ok then runtime.append_log(LOG, "disconnect failed pin=" .. tostring(pin) .. " err=" .. tostring(err)) end
    return ok
end

function runtime.connected_node(node, pin)
    if not node or not pin then return nil end
    local ok, connected = pcall(function() return node:getConnectedNode(pin) end)
    if ok and connected then return connected end
    ok, connected = pcall(function() return node:getConnectedNodeIx(pin) end)
    if ok and connected then return connected end
    return nil
end

-- Assign a material to a mesh's material pin(s). If group_index is provided,
-- only the Nth material pin (ordered by pin index) is wired; otherwise all
-- material pins are wired to the same material. This enables a single combined
-- OBJ with multiple usemtl groups (e.g. red cube group + green sphere group)
-- to receive distinct materials.
function runtime.connect_material_to_mesh_pins(mesh, mat, group_index)
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
                    runtime.append_log(LOG, "skipping material pin #" .. tostring(material_pin_ix) .. " (group filter " .. tostring(group_index) .. ")")
                else
                    if info.name then connected = runtime.connect_to(mesh, info.name, mat) or connected end
                    if info.id then connected = runtime.connect_to(mesh, info.id, mat) or connected end
                end
            end
        end
    end
    if group_index then
        runtime.append_log(LOG, "material pin #" .. tostring(group_index) .. " target on mesh (of " .. tostring(material_pin_ix) .. " material pins)")
    end
    return connected
end

function runtime.connect_material_to_all_mesh_pins(mesh, mat)
    return runtime.connect_material_to_mesh_pins(mesh, mat, nil)
end

function runtime.get_or_create_render_target()
    local rt = runtime.find_item_by_name("Hermes Render Target") or runtime.find_item_by_name("Hermes_RT")
    if rt then return rt end
    local node, err = runtime.create_node(octane.NT_RENDERTARGET, "Hermes Render Target", {300, 300})
    if not node then return nil, err end
    return node, nil
end

function runtime.ensure_connected_node(node, pin, type_id, name, position)
    if not node or not pin or not type_id then return nil end
    local existing = runtime.connected_node(node, pin)
    if existing then return existing end
    local item = runtime.find_item_by_name(name)
    if not item then item = runtime.create_node(type_id, name, position) end
    if item then runtime.connect_to(node, pin, item) end
    return item
end

function runtime.ensure_render_target_defaults(rt)
    if not rt then return false end
    runtime.ensure_connected_node(rt, octane.P_KERNEL or "kernel", octane.NT_KERN_DIRECTLIGHTING, "Hermes Direct Lighting Kernel", {520, 160})
    runtime.ensure_connected_node(rt, octane.P_ANIMATION or "animation", octane.NT_ANIMATION_SETTINGS, "Hermes Animation Settings", {520, 220})
    runtime.ensure_connected_node(rt, octane.P_RENDER_LAYER or "renderLayer", octane.NT_RENDER_LAYER, "Hermes Render Layer", {520, 360})
    runtime.ensure_connected_node(rt, octane.P_RENDER_PASSES or "renderPasses", octane.NT_RENDER_AOV_GROUP, "Hermes Render AOV Group", {520, 420})
    runtime.ensure_connected_node(rt, octane.P_OUTPUT_AOVS or "compositeAovs", octane.NT_OUTPUT_AOV_GROUP, "Hermes Output AOV Group", {520, 480})
    runtime.ensure_connected_node(rt, octane.P_IMAGER or "imager", octane.NT_IMAGER_CAMERA, "Hermes Imager", {520, 540})
    runtime.ensure_connected_node(rt, octane.P_POST_PROCESSING or "postproc", octane.NT_POSTPROCESSING, "Hermes Post Processing", {520, 600})
    if octane and octane.project then
        local pin = octane.P_FILM_SETTINGS or "filmSettings"
        local film = runtime.connected_node(rt, pin)
        if not film then
            local film_type = octane.NT_FILM_SETTINGS
            if film_type then
                local created, err = runtime.create_node(film_type, "Hermes Film Settings", {520, 300})
                if created then runtime.connect_to(rt, pin, created) end
            end
        end
    end
    return true
end

function runtime.activate_render_target(rt)
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
    if activated then runtime.append_log(LOG, "activated render target " .. tostring(rt)) end
    return activated
end

function runtime.set_max_render_time(rt, max_render_time)
    max_render_time = tonumber(max_render_time)
    if not max_render_time or max_render_time <= 0 then return false, "max_render_time unset or <=0 (0 = unlimited)" end
    local pin = octane.P_FILM_SETTINGS or "filmSettings"
    local film = runtime.connected_node(rt, pin) or runtime.connected_node(rt, "filmSettings")
    if not film then
        local film_type = octane.NT_FILM_SETTINGS
        if film_type then
            local created, err = runtime.create_node(film_type, "Hermes Film Settings", {520, 300})
            if not created then return false, "film create failed: " .. tostring(err) end
            runtime.connect_to(rt, pin, created)
            film = created
        end
    end
    if not film then return false, "film settings unavailable" end
    -- Probe the time-cap pin name. Octane builds vary: P_MAX_RENDER_TIME,
    -- "maxRenderTime", or "maxTime". maxSamples is known-IGNORED on this
    -- build, so we do NOT rely on it; this pin is the proper GPU stop.
    local ok_any = false
    for _, p in ipairs({octane.P_MAX_RENDER_TIME, "maxRenderTime", "maxTime", "maxRenderTimeSeconds"}) do
        if p then ok_any = runtime.set_pin_value(film, p, max_render_time) or ok_any end
    end
    if not ok_any then
        -- None of the known time-cap pins exist on this Octane build
        -- (maxSamples is likewise ignored). The Lua wait_for_render_ready
        -- wall-clock timeout is the effective convergence cap instead.
        runtime.append_log(LOG, "max_render_time: no honored pin on this Octane build (maxRenderTime ignored); relying on timeout_seconds wall-clock cap")
    else
        runtime.append_log(LOG, "max_render_time requested " .. tostring(max_render_time) .. " ok=true")
    end
    return ok_any
end

function runtime.request_render_restart(samples, width, height, max_render_time)
    if not (octane and octane.render) then return true, "Octane render API unavailable; acknowledged only" end
    local rt, rt_err = runtime.get_or_create_render_target()
    if not rt then return false, "render target failed: " .. tostring(rt_err) end
    runtime.ensure_render_target_defaults(rt)
    runtime.activate_render_target(rt)
    if max_render_time then
        local ok, merr = runtime.set_max_render_time(rt, max_render_time)
        if not ok then runtime.append_log(LOG, "max_render_time warn: " .. tostring(merr)) end
    end
    width = tonumber(width) or 1280
    height = tonumber(height) or 1280
    samples = samples or 64
    local last_errs = {}
    local function try_render_call(label, fn)
        local ok, result = pcall(fn)
        if not ok then table.insert(last_errs, label .. ": " .. tostring(result)) end
        return ok, result
    end
    -- Stop any in-flight render before (re)starting. Octane rejects a new
    -- start/restart while a previous render is still active
    -- ("Can't start a new render before finishing the previous render"), which
    -- previously left blank/black previews. stop() ends the current pass so the
    -- next start/restart is accepted. pause() alone is NOT enough (a paused
    -- render is still "in progress").
    pcall(function() if octane.render.stop then octane.render.stop() end end)
    pcall(function() octane.render.pause() end)
    -- NOTE: maxSamples is NOT a recognized key for octane.render.start on this
    -- Octane build, so it is intentionally NOT used; the render is instead
    -- bounded by wait_for_render_ready() polling the sample count to min_samples
    -- (with a wall-clock timeout), then the frame is grabbed. This avoids an
    -- unbounded render that would block every subsequent restart.
    local ok, result = try_render_call("start{renderTargetNode=rt}", function() return octane.render.start{ renderTargetNode=rt } end)
    if ok then return true, "render start requested (unbounded; bounded by wait_for_render_ready)" end
    ok, result = try_render_call("restart()", function() return octane.render.restart() end)
    if ok then return true, "render restart requested" end
    ok, result = try_render_call("start({renderTargetNode=rt})", function() return octane.render.start({ renderTargetNode=rt }) end)
    if ok then return true, "render start requested" end
    ok, result = try_render_call("continue()", function() return octane.render.continue() end)
    if ok then return true, "render continue requested" end
    return false, "render refresh failed; see bridge.log"
end

function runtime.request_bridge_close(reason)
    reason = reason or "releasing bridge window"
    if _G.close_requested then
        return
    end
    _G.close_requested = true
    if _G.bridge_timer then
        pcall(function() _G.bridge_timer:stop() end)
        pcall(function() octane.timer.stop(_G.bridge_timer) end)
    end
    runtime.append_log(LOG, reason)
    if _G.bridge_window then
        local closed = false
        local ok = pcall(function() octane.gui.closeWindow(_G.bridge_window) end)
        closed = closed or ok
        ok = pcall(function() _G.bridge_window:closeWindow() end)
        closed = closed or ok
    end
end

function runtime.sleep_seconds(seconds)
    seconds = tonumber(seconds) or 0.25
    if octane and octane.sleep then
        local ok = pcall(function() octane.sleep(seconds) end)
        if ok then return end
    end
    os.execute("sleep " .. tostring(seconds))
end

function runtime.wait_for_render_ready(min_samples, timeout_seconds)
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
            local beauty = tonumber(stats.beautySamplesPerPixel) or 0
            local info = tonumber(stats.infoSamplesPerPixel) or 0
            local pending = stats.hasPendingUpdates == true
            if (beauty >= min_samples or info >= min_samples) and not pending then
                return true, "beauty=" .. tostring(beauty) .. " info=" .. tostring(info) .. " pending=" .. tostring(pending)
            end
        end
        runtime.sleep_seconds(0.5)
    end
    return false, last
end

return runtime
