set_canvas(16, 16)
set_hotspot(0, 0)

fps = 15

-- 斜线
function draw_diagonal(start_x, start_y, steps, color, direction)
    local dir = direction or "down_right"
    for i = 0, steps - 1 do
        local x = start_x + i
        local y
        if dir == "down_right" then
            y = start_y + i
        elseif dir == "down_left" then
            y = start_y - i
        else
            y = start_y + i
        end
        draw_rect(x, y, 0, 0, color, 0)
    end
end

local function hex_to_rgb(hex)
    hex = hex:gsub("#", "")
    return {
        r = tonumber(hex:sub(1, 2), 16),
        g = tonumber(hex:sub(3, 4), 16),
        b = tonumber(hex:sub(5, 6), 16)
    }
end

local function clamp(val, min, max)
    return math.min(max, math.max(min, val))
end

local function hex_to_rgb(hex)
    hex = hex:gsub("#", "")
    return {
        r = tonumber(hex:sub(1, 2), 16) or 0,
        g = tonumber(hex:sub(3, 4), 16) or 0,
        b = tonumber(hex:sub(5, 6), 16) or 0
    }
end

local function rgb_to_hex(rgb)
    return string.format("#%02x%02x%02x",
        math.floor(clamp(rgb.r, 0, 255) + 0.5),
        math.floor(clamp(rgb.g, 0, 255) + 0.5),
        math.floor(clamp(rgb.b, 0, 255) + 0.5))
end

local function rgb_to_hsl(rgb)
    local r, g, b = rgb.r / 255, rgb.g / 255, rgb.b / 255
    local max, min = math.max(r, g, b), math.min(r, g, b)
    local h, s, l = 0, 0, (max + min) / 2

    if max ~= min then
        local d = max - min
        s = l > 0.5 and d / (2 - max - min) or d / (max + min)
        if max == r then
            h = (g - b) / d + (g < b and 6 or 0)
        elseif max == g then
            h = (b - r) / d + 2
        else
            h = (r - g) / d + 4
        end
        h = h * 60
    end
    return { h = h, s = s, l = l }
end

local function hsl_to_rgb(hsl)
    local h, s, l = hsl.h % 360, hsl.s, hsl.l
    local r, g, b

    if s == 0 then
        r, g, b = l, l, l
    else
        local function hue2rgb(p, q, t)
            if t < 0 then t = t + 1 end
            if t > 1 then t = t - 1 end
            if t < 1/6 then return p + (q - p) * 6 * t end
            if t < 1/2 then return q end
            if t < 2/3 then return p + (q - p) * (2/3 - t) * 6 end
            return p
        end
        local q = l < 0.5 and l * (1 + s) or l + s - l * s
        local p = 2 * l - q
        r = hue2rgb(p, q, h / 360 + 1/3)
        g = hue2rgb(p, q, h / 360)
        b = hue2rgb(p, q, h / 360 - 1/3)
    end
    return { r = r * 255, g = g * 255, b = b * 255 }
end

-- 主题色计算
local REF_BASE_HEX = "#33ebcb"
local REF_BASE_HSL = rgb_to_hsl(hex_to_rgb(REF_BASE_HEX))

local palette_map = {
    {"theme",       "#33ebcb"},
    {"theme_dim",   "#2bc7ac"},
    {"mid",         "#1e8a77"},
    {"shadow",      "#156355"},
    {"bg",          "#0e3f36"},
    {"bg_dark",     "#082520"},
}

local fixed_colors = {
    wood_light = "#896727",
    wood_mid   = "#684e1e",
    wood_dark  = "#493615",
    wood_deep  = "#281e0b"
}

function generate_palette(new_theme_hex)
    local new_base_rgb = hex_to_rgb(new_theme_hex)
    local new_base_hsl = rgb_to_hsl(new_base_rgb)
    
    local palette = {}
    for _, item in ipairs(palette_map) do
        local key = item[1]
        local original_hex = item[2]
        local orig_hsl = rgb_to_hsl(hex_to_rgb(original_hex))
        local dH = orig_hsl.h - REF_BASE_HSL.h
        local dS = orig_hsl.s - REF_BASE_HSL.s
        local dL = orig_hsl.l - REF_BASE_HSL.l
        local target_hsl = {
            h = new_base_hsl.h + dH,
            s = clamp(new_base_hsl.s + dS, 0, 1),
            l = clamp(new_base_hsl.l + dL, 0, 1)
        }
        palette[key] = rgb_to_hex(hsl_to_rgb(target_hsl))
    end
    for k, v in pairs(fixed_colors) do
        palette[k] = v
    end
    return palette
end

function Diamond_Sword(color)
    local c = generate_palette(color)
    draw_rect(0, 0, 1, 1, c.bg, 0)
    draw_rect(8, 8, 2, 2, c.bg_dark, 0)
    draw_diagonal(2, 0, 8, c.bg)
    draw_diagonal(0, 2, 8, c.bg)
    draw_diagonal(1, 2, 8, c.theme)
    draw_diagonal(2, 1, 8, c.theme)
    draw_diagonal(1, 1, 9, c.theme_dim)
    draw_rect(13, 13, 2, 2, c.bg_dark, 0)
    draw_rect(6, 12, 1, 1, c.bg_dark, 0)
    draw_rect(10, 10, 1, 1, c.bg_dark, 0)
    draw_rect(7, 11, 2, 1, c.bg_dark, 0)
    draw_rect(10, 10, 0, 0, c.mid, 0)
    draw_rect(12, 6, 1, 1, c.bg_dark, 0)
    draw_rect(11, 7, 1, 2, c.bg_dark, 0)
    draw_rect(9, 11, 0, 0, c.mid, 0)
    draw_rect(11, 8, 0, 1, c.mid, 0)
    draw_rect(12, 7, 0, 0, c.shadow, 0)
    draw_rect(8, 11, 0, 0, c.shadow, 0)
    draw_rect(7, 12, 0, 0, c.shadow, 0)
    draw_diagonal(11, 11, 3, c.wood_mid)
    draw_diagonal(12, 11, 2, c.wood_dark)
    draw_diagonal(11, 12, 2, c.wood_deep)
    draw_rect(12, 12, 0, 0, c.wood_light, 0)
    draw_rect(14, 14, 0, 0, c.mid, 0)
end


function on_render(frame)
    -- 获取主题色
    local color = get_win_theme_color_hex()
    
    if color ~= nil then
        if color == "#000000" or color == "#ffffff" then
            color = "#33ebcb"
        else
            local r = tonumber(string.sub(color, 2, 3), 16)
            local g = tonumber(string.sub(color, 4, 5), 16)
            local b = tonumber(string.sub(color, 6, 7), 16)
            local brightness = 0.299 * r + 0.587 * g + 0.114 * b
            
            -- 设定亮度阈值
            local low_threshold = 64
            local high_threshold = 2000
            
            -- 调整亮度
            if brightness < low_threshold then
                local increment = 30
                r = math.min(255, r + increment) 
                g = math.min(255, g + increment)
                b = math.min(255, b + increment)
            elseif brightness > high_threshold then
                local decrement = 30
                r = math.max(0, r - decrement)
                g = math.max(0, g - decrement)
                b = math.max(0, b - decrement)
            end
            color = string.format("#%02x%02x%02x", r, g, b)
        end
    else
        color = "#33ebcb"
    end
    
    Diamond_Sword(color)
end





