-- Cur2D 编辑器 Lua API 定义

--- 设置画布尺寸，创建透明 RGBA 画布
---@param w number 画布宽度（整数）
---@param h number 画布高度（整数）
---@return nil 无返回值
function set_canvas(w, h) end

--- 加载 PNG 图片资源到编辑器
---@param name string 资源名称（唯一标识）
---@param relative_path string 图片相对路径（相对于项目根目录）
---@return boolean 加载成功返回 true，失败返回 false
function load_png(name, relative_path) end

--- 在画布上绘制已加载的图片
---@param name string 已加载的资源名称
---@param x number 绘制的 X 坐标（整数）
---@param y number 绘制的 Y 坐标（整数）
---@return nil 无返回值
function add_image(name, x, y) end

--- 设置全局热点位置
---@param x number 热点 X 坐标（整数）
---@param y number 热点 Y 坐标（整数）
---@return nil 无返回值
function set_hotspot(x, y) end

--- 绘制矩形/圆角矩形
---@param x number 矩形左上角 X 坐标
---@param y number 矩形左上角 Y 坐标
---@param w number 矩形宽度
---@param h number 矩形高度
---@param color string 填充颜色（十六进制 RGB 格式）
---@param radius number 圆角半径（默认 0）
---@return nil 无返回值
function draw_rect(x, y, w, h, color, radius) end

--- 帧率控制
--- 控制编辑器预览时的刷新速度，值越高预览越流畅，但可能增加 CPU 占用
---@type number 
fps = 15

--- 总帧数
---@type number
---@deprecated
total_frames = 0

--- 渲染回调函数（编辑器每帧调用）
--- 需在 Lua 代码中自定义实现
---@param current_frame number 当前渲染的帧数
---@return nil 无返回值
function on_render(current_frame) end

--- 获取 Windows 主题颜色的十六进制值
---@return string 主题颜色的十六进制值
function get_win_theme_color_hex() end