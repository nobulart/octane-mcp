-- Octane MCP render save docs probe v2. Run inside Octane X.
local ROOT = "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
local OUT = ROOT .. "/render_save_docs_probe_v2.txt"
local f = io.open(OUT, "w")
if not f then print("cannot open " .. OUT); return end
local function w(s) f:write(tostring(s or ""), "\n"); f:flush() end
local function ser(v, d)
    d = d or 0
    if d > 5 then return "<max-depth>" end
    if type(v) ~= "table" then return tostring(v) end
    local parts = {}
    for k, val in pairs(v) do table.insert(parts, tostring(k) .. "=" .. ser(val, d+1)) end
    table.sort(parts)
    return "{" .. table.concat(parts, ", ") .. "}"
end
w("render save docs probe " .. os.date("!%Y-%m-%dT%H:%M:%SZ"))
w("help=" .. tostring(octane and octane.help ~= nil))
local names = {
    "octane.render.saveImage",
    "octane.render.saveImage2",
    "octane.render.saveImage3",
    "octane.render.saveRenderPass",
    "octane.render.saveRenderPass2",
    "octane.render.saveRenderPass3",
    "octane.render.grabRenderResult",
    "octane.render.synchronousTonemap",
    "octane.render.synchronousTonemap2",
    "octane.render.synchronousTonemap3",
    "octane.render.preview",
    "octane.render.previewHdr",
    "octane.render.previewHdr2",
}
for _, name in ipairs(names) do
    w("--- " .. name .. " ---")
    if octane and octane.help then
        local ok, doc = pcall(function() return octane.help.functionDoc(name) end)
        w("ok=" .. tostring(ok))
        w(ser(doc))
    end
end
f:close()
print("render save docs probe wrote " .. OUT)
