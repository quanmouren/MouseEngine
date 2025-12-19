import threading
import time
import inspect
import os
import time
import getpass
import toml
import psutil
import sys
from src.Tlog import TLog
from src.getWallpaperConfig import 获取当前壁纸
from src.mouses import get_current_monitor_index_minimal
from src.setMouse import 设置鼠标指针
from ui.settings_ui import open_settings_window
from src.Initialize import initialize_config
initialize_config()

try:
    from pystray import Icon, Menu, MenuItem
    from PIL import Image
    TRAY_AVAILABLE = True
except ImportError:
    print("[ERROR] 缺少 pystray 或 Pillow 库。请运行 'pip install pystray Pillow' 来启用系统托盘。")
    TRAY_AVAILABLE = False
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)
try:
    from ui.main_gui import App as ConfigApp 
    from ui.playlist_gui import App as PlaylistApp 
    UI_IMPORT_SUCCESS = True
except ImportError as e:
    print(f"[ERROR] 无法导入 UI 模块。请确保 ui/main_gui.py 和 ui/playlist_gui.py 存在。\n错误信息: {e}")
    UI_IMPORT_SUCCESS = False


stop_flag = threading.Event() 
global_threads = []
TRAY_ICON = None

CONFIG_FILE_PATH = "config.toml"
MOUSE_THEMES_DIR = "mouses"
CURSOR_ORDER_MAPPING = [
    "Arrow", "Help", "AppStarting", "Wait", "Crosshair", "IBeam",
    "Handwriting", "No", "SizeNS", "SizeWE", "SizeNWSE", "SizeNESW",
    "SizeAll", "Hand", "UpArrow"
]

log = TLog("main")

def start_thread(target_func, name):
    t = threading.Thread(target=target_func, name=name)
    t.daemon = True 
    t.start()
    global_threads.append(t)
    return t

def 获得函数名():
    frame = inspect.currentframe()
    if frame is not None and frame.f_back is not None:
        return frame.f_back.f_code.co_name
    log.error("无法获取函数名")
    return None

def run_ui_in_thread(UI_App_Class, title):
    """在一个新线程中运行指定的UI应用程序类"""
    if not UI_IMPORT_SUCCESS:
        log.error(f"UI 启动失败: 模块导入不成功，请检查文件路径和依赖。")
        return
        
    def ui_target():
        log.info(f"启动 UI: {title}")
        
        try:
            app = UI_App_Class()
            app.mainloop() 
            
        except Exception as e:
            log.error(f"启动 UI 线程 {title} 时发生错误: {e}")

        log.info(f"UI 线程 {title} 退出。")

    start_thread(ui_target, f"{title}_UI_Thread")

def open_config_mouse_gui(icon="icon300.png", item=None):
    """打开 '配置鼠标组' UI"""
    run_ui_in_thread(ConfigApp, "配置鼠标组")

def open_bind_mouse_gui(icon=None, item=None):
    """打开 '绑定鼠标组' UI"""
    run_ui_in_thread(PlaylistApp, "绑定鼠标组")

def open_settings_ui(icon=None, item=None):
    open_settings_window() 

def on_exit_request(icon, item):
    """安全退出所有线程和程序"""
    
    log.info("收到退出请求。开始安全关闭所有后台线程...")
    stop_flag.set()

    if TRAY_ICON:
        TRAY_ICON.stop()

def setup_pystray_icon():
    """设置 pystray 系统托盘图标和菜单"""
    global TRAY_ICON
    
    if not TRAY_AVAILABLE:
        log.error("系统托盘功能未启用。主程序将通过 time.sleep 循环运行。")
        return None
    
    icon_path = os.path.join(PROJECT_ROOT, "icon300.png")
    if not os.path.exists(icon_path):
        log.error(f"图标文件未找到: {icon_path}。请在项目根目录放置一个 icon.png 文件。")
        image = Image.new('RGB', (64, 64), color='black') 
    else:
        image = Image.open(icon_path)
        try:
            image.thumbnail((64, 64), Image.Resampling.LANCZOS)
        except AttributeError:
            image.thumbnail((64, 64), Image.ANTIALIAS) 

    menu = Menu(
        MenuItem('配置鼠标组', open_config_mouse_gui, enabled=UI_IMPORT_SUCCESS),
        MenuItem('绑定鼠标组', open_bind_mouse_gui, enabled=UI_IMPORT_SUCCESS),
        #MenuItem('设置', open_settings_ui),
        Menu.SEPARATOR,
        MenuItem('退出', on_exit_request)
        )

    TRAY_ICON = Icon("MouseEngine", image, "壁纸鼠标主题切换器", menu)
    
    return TRAY_ICON

def 触发刷新():
    log_func = TLog("触发刷新")
    winUserName = getpass.getuser()

    try:
        main_config = toml.load(CONFIG_FILE_PATH)
        config_path_we = main_config.get("path", {}).get("wallpaper_engine_config", "")
        enable_default = main_config.get("config", {}).get("enable_default_icon_group", False)
        wallpaper_map = main_config.get("wallpaper", {})
    except FileNotFoundError:
        log_func.error(f"读取主配置文件失败: {CONFIG_FILE_PATH} 未找到。")
        return False
    except Exception as e:
        log_func.error(f"读取主配置文件失败: {e}")
        return False


    monitor_index = get_current_monitor_index_minimal()
    log_func.debug(f"当前鼠标位于显示器索引: {monitor_index}")

    try:
        wallpaper_info = 获取当前壁纸(config_path_we, winUserName)
        if 0 <= monitor_index < len(wallpaper_info):
            当前鼠标指针id = wallpaper_info[monitor_index][1]
        else:
            log_func.error(f"获取当前壁纸信息失败，索引 {monitor_index} 超出范围。")
            当前鼠标指针id = None
    except Exception as e:
        log_func.error(f"获取当前壁纸信息异常: {e}")
        当前鼠标指针id = None

    log_func.debug(f"当前鼠标指针id: {当前鼠标指针id}")


    target_theme_name = None

    if 当前鼠标指针id:
        target_theme_name = wallpaper_map.get(str(当前鼠标指针id))

    if target_theme_name:
        log_func.info(f"找到对应主题名称: {target_theme_name}")
        theme_config_path = os.path.join(MOUSE_THEMES_DIR, target_theme_name, "config.toml")
    else:
        log_func.info(f"未找到壁纸 ID {当前鼠标指针id} 对应的自定义主题。")
        theme_config_path = None


    if theme_config_path and os.path.exists(theme_config_path):
        config_to_load = theme_config_path
        log_func.debug(f"加载自定义主题配置: {config_to_load}")
    elif enable_default:
        config_to_load = os.path.join(MOUSE_THEMES_DIR, "默认", "config.toml")
        log_func.info(f"启用默认图标组，加载默认配置: {config_to_load}")
    else:
        log_func.info("未找到主题配置，且未启用默认图标组，跳过设置。")
        return True

    if not os.path.exists(config_to_load):
        log_func.error(f"配置文件不存在: {config_to_load}。无法设置鼠标指针。")
        return False

    try:
        theme_config = toml.load(config_to_load)
        mouse_config = theme_config.get("mouses", {})

        cursor_paths_list = []
        for key in CURSOR_ORDER_MAPPING:
            path = mouse_config.get(key, "")
            cursor_paths_list.append(path)

        log_func.debug(f"生成的 cursor_paths 列表长度: {len(cursor_paths_list)}")

        if 设置鼠标指针(cursor_paths_list):
            log_func.info("鼠标指针主题设置成功。")
            return True
        else:
            log_func.error("设置鼠标指针主题失败。")
            return False

    except Exception as e:
        log_func.error(f"处理鼠标主题配置或设置指针失败: {e}")
        return False

def json监听():
    log_func = TLog(获得函数名())
    winUserName = getpass.getuser()

    try:
        config_data = toml.load(CONFIG_FILE_PATH)
        config_path = config_data.get("path", {}).get("wallpaper_engine_config", "")
    except FileNotFoundError:
        log_func.error(f"错误：{CONFIG_FILE_PATH} 文件未找到。请检查路径。")
        return
    except KeyError:
        log_func.error("错误：config.toml 缺少必要的 'path' -> 'wallpaper_engine_config' 键。")
        return

    # 首次加载壁纸信息
    try:
        wallpaperConfig = 获取当前壁纸(config_path, winUserName)
    except Exception as e:
        log_func.error(f"首次获取壁纸配置失败: {e}")
        return
    
    current_state = {index: project[1] for index, project in enumerate(wallpaperConfig)}

    log_func.info("初始壁纸状态:")
    for index, project_id in current_state.items():
        log_func.info(f"显示器{index}: {project_id}")

    触发刷新() # 首次刷新

    try:
        while not stop_flag.is_set(): # 检查停止标志
            log_func.debug("正在监听...")
            latest_wallpaperConfig = 获取当前壁纸(config_path, winUserName)

            for index, project in enumerate(latest_wallpaperConfig):
                latest_project_id = project[1]

                if index in current_state:
                    previous_project_id = current_state[index]

                    if latest_project_id != previous_project_id:
                        log_func.info(f"显示器 {index} 壁纸已更换 (ID: {previous_project_id} ->> {latest_project_id})")
                        current_state[index] = latest_project_id
                        触发刷新()
                else:
                    log_func.info(f"发现新的显示器 {index}，项目ID: {latest_project_id}")
                    current_state[index] = latest_project_id
                    触发刷新()


            time.sleep(1)


    except Exception as e:
        log_func.info(f"监听过程中发生错误: {e}")

    log_func.info("json监听任务结束。")


def 运行占用监控():
    if not psutil:
        return

    CURRENT_PROCESS = psutil.Process(os.getpid())
    MONITOR_INTERVAL = 3
    monitor_log = TLog(获得函数名())
    last_metrics = None
    last_monitor_time = time.time()
    try:
        while not stop_flag.is_set(): # 检查停止标志
            current_time = time.time()
            if current_time - last_monitor_time >= MONITOR_INTERVAL:
                try:
                    cpu_percent = CURRENT_PROCESS.cpu_percent(interval=None)
                    memory_info = CURRENT_PROCESS.memory_info()
                    mem_rss_mb = memory_info.rss / (1024 * 1024)
                    num_threads = CURRENT_PROCESS.num_threads()

                    current_metrics = [cpu_percent, mem_rss_mb, num_threads]

                    def get_color_tag(current_val, last_val):
                        if last_val is None:
                            return ""
                        if current_val > last_val:
                            return "<r" 
                        elif current_val < last_val:
                            return "<g" 
                        else:
                            return "" 

                    if last_metrics is not None:
                        cpu_tag = get_color_tag(cpu_percent, last_metrics[0])
                        mem_tag = get_color_tag(mem_rss_mb, last_metrics[1])
                        thread_tag = get_color_tag(num_threads, last_metrics[2])
                    else:
                        cpu_tag, mem_tag, thread_tag = "", "", ""

                    monitor_log.info(f"CPU 占用率: {cpu_tag}{cpu_percent:.2f}%>, 内存占用: {mem_tag}{mem_rss_mb:.2f} MB>, 线程数: {thread_tag}{num_threads}>")

                    last_metrics = current_metrics

                except psutil.NoSuchProcess:
                    monitor_log.error("进程不存在，无法获取性能数据。")
                    stop_flag.set()
                    break
                except Exception as e:
                    monitor_log.error(f"获取性能数据时发生错误: {e}")

                last_monitor_time = current_time

            if not stop_flag.is_set():
                 time.sleep(max(0, 0.1)) 

    except Exception as e:
        monitor_log.info(f"监控过程中发生错误: {e}")

    monitor_log.info("监控任务结束。")

if __name__ == "__main__":

    # 启动后台线程
    t1 = start_thread(json监听, "JsonListener")
    t2 = start_thread(运行占用监控, "ResourceMonitor")

    log.info("所有后台线程已启动。")

    # 启动系统托盘
    tray_icon = setup_pystray_icon()

    if tray_icon:
        log.info("系统托盘图标已启动。")
        try:
            tray_icon.run()
        except Exception as e:
            log.error(f"系统托盘运行时发生错误: {e}")
            stop_flag.set()
    else:
        log.info("程序将在无系统托盘模式下运行。使用 Ctrl+C 或任务管理器退出。")
        try:
            while not stop_flag.wait(timeout=1):
                pass
        except KeyboardInterrupt:
            log.info("主程序接收到 KeyboardInterrupt (Ctrl+C)。")
            stop_flag.set()
    log.info("等待后台线程结束...")
    for t in [t1, t2]:
        if t.is_alive():
            log.info(f"正在等待 {t.name} 退出...")
            t.join(timeout=5)

    log.info("程序已安全退出。")