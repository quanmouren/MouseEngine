set_canvas(64, 64)
set_hotspot(20, 1)

fps = 15


load_png("1", "image\\aero_arrow.png")
load_png("2", "image\\aero_arrow.png")

function on_render(frame)
    
    local pulse = math.sin(frame / fps * 2 * math.pi) 
    local y_offset = pulse * 10   
    add_image("2", 0+6, y_offset)
    

    add_image("1", 0, 0)
    draw_rect(100, 100, 50, 50, "#FF5500", 25)
    
end

