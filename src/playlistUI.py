import customtkinter as ctk
import os
import sys
import toml
import glob
from PIL import Image
import tkinter.messagebox as tk_messagebox 

from Tlog import TLog
from getWallpaperConfig import 获取当前壁纸 
from mouses import add_wallpaper, delete_wallpaper 
from setMouse import 设置鼠标指针 


log = TLog("PlaylistManagerUI") 
CONFIG_PATH = "config.toml"
MOUSE_BASE_PATH = "mouses"
try:
    WALLPAPER_ENGINE_CONFIG_PATH = toml.load(CONFIG_PATH)["path"]["wallpaper_engine_config"]
except KeyError:
    log.error("config.toml 中缺少 [path][wallpaper_engine_config] 键。")
    WALLPAPER_ENGINE_CONFIG_PATH = ""
try:
    WIN_USERNAME = os.getlogin()
except Exception:
    import getpass
    WIN_USERNAME = getpass.getuser()

def load_wallpaper_bindings(path=CONFIG_PATH) -> dict:
    try:
        config = toml.load(path)
        return {str(k): v for k, v in config.get('wallpaper', {}).items()}
    except Exception as e:
        log.error(f"加载壁纸绑定配置失败: {e}")
        return {}

def get_available_mouse_groups() -> list:
    groups = []
    config_files = glob.glob(os.path.join(MOUSE_BASE_PATH, '*', 'config.toml'))
    for file_path in config_files:
        group_name = os.path.basename(os.path.dirname(file_path))
        groups.append(group_name)
    return sorted(groups)

def find_preview_image_path(file_path: str) -> str:
    if not file_path: return None
    wallpaper_dir = os.path.dirname(file_path) if os.path.isfile(file_path) else file_path
    for ext in ['jpg', 'png', 'gif']:
        preview_path = os.path.join(wallpaper_dir, f"preview.{ext}")
        if os.path.exists(preview_path): return preview_path
    return None

def derive_wallpaper_id(file_path: str) -> str:
    if not file_path: return ""
    normalized_path = os.path.normpath(file_path)
    file_dir = os.path.dirname(normalized_path) if os.path.isfile(normalized_path) else normalized_path
    return os.path.basename(file_dir.replace('\\', '/'))

class PlaylistManagerPage(ctk.CTkFrame):
    
    def __init__(self, master, config_data):
        super().__init__(master)
        self.config_data = config_data 
        self.monitor_count = len(config_data)
        self.current_monitor_index = 0
        self.mouse_groups = get_available_mouse_groups()
        self.wallpaper_bindings = load_wallpaper_bindings()
        self.playlist_images = {} 
        
        self.MAX_COLS = 5 # 每行最多项目
        self.IMAGE_WIDTH = 160 # 默认图片宽度
        self.IMAGE_HEIGHT = 160 # 默认图片高度
        
        self.ITEM_WIDTH = self.IMAGE_WIDTH + 20
        # 列表项容器高度
        self.ITEM_HEIGHT = self.IMAGE_HEIGHT + 80


        # 布局设置
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) 
        
        # 顶部控制栏
        self.create_top_controls()
        
        # 主要网格展示区
        self.playlist_scroll_frame = ctk.CTkScrollableFrame(self, label_text="播放列表项目 (快速绑定鼠标组)")
        self.playlist_scroll_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # 初始化数据
        self.update_display_data()
        
    def create_top_controls(self):
        top_frame = ctk.CTkFrame(self)
        top_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        top_frame.columnconfigure(1, weight=1) 

        ctk.CTkLabel(top_frame, text="显示器:").grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")
        monitor_options = [f"显示器 {i+1}" for i in range(self.monitor_count)]
        self.monitor_select_combobox = ctk.CTkComboBox(
            top_frame, 
            values=monitor_options, 
            command=self.monitor_selection_changed
        )
        self.monitor_select_combobox.grid(row=0, column=1, padx=(5, 20), pady=10, sticky="ew")
        self.monitor_select_combobox.set(monitor_options[0])


            
    def monitor_selection_changed(self, choice):
        """处理显示器选择变化事件"""
        index = int(choice.split(' ')[-1]) - 1
        if 0 <= index < self.monitor_count:
            self.current_monitor_index = index
            self.update_display_data()

    def handle_mouse_group_binding(self, choice: str, wallpaper_id: str):
        """处理绑定/解除绑定逻辑"""
        selected_group = choice
        
        if not wallpaper_id.strip().isnumeric():
            tk_messagebox.showerror("错误", "壁纸 ID 无效，无法执行操作。")
            return

        if selected_group == "未绑定":
            try:
                delete_wallpaper(wallpaper_id)
                self.wallpaper_bindings.pop(wallpaper_id, None) 
                log.info(f"成功解除壁纸 ID: {wallpaper_id} 的鼠标组绑定。")
            except Exception as e:
                log.error(f"解除绑定失败: {e}")
                tk_messagebox.showerror("解除绑定错误", f"解除 {wallpaper_id} 绑定失败: {e}")
        
        elif selected_group in self.mouse_groups:
            try:
                add_wallpaper(selected_group, wallpaper_id)
                self.wallpaper_bindings[wallpaper_id] = selected_group 
                log.info(f"成功将壁纸 ID: {wallpaper_id} 快速绑定到组: {selected_group}")
            except Exception as e:
                log.error(f"快速绑定失败: {e}")
                tk_messagebox.showerror("绑定错误", f"壁纸 ID: {wallpaper_id} 绑定失败: {e}")
                
        else:
            tk_messagebox.showwarning("警告", f"选择了无效的鼠标组名: {selected_group}。请重新选择。")


    def update_playlist_grid(self, items_list, playlist_name):
        """更新网格播放列表"""
        
        for widget in self.playlist_scroll_frame.winfo_children():
            widget.destroy()

        self.playlist_images.clear() 
        self.playlist_scroll_frame.configure(label_text=f"当前播放列表: {playlist_name} (共 {len(items_list)} 项)")

        for i in range(self.MAX_COLS):
            self.playlist_scroll_frame.grid_columnconfigure(i, weight=1)

        for i, item_path in enumerate(items_list):
            
            wallpaper_id = derive_wallpaper_id(item_path)
            
            row = i // self.MAX_COLS
            col = i % self.MAX_COLS
            
            frame = ctk.CTkFrame(self.playlist_scroll_frame, width=self.ITEM_WIDTH, height=self.ITEM_HEIGHT)
            frame.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
            frame.grid_propagate(False) 
            frame.grid_columnconfigure(0, weight=1)
            label = ctk.CTkLabel(frame, text="加载中...", font=("", 10))
            label.grid(row=0, column=0, padx=5, pady=(5, 2), sticky="n")
            
            self.load_image_sync(label, item_path, i, wallpaper_id)
            
            current_binding = self.wallpaper_bindings.get(wallpaper_id, "未绑定")
            group_options = ["未绑定"] + self.mouse_groups 
            if current_binding != "未绑定" and current_binding not in self.mouse_groups:
                group_options.insert(1, current_binding) 
                
            combobox = ctk.CTkComboBox(
                frame, 
                values=group_options, 
                command=lambda choice, w_id=wallpaper_id: self.handle_mouse_group_binding(choice, w_id),
                width=self.ITEM_WIDTH - 20 
            )
            combobox.set(current_binding)
            combobox.grid(row=1, column=0, padx=10, pady=(2, 5), sticky="ew")
            
            ctk.CTkLabel(frame, text=f"ID: {wallpaper_id}", font=("", 15), text_color="gray").grid(row=2, column=0, padx=5, pady=(0, 5), sticky="n")

    def load_image_sync(self, label_widget, item_path, index, wallpaper_id):
        """
        同步加载图片并更新 UI。
        """
        preview_path = find_preview_image_path(item_path)
        
        if preview_path:
            try:
                img = Image.open(preview_path)
                img.thumbnail((self.IMAGE_WIDTH, self.IMAGE_HEIGHT), Image.Resampling.LANCZOS)
                
                playlist_image = ctk.CTkImage(light_image=img, size=(img.width, img.height))
                self.playlist_images[index] = playlist_image 
                
                label_widget.configure(image=self.playlist_images[index], text="")
                
            except Exception as e:
                log.error(f"加载或处理预览图失败: {e}")
                label_widget.configure(text=f"ID: {wallpaper_id}\n预览失败", image=None)
        else:
            label_widget.configure(text=f"ID: {wallpaper_id}\n无预览图", image=None)


    def update_display_data(self):
        """根据当前选中的显示器索引，更新 UI 区域 """
        self.mouse_groups = get_available_mouse_groups()
        self.wallpaper_bindings = load_wallpaper_bindings()
        
        if not self.config_data:
            tk_messagebox.showerror("错误", "无法加载壁纸配置数据。")
            return

        try:
            _, _, items_list, playlist_name = self.config_data[self.current_monitor_index]
        except IndexError:
            tk_messagebox.showerror("错误", "显示器索引超出范围。")
            items_list = []
            playlist_name = "未知播放列表"

        log.debug(f"加载显示器 {self.current_monitor_index + 1} 播放列表: {playlist_name}")

        self.update_playlist_grid(items_list, playlist_name)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("播放列表快速绑定工具")
        self.geometry("1100x800") 
        ctk.set_appearance_mode("System") 
        ctk.set_default_color_theme("blue") 
        
        # 设置窗口图标
        try:
            self.iconbitmap("icon300.ico")
        except Exception:
            pass 
        
        if not WALLPAPER_ENGINE_CONFIG_PATH:
            self.after(100, self.quit)
            return

        try:
            self.wallpaper_data = 获取当前壁纸(WALLPAPER_ENGINE_CONFIG_PATH, WIN_USERNAME)
            
            if not self.wallpaper_data:
                tk_messagebox.showerror("启动错误", "无法获取 Wallpaper Engine 壁纸配置，请检查路径和用户名。")
                self.after(100, self.quit) 
                return

        except Exception as e:
            log.error(f"启动错误：{e}")
            tk_messagebox.showerror("启动错误", f"加载壁纸配置失败: {e}")
            self.after(100, self.quit) 
            return
            
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.playlist_page = PlaylistManagerPage(self, config_data=self.wallpaper_data)
        self.playlist_page.grid(row=0, column=0, sticky="nsew") 

if __name__ == "__main__":
    app = App()
    app.mainloop()