-- Export Octane Lua API documentation from the running Octane X build.
-- Run inside Octane X. Output: ~/OctaneMCP/octane_lua_api.txt

local ROOT = "/Users/craig/OctaneMCP"
os.execute("mkdir -p '/Users/craig/OctaneMCP'")
local OUT = ROOT .. "/octane_lua_api.txt"
local LOG = ROOT .. "/api_export.log"

local function log(message)
    local lf = io.open(LOG, "a")
    if lf then
        lf:write(os.date("!%Y-%m-%dT%H:%M:%SZ"), " ", tostring(message), "\n")
        lf:close()
    end
end

log("api export starting")

local f, err = io.open(OUT, "w")
if not f then
    log("failed to open output: " .. tostring(err))
    print("Failed to open " .. OUT .. ": " .. tostring(err))
    return
end

local function writeln(s)
    f:write(tostring(s or ""), "\n")
end

writeln("Octane Lua API export")
writeln(os.date("!%Y-%m-%dT%H:%M:%SZ"))
writeln("")

if not octane or not octane.help then
    writeln("octane.help is not available in this runtime")
    f:close()
    log("octane.help not available; wrote " .. OUT)
    print("Wrote " .. OUT)
    return
end

local modules = octane.help.modules()
for moduleName, description in pairs(modules) do
    writeln("MODULE " .. tostring(moduleName))
    writeln(tostring(description))
    writeln("FUNCTIONS")
    local funcs = octane.help.functions(moduleName)
    for _, fn in ipairs(funcs) do
        local fullName = "octane." .. tostring(moduleName) .. "." .. tostring(fn)
        local ok, doc = pcall(function() return octane.help.functionDoc(octane[moduleName][fn]) end)
        if ok and doc then
            writeln("  " .. fullName .. " :: " .. tostring(doc.description or ""))
        else
            writeln("  " .. fullName)
        end
    end
    writeln("PROPERTIES")
    local props = octane.help.properties(moduleName)
    for _, propName in ipairs(props) do
        local ok, doc = pcall(function() return octane.help.propertiesDoc(moduleName, propName) end)
        if ok and doc then
            writeln("  " .. tostring(propName) .. " :: " .. tostring(doc.description or ""))
        else
            writeln("  " .. tostring(propName))
        end
    end
    writeln("CONSTANTS")
    local constants = octane.help.constants(moduleName)
    for _, constantName in ipairs(constants) do
        writeln("  " .. tostring(constantName))
    end
    writeln("")
end

f:close()
log("api export wrote " .. OUT)
print("Wrote " .. OUT)
