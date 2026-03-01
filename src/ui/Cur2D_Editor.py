# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: CC BY-NC-SA 4.0
import os
import time
import sys
import psutil
import tkinter as tk
from tkinter import font, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw
from lupa import LuaRuntime
import tomllib
from tkinterdnd2 import TkinterDnD
import winreg
import subprocess
import sys
import os

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from ui.widgets.lua_editor import LuaCodeEditor
    from ui.widgets.file_manager import ProjectResourceBrowser, LogPanel
except ImportError:
    try:
        from widgets.lua_editor import LuaCodeEditor
        from widgets.file_manager import ProjectResourceBrowser, LogPanel
    except ImportError:
        raise

if sys.platform == "win32":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

def get_win_theme_color_hex():
    """返回Windows主题色的十六进制"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM")
        accent_color = winreg.QueryValueEx(key, "AccentColor")[0]
        winreg.CloseKey(key)
        r, g, b = accent_color & 0xFF, (accent_color >> 8) & 0xFF, (accent_color >> 16) & 0xFF
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        return hex_color if hex_color not in ["#000000", "#ffffff"] else None
    except:
        return None

class RenderEngine:
    def __init__(self):
        self.canvas = None
        self.assets = {}
        self.bg_pattern = None
        self.global_hotspot = [0, 0]
        self.show_debug_lines = True
        self.project_root = ""
        self.is_preview_mode = False
        self.preview_image = None

    def set_canvas(self, w, h):
        self.canvas = Image.new('RGBA', (int(w), int(h)), (0, 0, 0, 0))
        self.bg_pattern = self.create_chessboard((int(w), int(h)))

    def create_chessboard(self, size, tile_size=8):
        img = Image.new('RGB', size, color='#ffffff')
        pixels = img.load()
        for i in range(0, size[0], tile_size):
            for j in range(0, size[1], tile_size):
                if (i // tile_size + j // tile_size) % 2 == 0:
                    for x in range(i, min(i + tile_size, size[0])):
                        for y in range(j, min(j + tile_size, size[1])):
                            pixels[x, y] = (220, 220, 220)
        return img

    def load_png(self, name, relative_path):
        full_path = os.path.join(self.project_root, relative_path.replace("\\", "/"))
        if os.path.exists(full_path):
            try:
                self.assets[name] = Image.open(full_path).convert("RGBA")
                return True
            except: return False
        return False

    def set_hotspot(self, x, y):
        self.global_hotspot = [int(x), int(y)]

    def add_image(self, name, x, y):
        if name in self.assets and self.canvas:
            img = self.assets[name]
            self.canvas.paste(img, (int(x), int(y)), img)

    def clear_canvas(self):
        if self.canvas:
            self.canvas.paste((0, 0, 0, 0), [0, 0, self.canvas.size[0], self.canvas.size[1]])

    def draw_rectangle(self, x, y, w, h, color="#FF0000", radius=0):
        if self.canvas:
            draw = ImageDraw.Draw(self.canvas)
            shape = [int(x), int(y), int(x + w), int(y + h)]
            if radius > 0:
                draw.rounded_rectangle(shape, radius=int(radius), fill=color)
            else:
                draw.rectangle(shape, fill=color)

    def get_preview_image(self):
        if self.is_preview_mode and self.preview_image: return self.preview_image
        if not self.canvas: return None
        preview = self.bg_pattern.copy()
        preview.paste(self.canvas, (0, 0), self.canvas)
        if self.show_debug_lines:
            draw, hx, hy = ImageDraw.Draw(preview), *self.global_hotspot
            line_color = (255, 0, 0, 255)
            draw.line([(hx - 15, hy), (hx + 15, hy)], fill=line_color, width=1)
            draw.line([(hx, hy - 15), (hx, hy + 15)], fill=line_color, width=1)
        return preview

    def set_preview_image(self, img_path):
        try:
            img = Image.open(img_path)
            img.thumbnail((400, 400), Image.Resampling.LANCZOS)
            preview = self.create_chessboard(img.size)
            preview.paste(img, (0, 0), img if img.mode == 'RGBA' else None)
            self.preview_image, self.is_preview_mode = preview, True
            return True
        except: return False

    def exit_preview_mode(self):
        self.is_preview_mode = False

class MouseEngineEditor:
    def __init__(self, root, project_name):
        self.root = root
        self.project_name = project_name
        self.project_root = os.path.abspath(os.path.join("projects", project_name))
        self.config_path = os.path.join(self.project_root, "project.toml")
        
        self.config = self.load_project_config()
        self.main_lua_path = os.path.join(self.project_root, self.config.get("main", "main.lua"))
        self.current_open_file = self.main_lua_path
        
        self.engine = RenderEngine()
        self.engine.project_root = self.project_root
        
        self.root.title(f"Cur2D Editor - {project_name}")
        self.root.geometry("1400x900")
        
        self.lua = None
        self.process = psutil.Process(os.getpid())
        self.last_frame_time = time.time()
        self.realtime_fps = 0.0
        self.current_frame = 1.0
        self.error_msg = None
        self.reload_job = None

        self.setup_ui()
        self.load_code_from_file(self.current_open_file)
        self.init_lua_env()
        self.log_panel.log("🚀 编辑器启动成功", "success")
        self.render_loop()

    def load_project_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "rb") as f: return tomllib.load(f)
        return {"main": "main.lua", "name": self.project_name}

    def setup_ui(self):
        self.main_content = tk.Frame(self.root)
        self.main_content.pack(fill=tk.BOTH, expand=True)
        self.main_paned = tk.PanedWindow(self.main_content, orient=tk.HORIZONTAL, sashwidth=6, bg="#333")
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # 左侧面板
        self.left_paned = tk.PanedWindow(self.main_paned, orient=tk.VERTICAL, sashwidth=6, bg="#333")
        self.preview_frame = tk.Frame(self.left_paned, bg="#252526")
        self.canvas_widget = tk.Canvas(self.preview_frame, highlightthickness=0, bg="#2b2b2b")
        self.canvas_widget.pack(expand=True, padx=20, pady=20)
        self.left_paned.add(self.preview_frame, height=450)
        
        self.browser_frame = tk.Frame(self.left_paned, bg="#2d2d30")
        self.resource_browser = ProjectResourceBrowser(self.browser_frame, project_root=self.project_root, 
                                                       on_file_select=self.on_image_file_select, 
                                                       on_code_open=self.on_code_file_open)
        self.resource_browser.pack(fill=tk.BOTH, expand=True)
        self.left_paned.add(self.browser_frame, height=300)
        self.main_paned.add(self.left_paned, width=500)

        # 右侧编辑器
        self.editor_frame = tk.Frame(self.main_paned, bg="#1e1e1e")
        self.code_editor = LuaCodeEditor(self.editor_frame)
        self.code_editor.pack(fill=tk.BOTH, expand=True)
        self.main_paned.add(self.editor_frame)

        # 日志与状态栏
        self.log_panel = LogPanel(self.root, height=100)
        self.log_panel.pack(fill=tk.X, side=tk.TOP)
        self.status_bar = tk.Label(self.root, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W, 
                                  bg="#007acc", fg="white", font=("Microsoft YaHei", 10))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.code_editor.bind("<<Modified>>", self.on_code_modified)

    def on_image_file_select(self, img_path):
        self.engine.set_preview_image(img_path)

    def on_code_file_open(self, code_path):
        self.current_open_file = code_path
        self.load_code_from_file(code_path)
        self.engine.exit_preview_mode()
        if code_path == self.main_lua_path: self.init_lua_env()

    def on_code_modified(self, event=None):
        if self.code_editor.edit_modified():
            if self.reload_job: self.root.after_cancel(self.reload_job)
            self.reload_job = self.root.after(500, self.save_and_reload)
            self.code_editor.edit_modified(False)

    def load_code_from_file(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                self.code_editor.set_code(f.read())
                self.code_editor.edit_modified(False)

    def save_and_reload(self):
        try:
            with open(self.current_open_file, 'w', encoding='utf-8') as f:
                f.write(self.code_editor.get_code())
            if self.current_open_file == self.main_lua_path: self.init_lua_env()
            self.engine.exit_preview_mode()
        except Exception as e:
            self.log_panel.log(f"❌ 保存失败：{str(e)}", "error")

    def init_lua_env(self):
        try:
            self.lua = LuaRuntime(unpack_returned_tuples=True)
            g = self.lua.globals()
            g.set_canvas, g.load_png, g.add_image = self.engine.set_canvas, self.engine.load_png, self.engine.add_image
            g.set_hotspot, g.draw_rect = self.engine.set_hotspot, self.engine.draw_rectangle
            g.get_win_theme_color_hex = get_win_theme_color_hex
            g.fps, g.total_frames = 60, 15 # 默认 1 秒动画
            
            self.lua.execute(self.code_editor.get_code())
            self.current_frame, self.error_msg = 1.0, None
            self.log_panel.log(f"🔧 Lua重载成功 (FPS:{g.fps} Total:{g.total_frames})", "success")
        except Exception as e:
            self.error_msg = str(e)
            self.log_panel.log(f"❌ Lua错误：{str(e)}", "error")

    def render_loop(self):
        now = time.time()
        delta = now - self.last_frame_time
        self.last_frame_time = now
        if delta > 0: self.realtime_fps = (self.realtime_fps * 0.9) + ((1.0 / delta) * 0.1)

        g = self.lua.globals() if self.lua else None
        fps_limit = g.fps if g and g.fps else 30
        total_f = g.total_frames if g and g.total_frames else 1

        if not self.engine.is_preview_mode:
            self.engine.clear_canvas()
            if self.lua and not self.error_msg and g.on_render:
                try: g.on_render(int(self.current_frame))
                except Exception as e: self.error_msg = str(e)

        preview = self.engine.get_preview_image()
        if preview:
            w, h = preview.size
            scale = max(1, 250 // min(w, h))
            scaled = preview.resize((w*scale, h*scale), Image.Resampling.NEAREST)
            self.tk_img = ImageTk.PhotoImage(scaled)
            self.canvas_widget.config(width=w*scale, height=h*scale)
            self.canvas_widget.create_image(0, 0, anchor=tk.NW, image=self.tk_img)

        if not self.error_msg:
            mem = self.process.memory_info().rss / 1024 / 1024
            self.status_bar.config(text=f"进度: {int(self.current_frame)}/{int(total_f)} | FPS: {self.realtime_fps:.1f} | 内存: {mem:.1f}MB", bg="#007acc")
            if not self.engine.is_preview_mode:
                self.current_frame = 1.0 if self.current_frame >= total_f else self.current_frame + 1
        else:
            self.status_bar.config(text=f"运行时错误: {self.error_msg[:60]}...", bg="#cc0000")

        self.root.after(max(1, int(1000 / fps_limit)), self.render_loop)

def main(project_name: str):
    target_project = project_name
    # 创建必要的文件夹结构防止报错
    os.makedirs(f"projects/{target_project}", exist_ok=True)
    if not os.path.exists(f"projects/{target_project}/main.lua"):
        with open(f"projects/{target_project}/main.lua", "w") as f:
            f.write("fps = 60\ntotal_frames = 60\nfunction on_render(frame)\n  set_canvas(32, 32)\n  draw_rect(frame % 32, 10, 5, 5, '#00FF00')\nend")

    root = TkinterDnD.Tk()
    app = MouseEngineEditor(root, target_project)
    root.mainloop()


if __name__ == "__main__":
    main("test_mouse")
    # 创建必要的文件夹结构防止报错
    