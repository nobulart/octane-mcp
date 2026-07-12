-- Octane X Lua API corpus exporter v3.
-- Run inside Octane X (Scripts menu). Output: structured JSON into
-- the container workspace: OctaneMCP/octane_lua_api.<build>.json
--
-- This is the Phase-1 artifact from
-- docs/octane-lua-api-bridge-review.md. It replaces the text-only
-- export_api_docs_v2.lua with machine-readable output that the
-- Python side (src/octanex_mcp/api_corpus.py) can ingest, validate,
-- and turn into a capability registry. The bridge is then generated
-- or validated against the ACTUAL Octane X build, not folklore.
--
-- Runtime probes are explicit about what we depend on:
--   project.getSceneGraph / nodegraph.getRootGraph
--   node.create / node:getPinCount / getPinInfoIx / setPinValue
--   render.start / restart / saveImage / getRenderResultStatistics
--   file.listDirectory / json.encode
-- plus which NT_/P_/A_ constants actually exist on THIS build
-- (e.g. NT_LIGHT_AREA, NT_ENV_TEXTURE, A_MAX_SAMPLES,
--  A_MAX_RENDER_TIME -> nil on some builds, which flips the
--  bridge's light/material/timeout strategy).

local ROOT = os.getenv("OCTANEX_MCP_WORKSPACE") or ((os.getenv("HOME") or "/tmp") .. "/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP")
local OUT_DIR = ROOT
local LOG = ROOT .. "/api_export_v3.log"

local function log(message)
    local f = io.open(LOG, "a")
    if f then
        f:write(os.date("!%Y-%m-%dT%H:%M:%SZ"), " ", tostring(message), "\n")
        f:close()
    else
        print("API export v3 cannot open log: " .. LOG)
    end
end

local function write_json(path, value)
    -- Use octane.json.encode when available; fall back to a minimal
    -- encoder so the exporter never hard-fails on a missing API.
    local ok, encoded = pcall(function()
        if octane and octane.json and octane.json.encode then
            return octane.json.encode(value)
        end
        return nil
    end)
    if ok and encoded then
        local f = io.open(path, "w")
        if f then f:write(encoded); f:close(); return true end
    end
    -- Fallback: write a JSON-ish form our Python reader can parse.
    local f = io.open(path, "w")
    if not f then return false end
    f:write("{\n")
    f:write('  "octane_available": ' .. tostring(octane ~= nil) .. ",\n")
    f:write('  "exported_at": "' .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. '",\n')
    f:write('  "note": "minimal fallback export (octane.json.encode unavailable)",\n')
    f:write('  "modules": [], "constants_by_prefix": {}, "feature_probes": {}\n')
    f:write("}\n")
    f:close()
    return true
end

log("api export v3 starting octane=" .. tostring(octane ~= nil) .. " help=" .. tostring(octane and octane.help ~= nil))

local corpus = {
    schema = "octanex-api-corpus/v1",
    exported_at = os.date("!%Y-%m-%dT%H:%M:%SZ"),
    octane_available = (octane ~= nil),
    octane_help_available = (octane and octane.help ~= nil),
    build = {},
    modules = {},
    constants_by_prefix = {},
    feature_probes = {},
}

-- Build/version if Octane exposes it.
if octane then
    local ok, v = pcall(function() return octane.getVersion and octane.getVersion() end)
    if ok then corpus.build.octane_version = tostring(v) end
    local ok2, b = pcall(function() return octane.getBuild and octane.getBuild() end)
    if ok2 then corpus.build.octane_build = tostring(b) end
end

-- Module inventory via octane.help.
if corpus.octane_help_available then
    local ok_modules, modules = pcall(function() return octane.help.modules() end)
    if ok_modules and modules then
        for moduleName, description in pairs(modules) do
            local entry = { description = tostring(description or "") }
            local ok_funcs, funcs = pcall(function() return octane.help.functions(moduleName) end)
            if ok_funcs and funcs then
                entry.functions = {}
                for _, fn in ipairs(funcs) do
                    table.insert(entry.functions, tostring(fn))
                end
            end
            local ok_props, props = pcall(function() return octane.help.properties(moduleName) end)
            if ok_props and props then
                entry.properties = {}
                for _, propName in ipairs(props) do
                    table.insert(entry.properties, tostring(propName))
                end
            end
            local ok_consts, consts = pcall(function() return octane.help.constants(moduleName) end)
            if ok_consts and consts then
                entry.constants = {}
                for _, constantName in ipairs(consts) do
                    table.insert(entry.constants, tostring(constantName))
                end
            end
            corpus.modules[tostring(moduleName)] = entry
        end
    end
end

-- Direct constants on `octane`, grouped by known prefix.
local PREFIXES = { "NT_", "P_", "A_", "PT_", "NT_ENV_", "NT_MAT_", "NT_LIGHT_", "NT_CAM_", "P_TRANSFORM_", "P_MAX_", "A_MAX_", "A_FILENAME" }
-- The above list is just a hint; walk every key on `octane` so we
-- never miss a build-specific constant.
if octane then
    for key, value in pairs(octane) do
        if type(key) == "string" then
            local prefix = key:match("^(%u+_)")
            if not prefix then
                -- Try to find a leading uppercase-run prefix (e.g. NT_ENV_TEXTURE).
                prefix = key:match("^(%u+_%u+_)") or key:match("^(%u+_)")
            end
            local bucket = prefix or "_other"
            corpus.constants_by_prefix[bucket] = corpus.constants_by_prefix[bucket] or {}
            corpus.constants_by_prefix[bucket][key] = (value ~= nil)
        end
    end
end

-- Feature probes: the exact calls the bridge depends on. Each records
-- whether it succeeded and (for enums like node types) the result shape.
local probes = {
    { "project.getSceneGraph", function() return octane.project and octane.project.getSceneGraph and octane.project.getSceneGraph() end },
    { "nodegraph.getRootGraph", function() return octane.nodegraph and octane.nodegraph.getRootGraph and octane.nodegraph.getRootGraph() end },
    { "node.create", function() return octane.node and octane.node.create end },
    { "render.start", function() return octane.render and octane.render.start end },
    { "render.restart", function() return octane.render and octane.render.restart end },
    { "render.saveImage", function() return octane.render and octane.render.saveImage end },
    { "render.getRenderResultStatistics", function() return octane.render and octane.render.getRenderResultStatistics end },
    { "file.listDirectory", function() return octane.file and octane.file.listDirectory end },
    { "json.encode", function() return octane.json and octane.json.encode end },
    { "timer.create", function() return octane.timer and octane.timer.create end },
    { "gui.create", function() return octane.gui and octane.gui.create end },
    { "apiinfo.getNodeTypeName", function() return octane.apiinfo and octane.apiinfo.getNodeTypeName end },
}
for _, probe in ipairs(probes) do
    local ok, result = pcall(probe[2])
    corpus.feature_probes[probe[1]] = {
        available = (ok and result ~= nil and result ~= false),
        error = (not ok) and tostring(result) or nil,
    }
end

-- Constant probes that change bridge strategy per build.
local constant_probes = {
    "NT_GEO_MESH", "NT_RENDERTARGET", "NT_ENV_DAYLIGHT", "NT_ENV_TEXTURE",
    "NT_MAT_DIFFUSE", "NT_MAT_GLOSSY", "NT_MAT_SPECULAR", "NT_MAT_METALLIC",
    "NT_MAT_EMISSIVE", "NT_LIGHT_AREA", "NT_LIGHT_SUN", "NT_CAM_THINLENS",
    "NT_CAM_PANORAMIC", "NT_FILM_SETTINGS", "P_MESH", "P_CAMERA",
    "P_ENVIRONMENT", "P_FOV", "P_POSITION", "P_TARGET", "P_DIFFUSE",
    "P_ROUGHNESS", "P_EMISSION", "P_MATERIAL", "P_MAX_SAMPLES",
    "P_MAX_RENDER_TIME", "A_FILENAME", "A_MAX_SAMPLES", "A_MAX_RENDER_TIME",
}
corpus.constant_probes = {}
for _, name in ipairs(constant_probes) do
    local value = nil
    local ok, v = pcall(function() return octane[name] end)
    if ok then value = v end
    corpus.constant_probes[name] = { exists = (value ~= nil), value = tostring(value or "nil") }
end

-- Write the corpus file. Build tag from discovered version if present.
local build_tag = "unknown"
if corpus.build.octane_build then
    build_tag = tostring(corpus.build.octane_build):gsub("[^%w%-]", "_")
elseif corpus.build.octane_version then
    build_tag = tostring(corpus.build.octane_version):gsub("[^%w%.%-]", "_")
end
local out_path = OUT_DIR .. "/octane_lua_api." .. build_tag .. ".json"
local written = write_json(out_path, corpus)
if written then
    log("api export v3 wrote " .. out_path)
    print("API export v3 wrote " .. out_path)
else
    log("api export v3 FAILED to write " .. out_path)
    print("API export v3 FAILED to write " .. out_path)
end
