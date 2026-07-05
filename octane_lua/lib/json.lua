-- Minimal JSON decoder for Hermes Octane bridge command envelopes.
-- Public domain / CC0-style: small self-contained recursive descent parser.
-- It intentionally decodes only JSON (no Lua extensions) and has no runtime deps.

local json = {}
json.null = {}

local function decode_error(text, pos, message)
    local near = text:sub(pos, pos + 32):gsub("\n", "\\n")
    return nil, message .. " at byte " .. tostring(pos) .. " near '" .. near .. "'"
end

local function skip_ws(text, pos)
    while true do
        local c = text:sub(pos, pos)
        if c == " " or c == "\t" or c == "\r" or c == "\n" then
            pos = pos + 1
        else
            return pos
        end
    end
end

local parse_value

local function parse_string(text, pos)
    if text:sub(pos, pos) ~= '"' then return decode_error(text, pos, "expected string") end
    pos = pos + 1
    local out = {}
    while pos <= #text do
        local c = text:sub(pos, pos)
        if c == '"' then return table.concat(out), pos + 1 end
        if c == "\\" then
            local esc = text:sub(pos + 1, pos + 1)
            if esc == '"' or esc == "\\" or esc == "/" then
                table.insert(out, esc)
                pos = pos + 2
            elseif esc == "b" then
                table.insert(out, "\b")
                pos = pos + 2
            elseif esc == "f" then
                table.insert(out, "\f")
                pos = pos + 2
            elseif esc == "n" then
                table.insert(out, "\n")
                pos = pos + 2
            elseif esc == "r" then
                table.insert(out, "\r")
                pos = pos + 2
            elseif esc == "t" then
                table.insert(out, "\t")
                pos = pos + 2
            elseif esc == "u" then
                local hex = text:sub(pos + 2, pos + 5)
                if not hex:match("^%x%x%x%x$") then return decode_error(text, pos, "invalid unicode escape") end
                local code = tonumber(hex, 16)
                if code and code < 128 then
                    table.insert(out, string.char(code))
                else
                    table.insert(out, "?")
                end
                pos = pos + 6
            else
                return decode_error(text, pos, "invalid escape")
            end
        else
            table.insert(out, c)
            pos = pos + 1
        end
    end
    return decode_error(text, pos, "unterminated string")
end

local function parse_number(text, pos)
    local start = pos
    if text:sub(pos, pos) == "-" then pos = pos + 1 end
    if text:sub(pos, pos) == "0" then
        pos = pos + 1
    else
        if not text:sub(pos, pos):match("%d") then return decode_error(text, pos, "expected number") end
        while text:sub(pos, pos):match("%d") do pos = pos + 1 end
    end
    if text:sub(pos, pos) == "." then
        pos = pos + 1
        if not text:sub(pos, pos):match("%d") then return decode_error(text, pos, "invalid fraction") end
        while text:sub(pos, pos):match("%d") do pos = pos + 1 end
    end
    local e = text:sub(pos, pos)
    if e == "e" or e == "E" then
        pos = pos + 1
        local sign = text:sub(pos, pos)
        if sign == "+" or sign == "-" then pos = pos + 1 end
        if not text:sub(pos, pos):match("%d") then return decode_error(text, pos, "invalid exponent") end
        while text:sub(pos, pos):match("%d") do pos = pos + 1 end
    end
    return tonumber(text:sub(start, pos - 1)), pos
end

local function parse_array(text, pos)
    pos = skip_ws(text, pos + 1)
    local arr = {}
    if text:sub(pos, pos) == "]" then return arr, pos + 1 end
    while true do
        local value
        value, pos = parse_value(text, pos)
        if value == nil then return nil, pos end
        table.insert(arr, value)
        pos = skip_ws(text, pos)
        local c = text:sub(pos, pos)
        if c == "]" then return arr, pos + 1 end
        if c ~= "," then return decode_error(text, pos, "expected ',' or ']'") end
        pos = skip_ws(text, pos + 1)
    end
end

local function parse_object(text, pos)
    pos = skip_ws(text, pos + 1)
    local obj = {}
    if text:sub(pos, pos) == "}" then return obj, pos + 1 end
    while true do
        local key
        key, pos = parse_string(text, pos)
        if key == nil then return nil, pos end
        pos = skip_ws(text, pos)
        if text:sub(pos, pos) ~= ":" then return decode_error(text, pos, "expected ':'") end
        local value
        value, pos = parse_value(text, skip_ws(text, pos + 1))
        if value == nil then return nil, pos end
        if value ~= json.null then obj[key] = value end
        pos = skip_ws(text, pos)
        local c = text:sub(pos, pos)
        if c == "}" then return obj, pos + 1 end
        if c ~= "," then return decode_error(text, pos, "expected ',' or '}'") end
        pos = skip_ws(text, pos + 1)
    end
end

function parse_value(text, pos)
    pos = skip_ws(text, pos)
    local c = text:sub(pos, pos)
    if c == '"' then return parse_string(text, pos) end
    if c == "{" then return parse_object(text, pos) end
    if c == "[" then return parse_array(text, pos) end
    if c == "-" or c:match("%d") then return parse_number(text, pos) end
    if text:sub(pos, pos + 3) == "true" then return true, pos + 4 end
    if text:sub(pos, pos + 4) == "false" then return false, pos + 5 end
    if text:sub(pos, pos + 3) == "null" then return json.null, pos + 4 end
    return decode_error(text, pos, "unexpected token")
end

function json.decode(text)
    if type(text) ~= "string" then return nil, "expected JSON string" end
    local value, pos = parse_value(text, 1)
    if value == nil then return nil, pos end
    pos = skip_ws(text, pos)
    if pos <= #text then return decode_error(text, pos, "trailing data") end
    return value, nil
end

return json
