-- Octane MCP render save probe v1. Run inside Octane X.
-- Dumps render.saveImage docs/constants and tries several save call signatures.

local ROOT = "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
local OUT = ROOT .. "/render_save_probe.txt"
local RENDERS = ROOT .. "/renders"
os.execute("mkdir -p '" .. RENDERS:gsub("'", "'\\''") .. "'")

local f = io.open(OUT, "w")
if not f then print("render save probe cannot open " .. OUT); return end
local function w(s) f:write(tostring(s or ""), "\n"); f:flush() end
local function ser(v, d)
    d = d or 0
    if d > 4 then return "<max-depth>" end
    if type(v) ~= "table" then return tostring(v) end
    local parts = {}
    for k, val in pairs(v) do table.insert(parts, tostring(k) .. "=" .. ser(val, d+1)) end
    table.sort(parts)
    return "{" .. table.concat(parts, ", ") .. "}"
end
local function exists(path)
    local fh = io.open(path, "rb")
    if fh then local n = fh:seek("end") or -1; fh:close(); return true, n end
    if octane and octane.file and octane.file.exists then
        local ok, yes = pcall(function() return octane.file.exists(path) end)
        if ok and yes then return true, -2 end
    end
    return false, -1
end
local function doc(name, fn)
    w("--- " .. name .. " ---")
    if octane and octane.help and fn then
        local ok, d = pcall(function() return octane.help.functionDoc(fn) end)
        w("doc_ok=" .. tostring(ok)); w(ser(d))
    else
        w("missing")
    end
end
w("render save probe " .. os.date("!%Y-%m-%dT%H:%M:%SZ"))
w("octane=" .. tostring(octane ~= nil) .. " render=" .. tostring(octane and octane.render ~= nil))
doc("render.saveImage", octane and octane.render and octane.render.saveImage)
doc("render.saveImage2", octane and octane.render and octane.render.saveImage2)
doc("render.saveImage3", octane and octane.render and octane.render.saveImage3)
w("octane.render.imageType=" .. ser(octane and octane.render and octane.render.imageType))
w("octane.imageType=" .. ser(octane and octane.imageType))
w("octane.imageSaveType=" .. ser(octane and octane.imageSaveType))
w("octane.imageSaveFormat=" .. ser(octane and octane.imageSaveFormat))
w("octane.render.imageSaveType=" .. ser(octane and octane.render and octane.render.imageSaveType))
w("octane.render.imageSaveFormat=" .. ser(octane and octane.render and octane.render.imageSaveFormat))

local constants = {}
local function add(label, value) if value ~= nil then table.insert(constants, {label, value}) end end
if octane then
    if octane.imageType then add("octane.imageType.PNG8", octane.imageType.PNG8); add("octane.imageType.PNG", octane.imageType.PNG) end
    if octane.imageSaveType then add("octane.imageSaveType.PNG8", octane.imageSaveType.PNG8); add("octane.imageSaveType.PNG", octane.imageSaveType.PNG) end
    if octane.imageSaveFormat then add("octane.imageSaveFormat.PNG8", octane.imageSaveFormat.PNG8); add("octane.imageSaveFormat.PNG", octane.imageSaveFormat.PNG) end
    if octane.render and octane.render.imageType then add("octane.render.imageType.PNG8", octane.render.imageType.PNG8); add("octane.render.imageType.PNG", octane.render.imageType.PNG) end
    if octane.render and octane.render.imageSaveType then add("octane.render.imageSaveType.PNG8", octane.render.imageSaveType.PNG8); add("octane.render.imageSaveType.PNG", octane.render.imageSaveType.PNG) end
    if octane.render and octane.render.imageSaveFormat then add("octane.render.imageSaveFormat.PNG8", octane.render.imageSaveFormat.PNG8); add("octane.render.imageSaveFormat.PNG", octane.render.imageSaveFormat.PNG) end
end
for _, c in ipairs(constants) do w("constant " .. c[1] .. "=" .. tostring(c[2])) end

local attempts = {}
local path_base = RENDERS .. "/probe_save"
for i, c in ipairs(constants) do
    local path = path_base .. "_" .. tostring(i) .. ".png"
    table.insert(attempts, {"saveImage " .. c[1], path, function() return octane.render.saveImage(path, c[2]) end})
    table.insert(attempts, {"saveImage2 " .. c[1], path:gsub("%.png$", "_2.png"), function() return octane.render.saveImage2(path:gsub("%.png$", "_2.png"), c[2]) end})
    table.insert(attempts, {"saveImage3 " .. c[1], path:gsub("%.png$", "_3.png"), function() return octane.render.saveImage3(path:gsub("%.png$", "_3.png"), c[2]) end})
end
if #attempts == 0 then
    for i, typ in ipairs({0,1,2,3,4,5,6,7,8,9,10}) do
        local path = path_base .. "_num" .. tostring(typ) .. ".png"
        table.insert(attempts, {"saveImage numeric " .. tostring(typ), path, function() return octane.render.saveImage(path, typ) end})
    end
end

for i, a in ipairs(attempts) do
    local label, path, fn = a[1], a[2], a[3]
    local ok, r1, r2, r3 = pcall(fn)
    local yes, size = exists(path)
    w("attempt " .. tostring(i) .. " " .. label .. " ok=" .. tostring(ok) .. " r1=" .. tostring(r1) .. " r2=" .. tostring(r2) .. " r3=" .. tostring(r3) .. " exists=" .. tostring(yes) .. " size=" .. tostring(size) .. " path=" .. path)
    if yes then break end
end
f:close()
print("render save probe wrote " .. OUT)
