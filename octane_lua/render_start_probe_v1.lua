-- Octane render.start signature probe v1
local ROOT = "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
local OUT = ROOT .. "/render_start_probe_v1.txt"

local function try_signature(desc, fn)
    local ok, res = pcall(fn)
    io.write(string.format("%-40s -> %s (ok=%s)\n", desc, ok and "OK" or "FAIL", tostring(ok)))
    if ok then
        io.write("  Result: " .. tostring(res) .. "\n")
    else
        io.write("  Error: " .. tostring(res) .. "\n")
    end
end

local rt, err = pcall(function()
    local items = {}
    for i=1,999 do
        local n = octane.nodegraph.getNodeByIndex(i)
        if not n then break end
        if n:getType() == octane.NT_RENDERTARGET then table.insert(items, n); break end
    end
    return items[1]
end)

local f = io.open(OUT, "w")
f:write("Octane render.start signature probe\n")
f:write(string.format("RT node found: %s\n", rt and "yes" or ("no - " .. tostring(err))))
f:write("\n--- Testing signatures ---\n")

if rt then
    try_signature("start{renderTargetNode=rt}", function() return octane.render.start{ renderTargetNode=rt } end)
    try_signature("start({},)", function() return octane.render.start({}) end)
    try_signature("start()", function() return octane.render.start() end)
end

try_signature("getmetatable", function() print(type(octane)); print(debug.getmetatable(octane.render)) return true end)

f:close()
print("Probe done, output in " .. OUT)