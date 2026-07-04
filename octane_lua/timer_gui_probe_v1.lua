-- Octane MCP timer/gui API probe v1. Run inside Octane X.
local ROOT = "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
local OUT = ROOT .. "/timer_gui_probe.txt"
local f = io.open(OUT, "w")
if not f then print("timer probe cannot open " .. OUT); return end
local function w(s) f:write(tostring(s or ""), "\n") end
local function ser(v, d)
    d = d or 0
    if d > 4 then return "<max-depth>" end
    if type(v) ~= "table" then return tostring(v) end
    local parts = {}
    for k, val in pairs(v) do table.insert(parts, tostring(k) .. "=" .. ser(val, d+1)) end
    table.sort(parts)
    return "{" .. table.concat(parts, ", ") .. "}"
end
w("timer/gui probe " .. os.date("!%Y-%m-%dT%H:%M:%SZ"))
w("octane=" .. tostring(octane ~= nil) .. " timer=" .. tostring(octane and octane.timer ~= nil) .. " gui=" .. tostring(octane and octane.gui ~= nil))
local funcs = {
    {"timer.create", octane and octane.timer and octane.timer.create},
    {"timer.start", octane and octane.timer and octane.timer.start},
    {"timer.stop", octane and octane.timer and octane.timer.stop},
    {"gui.create", octane and octane.gui and octane.gui.create},
    {"gui.createWindow", octane and octane.gui and octane.gui.createWindow},
    {"gui.showWindow", octane and octane.gui and octane.gui.showWindow},
    {"gui.dispatchGuiEvents", octane and octane.gui and octane.gui.dispatchGuiEvents},
}
for _, pair in ipairs(funcs) do
    local name, fn = pair[1], pair[2]
    w("--- " .. name .. " ---")
    if octane and octane.help and fn then
        local ok, doc = pcall(function() return octane.help.functionDoc(fn) end)
        w("doc_ok=" .. tostring(ok))
        w(ser(doc))
    else
        w("missing")
    end
end
f:close()
print("timer/gui probe wrote " .. OUT)
