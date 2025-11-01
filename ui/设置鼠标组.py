import tkinter as tk
from tkinter import ttk, filedialog
import os
from PIL import Image, ImageTk
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.mouses import 保存组配置
from tkinterdnd2 import DND_FILES, TkinterDnD

class FilePathInputApp:
    def __init__(self, root, icon_paths):
        self.root = root
        self.root.title("鼠标组设置")
        self.root.geometry("650x650")
        self.icon_paths = icon_paths
        self.icon_images = []
        
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(2, weight=1)
        
        title_label = ttk.Label(main_frame, text="demo配置鼠标组", 
                               font=('Arial', 12, 'bold'))
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 15))
        
        self.entries = []
        self.create_input_fields(main_frame)
        
        extra_frame = ttk.Frame(main_frame)
        extra_frame.grid(row=17, column=0, columnspan=4, pady=10, sticky=(tk.W, tk.E))
        
        extra_label = ttk.Label(extra_frame, text="鼠标组名称:")
        extra_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.extra_entry = ttk.Entry(extra_frame, width=50)
        self.extra_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        extra_frame.columnconfigure(1, weight=1)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=18, column=0, columnspan=4, pady=20)

        self.output_btn = ttk.Button(button_frame, text="输出路径列表", 
                                   command=self.output_paths)
        self.output_btn.grid(row=0, column=0, padx=5)
        self.clear_btn = ttk.Button(button_frame, text="清空所有", 
                                  command=self.clear_all)
        self.clear_btn.grid(row=0, column=1, padx=5)
    
    def load_icon(self, icon_path, size=(16, 16)):
        """加载图标并调整大小"""
        try:
            if os.path.exists(icon_path):
                image = Image.open(icon_path)
                image = image.resize(size, Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(image)
            else:
                print(f"警告: 图标文件不存在: {icon_path}")
                return self.create_default_icon(size)
        except Exception as e:
            print(f"加载图标时出错 {icon_path}: {e}")
            return self.create_default_icon(size)
    
    def create_default_icon(self, size):
        """创建默认图标"""
        image = Image.new('RGBA', size, (200, 200, 200, 255))
        return ImageTk.PhotoImage(image)
    
    def create_input_fields(self, parent):
        """创建15个输入框，每个都有标签、图标和浏览按钮"""
        labels = [
            "正常选择", "帮助选择", "后台运行", "忙", "精准选择",
            "文本选择", "手写", "不可用", "垂直调整大小", "水平调整大小",
            "对角线调整1", "对角线调整2", "移动", "链接选择", "候选"
        ]
        
        for i in range(15):
            row_label = ttk.Label(parent, text=f"{labels[i]}:")
            row_label.grid(row=i+1, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            icon_image = self.load_icon(self.icon_paths[i])
            self.icon_images.append(icon_image) 
            icon_label = ttk.Label(parent, image=icon_image)
            icon_label.grid(row=i+1, column=1, sticky=tk.W, padx=(0, 5), pady=2)
            entry = tk.Entry(parent, width=50)
            entry.grid(row=i+1, column=2, sticky=(tk.W, tk.E), pady=2, padx=(0, 5))
            self.setup_drag_drop(entry)
            browse_btn = ttk.Button(parent, text="浏览", 
                                  command=lambda e=entry: self.browse_file(e))
            browse_btn.grid(row=i+1, column=3, sticky=tk.W, pady=2)
            
            self.entries.append(entry)
    
    def setup_drag_drop(self, widget):
        """设置拖放功能（仅当 tkinterdnd2 可用时）"""
        def on_drop(event):
            file_path = event.data
            if file_path.startswith('{') and file_path.endswith('}'):
                file_path = file_path[1:-1]
            
            files = file_path.split()
            if files:
                file_path = files[0]
            
            widget.delete(0, tk.END)
            widget.insert(0, file_path)
        
        widget.drop_target_register(DND_FILES)
        widget.dnd_bind('<<Drop>>', on_drop)
    
    def browse_file(self, entry_widget):
        """打开文件选择对话框"""
        filename = filedialog.askopenfilename()
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)
    
    def output_paths(self):
        """输出所有路径作为列表"""
        paths = []
        for entry in self.entries:
            path = entry.get().strip()
            if not path:
                path = ""
            paths.append(path)
        
        extra_content = self.extra_entry.get().strip()
        
        print(f"鼠标组名称: {extra_content}")
        print("路径列表:", paths)
        
        保存组配置(extra_content,"mouses", paths)
    
    def clear_all(self):
        """清空所有输入框"""
        for entry in self.entries:
            entry.delete(0, tk.END)
        self.extra_entry.delete(0, tk.END)

def main():
    custom_icon_paths = [
        "image\\aero_arrow.png",
        "image\\aero_helpsel.png",
        "image\\aero_working_xl.png",
        "image\\aero_busy_xl.png",
        "image\\cross_il.png",
        "image\\beam_rl.png",
        "image\\aero_pen.png",
        "image\\aero_unavail.png",
        "image\\aero_ns.png",
        "image\\aero_ew.png",
        "image\\aero_nesw.png",
        "image\\aero_nwse.png",
        "image\\aero_move.png",
        "image\\aero_link.png",
        "image\\aero_up.png"
    ]

    root = TkinterDnD.Tk()
    app = FilePathInputApp(root, icon_paths=custom_icon_paths)
    root.mainloop()

if __name__ == "__main__":
    main()