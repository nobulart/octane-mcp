-- Inline JSON decoder (extracted from hermes_bridge_oneshot_v2.lua)
local JSON = {}
JSON._null = {}

local function jerr(t, p, m)
    return nil, m .. " at byte " .. p
end

local function skip_ws(t, p)
    while true do
        local c = t:sub(p, p)
        if c == " " or c == "\t" or c == "\r" or c == "\n" then
            p = p + 1
        else
            return p
        end
    end
end

local _parse

local function parse_string(t, p)
    if t:sub(p, p) ~= '"' then
        return jerr(t, p, "expected string")
    end
    p = p + 1
    local o = {}
    while p <= #t do
        local c = t:sub(p, p)
        if c == '"' then
            return table.concat(o), p + 1
        end
        if c == '\\' then
            local e = t:sub(p + 1, p + 1)
            if e == '"' or e == '\\' or e == '/' then
                table.insert(o, e)
                p = p + 2
            elseif e == 'n' then
                table.insert(o, '\n')
                p = p + 2
            elseif e == 't' then
                table.insert(o, '\t')
                p = p + 2
            elseif e == 'u' then
                local hex = t:sub(p + 2, p + 5)
                if not hex:match('^...$') then
                    return jerr(t, p, 'invalid unicode')
                end
                -- Skip full unicode decode; use basic char for now
                table.insert(o, '?')
                p = p + 6
            else
                table.insert(o, e)
                p = p + 2
            end
        else
            table.insert(o, c)
            p = p + 1
        end
    end
    return jerr(t, p, 'unterminated string')
end

local function parse_number(t, p)
    local s = p
    if t:sub(p, p) == '-' then
        p = p + 1
    end
    while t:sub(p, p):match('%d') do
        p = p + 1
    end
    if t:sub(p, p) == '.' then
        p = p + 1
        while t:sub(p, p):match('%d') do
            p = p + 1
        end
    end
    return tonumber(t:sub(s, p - 1)), p
end

local function parse_array(t, p)
    p = skip_ws(t, p + 1)
    local a = {}
    if t:sub(p, p) == ']' then
        return a, p + 1
    end
    while true do
        local v, p2 = _parse(t, p)
        if v == nil then
            return nil, p2
        end
        table.insert(a, v)
        p = skip_ws(t, p2)
        if t:sub(p, p) == ']' then
            return a, p + 1
        end
        if t:sub(p, p) ~= ',' then
            return jerr(t, p, ', or ]')
        end
        p = skip_ws(t, p + 1)
    end
end

local function parse_object(t, p)
    p = skip_ws(t, p + 1)
    local o = {}
    if t:sub(p, p) == '}' then
        return o, p + 1
    end
    while true do
        local k, kp = parse_string(t, p)
        p = skip_ws(t, kp)
        if t:sub(p, p) ~= ':' then
            return jerr(t, p, ':')
        end
        local v, vp = _parse(t, skip_ws(t, p + 1))
        p = skip_ws(t, vp)
        if v == JSON._null then
            -- skip null
        else
            o[k] = v
        end
        p = skip_ws(t, p)
        if t:sub(p, p) == '}' then
            return o, p + 1
        end
        if t:sub(p, p) ~= ',' then
            return jerr(t, p, ', or }')
        end
        p = skip_ws(t, p + 1)
    end
end

function _parse(t, p)
    p = skip_ws(t, p)
    local c = t:sub(p, p)
    if c == '"' then
        return parse_string(t, p)
    end
    if c == '{' then
        return parse_object(t, p)
    end
    if c == '[' then
        return parse_array(t, p)
    end
    if c == '-' or c:match('%d') then
        return parse_number(t, p)
    end
    local tw = t:sub(p, p + (p + 3 <= #t and 3 or #t - p))
    if tw == 'true' then
        return true, p + 4
    end
    local fw = t:sub(p, p + (p + 4 <= #t and 4 or #t - p))
    if fw == 'false' then
        return false, p + 5
    end
    local nw = t:sub(p, p + (p + 3 <= #t and 3 or #t - p))
    if nw == 'null' then
        return JSON._null, p + 4
    end
    return jerr(t, p, 'unexpected character')
end

function JSON.decode(text)
    if type(text) ~= 'string' then
        return nil, 'expected string'
    end
    local v, p = _parse(text, 1)
    if v == nil then
        return nil, p
    end
    p = skip_ws(text, p)
    if p <= #text then
        return jerr(text, p, 'trailing characters')
    end
    return v, nil
end

-- === TESTS ===
local pass = 0
local fail = 0

local function check_table(name, key, payload, expects)
    local parsed, err = JSON.decode(payload)
    if not parsed then
        print('FAIL: ' .. name .. ' - decode error: ' .. tostring(err))
        fail = fail + 1
        return
    end
    local t = parsed
    if key then
        t = parsed[key]
    end
    if type(t) ~= 'table' then
        print('FAIL: ' .. name .. ' - expected table, got ' .. type(t))
        fail = fail + 1
        return
    end
    for ek, ev in pairs(expects) do
        local actual = t[ek]
        if type(ev) == 'number' then
            if type(actual) == 'number' and math.abs(actual - ev) < 0.001 then
                print('PASS: ' .. name .. ' - ' .. ek .. '=' .. string.format('%.4g', ev))
                pass = pass + 1
            else
                print('FAIL: ' .. name .. ' - ' .. ek .. ' expected=' .. tostring(ev) .. ' got=' .. tostring(actual))
                fail = fail + 1
            end
        elseif actual ~= ev then
            print('FAIL: ' .. name .. ' - ' .. ek .. ' expected=' .. tostring(ev) .. ' got=' .. tostring(actual))
            fail = fail + 1
        else
            print('PASS: ' .. name .. ' - ' .. ek .. '=' .. tostring(ev))
            pass = pass + 1
        end
    end
end

-- Test 1: import_geometry
check_table('import_geometry', nil,
    '{"path":"scene.obj","format":"obj","name":"earth","samples":768}',
    {path='scene.obj', format='obj', name='earth', samples=768})

-- Test 2: set_camera
check_table('set_camera', nil,
    '{"position":[0.15,-3.15,1.05],"target":[0,0,0.05],"fov":34}',
    {fov=34})
-- Check arrays
local cam, _ = JSON.decode('{"position":[0.15,-3.15,1.05],"target":[0,0,0.05],"fov":34}')
if cam.position and cam.position[1] == 0.15 and cam.position[3] == 1.05 then
    print('PASS: set_camera - position array')
    pass = pass + 1
else
    print('FAIL: set_camera - position array')
    fail = fail + 1
end

-- Test 3: set_lighting
check_table('set_lighting', nil,
    '{"preset":"space_sun"}',
    {preset='space_sun'})

-- Test 4: create_material (key test for roughness/metallic)
check_table('create_material', nil,
    '{"name":"mat_land","color":[0.17,0.36,0.14],"roughness":0.58,"metallic":0.0}',
    {name='mat_land', roughness=0.58, metallic=0.0})

-- Test 5: start_render
check_table('start_render', nil,
    '{"samples":768,"width":1280,"height":720}',
    {samples=768, width=1280, height=720})

-- Test 6: save_preview
check_table('save_preview', nil,
    '{"path":"output/preview.png","width":1280}',
    {path='output/preview.png', width=1280})

-- Test 7: nested payload (parse_command style)
local raw = '{"op":"create_material","payload":{"name":"x","roughness":0.3,"metallic":0.0}}'
local cmd, err = JSON.decode(raw)
if cmd and cmd.payload and cmd.payload.roughness == 0.3 and cmd.payload.metallic == 0.0 then
    print('PASS: nested payload fields accessible')
    pass = pass + 1
else
    print('FAIL: nested payload fields - roughness=' .. tostring(cmd and cmd.payload and cmd.payload.roughness))
    fail = fail + 1
end

-- Test 8: null handling
check_table('null_field', nil,
    '{"name":"test","color":null}',
    {name='test'})

-- Test 9: escape sequences
local esc, _ = JSON.decode('{"text":"hello\\nworld\\ttab"}')
if esc and esc.text == 'hello\nworld\ttab' then
    print('PASS: escape sequences')
    pass = pass + 1
else
    print('FAIL: escape sequences - got "' .. tostring(esc and esc.text) .. '"')
    fail = fail + 1
end

-- Summary
print(('\nResults: %d passed, %d failed, %d total'):format(pass, fail, pass + fail))
os.exit(fail > 0 and 1 or 0)
