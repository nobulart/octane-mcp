-- @script-id saturn_scene_v2
-- @description Saturn with banded atmosphere, rings, moons, and starfield
-- @author Hermes Agent

local function build_saturn_scene()
    -- ======= STAGE 1 - HELPERS =======
    
    local function create_node(node_type, name)
        return octane.node.create { type = node_type, name = name }
    end
    
    local function set_pin(node, pin_label, ...)
        local args = { ... }
        if #args == 0 then return end
        
        local pin_id = nil
        for i = 1, 200 do
            local ok, pin_type = pcall(function() return octane.apiinfo.getPinIdName(pin_id) end)
            -- Try common pin name to id mappings
            local id_map = {
                ["value"] = octane.apiinfo.getAttributeId("value"),
                ["r"] = octane.apiinfo.getAttributeId("r"),
                ["g"] = octane.apiinfo.getAttributeId("g"),
                ["b"] = octane.apiinfo.getAttributeId("b"),
                ["rgb"] = octane.apiinfo.getAttributeId("rgb"),
                ["x"] = octane.apiinfo.getAttributeId("x"),
                ["y"] = octane.apiinfo.getAttributeId("y"),
                ["z"] = octane.apiinfo.getAttributeId("z"),
                ["input"] = octane.apiinfo.getAttributeId("input"),
                ["output"] = octane.apiinfo.getAttributeId("output"),
                ["scale"] = octane.apiinfo.getAttributeId("scale"),
                ["factor"] = octane.apiinfo.getAttributeId("factor"),
                ["color1"] = octane.apiinfo.getAttributeId("color1"),
                ["color2"] = octane.apiinfo.getAttributeId("color2"),
                ["min"] = octane.apiinfo.getAttributeId("min"),
                ["max"] = octane.apiinfo.getAttributeId("max"),
                ["threshold"] = octane.apiinfo.getAttributeId("threshold"),
                ["position"] = octane.apiinfo.getAttributeId("position"),
                ["target"] = octane.apiinfo.getAttributeId("target"),
                ["up"] = octane.apiinfo.getAttributeId("up"),
                ["fov"] = octane.apiinfo.getAttributeId("fov"),
                ["type"] = octane.apiinfo.getAttributeId("type"),
                ["seed"] = octane.apiinfo.getAttributeId("seed"),
                ["octaves"] = octane.apiinfo.getAttributeId("octaves"),
                ["lacunarity"] = octane.apiinfo.getAttributeId("lacunarity"),
                ["gain"] = octane.apiinfo.getAttributeId("gain"),
                ["offset"] = octane.apiinfo.getAttributeId("offset"),
                ["frequency"] = octane.apiinfo.getAttributeId("frequency"),
                ["strength"] = octane.apiinfo.getAttributeId("strength"),
                ["diffuse"] = octane.apiinfo.getAttributeId("diffuse"),
                ["specular"] = octane.apiinfo.getAttributeId("specular"),
                ["smooth"] = octane.apiinfo.getAttributeId("smooth"),
                ["ior"] = octane.apiinfo.getAttributeId("ior"),
                ["roughness"] = octane.apiinfo.getAttributeId("roughness"),
                ["opacity"] = octane.apiinfo.getAttributeId("opacity"),
                ["bump"] = octane.apiinfo.getAttributeId("bump"),
                ["texture"] = octane.apiinfo.getAttributeId("texture"),
                ["normal"] = octane.apiinfo.getAttributeId("normal"),
            }
            for k, v in pairs(id_map) do
                if k == pin_label then
                    pin_id = v
                    break
                end
            end
            if pin_id ~= nil then break end
        end
        
        if pin_id then
            node:setAttribute(pin_id, ...)
        end
    end
    
    local function connect_nodes(from_node, from_pin, to_node, to_pin)
        from_node:connectTo(from_pin, to_node, to_pin)
    end

    -- ======= STAGE 2 - CREATE GEOMETRY =======
    
    -- Saturn body (sphere)
    local saturn_sphere = create_node(octane.geometrySphereNode, "Saturn Body")
    set_pin(saturn_sphere, "radius", 2.0)
    set_pin(saturn_sphere, "segs_u", 128)
    set_pin(saturn_sphere, "segs_v", 64)

    -- Saturn rings (torus)
    local saturn_rings = create_node(octane.geometryTorusNode, "Saturn Rings")
    set_pin(saturn_rings, "radius", 4.0)
    set_pin(saturn_rings, "tube", 0.05)
    set_pin(saturn_rings, "rings", 4)
    set_pin(saturn_rings, "segs_u", 256)
    set_pin(saturn_rings, "segs_v", 32)
    set_pin(saturn_rings, "start_angle", 0)
    set_pin(saturn_rings, "end_angle", 360)
    
    -- Inner and outer radius for a realistic ring
    set_pin(saturn_rings, "innerRadius", 2.5)
    set_pin(saturn_rings, "outerRadius", 5.5)

    -- Enceladus (bright icy moon)
    local enceladus = create_node(octane.geometrySphereNode, "Enceladus")
    set_pin(enceladus, "radius", 0.15)
    set_pin(enceladus, "segs_u", 32)
    set_pin(enceladus, "segs_v", 16)

    -- Titan (larger moon, amber world)
    local titan = create_node(octane.geometrySphereNode, "Titan")
    set_pin(titan, "radius", 0.4)
    set_pin(titan, "segs_u", 32)
    set_pin(titan, "segs_v", 16)

    -- Mimas (tiny moon, cratered appearance)
    local mimas = create_node(octane.geometrySphereNode, "Mimas")
    set_pin(mimas, "radius", 0.08)
    set_pin(mimas, "segs_u", 32)
    set_pin(mimas, "segs_v", 16)

    -- Background sphere for starfield
    local bg_sphere = create_node(octane.geometrySphereNode, "Starfield BG")
    set_pin(bg_sphere, "radius", 100.0)
    set_pin(bg_sphere, "segs_u", 128)
    set_pin(bg_sphere, "segs_v", 64)
    
    -- Invert normals for inside rendering - use a plane instead
    local bg_plane = create_node(octane.geometryPlaneNode, "Starfield Background")
    set_pin(bg_plane, "width", 200.0)
    set_pin(bg_plane, "height", 200.0)

    -- ======= STAGE 3 - STARFIELD ENVIRONMENT =======
    
    -- Create procedural starfield noise
    local star_noise = create_node(octane.texGradientNode, "Star Noise")
    set_pin(star_noise, "type", 6) -- Vector to RGB Mode gradient
    set_pin(star_noise, "gradientType", 5) -- RGB Mode - produces noise-like output
    
    local star_threshold = create_node(octane.mathNode, "Star Threshold")
    set_pin(star_threshold, "type", 12) -- Step function
    
    local star_color = create_node(octane.mathNode, "Star Brightness")
    set_pin(star_color, "type", 7) -- Max
    
    -- Another noise pass for star color variation
    local star_color_noise = create_node(octane.texGradientNode, "Star Color Noise")
    set_pin(star_color_noise, "type", 6)
    set_pin(star_color_noise, "gradientType", 5)
    
    -- RGB Curves for star color mapping
    local star_rgb = create_node(octane.texRGBCurvesNode, "Star Color Map")
    
    -- Mix star colors based on noise
    local star_mix = create_node(octane.texMixRGBNode, "Star Color Mix")
    
    -- Stars on/off mask
    local stars_onoff = create_node(octane.texRGBCurvesNode, "Stars On/Off")
    
    -- Black background color
    local star_bg_color = create_node(octane.texRGBNode, "Space Black")
    set_pin(star_bg_color, "value", 0.0, 0.0, 0.0)
    
    -- Final starfield via mix
    local starfield_final = create_node(octane.texMixRGBNode, "Starfield Final")
    set_pin(starfield_final, "fac", 1.0) -- Full starfield

    -- ======= STAGE 4 - SATURN BANDED MATERIAL =======
    
    -- Latitude noise for banding
    local saturn_bands = create_node(octane.texGradientNode, "Saturn Latitude Noise")
    set_pin(saturn_bands, "type", 3) -- Vector to RGB Mode
    set_pin(saturn_bands, "gradientType", 6) -- Spherical - gives latitude-based bands
    
    -- Warp noise for organic band movement
    local saturn_noise_detail = create_node(octane.texGradientNode, "Saturn Noise Detail")
    set_pin(saturn_noise_detail, "type", 6)
    set_pin(saturn_noise_detail, "gradientType", 5)
    
    -- Combine - use the spherical gradient as the main banding
    -- Apply an RGB curves to sharpen the bands
    local band_sharpen = create_node(octane.texRGBCurvesNode, "Band Sharpen")
    
    -- Create Saturn band colors
    local band_dark = create_node(octane.texRGBNode, "Band Dark")
    set_pin(band_dark, "value", 0.55, 0.40, 0.25) -- Dark brown
    
    local band_mid = create_node(octane.texRGBNode, "Band Mid")
    set_pin(band_mid, "value", 0.78, 0.62, 0.38) -- Tan
    
    local band_light = create_node(octane.texRGBNode, "Band Light")
    set_pin(band_light, "value", 0.88, 0.78, 0.58) -- Pale gold
    
    local band_lighter = create_node(octane.texRGBNode, "Band Lighter")
    set_pin(band_lighter, "value", 0.92, 0.85, 0.68) -- Light warm

    -- Mix 1: Dark + Mid
    local mix1 = create_node(octane.texMixRGBNode, "Saturn Mix 1")
    
    -- Mix 2: Result + Light
    local mix2 = create_node(octane.texMixRGBNode, "Saturn Mix 2")
    
    -- Mix 3: Result + Lighter  
    local mix3 = create_node(octane.texMixRGBNode, "Saturn Mix 3")

    -- Saturn final color output
    local saturn_color = create_node(octane.texRGBNode, "Saturn Color")
    set_pin(saturn_color, "value", 0.75, 0.60, 0.35)

    -- Saturn glossy material
    local saturn_mat = create_node(octane.matGlossyNode, "Saturn Planet Material")
    set_pin(saturn_mat, "smooth", true)
    set_pin(saturn_mat, "diffuse", 0.0, 0.0, 0.0) -- Will connect noise
    set_pin(saturn_mat, "roughness", 0.5)
    set_pin(saturn_mat, "ior", 1.4)

    -- ======= STAGE 5 - RING MATERIAL =======
    
    -- Noise for ring banding
    local ring_noise = create_node(octane.texGradientNode, "Ring Band Noise")
    set_pin(ring_noise, "type", 3)
    set_pin(ring_noise, "gradientType", 5) -- White Noise
    
    local ring_sharp = create_node(octane.texRGBCurvesNode, "Ring Band Sharp")
    
    -- Ring color palette
    local ring_light = create_node(octane.texRGBNode, "Ring Light")
    set_pin(ring_light, "value", 0.82, 0.76, 0.62) -- Light tan
    
    local ring_mid_color = create_node(octane.texRGBNode, "Ring Mid Color")
    set_pin(ring_mid_color, "value", 0.68, 0.60, 0.45) -- Medium brown
    
    local ring_dark = create_node(octane.texRGBNode, "Ring Dark")
    set_pin(ring_dark, "value", 0.45, 0.38, 0.28) -- Dark brown
    
    local ring_mix_1 = create_node(octane.texMixRGBNode, "Ring Mix 1")
    local ring_mix_2 = create_node(octane.texMixRGBNode, "Ring Mix 2")
    
    -- Ring transparency (Cassini division etc)
    local ring_opacity = create_node(octane.texRGBNode, "Ring Opacity Map")
    set_pin(ring_opacity, "value", 0.7, 0.7, 0.7)
    
    local ring_opacity_noise = create_node(octane.texGradientNode, "Ring Gap Noise")
    set_pin(ring_opacity_noise, "type", 3)
    set_pin(ring_opacity_noise, "gradientType", 5)
    
    -- Ring glossy material
    local ring_mat = create_node(octane.matGlossyNode, "Saturn Rings Material")
    set_pin(ring_mat, "diffuse", 0.0, 0.0, 0.0)
    set_pin(ring_mat, "roughness", 0.7)
    set_pin(ring_mat, "ior", 1.3)
    set_pin(ring_mat, "opacity", 1.0)

    -- ======= STAGE 6 - MOON MATERIALS =======
    
    -- Enceladus - bright icy material
    local enceladus_mat = create_node(octane.matGlossyNode, "Enceladus Material")
    set_pin(enceladus_mat, "diffuse", 0.95, 0.93, 0.95)
    set_pin(enceladus_mat, "roughness", 0.2)
    set_pin(enceladus_mat, "smooth", true)
    
    -- Titan - warm amber
    local titan_mat = create_node(octane.matGlossyNode, "Titan Material")
    set_pin(titan_mat, "diffuse", 0.70, 0.52, 0.30)
    set_pin(titan_mat, "roughness", 0.5)
    
    -- Mimas - icy gray
    local mimas_mat = create_node(octane.matGlossyNode, "Mimas Material")
    set_pin(mimas_mat, "diffuse", 0.80, 0.78, 0.75)
    set_pin(mimas_mat, "roughness", 0.4)

    -- ======= STAGE 7 - CONNECT NODES =======
    
    -- === Saturn body material connections ===
    -- Use the spherical gradient for latitude banding
    -- Mix: fac = band_sharpen, color1 = mid, color2 = dark
    connect_nodes(band_sharpen, "output", mix1, "fac")
    connect_nodes(band_mid, "value", mix1, "color1")
    connect_nodes(band_dark, "value", mix1, "color2")
    
    -- Mix: fac = band_sharpen, color1 = light, color2 = mix1
    connect_nodes(band_sharpen, "output", mix2, "fac")
    connect_nodes(band_light, "value", mix2, "color1")
    connect_nodes(band_sharpen, "output", mix2, "color2")
    -- Actually let's mix differently - use multiple thresholds
    
    -- Alternative approach: use the spherical gradient (latitude) to blend bands
    connect_nodes(saturn_bands, "output", mix1, "fac")
    connect_nodes(band_mid, "value", mix1, "color1")
    connect_nodes(band_dark, "value", mix1, "color2")
    
    connect_nodes(saturn_bands, "output", mix2, "fac")
    connect_nodes(band_light, "value", mix2, "color1")
    connect_nodes(band_mid, "value", mix2, "color2")
    
    connect_nodes(saturn_bands, "output", mix3, "fac")
    connect_nodes(band_light, "value", mix3, "color1")
    connect_nodes(band_lighter, "value", mix3, "color2")
    
    -- Connect Saturn material diffuse to the banding output
    -- (simplified - connect mix1 to diffuse)
    connect_nodes(mix1, "output", saturn_mat, "diffuse")

    -- === Ring material connections ===
    connect_nodes(ring_noise, "output", ring_mix_1, "fac")
    connect_nodes(ring_light, "value", ring_mix_1, "color1")
    connect_nodes(ring_mid_color, "value", ring_mix_1, "color2")
    
    connect_nodes(ring_sharp, "output", ring_mat, "diffuse")
    
    -- Use ring_mix for diffuse instead
    connect_nodes(ring_mix_1, "output", ring_mat, "diffuse")

    -- Assign materials to geometry
    connect_nodes(saturn_mat, "default", saturn_sphere, "default")
    connect_nodes(ring_mat, "default", saturn_rings, "default")
    connect_nodes(enceladus_mat, "default", enceladus, "default")
    connect_nodes(titan_mat, "default", titan, "default")
    connect_nodes(mimas_mat, "default", mimas, "default")

    -- === Starfield connections ===
    connect_nodes(star_rgb, "output", star_bg_color, "value")
    
    -- Mix stars with black background
    connect_nodes(star_threshold, "output", starfield_final, "fac")
    connect_nodes(star_color_noise, "output", starfield_final, "color1")
    connect_nodes(star_bg_color, "value", starfield_final, "color2")

    -- === Environment setup ===
    -- Use a large background node for the starfield in the environment
    local env_bg = create_node(octane.envDaylightNode, "Saturn Environment")
    set_pin(env_bg, "sky_color", 0.0, 0.0, 0.0) -- Black sky
    set_pin(env_bg, "groundColor", 0.0, 0.0, 0.0) -- Black ground
    set_pin(env_bg, "power", 0.5)
    set_pin(env_bg, "model", 3) -- Hosek-Wilkie
    
    -- We'll use the starfield_final as the background texture
    -- (In Octane X, we connect to the environment's texture slot)

    -- ======= STAGE 8 - CAMERA =======
    
    local camera = create_node(octane.camThinLensNode, "Saturn Camera")
    connect_nodes(camera, "camera", render_target, "camera")
    set_pin(camera, "pos", 6.0, 3.0, 8.0) -- Camera position
    set_pin(camera, "target", 0.0, 0.0, 0.0) -- Look at center

    -- Enable depth of field
    local dof_settings = create_node(octane.dofSettingsNode, "Camera DOF")
    set_pin(dof_settings, "focusDistance", 10.0)
    set_pin(dof_settings, "fNumber", 2.8)
    set_pin(dof_settings, "blurShape", 1) -- Circle
    
    -- ======= STAGE 9 - RENDER TARGET =======
    
    local render_target = create_node(octane.renderTargetNode, "Saturn Render Target")

    -- ======= STAGE 10 - DIRECT LIGHTING KERNEL =======
    
    local kernel = create_node(octane.kernDirectLightingNode, "Direct Lighting Kernel")

    -- ======= STAGE 11 - FILM SETTINGS =======
    
    local film_settings = create_node(octane.filmSettingsNode, "Film Settings")

    -- ======= STAGE 12 - CONNECT RENDER TARGET =======
    
    connect_nodes(camera, "camera", render_target, "camera")
    connect_nodes(film_settings, "filmSettings", render_target, "filmSettings")
    connect_nodes(kernel, "kernel", render_target, "kernel")

    -- ======= STAGE 13 - RENDER START =======
    
    octane.render.start()

    local function onShutdown(graph)
    end
    
    return { scene = "Saturn", elements = { "Saturn Body", "Saturn Rings", "Enceladus", "Titan", "Mimas" } }
end

-- Execute
build_saturn_scene()
