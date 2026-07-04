-- Export Octane Lua API documentation from Octane X, verbose v2.
-- Run inside Octane X. Output: container OctaneMCP/octane_lua_api.txt

local ROOT = "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
local OUT = ROOT .. "/octane_lua_api.txt"
local LOG = ROOT .. "/api_export.log"

local function log(message)
    local lf = io.open(LOG, "a")
    if lf then
        lf:write(os.date("!%Y-%m-%dT%H:%M:%SZ"), " ", tostring(message), "\n")
        lf:close()
    else
        print("API export v2 cannot open log: " .. LOG)
    end
end

local function writeln(f, s)
    f:write(tostring(s or ""), "\n")
end

log("api export v2 starting octane=" .. tostring(octane ~= nil) .. " help=" .. tostring(octane and octane.help ~= nil))

local f, err = io.open(OUT, "w")
if not f then
    log("failed to open output: " .. tostring(err))
    print("API export v2 failed to open " .. OUT .. ": " .. tostring(err))
    return
end

writeln(f, "Octane Lua API export v2")
writeln(f, os.date("!%Y-%m-%dT%H:%M:%SZ"))
writeln(f, "octane=" .. tostring(octane ~= nil))
writeln(f, "octane.help=" .. tostring(octane and octane.help ~= nil))
writeln(f, "")

if not octane or not octane.help then
    writeln(f, "octane.help is not available in this runtime")
    f:close()
    log("octane.help not available; wrote minimal " .. OUT)
    print("API export v2 wrote minimal file: " .. OUT)
    return
end

local ok_modules, modules = pcall(function() return octane.help.modules() end)
if not ok_modules then
    writeln(f, "octane.help.modules failed: " .. tostring(modules))
    f:close()
    log("modules failed: " .. tostring(modules))
    print("API export v2 modules failed: " .. tostring(modules))
    return
end

for moduleName, description in pairs(modules) do
    writeln(f, "MODULE " .. tostring(moduleName))
    writeln(f, tostring(description))
    writeln(f, "FUNCTIONS")
    local ok_funcs, funcs = pcall(function() return octane.help.functions(moduleName) end)
    if ok_funcs and funcs then
        for _, fn in ipairs(funcs) do
            local fullName = "octane." .. tostring(moduleName) .. "." .. tostring(fn)
            local ok_doc, doc = pcall(function() return octane.help.functionDoc(octane[moduleName][fn]) end)
            if ok_doc and doc then
                writeln(f, "  " .. fullName .. " :: " .. tostring(doc.description or ""))
            else
                writeln(f, "  " .. fullName)
            end
        end
    else
        writeln(f, "  <functions unavailable: " .. tostring(funcs) .. ">")
    end
    writeln(f, "PROPERTIES")
    local ok_props, props = pcall(function() return octane.help.properties(moduleName) end)
    if ok_props and props then
        for _, propName in ipairs(props) do
            writeln(f, "  " .. tostring(propName))
        end
    end
    writeln(f, "CONSTANTS")
    local ok_consts, constants = pcall(function() return octane.help.constants(moduleName) end)
    if ok_consts and constants then
        for _, constantName in ipairs(constants) do
            writeln(f, "  " .. tostring(constantName))
        end
    end
    writeln(f, "")
end

f:close()
log("api export v2 wrote " .. OUT)
print("API export v2 wrote " .. OUT)
