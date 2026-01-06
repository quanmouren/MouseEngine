import customtkinter as ctk
import os
import sys
import toml
from PIL import Image, ImageSequence
import tkinter.messagebox as tk_messagebox 
import glob
import getpass
from customtkinter import filedialog 



from Tlog import TLog
from getWallpaperConfig import 获取当前壁纸
from mouses import 保存组配置, wallpaper, delete_wallpaper, wallpaper
from setMouse import 设置鼠标指针
project_root = os.path.dirname(os.path.abspath(__file__))


# 初始化日志和全局变量
log = TLog("WallpaperUI") 
WIN_USERNAME = getpass.getuser()
CONFIG_PATH = os.path.join(project_root, "config.toml")
MOUSE_BASE_PATH = os.path.join(project_root, "mouses")
WALLPAPER_ENGINE_CONFIG_PATH = toml.load(CONFIG_PATH)["path"]["wallpaper_engine_config"]

# 数据加载辅助函数
def load_toml_config(path=CONFIG_PATH):
    """加载顶层 config.toml 文件"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return toml.load(f)
    except Exception as e:
        log.error(f"加载主配置文件失败: {e}")
        return {}

def get_mouse_group_name(wallpaper_id: str) -> str:
    """根据壁纸 ID 获取对应的鼠标组名称"""
    return wallpaper(wallpaper_id, CONFIG_PATH)

def get_mouse_config_paths(group_name: str) -> dict:
    """加载指定鼠标组的 config.toml 中的光标路径"""
    if not group_name:
        return {}
    
    mouse_config_path = os.path.join(MOUSE_BASE_PATH, group_name, "config.toml")
    try:
        with open(mouse_config_path, 'r', encoding='utf-8') as f:
            config = toml.load(f)
            return config.get('mouses', {})
    except FileNotFoundError:
        log.error(f"鼠标组配置未找到: {group_name}. 路径: {mouse_config_path}")
        return {}
    except Exception as e:
        log.error(f"加载鼠标组配置失败: {e}")
        return {}

def get_available_mouse_groups() -> list:
    """查找 MOUSE_BASE_PATH 下所有包含 config.toml 文件的目录作为鼠标组名"""
    groups = []
    config_files = glob.glob(os.path.join(MOUSE_BASE_PATH, '*', 'config.toml'))
    
    for file_path in config_files:
        group_name = os.path.basename(os.path.dirname(file_path))
        groups.append(group_name)
        
    return sorted(groups)

def find_preview_image_path(file_path: str) -> str:
    """根据壁纸文件路径查找 preview 图像文件"""#BUG 视频壁纸索引错误/预览图定位错误
    if not file_path:
        return None

    if os.path.isfile(file_path):
        wallpaper_dir = os.path.dirname(file_path)
    else:
        wallpaper_dir = file_path
        
    for ext in ['jpg', 'png', 'gif']:
        preview_path = os.path.join(wallpaper_dir, f"preview.{ext}")
        if os.path.exists(preview_path):
            return preview_path
            
    log.error(f"未找到预览图: {wallpaper_dir}")
    return None

def derive_wallpaper_id(file_path: str) -> str:
    """
    从壁纸文件路径中提取壁纸 ID (通常是最后一级目录名)
    加载播放列表使用
    """
    if not file_path:
        return ""
    normalized_path = os.path.normpath(file_path)
    if os.path.isfile(normalized_path):
        file_dir = os.path.dirname(normalized_path)
    else:
        file_dir = normalized_path
    dir_path_normalized = file_dir.replace('\\', '/')
    return os.path.basename(dir_path_normalized)

# CustomTkinter UI 实现
class WallpaperConfigPage(ctk.CTkFrame):
    def __init__(self, master, config_data):
        super().__init__(master)
        self.config_data = config_data 
        self.monitor_count = len(config_data)
        self.current_monitor_index = 0
        self.cursor_entry_widgets = {}
        self.playlist_images = {} 
        self.preview_image = None 
        self.main_area_data = (None, None) 
        self.currently_displayed_playlist_data = ([], "") 

        # 光标名称顺序
        self.CURSOR_ORDER = [
            "Arrow", "Help", "AppStarting", "Wait", "Crosshair", "IBeam", 
            "Handwriting", "No", "SizeNS", "SizeWE", "SizeNWSE", "SizeNESW", 
            "SizeAll", "Hand", "UpArrow"
        ]
        
        # 光标名称映射
        self.CURSOR_MAPPING = [
            ("Arrow", "标准选择 (Arrow)"), 
            ("Help", "帮助选择 (Help)"), 
            ("AppStarting", "后台运行 (AppStarting)"), 
            ("Wait", "忙碌 (Wait)"), 
            ("Crosshair", "精确定位 (Crosshair)"), 
            ("IBeam", "文本选择 (IBeam)"), 
            ("Handwriting", "手写 (Handwriting)"), 
            ("No", "不可用 (No)"), 
            ("SizeNS", "垂直调整 (SizeNS)"), 
            ("SizeWE", "水平调整 (SizeWE)"), 
            ("SizeNWSE", "对角调整 1 (SizeNWSE)"), 
            ("SizeNESW", "对角调整 2 (SizeNESW)"), 
            ("SizeAll", "移动 (SizeAll)"), 
            ("Hand", "链接选择 (Hand)"), 
            ("UpArrow", "替代选择 (UpArrow)")
        ]
            
        # 左侧固定宽度
        self.MAIN_FRAME_LEFT_WIDTH = 300

        # 布局设置
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(1, weight=1) 
        self.grid_rowconfigure(2, weight=0) 
        
        # 顶部控制栏
        self.create_top_controls()
        
        # 主要功能区
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="nsew")
        
        self.main_frame.grid_columnconfigure(0, weight=0, minsize=self.MAIN_FRAME_LEFT_WIDTH) # 固定宽度
        self.main_frame.grid_columnconfigure(1, weight=1) # 完全自适应
        
        self.create_secondary_area()
        # 初始化数据
        self.update_display_data()

    # 创建顶部控制栏
    def create_top_controls(self):
        top_frame = ctk.CTkFrame(self)
        top_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=5)
        top_frame.columnconfigure(2, weight=1)

        ctk.CTkLabel(top_frame, text="选择显示器:", width=100).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        monitor_options = [f"显示器 {i+1}" for i in range(self.monitor_count)]
        self.monitor_select_combobox = ctk.CTkComboBox(
            top_frame, 
            values=monitor_options, 
            command=self.monitor_selection_changed
        )
        self.monitor_select_combobox.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.monitor_select_combobox.set(monitor_options[0])

        refresh_btn = ctk.CTkButton(top_frame, text="刷新壁纸数据", command=self.刷新壁纸数据)
        refresh_btn.grid(row=0, column=2, padx=10, pady=10, sticky="e")
        
    def 刷新壁纸数据(self):
        """重新加载壁纸配置数据并更新 UI (保留逻辑)"""
        try:
            new_data = 获取当前壁纸(WALLPAPER_ENGINE_CONFIG_PATH, WIN_USERNAME)
            if new_data:
                self.config_data = new_data
                self.monitor_count = len(new_data)
                
                if self.current_monitor_index >= self.monitor_count:
                    self.current_monitor_index = 0
                    
                monitor_options = [f"显示器 {i+1}" for i in range(self.monitor_count)]
                self.monitor_select_combobox.configure(values=monitor_options)
                self.monitor_select_combobox.set(monitor_options[self.current_monitor_index])
                
                self.update_display_data()
                log.info("壁纸配置数据刷新成功。")
            else:
                tk_messagebox.showerror("刷新失败", "无法获取最新的壁纸配置数据。")
        except Exception as e:
            log.error(f"刷新壁纸数据时发生错误: {e}")
            tk_messagebox.showerror("刷新错误", f"刷新壁纸配置失败: {e}")


    def monitor_selection_changed(self, choice):
        """处理显示器选择变化事件"""
        index = int(choice.split(' ')[-1]) - 1
        if 0 <= index < self.monitor_count:
            self.current_monitor_index = index
            self.update_display_data()

    # 主要功能区
    def update_wallpaper_info_custom(self, file_path, wallpaper_id):
        """更新左侧壁纸信息，接受 file_path 和 wallpaper_id"""
        self.path_label.configure(text=f"路径: {file_path}")
        self.id_label.configure(text=f"ID: {wallpaper_id}")

        preview_path = find_preview_image_path(file_path)
        if preview_path:
            try:
                img = Image.open(preview_path)
                MAX_DISPLAY_SIZE = (470, 280)  # 固定最大尺寸
                #缩放
                img_ratio = img.width / img.height
                target_ratio = MAX_DISPLAY_SIZE[0] / MAX_DISPLAY_SIZE[1]
                
                if img_ratio > target_ratio:
                    new_width = MAX_DISPLAY_SIZE[0]
                    new_height = int(new_width / img_ratio)
                else:
                    new_height = MAX_DISPLAY_SIZE[1]
                    new_width = int(new_height * img_ratio)
                
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                self.preview_image = ctk.CTkImage(light_image=img, size=(new_width, new_height))
                self.preview_label.configure(image=self.preview_image, text="")
            except Exception as e:
                self.preview_label.configure(text=f"加载失败: {preview_path}\n{e}", image=None)
                log.error(f"加载预览图失败: {e}")
        else:
            self.preview_label.configure(text="无预览图", image=None)#BUG 造成line 567 self.handle_playlist_item_click(path))错误

    def update_mouse_config_custom(self, file_path, wallpaper_id):
        """加载并填充鼠标组配置，接受 file_path 和 wallpaper_id"""
        group_name = get_mouse_group_name(wallpaper_id)
        
        if not group_name:
            if wallpaper_id and wallpaper_id.isnumeric():
                self.mouse_group_name_label.configure(text=f"鼠标组: 未绑定 ID {wallpaper_id}")
            else:
                self.mouse_group_name_label.configure(text=f"鼠标组: 未绑定 (无法获取ID)")
        else:
            self.mouse_group_name_label.configure(text=f"鼠标组: {group_name}")
            
        cursor_paths = get_mouse_config_paths(group_name)
        if hasattr(self, 'mouse_group_select_combobox'):
            group_options = ["从现有组选择"] + get_available_mouse_groups()
            self.mouse_group_select_combobox.configure(values=group_options)
            if group_name and group_name in group_options:
                self.mouse_group_select_combobox.set(group_name)
            else:
                self.mouse_group_select_combobox.set(group_options[0])

        for name in self.CURSOR_ORDER: 
            entry = self.cursor_entry_widgets.get(name)
            if entry:
                path = cursor_paths.get(name, "")
                entry.delete(0, ctk.END)
                entry.insert(0, path)

    # 主要功能区
    def create_wallpaper_info_area(self, current_data):
        for widget in self.main_frame.grid_slaves(row=0, column=0):
            widget.destroy()

        left_frame = ctk.CTkFrame(self.main_frame, width=self.MAIN_FRAME_LEFT_WIDTH)
        left_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(0, weight=1) 

        self.preview_label = ctk.CTkLabel(left_frame, text="加载预览图...")
        self.preview_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        info_frame = ctk.CTkFrame(left_frame)
        info_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        info_frame.grid_columnconfigure(0, weight=1)

        self.path_label = ctk.CTkLabel(info_frame, text="路径: 未知", wraplength=self.MAIN_FRAME_LEFT_WIDTH - 40, justify="left")
        self.path_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        
        self.id_label = ctk.CTkLabel(info_frame, text="ID: 未知", justify="left")
        self.id_label.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        
        # 初始加载
        file_path, wallpaper_id, _, _ = current_data
        self.update_wallpaper_info_custom(file_path, wallpaper_id)

    # 鼠标组快速选择处理函数
    def mouse_group_selection_changed(self, choice):
        """处理鼠标组选择变化事件，加载选定组的配置"""
        group_name = choice
        
        # 选中提示项时不进行配置加载
        if group_name == "从现有组选择" or group_name == "为此组命名":
            # 重新加载当前壁纸绑定的配置 
            file_path, wallpaper_id, _, _ = self.config_data[self.current_monitor_index]
            self.update_mouse_config_custom(file_path, wallpaper_id)
            return

        # 加载选定组的配置
        cursor_paths = get_mouse_config_paths(group_name)

        # 填充输入框
        for name in self.CURSOR_ORDER:
            entry = self.cursor_entry_widgets.get(name)
            if entry:
                path = cursor_paths.get(name, "")
                entry.delete(0, ctk.END)
                entry.insert(0, path)

        # 更新鼠标组名称标签
        self.mouse_group_name_label.configure(text=f"鼠标组: {group_name} (已加载配置)")

    # 创建主要功能区
    def create_mouse_config_area(self, current_data):
        # 清理旧组件
        for widget in self.main_frame.grid_slaves(row=0, column=1):
            widget.destroy()
            
        right_frame = ctk.CTkFrame(self.main_frame)
        right_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        right_frame.grid_columnconfigure(1, weight=1) 

        IMAGE_MAPPING = {        #TODO 重绘图标

            "Arrow": "aero_arrow.png",
            "Help": "aero_helpsel.png",
            "AppStarting": "aero_working_xl.png",
            "Wait": "aero_busy_xl.png",
            "Crosshair": "cross_il.png",
            "IBeam": "beam_rl.png",
            "Handwriting": "aero_pen.png",
            "No": "aero_unavail.png",
            "SizeNS": "aero_ns.png",
            "SizeWE": "aero_ew.png",
            "SizeNWSE": "aero_nwse.png",
            "SizeNESW": "aero_nesw.png",
            "SizeAll": "aero_move.png",
            "Hand": "aero_link.png",
            "UpArrow": "aero_up.png"
        }
        
        image_dir = "image"

        self.cursor_preview_images = {} 

        header_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 5), sticky="ew")
        header_frame.columnconfigure(1, weight=1) 

        available_groups = get_available_mouse_groups()
        group_options = ["从现有组选择"] + available_groups
        self.mouse_group_select_combobox = ctk.CTkComboBox(
            header_frame,
            values=group_options,
            command=self.mouse_group_selection_changed,
            width=150
        )
        self.mouse_group_select_combobox.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")
        self.mouse_group_select_combobox.set(group_options[0])
        
        self.mouse_group_name_label = ctk.CTkLabel(
            header_frame, 
            text="鼠标组配置", 
            font=ctk.CTkFont(weight="bold"), 
            justify="left",
            anchor="w",
            wraplength=200 
        )
        self.mouse_group_name_label.grid(row=0, column=1, padx=0, pady=5, sticky="ew") 

        content_frame = ctk.CTkFrame(right_frame)
        content_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="nsew") 
        content_frame.columnconfigure(2, weight=1)
        
        self.cursor_entry_widgets = {}
        for i, (key, label_text) in enumerate(self.CURSOR_MAPPING):
            ctk.CTkLabel(content_frame, text=f"{i+1}. {label_text}:").grid(row=i, column=0, padx=(10, 5), pady=4, sticky="w")
            
            img_name = IMAGE_MAPPING.get(key)
            img_path = os.path.join(image_dir, img_name) if img_name else ""
            
            icon_label = ctk.CTkLabel(content_frame, text="")
            
            if os.path.exists(img_path):
                try:
                    pil_img = Image.open(img_path)
                    ctk_icon = ctk.CTkImage(light_image=pil_img, size=(24, 24))
                    icon_label.configure(image=ctk_icon)
                    self.cursor_preview_images[key] = ctk_icon 
                except Exception as e:
                    log.error(f"无法打开图片 {img_name}: {e}")
            else:
                log.error(f"未找到图片文件: {img_path}")
            
            icon_label.grid(row=i, column=1, padx=5, pady=4)

            entry = ctk.CTkEntry(content_frame, height=25)
            entry.grid(row=i, column=2, padx=5, pady=4, sticky="ew")
            self.cursor_entry_widgets[key] = entry 
            # 浏览按钮
            browse_btn = ctk.CTkButton(content_frame, text="浏览", width=60, 
                                             command=lambda name=key: self.浏览光标文件(name)) 
            browse_btn.grid(row=i, column=3, padx=(0, 10), pady=4, sticky="e")
        
        save_btn = ctk.CTkButton(right_frame, text="保存并应用配置", command=self.保存并应用配置) 
        save_btn.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="ew") 

        file_path, wallpaper_id, _, _ = current_data
        self.update_mouse_config_custom(file_path, wallpaper_id)
        
        right_frame.grid_rowconfigure(1, weight=1)
    def get_all_cursor_paths(self) -> list:
        """
        获取所有光标路径输入框的内容，并按 self.CURSOR_ORDER 顺序返回一个列表。
        
        """
        cursor_path_list = []
        
        if not hasattr(self, 'CURSOR_ORDER') or not hasattr(self, 'cursor_entry_widgets'):
            log.error("错误：CURSOR_ORDER 或 cursor_entry_widgets 未初始化。")
            return []
        
        for cursor_name in self.CURSOR_ORDER:
            entry_widget = self.cursor_entry_widgets.get(cursor_name)
            
            if entry_widget:
                path = entry_widget.get().strip()
                cursor_path_list.append(path)
            else:
                cursor_path_list.append("")
                
        return cursor_path_list


    def get_wallpaper_id_and_group_selection(self) -> list:
            """
            获取当前正在编辑的壁纸id和组名
            """
            result_list = []
            
            if hasattr(self, 'main_area_data') and len(self.main_area_data) >= 2:
                wallpaper_id = self.main_area_data[1]
            else:
                wallpaper_id = ""
            result_list.append(wallpaper_id)

            if hasattr(self, 'mouse_group_select_combobox'):
                selected_group = self.mouse_group_select_combobox.get()
            else:
                selected_group = ""
            result_list.append(selected_group)
            return result_list


    def 浏览光标文件(self, cursor_name):
        """
        处理浏览按钮点击事件，选择 .ani 或 .cur 文件。
        """
        entry = self.cursor_entry_widgets.get(cursor_name)
        if not entry:
            log.error(f"找不到对应的输入框 widget: {cursor_name}")
            return
            
        current_path = entry.get()
        initial_dir = os.path.dirname(current_path) if current_path else None
        chinese_label = next((label for key, label in self.CURSOR_MAPPING if key == cursor_name), cursor_name)

        file_path = filedialog.askopenfilename(
            title=f"选择 {chinese_label} 光标文件",
            filetypes=[
                ("光标文件", "*.ani;*.cur"),
                ("动态光标", "*.ani"),
                ("静态光标", "*.cur"),
                ("所有文件", "*.*")
            ],
            initialdir=initial_dir
        )
        
        # 选择文件
        if file_path: #TODO 选择文件添加判断，支持选择inf文件一键读取，支持致美化
            normalized_path = os.path.normpath(file_path)
            # 更新对应的输入框
            entry.delete(0, ctk.END)
            entry.insert(0, normalized_path)
            log.info(f"为 {cursor_name} 选择了光标文件: {normalized_path}")

    def 保存并应用配置(self):
        wallpaper_id, selected_group = self.get_wallpaper_id_and_group_selection()
        if selected_group == "" or selected_group == "从现有组选择" or selected_group == "为此组命名":
            log.error("鼠标组名称不正确")
            self.mouse_group_select_combobox.set("为此组命名")
            tk_messagebox.showinfo("错误", "请为此组命名")
        else:
            cursor_path_list = self.get_all_cursor_paths()
            log.debug(cursor_path_list)
            保存组配置(selected_group, "mouses", cursor_path_list)
            log.debug(f"正在保存壁纸: {wallpaper_id} 的鼠标配置. 组名: {selected_group}")
            add_wallpaper(selected_group, wallpaper_id)

    # 次要功能区
    def create_secondary_area(self):
        self.playlist_scroll_frame = ctk.CTkScrollableFrame(self, label_text="当前播放列表", orientation="horizontal", height=90)
        self.playlist_scroll_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=(5, 10), sticky="ew")

    def update_playlist_preview(self, items_list, playlist_name):
        """更新底部的播放列表预览，接受 items_list 和 playlist_name"""
        
        for widget in self.playlist_scroll_frame.winfo_children():
            widget.destroy()

        self.playlist_images.clear() 

        self.playlist_scroll_frame.configure(label_text=f"当前播放列表: {playlist_name} (共 {len(items_list)} 项)")

        # 图片和容器尺寸
        FRAME_SIZE = (80, 80) 
        IMAGE_SIZE = (70, 70) 
        
        for i, item_path in enumerate(items_list):
            preview_path = find_preview_image_path(item_path)
            
            frame = ctk.CTkFrame(self.playlist_scroll_frame, width=FRAME_SIZE[0], height=FRAME_SIZE[1], cursor="hand2")
            frame.pack(side="left", padx=5 , pady=5)
            frame.pack_propagate(False) 
            
            frame.bind("<Button-1>", lambda event, path=item_path: self.handle_playlist_item_click(path))
            
            if preview_path:
                try:
                    img = Image.open(preview_path)
                    img.thumbnail(IMAGE_SIZE) 
                    
                    playlist_image = ctk.CTkImage(light_image=img, size=(img.width, img.height))
                    self.playlist_images[i] = playlist_image 
                    
                    label = ctk.CTkLabel(frame, image=self.playlist_images[i], text="", cursor="hand2")
                    label.pack(expand=True, fill="both", padx=5, pady=5) 
                    
                    label.bind("<Button-1>", lambda event, path=item_path: self.handle_playlist_item_click(path))
                except Exception:
                    ctk.CTkLabel(frame, text="预览失败", font=("", 8)).pack(expand=True)
            else:
                ctk.CTkLabel(frame, text=f"项目 {i+1}", font=("", 8)).pack(expand=True)
            
    def handle_playlist_item_click(self, file_path: str):
        """处理播放列表项目点击事件，将该壁纸加载到主区域进行编辑"""
        wallpaper_id = derive_wallpaper_id(file_path)
        log.info(f"点击播放列表项目: {file_path}, ID: {wallpaper_id}. 正在加载到主编辑区。")

        # 更新当前编辑数据
        self.main_area_data = (file_path, wallpaper_id)

        # 更新主区域
        self.update_wallpaper_info_custom(file_path, wallpaper_id)
        self.update_mouse_config_custom(file_path, wallpaper_id)
        

    # 核心数据更新函数
    def update_display_data(self):
        """根据当前选中的显示器索引，更新所有 UI 区域"""
        
        if not self.config_data:
            tk_messagebox.showerror("错误", "无法加载壁纸配置数据，请检查 config.json 路径。")
            return

        current_data = self.config_data[self.current_monitor_index]
        file_path, wallpaper_id, items_list, playlist_name = current_data
        log.debug(f"加载显示器 {self.current_monitor_index + 1} 数据: {wallpaper_id}")

        # 设置当前主编辑区的数据
        self.main_area_data = (file_path, wallpaper_id)
        self.currently_displayed_playlist_data = (items_list, playlist_name) 
        
        # 更新左侧壁纸信息
        self.create_wallpaper_info_area(current_data)
        # 更新右侧鼠标配置
        self.create_mouse_config_area(current_data) 
        # 更新底部播放列表
        self.update_playlist_preview(items_list, playlist_name)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Wallpaper Engine 扩展配置工具")
        
        self.geometry("900x910") 
        
        ctk.set_appearance_mode("System") 
        ctk.set_default_color_theme("blue") 
        try:
            wallpaper_data = 获取当前壁纸(WALLPAPER_ENGINE_CONFIG_PATH, WIN_USERNAME)
            
            if not wallpaper_data:
                tk_messagebox.showerror("启动错误", "无法获取 Wallpaper Engine 壁纸配置，请检查路径和用户名。")
                self.after(100, self.quit) 
                return

        except Exception as e:
            log.error(f"启动错误：{e}")
            tk_messagebox.showerror("启动错误", f"加载壁纸配置失败: {e}")
            self.after(100, self.quit) 
            return
            
        if not 'wallpaper_data' in locals():
            self.quit()
            return

        # 布局
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 添加页面
        self.wallpaper_page = WallpaperConfigPage(self, config_data=wallpaper_data)
        self.wallpaper_page.grid(row=0, column=0, sticky="nsew") 

if __name__ == "__main__":
    app = App()
    app.mainloop()