-- Render target check: inspect RT node directly and save results
local ROOT = "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
local OUT = ROOT .. "/render_target_inspect_v2.txt"

local f = io.open(OUT, "w")

f:write("=== Render Target Inspection ===\n\n")

local rt_found = nil

for i = 1, 999 do
    local n = octane.nodegraph.getNodeByIndex(i)
    if not n then break end
    local tname = tostring(n:GetType())
    if string.find(tname or "", "RENDERTARGET", 1, true) then
        rt_found = n
        f:write(string.format("Found render target node:\n"))
        f:write(string.format("  type: %s\n", n:GetType()))
        f:write(string.format("  name: %s\n", n:getName() or "(no name)"))
        
        -- List pins using correct uppercase
        local pc = n:getPinCount()
        f:write(string.format("  pin count: %d\n", pc))
        for j=1,pc do
            local pinfo = n:GetPinInfo(j)
            if pinfo then
                local pin_name = pinfo[3] or "(no name)"
                f:write(string.format("    pin %d kind: %s name: %s\n", j, tostring(pinfo[2]), pin_name))
            end
        end
        break
    end
end

if not rt_found then
    f:write("No render target found in scene\n")
else
    -- Try to activate it
    local ok = octane.project.select({rt_found})
    f:write(string.format("\nSelect OK: %s\n", ok and "true" or "false"))
    
    -- Check if active
    local active = octane.project.getActiveNode()
    f:write(string.format("Active node type: %s\n", active and active:GetType() or "nil"))
end

f:close()
print("Output saved to "..OUT)