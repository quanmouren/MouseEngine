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
        try:
            if platform.system() != "Windows" or winreg is None:
                return False
            
            # 检查自启动注册表项
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            try:
                # 尝试读取 MouseEngine 项
                value, _ = winreg.QueryValueEx(key, "MouseEngine")
                log.val(f"自启动项值: {value}")
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            log.error(f"获取自启动状态失败: {e}")
            return False
    
    def set_auto_start(self, enabled):
        try:
            if platform.system() != "Windows" or winreg is None:
                return False
            
            # 打开自启动注册表项
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            
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
                    winreg.CloseKey(key)
                    return False
                
                # 设置自启动项
                winreg.SetValueEx(key, "MouseEngine", 0, winreg.REG_SZ, f'"{exe_path}"')
                log.info(f"已设置自启动: {exe_path}")
            else:
                # 删除自启动项
                try:
                    winreg.DeleteValue(key, "MouseEngine")
                    log.info("已取消自启动")
                except FileNotFoundError:
                    # 项不存在，无需处理
                    pass
            
            winreg.CloseKey(key)
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
