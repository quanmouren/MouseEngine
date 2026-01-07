import threading
import time
import inspect
import os
import getpass
import toml
import sys
import subprocess
try:
    import psutil
except Exception:
    psutil = None

from Tlog import TLog
from getWallpaperConfig import 获取当前壁纸
from mouses import get_current_monitor_index_minimal
from setMouse import 设置鼠标指针
from settingsUI import open_settings_window
from Initialize import initialize_config

initialize_config()

try:
    from pystray import Icon, Menu, MenuItem
    from PIL import Image
    TRAY_AVAILABLE = True
except ImportError:
    print("[ERROR] 缺少 pystray 或 Pillow 库。请运行 'pip install pystray Pillow' 来启用系统托盘。")
    TRAY_AVAILABLE = False

UI_IMPORT_SUCCESS = True

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

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
active_ui_processes = {}  


def _script_abs_path(filename: str) -> str:
    return os.path.join(PROJECT_ROOT, filename)


def _kill_process(p: subprocess.Popen, timeout_sec: float = 2.0):
    """尽力结束子进程（Windows 上 terminate 就够用；必要时 kill）"""
    try:
        if p is None:
            return
        if p.poll() is not None:
            return
        p.terminate()
        t0 = time.time()
        while time.time() - t0 < timeout_sec:
            if p.poll() is not None:
                return
            time.sleep(0.05)
        try:
            p.kill() # 强杀
        except Exception:
            pass
    except Exception:
        pass


def run_ui_in_process(script_filename: str, title: str):
    """用独立进程启动 UI，避免 Tk/CTk 在线程里反复创建导致越来越卡"""
    if not UI_IMPORT_SUCCESS:
        log.error("UI 启动失败: 模块导入不成功，请检查文件路径和依赖。")
        return
    old = active_ui_processes.get(title)
    if old and old.poll() is None:
        log.warning(f"UI '{title}' 已经在运行中，请勿重复点击。")
        return

    script_path = _script_abs_path(script_filename)
    if not os.path.exists(script_path):
        log.error(f"UI 脚本不存在：{script_path}")
        return

    try:
        p = subprocess.Popen(
            [sys.executable, script_path],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        active_ui_processes[title] = p
        log.info(f"启动 UI 进程: {title} (pid={p.pid})")
    except Exception as e:
        log.error(f"启动 UI 进程失败 {title}: {e}")


def open_config_mouse_gui(icon=None, item=None):
    """打开 '配置鼠标组' UI"""
    run_ui_in_process("mainUI.py", "配置鼠标组")


def open_bind_mouse_gui(icon=None, item=None):
    """打开 '绑定鼠标组' UI"""
    run_ui_in_process("playlistUI.py", "绑定鼠标组")


def open_settings_ui(icon=None, item=None):
    open_settings_window()

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


def on_exit_request(icon, item):
    """安全退出所有线程和程序"""
    log.info("收到退出请求。开始安全关闭所有后台线程...")
    stop_flag.set()

    # 停托盘
    try:
        if TRAY_ICON:
            TRAY_ICON.stop()
    except Exception:
        pass

    for title, p in list(active_ui_processes.items()):
        try:
            if p and p.poll() is None:
                log.info(f"正在关闭 UI 进程: {title} (pid={p.pid})")
                _kill_process(p)
        except Exception:
            pass
        finally:
            active_ui_processes.pop(title, None)


def setup_pystray_icon():
    """设置 pystray 系统托盘图标和菜单"""
    global TRAY_ICON

    if not TRAY_AVAILABLE:
        log.error("系统托盘功能未启用。主程序将通过 time.sleep 循环运行。")
        return None

    icon_path = os.path.join(PROJECT_ROOT, "icon300.ico")
    if not os.path.exists(icon_path):
        log.error(f"图标文件未找到: {icon_path}。缺失 icon300.ico文件")
        image = Image.new("RGB", (64, 64), color="black")
    else:
        image = Image.open(icon_path)
        try:
            image.thumbnail((64, 64), Image.Resampling.LANCZOS)
        except AttributeError:
            image.thumbnail((64, 64), Image.ANTIALIAS)

    menu = Menu(
        MenuItem("配置鼠标组", open_config_mouse_gui, enabled=UI_IMPORT_SUCCESS),
        MenuItem("绑定鼠标组", open_bind_mouse_gui, enabled=UI_IMPORT_SUCCESS),
        # MenuItem("设置", open_settings_ui),
        Menu.SEPARATOR,
        MenuItem("退出", on_exit_request),
    )

    TRAY_ICON = Icon("MouseEngine", image, "光标引擎", menu)
    return TRAY_ICON

def 触发刷新(target_wallpaper_id=None, changed_monitor_index=None):
    log_func = TLog("触发刷新")
    try:
        main_cfg = toml.load(CONFIG_FILE_PATH)
        enable_default = bool(main_cfg.get("config", {}).get("enable_default_icon_group", False))
        wallpaper_map = main_cfg.get("wallpaper", {}) or {}
    except FileNotFoundError:
        log_func.error(f"读取主配置失败: {CONFIG_FILE_PATH} 未找到。")
        return False
    except Exception as e:
        log_func.error(f"读取主配置失败: {e}")
        return False

    if target_wallpaper_id is None:
        log_func.error("未提供 target_wallpaper_id，无法按“刷新事件”应用主题。")
        return False

    target_id_str = str(target_wallpaper_id).strip()
    if not target_id_str:
        log_func.error("target_wallpaper_id 为空字符串，无法应用主题。")
        return False

    if changed_monitor_index is not None:
        log_func.debug(f"收到刷新事件：显示器 {changed_monitor_index} - 壁纸ID {target_id_str}")
    else:
        log_func.debug(f"收到刷新事件：壁纸ID {target_id_str}")

    theme_value = wallpaper_map.get(target_id_str)

    if not theme_value:
        log_func.info(f"未找到壁纸 ID {target_id_str} 对应的自定义主题。")
        if not enable_default:
            log_func.info("未启用默认图标组，跳过。")
            return False
        theme_dir = os.path.join("mouses", "默认")
        log_func.info(f"启用默认图标组，加载默认配置: {theme_dir}\\config.toml")
    else:
        theme_dir = str(theme_value).strip().strip('"').strip("'")
        theme_dir = theme_dir.replace("/", os.sep).replace("\\", os.sep)
        if (os.sep not in theme_dir) and (not theme_dir.lower().startswith("mouses")):
            theme_dir = os.path.join("mouses", theme_dir)

    try:
        group_config_path = os.path.join(theme_dir, "config.toml")
        if not os.path.exists(group_config_path):
            log_func.error(f"配置文件不存在: {group_config_path}（theme_dir={theme_dir}）")
            return False

        group_cfg = toml.load(group_config_path)

        if "mouses" not in group_cfg or not isinstance(group_cfg["mouses"], dict):
            log_func.error(f"配置缺少 [mouses] 段或格式错误: {group_config_path}")
            return False

        mouses_section = group_cfg["mouses"]

        order = [
            "Arrow", "Help", "AppStarting", "Wait", "Crosshair",
            "IBeam", "Handwriting", "No", "SizeNS", "SizeWE",
            "SizeNWSE", "SizeNESW", "SizeAll", "Hand", "UpArrow"
        ]

        cursor_paths_list = []
        for name in order:
            raw = mouses_section.get(name, "")
            rel = str(raw).strip().strip('"').strip("'") if raw is not None else ""
            rel = rel.replace("/", os.sep).replace("\\", os.sep)

            if not rel:
                cursor_paths_list.append("")
                continue

            cursor_paths_list.append(rel)

        log_func.debug(f"生成的 cursor_paths 列表长度: {len(cursor_paths_list)}")

        ok = 设置鼠标指针(cursor_paths_list)
        if ok:
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
        latest_wallpaperConfig = 获取当前壁纸(config_path, winUserName)
    except Exception as e:
        log_func.error(f"读取 Wallpaper Engine 配置失败: {e}")
        return

    current_state = {}
    for index, project in enumerate(latest_wallpaperConfig):
        current_state[index] = project[1]

    log_func.info("初始壁纸状态:")
    for index, project_id in current_state.items():
        log_func.info(f"显示器{index}: {project_id}")

    first_id = current_state.get(0)
    if first_id is None and len(current_state) > 0:
        first_id = next(iter(current_state.values()))
    if first_id is not None:
        触发刷新(first_id, changed_monitor_index=0)

    # 循环监听
    try:
        while not stop_flag.is_set():
            log_func.debug("正在监听...")
            latest_wallpaperConfig = 获取当前壁纸(config_path, winUserName)

            for index, project in enumerate(latest_wallpaperConfig):
                latest_project_id = project[1]
                old_id = current_state.get(index)

                if old_id != latest_project_id:
                    log_func.info(f"显示器 {index} 壁纸已更换 (ID: {old_id} -> {latest_project_id})")
                    current_state[index] = latest_project_id

                    触发刷新(latest_project_id, changed_monitor_index=index)

            time.sleep(1)

    except Exception as e:
        log_func.error(f"监听循环异常: {e}")
        return


def 运行占用监控():
    if not psutil:
        return

    CURRENT_PROCESS = psutil.Process(os.getpid())
    MONITOR_INTERVAL = 3
    monitor_log = TLog(获得函数名())
    last_metrics = None
    last_monitor_time = time.time()

    try:
        while not stop_flag.is_set():
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

                    monitor_log.info(
                        f"CPU 占用率: {cpu_tag}{cpu_percent:.2f}%>, 内存占用: {mem_tag}{mem_rss_mb:.2f} MB>, 线程数: {thread_tag}{num_threads}>"
                    )

                    last_metrics = current_metrics

                except psutil.NoSuchProcess:
                    monitor_log.error("进程不存在，无法获取性能数据。")
                    stop_flag.set()
                    break
                except Exception as e:
                    monitor_log.error(f"获取性能数据时发生错误: {e}")

                last_monitor_time = current_time

            if not stop_flag.is_set():
                time.sleep(0.1)

    except Exception as e:
        monitor_log.info(f"监控过程中发生错误: {e}")

    monitor_log.info("监控任务结束。")


if __name__ == "__main__":
    # 启动后台线程
    t1 = start_thread(json监听, "JsonListener")
    if log.on_DEBUG == True:
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

    for title, p in list(active_ui_processes.items()):
        try:
            if p and p.poll() is None:
                _kill_process(p)
        except Exception:
            pass

    log.info("程序已安全退出。")
