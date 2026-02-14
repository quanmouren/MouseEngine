# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: CC BY-NC-SA 4.0
import os
import time
import psutil
import tkinter as tk
from tkinter import font, messagebox
from PIL import Image, ImageTk, ImageDraw
from lupa import LuaRuntime
import tomllib

# 渲染引擎
class RenderEngine:
    def __init__(self):
        self.canvas = None
        self.assets = {}
        self.bg_pattern = None
        self.global_hotspot = [0, 0]
        self.show_debug_lines = True
        self.project_root = "" # 动态项目根目录

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
        """自动根据项目根目录拼接路径"""
        # 处理 Lua 中可能传入的反斜杠
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

# 编辑器
class MouseEngineEditor:
    def __init__(self, root, project_name):
        self.root = root
        self.project_name = project_name
        self.project_root = os.path.abspath(os.path.join("projects", project_name))
        self.config_path = os.path.join(self.project_root, "project.toml")
        
        # 加载项目配置
        self.config = self.load_project_config()
        # 根据配置决定主 Lua 文件路径
        self.lua_filename = self.config.get("main", "main.lua")
        self.lua_path = os.path.join(self.project_root, self.lua_filename)
        
        self.engine = RenderEngine()
        self.engine.project_root = self.project_root
        
        self.root.title(f"Cur2D Editor - {project_name} ({self.lua_filename})")
        self.root.geometry("1100x700")
        
        self.lua = None
        self.process = psutil.Process(os.getpid())
        self.last_frame_time = time.time()
        self.realtime_fps = 0.0
        self.current_frame = 1
        self.error_msg = None
        self.reload_job = None

        self.setup_ui()
        self.load_code_from_file()
        self.init_lua_env()
        self.render_loop()

    def load_project_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "rb") as f:
                return tomllib.load(f)
        else:
            # 默认配置
            return {"main": "main.lua", "name": self.project_name, "Type": "Cur2D Editor"}

    def setup_ui(self):
        self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=6, bg="#333")
        self.paned.pack(fill=tk.BOTH, expand=True)

        self.left_frame = tk.Frame(self.paned, bg="#252526")
        self.canvas_widget = tk.Canvas(self.left_frame, highlightthickness=0, bg="#2b2b2b")
        self.canvas_widget.pack(expand=True, padx=20, pady=20)
        self.paned.add(self.left_frame, width=400)

        self.right_frame = tk.Frame(self.paned, bg="#1e1e1e")
        code_font = font.Font(family="Consolas", size=12)
        self.code_text = tk.Text(self.right_frame, bg="#1e1e1e", fg="#d4d4d4",
                                insertbackground="white", font=code_font, undo=True,
                                padx=10, pady=10, borderwidth=0)
        self.code_text.pack(fill=tk.BOTH, expand=True)
        self.paned.add(self.right_frame)

        self.status_bar = tk.Label(self.root, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W,
                                  bg="#007acc", fg="white", font=("Segoe UI", 10))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.code_text.bind("<<Modified>>", self.on_code_modified)
        self.code_text.bind("<Tab>", self.handle_tab)

    def handle_tab(self, event):
        self.code_text.insert(tk.INSERT, "    ")
        return 'break'

    def on_code_modified(self, event=None):
        if self.code_text.edit_modified():
            if self.reload_job:
                self.root.after_cancel(self.reload_job)
            self.reload_job = self.root.after(500, self.save_and_reload)
            self.code_text.edit_modified(False)

    def load_code_from_file(self):
        if os.path.exists(self.lua_path):
            self.code_text.delete("1.0", tk.END)
            with open(self.lua_path, 'r', encoding='utf-8') as f:
                self.code_text.insert("1.0", f.read())
            self.code_text.edit_modified(False)

    def save_and_reload(self):
        code = self.code_text.get("1.0", tk.END)
        os.makedirs(os.path.dirname(self.lua_path), exist_ok=True)
        with open(self.lua_path, 'w', encoding='utf-8') as f:
            f.write(code)
        self.init_lua_env()

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
            
            self.lua.execute(self.code_text.get("1.0", tk.END))
            self.error_msg = None
            self.status_bar.config(bg="#007acc", text=f"Active Project: {self.project_name}")
        except Exception as e:
            self.error_msg = str(e)
            self.status_bar.config(bg="#a30000", text="Lua Error")

    def render_loop(self):
        now = time.time()
        delta = now - self.last_frame_time
        self.last_frame_time = now
        if delta > 0:
            self.realtime_fps = (self.realtime_fps * 0.9) + ((1.0 / delta) * 0.1)

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
            fps_val = g.fps if g and g.fps else 30
            total = g.total_frames if g and g.total_frames and g.total_frames > 0 else fps_val
            mem = self.process.memory_info().rss / 1024 / 1024
            self.status_bar.config(text=f"Project: {self.project_name} | Frame: {int(self.current_frame):03d} | {self.realtime_fps:.1f} FPS | Mem: {mem:.1f}MB")
            self.current_frame = 1 if self.current_frame >= total else self.current_frame + 1
        else:
            self.status_bar.config(text=f"Runtime Error: {self.error_msg[:60]}...")

        delay = max(1, int(1000 / (g.fps if self.lua and g.fps else 30)))
        self.root.after(delay, self.render_loop)

if __name__ == "__main__":
    target = "test_mouse"
    

    root = tk.Tk()
    app = MouseEngineEditor(root, "test_mouse")
    root.mainloop()