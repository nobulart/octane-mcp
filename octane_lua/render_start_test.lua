-- Simple start_render probe: just call it with nothing first and log results
local ROOT = "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
local OUT = ROOT .. "/render_start_test_v2.txt"

local f = io.open(OUT, "w")

f:write("=== start_render Test ===\n\n")

-- Test 1: start with nothing
local ok, err = pcall(function()
    local r = octane.render.start()
    return true, tostring(r)
end)

if ok then
    f:write("Test 1 - octane.render.start() with no args:\n")
    f:write("  Result: OK\n")
else
    f:write("Test 1 - octane.render.start() with no args:\n")
    f:write(string.format("  Error: %s\n", err))
end

f:close()
print("Output saved to "..OUT)