import io, sys

NEW_FUNC = r'''local function request_render_restart(samples, width, height)
    -- Bulletproof: called from EVERY scene-assembly handler (import_geometry,
    -- create_material, set_camera, set_lighting, save_preview). A hard error
    -- here would abort the whole drain script and strand the rest of the queue,
    -- so the ENTIRE body runs inside one pcall. Any internal failure returns
    -- (false, err) so callers log an honest failure instead of dropping the cmd.
    local ok, a, b = pcall(function()
        if not (octane and octane.render) then return true, "Octane render API unavailable; acknowledged only" end
        append_log("request_render_restart: entered samples=" .. tostring(samples))
        local rt, rt_err = get_or_create_render_target()
        if not rt then return false, "render target failed: " .. tostring(rt_err) end
        pcall(ensure_render_target_defaults, rt)
        pcall(activate_render_target, rt)
        pcall(set_render_resolution, rt, width or DEFAULT_WIDTH, height or DEFAULT_HEIGHT)
        samples = samples or 64
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
'''

files = ["octane_lua/hermes_bridge_oneshot_v2.lua", "octane_lua/hermes_bridge_persistent_v1.lua"]
for f in files:
    s = open(f).read()
    start = s.index("local function request_render_restart(samples, width, height)")
    em = "local function render_stat_number"
    em_idx = s.index(em)
    seg = s[start:em_idx]
    last = seg.rfind("\nend\n")
    if last == -1:
        print("FAIL: no col-0 end found in", f); sys.exit(1)
    old_span = s[start:start + last + 5]
    new_s = s[:start] + NEW_FUNC + "\n" + s[start + last + 5:]
    open(f, "w").write(new_s)
    print("patched", f, "replaced", len(old_span), "chars")
