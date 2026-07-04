-- Octane MCP scene inspection v1
-- Run inside Octane X. Dumps scene items, node types, pins, and connections.

local ROOT = "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
local OUT = ROOT .. "/scene_inspect.txt"
local LOG = ROOT .. "/scene_inspect.log"

local function log(msg)
    local f = io.open(LOG, "a")
    if f then f:write(os.date("!%Y-%m-%dT%H:%M:%SZ"), " ", tostring(msg), "\n"); f:close() end
end

local function serialize(v, depth)
    depth = depth or 0
    if depth > 3 then return "<max-depth>" end
    local t = type(v)
    if t ~= "table" then return tostring(v) end
    local parts = {}
    for k, val in pairs(v) do
        table.insert(parts, tostring(k) .. "=" .. serialize(val, depth + 1))
    end
    table.sort(parts)
    return "{" .. table.concat(parts, ", ") .. "}"
end

local function writeln(f, s) f:write(tostring(s or ""), "\n") end

local f, err = io.open(OUT, "w")
if not f then
    print("scene inspect failed to open " .. OUT .. ": " .. tostring(err))
    return
end

writeln(f, "Octane MCP scene inspection v1")
writeln(f, os.date("!%Y-%m-%dT%H:%M:%SZ"))
writeln(f, "octane=" .. tostring(octane ~= nil) .. " node=" .. tostring(octane and octane.node ~= nil) .. " project=" .. tostring(octane and octane.project ~= nil))
writeln(f, "")

local function api_name(kind, id)
    if not (octane and octane.apiinfo) then return "" end
    local ok, result
    if kind == "node" then ok, result = pcall(function() return octane.apiinfo.getNodeTypeName(id) end) end
    if kind == "pin" then ok, result = pcall(function() return octane.apiinfo.getPinIdName(id) end) end
    if kind == "pintype" then ok, result = pcall(function() return octane.apiinfo.getPinTypeName(id) end) end
    if ok and result then return tostring(result) end
    return ""
end

local graph = nil
if octane and octane.project and octane.project.getSceneGraph then
    local ok, g = pcall(function() return octane.project.getSceneGraph() end)
    if ok then graph = g end
end
if not graph and octane and octane.nodegraph and octane.nodegraph.getRootGraph then
    local ok, g = pcall(function() return octane.nodegraph.getRootGraph() end)
    if ok then graph = g end
end

if not graph then
    writeln(f, "NO SCENE GRAPH")
    f:close(); print("scene inspect wrote " .. OUT); return
end

local ok_items, items = pcall(function() return graph:getOwnedItems() end)
writeln(f, "getOwnedItems ok=" .. tostring(ok_items) .. " count=" .. tostring(items and #items or 0))
writeln(f, "")

if ok_items and items then
    for idx, item in ipairs(items) do
        writeln(f, "ITEM " .. tostring(idx) .. " tostring=" .. tostring(item))
        local okp, props = pcall(function() return item:getProperties() end)
        writeln(f, "  props_ok=" .. tostring(okp) .. " props=" .. serialize(props))
        local node_type = props and (props.type or props.nodeType or props.nodeTypeId)
        if node_type then writeln(f, "  node_type_name=" .. api_name("node", node_type)) end
        local okni, ni = pcall(function() return item:getNodeInfo() end)
        writeln(f, "  node_info_ok=" .. tostring(okni) .. " node_info=" .. serialize(ni))
        local okpc, pc = pcall(function() return item:getPinCount() end)
        writeln(f, "  pin_count_ok=" .. tostring(okpc) .. " pin_count=" .. tostring(pc))
        if okpc and pc then
            for i = 1, pc do
                local okpi, pi = pcall(function() return item:getPinInfoIx(i) end)
                if not okpi then okpi, pi = pcall(function() return item:getPinInfoIx(i - 1) end) end
                local pin_id = pi and (pi.id or pi.pinId)
                local pin_type = pi and (pi.type or pi.pinType)
                writeln(f, "    PIN " .. tostring(i) .. " ok=" .. tostring(okpi) .. " id_name=" .. api_name("pin", pin_id) .. " type_name=" .. api_name("pintype", pin_type) .. " info=" .. serialize(pi))
                local okcn, cn = pcall(function() return item:getConnectedNodeIx(i) end)
                if not okcn then okcn, cn = pcall(function() return item:getConnectedNodeIx(i - 1) end) end
                writeln(f, "      connected_ok=" .. tostring(okcn) .. " connected=" .. tostring(cn))
            end
        end
        writeln(f, "")
    end
end

f:close()
log("scene inspect wrote " .. OUT)
print("scene inspect wrote " .. OUT)
