# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: CC BY-NC-SA 4.0
import os
import time
import sys
import shutil
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from PIL import Image, ImageTk, ImageDraw
from tkinterdnd2 import TkinterDnD, DND_FILES

BG_DARK = "#2d2d30"
BG_MID = "#3c3f41"
BG_LIGHT = "#45494a"
TEXT_COLOR = "#ffffff"
HIGHLIGHT_COLOR = "#007acc"
FOLDER_COLOR = "#ffd700"
FILE_COLOR = "#e0e0e0"
ICON_SIZE = (64, 64)
GRID_SPACING = 20
SUPPORTED_IMG = (".png", ".jpg", ".jpeg", ".bmp", ".ico", ".cur")
CODE_FILES = (".lua", ".py", ".toml", ".txt", ".md", ".json", ".xml", ".html", ".css", ".js")

if sys.platform == "win32":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

class LogPanel(tk.Frame):
    """独立的日志面板组件，可以单独使用"""
    def __init__(self, parent, height=100, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(bg=BG_MID, height=height)
        self.pack_propagate(False)

        self.log_header = tk.Frame(self, bg=BG_DARK, height=24)
        self.log_header.pack(fill=tk.X, side=tk.TOP)
        self.log_header.pack_propagate(False)
        
        tk.Label(self.log_header, text=" 操作日志", bg=BG_DARK, fg=TEXT_COLOR, 
                 font=("Microsoft YaHei", 9), anchor="w").pack(side=tk.LEFT, fill=tk.Y)
        
        self.clear_log_btn = tk.Button(
            self.log_header, text="清空", bg=BG_LIGHT, fg=TEXT_COLOR,
            relief=tk.FLAT, cursor="hand2", font=("Microsoft YaHei", 8),
            command=self.clear_log
        )
        self.clear_log_btn.pack(side=tk.RIGHT, padx=5, pady=2)

        self.log_text = scrolledtext.ScrolledText(
            self, bg=BG_DARK, fg=TEXT_COLOR,
            font=("Consolas", 9), insertbackground=TEXT_COLOR,
            state=tk.DISABLED, wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        self.log_text.tag_config("info", foreground="#4fc3f7")
        self.log_text.tag_config("success", foreground="#81c784")
        self.log_text.tag_config("warning", foreground="#ffb74d")
        self.log_text.tag_config("error", foreground="#e57373")
        self.log_text.tag_config("time", foreground="#78909c")

    def log(self, message, level="info"):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] ", "time")
        self.log_text.insert(tk.END, f"{message}\n", level)
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)

    def clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log("📋 日志已清空", "info")

class ProjectResourceBrowser(tk.Frame):
    """项目资源浏览器组件，支持拖放复制"""
    def __init__(self, parent, project_root, 
                 on_file_select=None, on_code_open=None, log_func=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.project_root = os.path.abspath(project_root)
        self.virtual_root_name = os.path.basename(self.project_root)
        self.current_path = self.project_root
        self.on_file_select = on_file_select or (lambda x: None)
        self.on_code_open = on_code_open or (lambda x: None)
        self.log_func = log_func or (lambda msg, lv: print(f"[{lv}] {msg}"))
        
        self.selected_item = None
        self.image_refs = []
        self.thumbnail_cache = {}
        self.item_cards = []
        self.columns = 0

        self.setup_ui()
        self.bind_dnd_event()
        self.default_folder_icon = self.generate_default_icon("folder")
        self.default_file_icon = self.generate_default_icon("file")
        self.after(100, self.refresh_browser)

    def setup_ui(self):
        self.toolbar = tk.Frame(self, bg=BG_MID, height=30)
        self.toolbar.pack(fill=tk.X, side=tk.TOP, padx=1, pady=1)
        self.toolbar.pack_propagate(False)

        self.back_btn = tk.Button(
            self.toolbar, text="⬆ 上级", bg=BG_LIGHT, fg=TEXT_COLOR,
            relief=tk.FLAT, cursor="hand2", command=self.go_parent_dir, font=("Microsoft YaHei", 9)
        )
        self.back_btn.pack(side=tk.LEFT, padx=5, pady=3)

        self.refresh_btn = tk.Button(
            self.toolbar, text="🔄 刷新", bg=BG_LIGHT, fg=TEXT_COLOR,
            relief=tk.FLAT, cursor="hand2", command=self.refresh_browser, font=("Microsoft YaHei", 9)
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5, pady=3)

        self.address_var = tk.StringVar()
        self.address_entry = tk.Entry(
            self.toolbar, textvariable=self.address_var, bg=BG_DARK, fg=TEXT_COLOR,
            relief=tk.FLAT, font=("Microsoft YaHei", 9)
        )
        self.address_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=3)

        self.scroll_frame = tk.Frame(self, bg=BG_DARK)
        self.scroll_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        self.v_scroll = ttk.Scrollbar(self.scroll_frame, orient=tk.VERTICAL)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll = ttk.Scrollbar(self.scroll_frame, orient=tk.HORIZONTAL)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(
            self.scroll_frame, bg=BG_DARK, highlightthickness=0,
            yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        self.grid_container = tk.Frame(self.canvas, bg=BG_DARK)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.grid_container, anchor="nw")

        self.grid_container.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)

    def bind_dnd_event(self):
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<DragEnter>>", self.on_drag_enter)
        self.dnd_bind("<<DragOver>>", self.on_drag_over)
        self.dnd_bind("<<Drop>>", self.on_drop)

    def on_drag_enter(self, event):
        return TkinterDnD.COPY

    def on_drag_over(self, event):
        return TkinterDnD.COPY

    def parse_drop_paths(self, data):
        paths = []
        if data.startswith("{"):
            parts = data.split("} {")
            for part in parts:
                path = part.strip("{} ").replace("/", "\\")
                if os.path.exists(path):
                    paths.append(path)
        else:
            for path in data.split():
                path = path.strip().replace("/", "\\")
                if os.path.exists(path):
                    paths.append(path)
        return paths

    def on_drop(self, event):
        source_paths = self.parse_drop_paths(event.data)
        if not source_paths:
            self.log_func("⚠️ 拖入失败：未识别到有效文件/文件夹", "warning")
            return

        success_count = 0
        fail_count = 0
        skip_count = 0

        self.log_func(f"📥 开始拖入 {len(source_paths)} 个文件/文件夹...", "info")

        for source_path in source_paths:
            file_name = os.path.basename(source_path)
            target_path = os.path.join(self.current_path, file_name)

            if not os.path.abspath(target_path).startswith(self.project_root):
                fail_count += 1
                self.log_func(f"❌ 拒绝复制「{file_name}」：超出项目根目录范围", "error")
                continue

            if os.path.exists(target_path):
                self.log_func(f"⏭️  跳过「{file_name}」：文件已存在", "warning")
                skip_count += 1
                continue

            try:
                if os.path.isfile(source_path):
                    shutil.copy2(source_path, target_path)
                    self.log_func(f"✅ 成功复制文件：{file_name}", "success")
                    success_count += 1
                elif os.path.isdir(source_path):
                    shutil.copytree(source_path, target_path, dirs_exist_ok=True)
                    self.log_func(f"✅ 成功复制文件夹：{file_name}", "success")
                    success_count += 1
            except Exception as e:
                fail_count += 1
                self.log_func(f"❌ 复制失败「{file_name}」：{str(e)}", "error")

        if success_count > 0:
            self.refresh_browser()

        self.log_func(f"📊 拖入完成：成功 {success_count} 个，跳过 {skip_count} 个，失败 {fail_count} 个", "info")

    def generate_default_icon(self, icon_type):
        img = Image.new("RGBA", ICON_SIZE, (0,0,0,0))
        draw = ImageDraw.Draw(img)
        if icon_type == "folder":
            draw.polygon([(10, 20), (54, 20), (54, 54), (10, 54)], fill=FOLDER_COLOR)
            draw.polygon([(10, 20), (20, 10), (44, 10), (54, 20)], fill=FOLDER_COLOR)
            draw.rectangle([(10, 20), (54, 22)], fill="#e6b800")
        else:
            draw.rectangle([(15, 10), (49, 54)], fill=FILE_COLOR)
            draw.polygon([(49, 10), (49, 24), (35, 10)], fill="#bbbbbb")
            draw.rectangle([(20, 30), (44, 32)], fill="#999999")
            draw.rectangle([(20, 38), (44, 40)], fill="#999999")
        return ImageTk.PhotoImage(img)

    def get_virtual_path(self, real_path):
        try:
            relative = os.path.relpath(real_path, os.path.dirname(self.project_root))
            return relative.replace("/", "\\")
        except:
            return self.virtual_root_name

    def update_scroll_region(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_resize(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.arrange_grid()

    def refresh_browser(self):
        for widget in self.grid_container.winfo_children():
            widget.destroy()
        self.image_refs.clear()
        self.selected_item = None
        self.item_cards = []
        self.columns = 0

        self.address_var.set(self.get_virtual_path(self.current_path))
        self.back_btn.config(state=tk.NORMAL if self.current_path != self.project_root else tk.DISABLED)

        try:
            items = sorted(os.scandir(self.current_path), key=lambda x: (not x.is_dir(), x.name.lower()))
        except Exception as e:
            tk.Label(self.grid_container, text=f"无法访问目录: {str(e)}", bg=BG_DARK, fg="#ff6666").pack(expand=True)
            return

        if not items:
            tk.Label(
                self.grid_container, text="当前目录为空\n可拖入文件/文件夹到此处", bg=BG_DARK, fg="#888888",
                font=("Microsoft YaHei", 10), justify=tk.CENTER
            ).pack(expand=True, pady=30)
            return

        for item in items:
            if item.name.startswith("."):
                continue
            card = self.create_item_card(item)
            self.item_cards.append(card)

        self.after_idle(self.arrange_grid)

    def create_item_card(self, item):
        is_dir = item.is_dir()
        item_name = item.name
        item_path = item.path

        card = tk.Frame(
            self.grid_container, bg=BG_DARK, width=ICON_SIZE[0]+10,
            height=ICON_SIZE[1]+30, cursor="hand2"
        )
        icon_label = tk.Label(card, bg=BG_DARK)
        icon_label.pack(pady=(5, 2))
        name_label = tk.Label(
            card, text=item_name, bg=BG_DARK, fg=TEXT_COLOR,
            font=("Microsoft YaHei", 8), wraplength=ICON_SIZE[0]+10, justify=tk.CENTER
        )
        name_label.pack(fill=tk.X, padx=2)

        if is_dir:
            icon = self.default_folder_icon
        else:
            ext = os.path.splitext(item_name)[1].lower()
            if ext in SUPPORTED_IMG:
                try:
                    if item_path not in self.thumbnail_cache:
                        img = Image.open(item_path)
                        img.thumbnail(ICON_SIZE, Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
                        self.thumbnail_cache[item_path] = ImageTk.PhotoImage(img)
                    icon = self.thumbnail_cache[item_path]
                except:
                    icon = self.default_file_icon
            else:
                icon = self.default_file_icon

        icon_label.config(image=icon)
        self.image_refs.append(icon)

        card.item_path = item_path
        card.is_dir = is_dir
        for widget in [card, icon_label, name_label]:
            widget.bind("<Button-1>", lambda e, c=card: self.select_item(c))
            widget.bind("<Double-1>", lambda e, c=card: self.double_click_item(c))

        return card

    def arrange_grid(self):
        if not self.item_cards:
            return
        canvas_width = self.canvas.winfo_width()
        card_width = ICON_SIZE[0] + GRID_SPACING
        columns = max(1, int(canvas_width // card_width))
        if columns == self.columns:
            return
        self.columns = columns

        for card in self.item_cards:
            card.grid_forget()
        for idx, card in enumerate(self.item_cards):
            row = idx // columns
            col = idx % columns
            card.grid(row=row, column=col, padx=GRID_SPACING//2, pady=GRID_SPACING//2, sticky="n")
        self.update_scroll_region()

    def select_item(self, card):
        if self.selected_item:
            self.selected_item.config(bg=BG_DARK)
            for w in self.selected_item.winfo_children():
                w.config(bg=BG_DARK)
        
        self.selected_item = card
        card.config(bg=HIGHLIGHT_COLOR)
        for w in card.winfo_children():
            w.config(bg=HIGHLIGHT_COLOR)

        if not card.is_dir:
            ext = os.path.splitext(card.item_path)[1].lower()
            if ext in SUPPORTED_IMG:
                self.on_file_select(card.item_path)
            elif ext in CODE_FILES:
                self.on_code_open(card.item_path)

    def double_click_item(self, card):
        if card.is_dir:
            self.current_path = card.item_path
            self.refresh_browser()
        else:
            ext = os.path.splitext(card.item_path)[1].lower()
            if ext in CODE_FILES:
                self.on_code_open(card.item_path)

    def go_parent_dir(self):
        if self.current_path != self.project_root:
            self.current_path = os.path.dirname(self.current_path)
            self.refresh_browser()

    def on_mouse_wheel(self, event):
        if event.delta:
            self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

if __name__ == "__main__":
    def demo_select_img(path):
        print(f"[演示] 选中图片: {path}")

    def demo_open_code(path):
        print(f"[演示] 打开代码: {path}")

    demo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.exists(demo_root):
        demo_root = os.path.abspath(".")

    root = TkinterDnD.Tk()
    root.title("File Manager - 独立运行演示")
    root.geometry("800x600")
    root.configure(bg=BG_DARK)

    browser = ProjectResourceBrowser(
        root, 
        project_root=demo_root,
        on_file_select=demo_select_img,
        on_code_open=demo_open_code,
        bg=BG_DARK
    )
    browser.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    log_panel = LogPanel(root, height=120)
    log_panel.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)

    browser.log_func = log_panel.log
    log_panel.log("🚀 File Manager 独立运行演示启动", "success")
    log_panel.log(f"📂 当前项目目录: {demo_root}", "info")

    root.mainloop()