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
try:
    from ui.widgets.lua_editor import LuaCodeEditor
    from ui.widgets.file_manager import ProjectResourceBrowser, LogPanel
except:
    from widgets.lua_editor import LuaCodeEditor
    from widgets.file_manager import ProjectResourceBrowser, LogPanel

if sys.platform == "win32":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

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
        relative_path = relative_path.replace("\\", "/")
        full_path = os.path.join(self.project_root, relative_path)
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
        if self.is_preview_mode and self.preview_image:
            return self.preview_image
            
        if not self.canvas: return None
        preview = self.bg_pattern.copy()
        preview.paste(self.canvas, (0, 0), self.canvas)
        if self.show_debug_lines:
            draw = ImageDraw.Draw(preview)
            hx, hy = self.global_hotspot
            line_color = (255, 0, 0, 255)
            draw.line([(hx - 15, hy), (hx + 15, hy)], fill=line_color, width=1)
            draw.line([(hx, hy - 15), (hx, hy + 15)], fill=line_color, width=1)
            draw.rectangle([hx-1, hy-1, hx+1, hy+1], fill=line_color)
        return preview

    def set_preview_image(self, img_path):
        try:
            img = Image.open(img_path)
            img.thumbnail((400, 400), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
            preview = self.create_chessboard(img.size)
            if img.mode == 'RGBA':
                preview.paste(img, (0, 0), img)
            else:
                preview.paste(img, (0, 0))
            self.preview_image = preview
            self.is_preview_mode = True
            return True
        except Exception as e:
            return False

    def exit_preview_mode(self):
        self.is_preview_mode = False
        self.preview_image = None

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
        
        self.root.title(f"Cur2D Editor - {project_name} ({os.path.basename(self.current_open_file)})")
        self.root.geometry("1400x900")
        
        self.lua = None
        self.process = psutil.Process(os.getpid())
        self.last_frame_time = time.time()
        self.realtime_fps = 0.0
        self.current_frame = 1
        self.error_msg = None
        self.reload_job = None

        self.setup_ui()
        self.load_code_from_file(self.current_open_file)
        self.init_lua_env()
        self.log_panel.log("🚀 编辑器启动成功", "success")
        self.render_loop()

    def load_project_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "rb") as f:
                return tomllib.load(f)
        else:
            return {"main": "main.lua", "name": self.project_name, "Type": "Cur2D Editor"}

    def setup_ui(self):
        self.main_content = tk.Frame(self.root)
        self.main_content.pack(fill=tk.BOTH, expand=True)

        self.main_paned = tk.PanedWindow(self.main_content, orient=tk.HORIZONTAL, sashwidth=6, bg="#333")
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        self.left_paned = tk.PanedWindow(self.main_paned, orient=tk.VERTICAL, sashwidth=6, bg="#333")
        
        self.preview_frame = tk.Frame(self.left_paned, bg="#252526")
        self.canvas_widget = tk.Canvas(self.preview_frame, highlightthickness=0, bg="#2b2b2b")
        self.canvas_widget.pack(expand=True, padx=20, pady=20)
        self.left_paned.add(self.preview_frame, height=450)
        
        self.browser_frame = tk.Frame(self.left_paned, bg="#2d2d30")
        self.resource_browser = ProjectResourceBrowser(
            self.browser_frame,
            project_root=self.project_root,
            on_file_select=self.on_image_file_select,
            on_code_open=self.on_code_file_open,
            bg="#2d2d30"
        )
        self.resource_browser.pack(fill=tk.BOTH, expand=True)
        self.left_paned.add(self.browser_frame, height=300)

        self.main_paned.add(self.left_paned, width=500)

        self.editor_frame = tk.Frame(self.main_paned, bg="#1e1e1e")
        self.code_editor = LuaCodeEditor(self.editor_frame)
        self.code_editor.pack(fill=tk.BOTH, expand=True)
        self.main_paned.add(self.editor_frame)

        self.log_panel = LogPanel(self.root, height=100)
        self.log_panel.pack(fill=tk.X, side=tk.TOP, padx=0, pady=0)
        self.resource_browser.log_func = self.log_panel.log

        self.status_bar = tk.Label(
            self.root, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W,
            bg="#007acc", fg="white", font=("Microsoft YaHei", 10)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.code_editor.bind("<<Modified>>", self.on_code_modified)

    def on_image_file_select(self, img_path):
        self.engine.set_preview_image(img_path)
        self.log_panel.log(f"🖼️  预览图片：{os.path.basename(img_path)}", "info")

    def on_code_file_open(self, code_path):
        try:
            with open(code_path, 'r', encoding='utf-8') as f:
                code = f.read()
            self.code_editor.set_code(code)
            self.code_editor.edit_modified(False)
            self.current_open_file = code_path
            self.root.title(f"Cur2D Editor - {self.project_name} ({os.path.basename(code_path)})")
            self.log_panel.log(f"📄 打开文件：{os.path.relpath(code_path, self.project_root)}", "info")
            
            self.engine.exit_preview_mode()
            
            if code_path == self.main_lua_path:
                self.init_lua_env()
        except Exception as e:
            self.log_panel.log(f"❌ 打开文件失败：{str(e)}", "error")

    def on_code_modified(self, event=None):
        if self.code_editor.edit_modified():
            if self.reload_job:
                self.root.after_cancel(self.reload_job)
            self.reload_job = self.root.after(500, self.save_and_reload)
            self.code_editor.edit_modified(False)

    def load_code_from_file(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            self.code_editor.set_code(code)
            self.code_editor.edit_modified(False)

    def save_and_reload(self):
        code = self.code_editor.get_code()
        try:
            os.makedirs(os.path.dirname(self.current_open_file), exist_ok=True)
            with open(self.current_open_file, 'w', encoding='utf-8') as f:
                f.write(code)
            self.log_panel.log(f"💾 保存成功：{os.path.relpath(self.current_open_file, self.project_root)}", "success")
            
            if self.current_open_file == self.main_lua_path:
                self.init_lua_env()
            self.engine.exit_preview_mode()
        except Exception as e:
            self.log_panel.log(f"❌ 保存失败：{str(e)}", "error")

    def init_lua_env(self):
        try:
            self.lua = LuaRuntime(unpack_returned_tuples=True)
            g = self.lua.globals()
            g.set_canvas = self.engine.set_canvas
            g.load_png = self.engine.load_png
            g.add_image = self.engine.add_image
            g.set_hotspot = self.engine.set_hotspot
            g.draw_rect = self.engine.draw_rectangle
            g.fps = 60
            g.total_frames = 0
            
            self.lua.execute(self.code_editor.get_code())
            self.error_msg = None
            self.log_panel.log("🔧 Lua环境初始化成功", "success")
        except Exception as e:
            self.error_msg = str(e)
            self.log_panel.log(f"❌ Lua错误：{str(e)}", "error")

    def render_loop(self):
        now = time.time()
        delta = now - self.last_frame_time
        self.last_frame_time = now
        if delta > 0:
            self.realtime_fps = (self.realtime_fps * 0.9) + ((1.0 / delta) * 0.1)

        if not self.engine.is_preview_mode:
            self.engine.clear_canvas()
            if self.lua:
                g = self.lua.globals()
                if g.on_render and not self.error_msg:
                    try:
                        g.on_render(self.current_frame)
                    except Exception as e:
                        self.error_msg = str(e)

        preview = self.engine.get_preview_image()
        if preview:
            self.tk_img = ImageTk.PhotoImage(preview)
            self.canvas_widget.config(width=preview.width, height=preview.height)
            self.canvas_widget.create_image(0, 0, anchor=tk.NW, image=self.tk_img)

        if not self.error_msg:
            g = self.lua.globals() if self.lua else None
            fps_val = g.fps if g and g.fps else 30
            total = g.total_frames if g and g.total_frames and g.total_frames > 0 else fps_val
            mem = self.process.memory_info().rss / 1024 / 1024
            mode_text = "图片预览" if self.engine.is_preview_mode else "Lua渲染"
            self.status_bar.config(
                text=f"项目: {self.project_name} | 模式: {mode_text} | 帧: {int(self.current_frame):03d} | "
                     f"帧率: {self.realtime_fps:.1f} FPS | 内存: {mem:.1f}MB"
            )
            if not self.engine.is_preview_mode:
                self.current_frame = 1 if self.current_frame >= total else self.current_frame + 1
        else:
            self.status_bar.config(text=f"运行时错误: {self.error_msg[:50]}...")

        delay = max(1, int(1000 / (g.fps if self.lua and g.fps else 30)))
        self.root.after(delay, self.render_loop)

if __name__ == "__main__":
    target_project = "test_mouse"
    root = TkinterDnD.Tk()
    app = MouseEngineEditor(root, target_project)
    root.mainloop()