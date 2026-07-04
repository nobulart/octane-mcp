-- Octane MCP diagnostic v2. Run inside Octane X.
-- Writes markers to several likely writable locations and prints a summary.

local paths = {
    "/Users/craig/OctaneMCP/octane_diag_user.txt",
    "/tmp/octane_diag_tmp.txt",
    "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/octane_diag_container.txt",
    "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/tmp/octane_diag_container_tmp.txt",
}

local function try_write(path, text)
    local f, err = io.open(path, "w")
    if not f then return false, tostring(err) end
    f:write(text)
    f:close()
    return true, "ok"
end

local summary = {}
local octane_state = "octane=" .. tostring(octane ~= nil) .. " octane_help=" .. tostring(octane and octane.help ~= nil) .. " octane_node=" .. tostring(octane and octane.node ~= nil)
for _, p in ipairs(paths) do
    local ok, msg = try_write(p, "Octane MCP diagnostic v2\n" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\n" .. octane_state .. "\n")
    table.insert(summary, p .. " => " .. tostring(ok) .. " " .. tostring(msg))
end

local text = table.concat(summary, "\n")
print("Octane MCP diagnostic v2:\n" .. text)

-- Also try writing a compact status to the normal MCP status path.
try_write("/Users/craig/OctaneMCP/octane_diag_summary.txt", text .. "\n" .. octane_state .. "\n")
