import webview
import os
import toml
from Tlog import TLog
import platform
import re 
import tkinter as tk
from tkinter import filedialog
from path_utils import resolve_path, get_project_root
try:
    import psutil
except ImportError:
    psutil = None
try:
    if platform.system() == "Windows":
        import winreg
        import win32com.client
        import win32gui
        import win32process
    else:
        winreg = None
        win32com = None
        win32gui = None
        win32process = None
except ImportError:
    winreg = None
    win32com = None
    win32gui = None
    win32process = None
import shutil
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
        try:
            if platform.system() != "Windows":
                return False
            
            # 获取启动文件夹路径
            startup_folder = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            shortcut_path = os.path.join(startup_folder, 'MouseEngine.lnk')
            
            # 检查快捷方式是否存在
            exists = os.path.exists(shortcut_path)
            log.val(f"自启动快捷方式存在: {exists}")
            return exists
        except Exception as e:
            log.error(f"获取自启动状态失败: {e}")
            return False
    
    def set_auto_start(self, enabled):
        try:
            if platform.system() != "Windows" or win32com is None:
                return False
            
            # 获取启动文件夹路径
            startup_folder = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            shortcut_path = os.path.join(startup_folder, 'MouseEngine.lnk')
            
            if enabled:
                # 尝试多个可能的路径查找 MouseEngine.exe
                possible_paths = [
                    # 尝试在项目根目录的上级目录
                    os.path.join(os.path.dirname(get_project_root()), "MouseEngine.exe"),
                    # 尝试在项目根目录
                    os.path.join(get_project_root(), "MouseEngine.exe"),
                    # 尝试在当前工作目录
                    os.path.join(os.getcwd(), "MouseEngine.exe"),
                    # 尝试在当前文件所在目录
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "MouseEngine.exe")
                ]
                
                exe_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        exe_path = path
                        break
                
                if not exe_path:
                    log.error(f"未找到 MouseEngine.exe。尝试的路径: {possible_paths}")
                    return False
                
                # 创建快捷方式
                shell = win32com.client.Dispatch('WScript.Shell')
                shortcut = shell.CreateShortcut(shortcut_path)
                shortcut.TargetPath = exe_path
                shortcut.WorkingDirectory = os.path.dirname(exe_path)
                shortcut.Description = "MouseEngine 自启动"
                shortcut.Save()
                log.info(f"已创建自启动快捷方式: {shortcut_path}")
            else:
                # 删除快捷方式
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                    log.info(f"已删除自启动快捷方式: {shortcut_path}")
                else:
                    log.info("自启动快捷方式不存在，无需删除")
            
            return True
        except Exception as e:
            log.error(f"设置自启动失败: {e}")
            return False

    def get_wp_path(self):
        config_path = resolve_path("config.toml")
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
            config_path = resolve_path("config.toml")
            # 无论文件是否存在，都先尝试加载现有配置
            if os.path.exists(config_path):
                config_data = toml.load(config_path)
            else:
                config_data = {}
            
            # 确保 path 部分存在
            if "path" not in config_data:
                config_data["path"] = {}
            
            # 更新 wallpaper_engine_config 的值
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
            config_path = resolve_path("config.toml")
            # 无论文件是否存在，都先尝试加载现有配置
            if os.path.exists(config_path):
                config_data = toml.load(config_path)
            else:
                config_data = {}
            
            # 确保 config 部分存在
            if "config" not in config_data:
                config_data["config"] = {}
            
            # 更新 pause_on_fullscreen 的值
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
            config_path = resolve_path("config.toml")
            if not os.path.exists(config_path):
                return False
            
            config_data = toml.load(config_path)
            return config_data.get("config", {}).get("pause_on_fullscreen", False)
        except Exception as e:
            log.error(f"获取全屏暂停状态失败: {e}")
            return False
    def 严格窗口判定(self, status):
        try:
            config_path = resolve_path("config.toml")
            # 尝试加载现有配置
            if os.path.exists(config_path):
                config_data = toml.load(config_path)
            else:
                config_data = {}
            
            # 确保config部分存在
            if "config" not in config_data:
                config_data["config"] = {}
            
            # 更新strict_window_judgment的值
            config_data["config"]["strict_window_judgment"] = status
            
            # 保存配置
            with open(config_path, "w", encoding="utf-8") as f:
                toml.dump(config_data, f)
            
            return True
        except Exception as e:
            log.error(f"设置严格窗口判定状态失败: {e}")
            return False
    def 严格窗口判定状态(self):
        # 获取状态
        try:
            config_path = resolve_path("config.toml")
            if not os.path.exists(config_path):
                return False
            
            config_data = toml.load(config_path)
            return config_data.get("config", {}).get("strict_window_judgment", False)
        except Exception as e:
            log.error(f"获取严格窗口判定状态失败: {e}")
            return False
    
    def get_show_more_menu(self):
        # 获取显示更多菜单内容状态
        try:
            config_path = resolve_path("config.toml")
            if not os.path.exists(config_path):
                return False
            
            config_data = toml.load(config_path)
            return config_data.get("config", {}).get("show_more_menu", False)
        except Exception as e:
            log.error(f"获取显示更多菜单内容状态失败: {e}")
            return False
    
    def set_show_more_menu(self, status):
        try:
            config_path = resolve_path("config.toml")
            # 无论文件是否存在，都先尝试加载现有配置
            if os.path.exists(config_path):
                config_data = toml.load(config_path)
            else:
                config_data = {}
            
            # 确保 config 部分存在
            if "config" not in config_data:
                config_data["config"] = {}
            
            # 更新 show_more_menu 的值
            config_data["config"]["show_more_menu"] = status
            
            # 保存配置
            with open(config_path, "w", encoding="utf-8") as f:
                toml.dump(config_data, f)
            
            return True
        except Exception as e:
            log.error(f"设置显示更多菜单内容状态失败: {e}")
            return False
    def 清理缓存(self):
        # 清理主目录下的cache文件夹和html\cache文件夹内的所有文件
        try:
            # 清理主目录下的cache文件夹
            main_cache_dir = resolve_path("cache")
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
            html_cache_dir = resolve_path("html/cache")
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

    def set_enable_default_icon_group(self, status):
        try:
            config_path = resolve_path("config.toml")
            # 无论文件是否存在，都先尝试加载现有配置
            if os.path.exists(config_path):
                config_data = toml.load(config_path)
            else:
                config_data = {}
            
            # 确保 config 部分存在
            if "config" not in config_data:
                config_data["config"] = {}
            
            # 更新 enable_default_icon_group 的值
            config_data["config"]["enable_default_icon_group"] = status
            
            # 保存配置
            with open(config_path, "w", encoding="utf-8") as f:
                toml.dump(config_data, f)
            
            return True
        except Exception as e:
            log.error(f"设置默认图标组状态失败: {e}")
            return False
    
    def get_enable_default_icon_group(self):
        # 获取默认图标组状态
        try:
            config_path = resolve_path("config.toml")
            if not os.path.exists(config_path):
                return True
            
            config_data = toml.load(config_path)
            return config_data.get("config", {}).get("enable_default_icon_group", True)
        except Exception as e:
            log.error(f"获取默认图标组状态失败: {e}")
            return True

    def preview_path(self, path):
        return os.path.exists(path) if path else False

    def get_third_party_notices(self):
        try:
            notices_path = resolve_path("FINAL_THIRD_PARTY_NOTICES.txt")
            log.info(f"尝试读取第三方许可证文件: {notices_path}")
            if os.path.exists(notices_path):
                log.info(f"找到第三方许可证文件: {notices_path}")
                with open(notices_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                log.info(f"成功读取第三方许可证文件，长度: {len(content)} 字符")
                return content
            else:
                log.warning(f"第三方许可证文件不存在: {notices_path}")
                return "FINAL_THIRD_PARTY_NOTICES.txt 文件不存在"
        except Exception as e:
            log.error(f"读取第三方许可证文件失败: {e}")
            return "读取第三方许可证文件失败"

    def get_program_whitelist(self):
        try:
            config_path = resolve_path("config.toml")
            if not os.path.exists(config_path):
                return {}
            
            config_data = toml.load(config_path)
            return config_data.get("program_whitelist", {})
        except Exception as e:
            log.error(f"获取程序白名单失败: {e}")
            return {}

    def add_program_whitelist(self, program, cursor_group):
        try:
            config_path = resolve_path("config.toml")
            # 加载现有配置
            if os.path.exists(config_path):
                config_data = toml.load(config_path)
            else:
                config_data = {}
            
            # 确保 program_whitelist 部分存在
            if "program_whitelist" not in config_data:
                config_data["program_whitelist"] = {}
            
            # 添加或更新绑定
            config_data["program_whitelist"][program] = cursor_group
            
            # 保存配置
            with open(config_path, "w", encoding="utf-8") as f:
                toml.dump(config_data, f)
            
            log.info(f"添加程序白名单: {program} -> {cursor_group}")
            return True
        except Exception as e:
            log.error(f"添加程序白名单失败: {e}")
            return False

    def delete_program_whitelist(self, program):
        try:
            config_path = resolve_path("config.toml")
            # 加载现有配置
            if os.path.exists(config_path):
                config_data = toml.load(config_path)
            else:
                config_data = {}
            
            # 确保 program_whitelist 部分存在
            if "program_whitelist" in config_data:
                # 删除绑定
                if program in config_data["program_whitelist"]:
                    del config_data["program_whitelist"][program]
                    
                    # 保存配置
                    with open(config_path, "w", encoding="utf-8") as f:
                        toml.dump(config_data, f)
                    
                    log.info(f"删除程序白名单: {program}")
                    return True
            
            return False
        except Exception as e:
            log.error(f"删除程序白名单失败: {e}")
            return False



    def get_cursor_groups(self):
        try:
            from path_utils import resolve_path
            import glob
            import os
            MOUSE_BASE_PATH = resolve_path("mouses")
            groups = []
            # 使用绝对路径搜索
            search_pattern = os.path.join(MOUSE_BASE_PATH, '*', 'config.toml')
            config_files = glob.glob(search_pattern)
            for file_path in config_files:
                group_name = os.path.basename(os.path.dirname(file_path))
                groups.append(group_name)
            return sorted(groups) if groups else ["默认"]
        except Exception as e:
            log.error(f"获取光标组失败: {e}")
            return ["默认"]


    def get_all_windows(self):
        try:
            if win32gui is None or win32process is None:
                log.error("win32gui 或 win32process 模块不可用")
                return []
            if psutil is None:
                log.error("psutil 模块不可用")
                return []
            
            windows = []
            
            def enum_windows_callback(hwnd, windows):
                # 只处理可见窗口
                if win32gui.IsWindowVisible(hwnd):
                    # 获取窗口标题
                    title = win32gui.GetWindowText(hwnd)
                    if title:
                        try:
                            # 获取进程ID
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            # 获取进程名
                            proc = psutil.Process(pid)
                            proc_name = proc.name()
                            windows.append({
                                "title": title,
                                "process_name": proc_name
                            })
                        except Exception:
                            pass
            
            # 枚举所有窗口
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            # 去重
            seen_processes = set()
            unique_windows = []
            for window in windows:
                if window["process_name"] not in seen_processes:
                    seen_processes.add(window["process_name"])
                    unique_windows.append(window)
            
            return unique_windows
        except Exception as e:
            log.error(f"获取所有窗口失败: {e}")
            return []
    
    def 设置默认组为Windows默认光标(self):
        try:
            MOUSE_BASE_PATH = resolve_path("mouses")
            default_path = os.path.join(MOUSE_BASE_PATH, "默认")
            
            if os.path.exists(default_path):
                shutil.rmtree(default_path)
                log.info(f"已删除原默认光标组: {default_path}")
            
            os.makedirs(default_path, exist_ok=True)
            
            cursor_files = {
                "Arrow": "aero_arrow.cur",
                "Help": "aero_helpsel.cur",
                "AppStarting": "aero_working.ani",
                "Wait": "aero_busy.ani",
                "Crosshair": "cross_i.cur",
                "IBeam": "beam_i.cur",
                "Handwriting": "aero_pen.cur",
                "No": "aero_unavail.cur",
                "SizeNS": "aero_ns.cur",
                "SizeWE": "aero_ew.cur",
                "SizeNWSE": "aero_nwse.cur",
                "SizeNESW": "aero_nesw.cur",
                "SizeAll": "aero_move.cur",
                "Hand": "aero_link.cur",
                "UpArrow": "aero_up.cur"
            }
            
            windows_cursors_path = os.path.join(os.environ.get("WINDIR", "C:\Windows"), "Cursors")
            
            config_path = os.path.join(default_path, "config.toml")
            config_content = "[mouses]\n"
            for cursor_name, cursor_file in cursor_files.items():
                cursor_path = os.path.join(windows_cursors_path, cursor_file)
                if os.path.exists(cursor_path):
                    cursor_path = cursor_path.replace('\\', '\\\\')
                    config_content += f'{cursor_name} = "{cursor_path}"\n'
                else:
                    config_content += f'{cursor_name} = ""\n'
            
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(config_content)
            log.info(f"已创建默认光标配置文件：{config_path}")
            
            log.info(f"已成功将默认组设置为Windows默认光标：{config_path}")
            return True
        except Exception as e:
            log.error(f"设置默认组为Windows默认光标失败: {e}")
            return False


if __name__ == "__main__":
    api = SettingsApi()

    # 获取 HTML 文件的绝对路径
    html_file = resolve_path("html/settingsUI.html")
    window = webview.create_window("设置", html_file, js_api=api, width=950, height=650)
    api.set_window(window)
    if log.on_DEBUG:
        webview.start(debug=True)
    else:
        webview.start()
