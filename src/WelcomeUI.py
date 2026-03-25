# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: BSD-3-Clause
import webview
from threading import Thread
from Tlog import TLog
log = TLog("MouseEngineWelcomeUI")
import os
import platform
import re
from path_utils import resolve_path

try:
    if platform.system() == "Windows":
        import winreg
    else:
        winreg = None
except ImportError:
    winreg = None

log.on_DEBUG = True

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
            log.error(f"解析 libraryfolders.vdf 时出错: {e}")
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

class Api:
    def __init__(self, on_path_selected_callback):
        self.on_path_selected_callback = on_path_selected_callback
    
    def auto_find_wallpaper_engine(self):
        try:
            found_path = find_wallpaper_engine_path_advanced()
            if found_path:
                return {"success": True, "path": found_path}
            else:
                return {"success": False, "message": "未找到 Wallpaper Engine 路径"}
        except Exception as e:
            log.error(f"自动查找失败: {e}")
            return {"success": False, "message": str(e)}
    
    def browse_folder(self):
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            initial_dir = os.path.expanduser("~") if platform.system() != "Windows" else "C:\\"
            folder_path = filedialog.askdirectory(
                title="选择 Wallpaper Engine 根目录", 
                initialdir=initial_dir
            )
            root.destroy()
            if folder_path:
                return {"success": True, "path": folder_path}
            else:
                return {"success": False, "message": "未选择文件夹"}
        except Exception as e:
            log.error(f"浏览文件夹失败: {e}")
            return {"success": False, "message": str(e)}
    
    def validate_path(self, path):
        try:
            if not path:
                return {"success": False, "message": "请输入 Wallpaper Engine 的安装路径。"}
            
            validation_path = os.path.join(path, "wallpaper64.exe")
            if not os.path.exists(validation_path):
                return {"success": False, "message": f"在所选路径中未找到关键文件 'wallpaper64.exe'。\n请确保路径指向 Wallpaper Engine 的根目录。"}
            
            return {"success": True}
        except Exception as e:
            log.error(f"验证路径失败: {e}")
            return {"success": False, "message": str(e)}
    
    def confirm_path(self, path, use_default_cursor=True):
        try:
            self.on_path_selected_callback(path, use_default_cursor)
        except Exception as e:
            log.error(f"确认路径失败: {e}")
    
    def exit_app(self):
        try:
            if win:
                win.destroy()
            log.info("欢迎界面已安全退出")
        except Exception as e:
            log.error(f"退出欢迎界面时出错: {e}")

win = None

def get_wallpaper_engine_path_ui():
    result = [None, True]
    
    def on_path_selected(path, use_default_cursor=True):
        result[0] = path
        result[1] = use_default_cursor
        if win:
            win.destroy()
    
    api = Api(on_path_selected)
    main_html_path = resolve_path("html/welcomeUIWeb.html")
    
    global win
    win = webview.create_window(
        "欢迎！应用程序配置向导",
        main_html_path,
        js_api=api,
        width=600,
        height=360,
        resizable=False,
        easy_drag=True
    )
    
    webview.start(debug=False, http_server=True)
    return result[0], result[1]

if __name__ == "__main__":
    final_path, use_default_cursor = get_wallpaper_engine_path_ui()
    
    if final_path:
        print(f"路径: {final_path}")
        print(f"使用默认光标: {use_default_cursor}")
    else:
        pass
        # sys.exit()
