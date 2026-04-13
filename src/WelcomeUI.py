# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: BSD-3-Clause
import webview
from threading import Thread
from Tlog import TLog
log = TLog("MouseEngineWelcomeUI")
import os
import platform
import re
import sys
from path_utils import resolve_path

try:
    if platform.system() == "Windows":
        import winreg
    else:
        winreg = None
except ImportError:
    winreg = None

log.on_DEBUG = True


def get_version_from_path(exe_path):
    version_file = os.path.join(os.path.dirname(exe_path), "version.toml")
    if os.path.exists(version_file):
        try:
            import toml
            version_data = toml.load(version_file)
            return version_data.get("__version__", None)
        except Exception:
            pass
    return None

def check_other_versions_in_startup():
    startup_folder = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
    
    if not os.path.exists(startup_folder):
        return []
    
    current_exe_path = sys.executable
    current_exe_name = os.path.basename(current_exe_path).lower()
    
    other_versions = []
    
    try:
        for filename in os.listdir(startup_folder):
            if filename.lower().startswith('mouseengine') and filename.endswith('.lnk'):
                shortcut_path = os.path.join(startup_folder, filename)
                
                try:
                    import win32com.client
                    shell = win32com.client.Dispatch('WScript.Shell')
                    shortcut = shell.CreateShortcut(shortcut_path)
                    target_path = shortcut.TargetPath
                    
                    target_name = os.path.basename(target_path).lower()
                    
                    if target_name != current_exe_name and target_name.endswith('.exe'):
                        version = get_version_from_path(target_path)
                        
                        other_versions.append({
                            'shortcut_name': filename,
                            'shortcut_path': shortcut_path,
                            'target_path': target_path,
                            'target_name': target_name,
                            'version': version if version else "过时的版本"
                        })
                except Exception as e:
                    log.warning(f"读取快捷方式 {filename} 失败: {e}")
    except Exception as e:
        log.error(f"检查启动文件夹失败: {e}")
    
    return other_versions


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


class UpgradeApi:
    def __init__(self, on_upgrade_callback, on_skip_callback, window_ref):
        self.on_upgrade_callback = on_upgrade_callback
        self.on_skip_callback = on_skip_callback
        self._window = window_ref

    def get_old_versions(self):
        return check_other_versions_in_startup()

    def get_current_version(self):
        try:
            version_path = resolve_path("version.toml")
            if os.path.exists(version_path):
                import toml
                version_data = toml.load(version_path)
                return version_data.get("__version__", "Beta1.3")
            return "Beta1.3"
        except Exception as e:
            log.error(f"获取版本失败: {e}")
            return "Beta1.3"

    def cleanup_old_versions(self):
        try:
            versions = check_other_versions_in_startup()
            
            if not versions:
                return {"success": True, "message": "没有旧版本需要清理", "count": 0}
            
            deleted_count = 0
            for version in versions:
                shortcut_path = version.get('shortcut_path')
                if shortcut_path and os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                    deleted_count += 1
                    log.info(f"已删除旧版本快捷方式: {shortcut_path}")
            
            print(f"[模拟升级] 已清理 {deleted_count} 个旧版本")
            return {"success": True, "message": f"已清理 {deleted_count} 个旧版本", "count": deleted_count}
        except Exception as e:
            log.error(f"清理旧版本失败: {e}")
            return {"success": False, "message": str(e), "count": 0}

    def close_window(self):
        try:
            if self._window:
                self._window.destroy()
        except Exception as e:
            log.error(f"关闭窗口失败: {e}")

    def on_upgrade_clicked(self):
        self.on_upgrade_callback()
        self.close_window()

    def on_skip_clicked(self):
        self.on_skip_callback()
        self.close_window()


win = None
upgrade_win = None

def run_upgrade_check():
    old_versions = check_other_versions_in_startup()
    
    if not old_versions:
        log.info("没有发现旧版本，跳过升级检查")
        return False
    
    log.info(f"发现 {len(old_versions)} 个旧版本，显示升级确认界面")
    
    result = [False]
    
    def on_upgrade():
        print("[升级流程] 用户点击了一键升级")
        result[0] = True
    
    def on_skip():
        print("[升级流程] 用户点击了跳过")
        result[0] = False
    
    global upgrade_win
    upgrade_api = UpgradeApi(on_upgrade, on_skip, None)
    html_file = resolve_path("html/upgradeConfirm.html")
    upgrade_win = webview.create_window("版本升级", html_file, js_api=upgrade_api, width=600, height=360, resizable=False)
    upgrade_api._window = upgrade_win
    webview.start(http_server=True)
    
    return result[0]


def get_wallpaper_engine_path_ui():
    # 检查是否有旧版本需要升级
    #run_upgrade_check()
    
    # 继续显示欢迎界面
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
