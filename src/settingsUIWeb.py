import webview
import os
import toml
from Tlog import TLog
import os

import platform
import re 
import tkinter as tk
from tkinter import filedialog
try:
    if platform.system() == "Windows":
        import winreg
    else:
        winreg = None
except ImportError:
    winreg = None

log = TLog("SettingsUI")

def find_steam_install_path():
    if platform.system() != "Windows" or winreg is None:
        return None
        
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        winreg.CloseKey(key)
        return steam_path.replace('/', '\\')
        
    except (FileNotFoundError, Exception):
        return None

def get_all_steam_library_paths(steam_main_path):
    library_paths = []
    if steam_main_path:
        library_paths.append(os.path.join(steam_main_path, "steamapps"))
        vdf_path = os.path.join(steam_main_path, "steamapps", "libraryfolders.vdf")
    else:
        return library_paths 

    if os.path.exists(vdf_path):
        try:
            with open(vdf_path, 'r', encoding='utf-8') as f:
                content = f.read()
            path_matches = re.findall(r'"\d+"\s+"(.+?)"', content)
            
            for path in path_matches:
                normalized_path = path.replace('\\\\', '\\').replace('/', '\\')
                library_paths.append(os.path.join(normalized_path, "steamapps"))
        except Exception as e:
            print(f"解析 libraryfolders.vdf 时出错: {e}")
    return library_paths

def find_wallpaper_engine_path_advanced():
    if platform.system() != "Windows":
        default_path = os.path.expanduser("~/.steam/steam/steamapps/common/wallpaper_engine")
        if os.path.exists(default_path) and os.path.exists(os.path.join(default_path, "wallpaper64.exe")):
            return default_path
        return None

    steam_main_path = find_steam_install_path()
    all_library_paths = get_all_steam_library_paths(steam_main_path)
    
    if not all_library_paths:
        common_paths = ["C:\\Program Files (x86)\\Steam", "C:\\Program Files\\Steam"]
        for path in common_paths:
            check_path = os.path.join(path, "steamapps", "common", "wallpaper_engine")
            if os.path.exists(os.path.join(check_path, "wallpaper64.exe")):
                 return check_path
        return None 

    for library_path in all_library_paths:
        we_path = os.path.join(library_path, "common", "wallpaper_engine")
        exe_path = os.path.join(we_path, "wallpaper64.exe")
        
        if os.path.exists(exe_path):
            return we_path
            
    return None
log.val(find_wallpaper_engine_path_advanced())



class SettingsApi:
    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

    def get_auto_start(self):
        log.info("获取自启动状态")
        return False 

    def get_wp_path(self):
        config_path = os.path.join(os.path.dirname(__file__), "config.toml")
        try:
            cfg = toml.load(config_path)
            return cfg.get("path", {}).get("wallpaper_engine_config", "")
        except:
            return ""
        
    def 自动查找路径(self):
        path = find_wallpaper_engine_path_advanced()
        if path:
            path = os.path.join(path, "config.json")
            log.val(path)
            return path
        else:
            log.error("未能自动找到壁纸引擎路径")
            return None
    def 验证路径(self, path):
        # 验证路径是否存在，查找config.json文件是否存在
        if not path:
            return False
        
        # 检查路径是否存在
        if not os.path.exists(path):
            return False
        
        if os.path.basename(path) != "config.json":
            # 如果路径是目录，检查其中是否有config.json
            if os.path.isdir(path):
                config_path = os.path.join(path, "config.json")
                if os.path.exists(config_path):
                    path = config_path
                else:
                    return False
            else:
                return False
        
        # 如果路径有效，保存至config.toml文件
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config.toml")
            if not os.path.exists(config_path):
                config_data = {"path": {"wallpaper_engine_config": path}}
            else:
                # 如果文件存在，读取并更新
                config_data = toml.load(config_path)
                if "path" not in config_data:
                    config_data["path"] = {}
                config_data["path"]["wallpaper_engine_config"] = path
            
            # 保存配置
            with open(config_path, "w", encoding="utf-8") as f:
                toml.dump(config_data, f)
            
            return True
        except Exception as e:
            log.error(f"保存路径失败: {e}")
            return False
    def 路径预览选择(self, path):#BUG 多次连续触发崩溃
        try:
            
            
            # 创建一个临时的tk根窗口
            root = tk.Tk()
            root.withdraw()  # 隐藏窗口
            
            # 打开文件选择对话框
            file_path = filedialog.askopenfilename(
                title="选择 Wallpaper Engine 配置文件",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
                initialdir=os.path.dirname(path) if path else ""
            )
            
            root.destroy()  # 销毁临时窗口
            
            # 直接返回选择的路径
            return file_path
        except Exception as e:
            log.error(f"文件选择失败: {e}")
            return None
    def 全屏暂停(self, status):
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config.toml")
            if not os.path.exists(config_path):
                config_data = {"config": {"pause_on_fullscreen": status}}
            else:
                config_data = toml.load(config_path)
                if "config" not in config_data:
                    config_data["config"] = {}
                config_data["config"]["pause_on_fullscreen"] = status
            
            # 保存配置
            with open(config_path, "w", encoding="utf-8") as f:
                toml.dump(config_data, f)
            
            return True
        except Exception as e:
            log.error(f"设置全屏暂停状态失败: {e}")
            return False
    def 全屏暂停状态(self):
        # 获取全屏暂停状态
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config.toml")
            if not os.path.exists(config_path):
                return False
            
            config_data = toml.load(config_path)
            return config_data.get("config", {}).get("pause_on_fullscreen", False)
        except Exception as e:
            log.error(f"获取全屏暂停状态失败: {e}")
            return False
    def 清理缓存(self):
        # 清理主目录下的cache文件夹和html\cache文件夹内的所有文件
        try:
            # 清理主目录下的cache文件夹
            main_cache_dir = os.path.join(os.path.dirname(__file__), "cache")
            if os.path.exists(main_cache_dir):
                for root, dirs, files in os.walk(main_cache_dir, topdown=False):
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        os.remove(file_path)
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        os.rmdir(dir_path)
                log.info("主目录缓存清理完成")
            
            # 清理html\cache文件夹
            html_cache_dir = os.path.join(os.path.dirname(__file__), "html", "cache")
            if os.path.exists(html_cache_dir):
                for file_name in os.listdir(html_cache_dir):
                    file_path = os.path.join(html_cache_dir, file_name)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                log.info("HTML缓存清理完成")
            
            log.info("缓存清理完成")
            return True
        except Exception as e:
            log.error(f"清理缓存失败: {e}")
            return False

    def get_cursor_status(self):
        return True

    def get_cursor_status(self):
        return True

    def preview_path(self, path):
        return os.path.exists(path) if path else False

if __name__ == "__main__":
    api = SettingsApi()

    window = webview.create_window("设置", "html/settingsUI.html", js_api=api, width=950, height=650)
    api.set_window(window)
    if log.on_DEBUG:
        webview.start(debug=True)
    else:
        webview.start()
