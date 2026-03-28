# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: BSD-3-Clause
import threading
import time
import inspect
import os
import getpass
import toml
import sys
import subprocess
import win32gui
import win32process
from getActiveWallpaper import get_active_ids
#from test_测试句柄更新 import get_active_ids_optimized as get_active_ids
try:
    import psutil
except Exception:
    psutil = None

from Tlog import TLog
from getWallpaperConfig import 获取当前壁纸列表
from mouses import get_current_monitor_index_minimal
from setMouse import 设置鼠标指针
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

from path_utils import get_project_root
PROJECT_ROOT = get_project_root()

stop_flag = threading.Event()
global_threads = []
TRAY_ICON = None
initial_loading_done = False
last_in_whitelist = None  # 跟踪上一次焦点窗口是否在白名单中

from path_utils import resolve_path
CONFIG_FILE_PATH = resolve_path("config.toml")
MOUSE_THEMES_DIR = resolve_path("mouses")
CURSOR_ORDER_MAPPING = [
    "Arrow", "Help", "AppStarting", "Wait", "Crosshair", "IBeam",
    "Handwriting", "No", "SizeNS", "SizeWE", "SizeNWSE", "SizeNESW",
    "SizeAll", "Hand", "UpArrow"
]

log = TLog("main")
active_ui_processes = {}  
def get_process_name():
    """获取当前焦点窗口的进程名"""
    try:
        # 获取当前前台窗口句柄
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            # 获取进程ID
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                # 获取进程名
                proc = psutil.Process(pid)
                proc_name = proc.name()
                return proc_name
            except psutil.NoSuchProcess:
                return "N/A"
    except Exception as e:
        return "N/A"

def _script_abs_path(filename: str) -> str:
    path = os.path.join(PROJECT_ROOT, filename)
    log.val(f"filename={filename}, path={path}")
    return path


def _kill_process(p: subprocess.Popen, timeout_sec: float = 2.0):
    """尽力结束子进程"""
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
            stdout=None,  
            stderr=None,
        )
        active_ui_processes[title] = p
        log.info(f"启动 UI 进程: {title} (pid={p.pid})")
    except Exception as e:
        log.error(f"启动 UI 进程失败 {title}: {e}")

def open_bind_mouse_gui_test(icon="icon300.ico", item=None):
    """打开 '绑定鼠标组' UI"""
    run_ui_in_process("mainUIWeb.py", "绑定鼠标组")

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


def open_config_mouse_gui(icon=None, item=None):
    """打开 '配置鼠标组' UI"""
    run_ui_in_process("mouseUI.py", "配置鼠标组")


def open_bind_mouse_gui(icon="icon300.ico", item=None):
    """打开 '绑定鼠标组' UI"""
    run_ui_in_process("mainUIWeb.py", "绑定鼠标组")


def open_settings_ui(icon=None, item=None):
    """打开 '设置' UI"""
    run_ui_in_process("settingsUIWeb.py", "设置")

def setup_pystray_icon():
    """设置 pystray 系统托盘图标和菜单"""
    global TRAY_ICON

    if not TRAY_AVAILABLE:
        log.error("系统托盘功能未启用。主程序将通过 time.sleep 循环运行。")
        return None

    icon_path = os.path.join(PROJECT_ROOT, "icon300.ico")
    log.val(f"icon_path={icon_path}")
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
        MenuItem("设置", open_settings_ui, enabled=UI_IMPORT_SUCCESS),
        Menu.SEPARATOR,
        MenuItem("退出", on_exit_request),
    )

    TRAY_ICON = Icon("MouseEngine", image, "光标引擎", menu)
    return TRAY_ICON

def 触发刷新(target_wallpaper_id=None, changed_monitor_index=None):
    log_func = TLog("触发刷新")
    try:
        log_func.val(f"CONFIG_FILE_PATH={CONFIG_FILE_PATH}")
        main_cfg = toml.load(CONFIG_FILE_PATH)
        enable_default = bool(main_cfg.get("config", {}).get("enable_default_icon_group", False))
        wallpaper_map = main_cfg.get("wallpaper", {}) or {}
        program_whitelist = main_cfg.get("program_whitelist", {}) or {}
    except FileNotFoundError:
        log_func.error(f"读取主配置失败: {CONFIG_FILE_PATH} 未找到。")
        return False
    except Exception as e:
        log_func.error(f"读取主配置失败: {e}")
        return False

    # 程序白名单检查
    current_process_name = get_process_name()
    if current_process_name:
        log_func.debug(f"当前焦点程序: {current_process_name}")
        whitelist_theme = program_whitelist.get(current_process_name)
        if whitelist_theme:
            theme_dir = str(whitelist_theme).strip().strip('"').strip("'")
            theme_dir = theme_dir.replace("/", os.sep).replace("\\", os.sep)
            if (os.sep not in theme_dir) and (not theme_dir.lower().startswith("mouses")):
                theme_dir = os.path.join(MOUSE_THEMES_DIR, theme_dir)
            log_func.info(f"程序白名单匹配: {current_process_name} -> {theme_dir}")
            log_func.val(f"theme_dir={theme_dir}")
            
            # 直接使用白名单主题，跳过壁纸ID匹配
            try:
                group_config_path = os.path.join(theme_dir, "config.toml")
                log_func.val(f"group_config_path={group_config_path}")
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
                    log_func.info("鼠标指针主题设置成功（程序白名单）。")
                    return True
                else:
                    log_func.error("设置鼠标指针主题失败。")
                    return False

            except Exception as e:
                log_func.error(f"处理鼠标主题配置或设置指针失败: {e}")
                return False
        else:
            log_func.debug(f"程序 {current_process_name} 不在白名单中，继续使用壁纸ID匹配")
    else:
        log_func.debug("无法获取当前焦点程序名，继续使用壁纸ID匹配")

    if target_wallpaper_id is None:
        log_func.debug("未提供 target_wallpaper_id，尝试获取当前活跃壁纸ID")
        try:
            # 尝试获取当前活跃的壁纸ID
            active_ids = get_active_ids()
            if active_ids:
                target_wallpaper_id = list(active_ids)[0]
                log_func.info(f"获取到当前活跃壁纸ID: {target_wallpaper_id}")
            else:
                log_func.error("未获取到活跃壁纸ID，无法应用主题。")
                return False
        except Exception as e:
            log_func.error(f"获取活跃壁纸ID失败: {e}")
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
            log_func.error("未启用默认图标组，跳过。")
            return False
        theme_dir = os.path.join(MOUSE_THEMES_DIR, "默认")
        log_func.val(f"theme_dir={theme_dir}")
        log_func.info(f"启用默认图标组，加载默认配置: {theme_dir}\\config.toml")
    else:
        theme_dir = str(theme_value).strip().strip('"').strip("'")
        theme_dir = theme_dir.replace("/", os.sep).replace("\\", os.sep)
        if (os.sep not in theme_dir) and (not theme_dir.lower().startswith("mouses")):
            theme_dir = os.path.join(MOUSE_THEMES_DIR, theme_dir)
        log_func.val(f"theme_dir={theme_dir}")

    try:
        group_config_path = os.path.join(theme_dir, "config.toml")
        log_func.val(f"group_config_path={group_config_path}")
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

LAST_JSON_TRIGGER_TIME = 0 # ram更新锁

# 保存活跃壁纸ID到temp_storage.toml文件
def save_active_wallpaper_id(wallpaper_id, log_func):
    """
    保存活跃壁纸ID到temp_storage.toml文件
    Args:
        wallpaper_id: 壁纸ID
        log_func: 日志函数
    """
    from path_utils import resolve_path
    temp_storage_path = resolve_path('temp_storage.toml')
    log.val(f"temp_storage_path={temp_storage_path}")
    
    try:
        # 读取现有内容或创建新内容
        if os.path.exists(temp_storage_path):
            with open(temp_storage_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)
        else:
            data = {}
        
        # 确保 [Wallpaper Engine] 部分存在
        if 'Wallpaper Engine' not in data:
            data['Wallpaper Engine'] = {}
        
        # 保存 active 项
        data['Wallpaper Engine']['active'] = wallpaper_id
        
        # 写回文件
        with open(temp_storage_path, 'w', encoding='utf-8') as f:
            toml.dump(data, f)
    except Exception as e:
        log_func.error(f"保存文件失败: {e}")

def json监听():
    global LAST_JSON_TRIGGER_TIME
    global initial_loading_done
    log_func = TLog(获得函数名())
    winUserName = getpass.getuser()

    # 加载配置路径
    try:
        log_func.val(f"CONFIG_FILE_PATH={CONFIG_FILE_PATH}")
        config_data = toml.load(CONFIG_FILE_PATH)
        config_path = config_data.get("path", {}).get("wallpaper_engine_config", "")
        log_func.val(f"config_path={config_path}")
    except FileNotFoundError:
        log_func.error(f"错误：{CONFIG_FILE_PATH} 未找到。")
        return
    except KeyError:
        log_func.error("错误：config.toml 缺少必要的路径配置。")
        return

    # 首次加载壁纸信息
    try:
        latest_wallpaperConfig = 获取当前壁纸列表(config_path, winUserName)
    except Exception as e:
        log_func.error(f"读取配置失败: {e}")
        return

    current_state = {}
    for index, project in enumerate(latest_wallpaperConfig):
        current_state[index] = project[1]

    # 当RAM首次加载失败时初始触发一次
    if current_state and not initial_loading_done:
        first_id = current_state.get(0) or next(iter(current_state.values()))
        log_func.info(f"Json初始状态触发: {first_id}")
        
        # 保存到 temp_storage.toml 文件
        save_active_wallpaper_id(first_id, log_func)
        
        LAST_JSON_TRIGGER_TIME = time.time()  # 更新时间戳
        触发刷新(first_id, changed_monitor_index=0)
        initial_loading_done = True
        log_func.info("首次加载成功")

    # 循环监听
    try:
        while not stop_flag.is_set():#TODO 暂未对json做全屏暂停
            latest_wallpaperConfig = 获取当前壁纸列表(config_path, winUserName)

            for index, project in enumerate(latest_wallpaperConfig):
                latest_project_id = project[1]
                old_id = current_state.get(index)

                if old_id != latest_project_id:
                    log_func.info(f"显示器 {index} (Json) 壁纸更换: {old_id} -> {latest_project_id}")
                    current_state[index] = latest_project_id
                    
                    # 保存到 temp_storage.toml 文件
                    save_active_wallpaper_id(latest_project_id, log_func)
                    
                    # 更新全局时间戳，通知RAM监听器进入10s冷却期
                    LAST_JSON_TRIGGER_TIME = time.time()
                    触发刷新(latest_project_id, changed_monitor_index=index)

            time.sleep(1)
    except Exception as e:
        log_func.error(f"Json监听循环异常: {e}")


def 焦点监听():
    """
    监听焦点窗口变化
    使用状态锁避免不必要的刷新
    """
    global last_in_whitelist
    log_func = TLog(获得函数名())
    log_func.info("初始化焦点监听器")
    
    last_process_name = None
    check_count = 0
    
    try:
        while not stop_flag.is_set():
            try:
                current_process_name = get_process_name()
                check_count += 1
                
                if check_count % 25 == 0:
                    log_func.debug(f"焦点监听运行中，当前焦点: {current_process_name}")
                
                if current_process_name != last_process_name:
                    if last_process_name is not None:
                        log_func.info(f"焦点窗口变化: {last_process_name} -> {current_process_name}")
                    else:
                        log_func.info(f"初始焦点窗口: {current_process_name}")
                    
                    last_process_name = current_process_name
                    
                    # 检查当前和上一次进程是否在白名单中
                    try:
                        main_cfg = toml.load(CONFIG_FILE_PATH)
                        program_whitelist = main_cfg.get("program_whitelist", {}) or {}
                        
                        current_in_whitelist = current_process_name in program_whitelist
                        last_in_whitelist_value = last_in_whitelist
                        
                        if last_in_whitelist_value is None:
                            # 首次运行触发刷新
                            log_func.debug("首次运行，触发刷新")
                            触发刷新(target_wallpaper_id=None, changed_monitor_index=None)
                            last_in_whitelist = current_in_whitelist
                        elif current_in_whitelist != last_in_whitelist_value:
                            # 白名单状态发生变化
                            log_func.debug(f"白名单状态变化: {last_in_whitelist_value} -> {current_in_whitelist}，触发刷新")
                            触发刷新(target_wallpaper_id=None, changed_monitor_index=None)
                            last_in_whitelist = current_in_whitelist
                        elif current_in_whitelist and last_in_whitelist_value:
                            # 都在白名单中
                            log_func.debug(f"白名单内切换: {last_process_name} -> {current_process_name}，触发刷新")
                            触发刷新(target_wallpaper_id=None, changed_monitor_index=None)
                            last_in_whitelist = current_in_whitelist
                        else:
                            # 都不在白名单中
                            log_func.debug(f"都不在白名单中，跳过刷新")
                            last_in_whitelist = current_in_whitelist
                    
                    except Exception as e:
                        log_func.error(f"检查白名单状态失败: {e}")
                        # 容错
                        触发刷新(target_wallpaper_id=None, changed_monitor_index=None)
                
            except Exception as e:
                log_func.error(f"焦点监听异常: {e}")
            
            time.sleep(0.5)
    
    except Exception as e:
        log_func.error(f"焦点监听循环异常: {e}")


def ram监听():
    """
    基于进程句柄监听播放列表状态
    受Json触发后的10秒冷却保护
    """
    global LAST_JSON_TRIGGER_TIME
    global initial_loading_done
    log_func = TLog(获得函数名())
    log_func.info("初始化 RAM 监听器")

    # 首次加载壁纸信息
    try:
        last_active_ids = get_active_ids()
    except Exception as e:
        log_func.error(f"首次获取 RAM 列表失败: {e}")
        last_active_ids = set()

    # 初始显示
    if last_active_ids and not initial_loading_done:
        log_func.info(f"RAM初始检测到活跃 ID: {last_active_ids}")
        # 检查是否启用全屏暂停
        try:
            main_cfg = toml.load(CONFIG_FILE_PATH)
            pause_on_fullscreen = bool(main_cfg.get("config", {}).get("pause_on_fullscreen", False))
            if pause_on_fullscreen and is_fullscreen_app_running():
                log_func.info("检测到全屏应用，跳过初始触发")
            else:
                initial_id = list(last_active_ids)[0]
                save_active_wallpaper_id(initial_id, log_func)
                触发刷新(initial_id, changed_monitor_index=0)
                initial_loading_done = True
                log_func.info("首次加载成功（使用RAM）")
        except Exception as e:
            log_func.error(f"读取配置失败: {e}")
            initial_id = list(last_active_ids)[0]
            save_active_wallpaper_id(initial_id, log_func)
            触发刷新(initial_id, changed_monitor_index=0)
            initial_loading_done = True
            log_func.info("首次加载成功")

    # 循环监听
    try:
        while not stop_flag.is_set():
            # 检查是否启用全屏暂停
            try:
                main_cfg = toml.load(CONFIG_FILE_PATH)
                pause_on_fullscreen = bool(main_cfg.get("config", {}).get("pause_on_fullscreen", False))
                if pause_on_fullscreen and is_fullscreen_app_running():
                    log_func.debug("检测到全屏应用，跳过RAM检测")
                    time.sleep(10)
                    continue
            except Exception as e:
                log_func.error(f"读取配置失败: {e}")
            
            current_ids = get_active_ids()
            # 检测是否有新ID出现
            new_ids = current_ids - last_active_ids
            
            if new_ids:
                # 检查是否处于冷近期
                cooldown_remaining = 10 - (time.time() - LAST_JSON_TRIGGER_TIME)
                
                if cooldown_remaining > 0:
                    log_func.debug(f"处于Json冷却期(剩余 {cooldown_remaining:.1f}s)，跳过RAM触发: {new_ids}")
                    # 同步状态，防止多次触发
                    last_active_ids = current_ids
                else:
                    for latest_id in new_ids:
                        log_func.info(f"检测到RAM活跃变更: {latest_id}")
                        
                        # 保存到 temp_storage.toml 文件
                        save_active_wallpaper_id(latest_id, log_func)
                        
                        触发刷新(latest_id, changed_monitor_index=0)
                    last_active_ids = current_ids
            
            # 对集合数量变化，同步集合状态
            elif last_active_ids != current_ids:
                last_active_ids = current_ids

            time.sleep(10)
    except Exception as e:
        log_func.error(f"RAM监听循环异常: {e}")

def is_fullscreen_app_running():
    """
    检测是否有应用程序在全屏运行
    """
    try:
        import win32gui
        import win32api
        
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindow(hwnd):
                # 获取窗口矩形
                rect = win32gui.GetWindowRect(hwnd)
                # 获取屏幕尺寸
                screen_width = win32api.GetSystemMetrics(0)
                screen_height = win32api.GetSystemMetrics(1)
                # 检查窗口是否覆盖整个屏幕
                window_width = rect[2] - rect[0]
                window_height = rect[3] - rect[1]
                # 检测全屏窗口
                is_fullscreen = (window_width == screen_width and window_height == screen_height and 
                               rect[0] == 0 and rect[1] == 0)
                # 检测最大化窗口
                is_maximized = (window_width >= screen_width - 20 and 
                              window_height >= screen_height - 20 and
                              rect[0] <= 10 and rect[1] <= 10)
                
                if is_fullscreen or is_maximized:
                    # 排除桌面窗口、任务栏和其他系统窗口
                    class_name = win32gui.GetClassName(hwnd)
                    window_title = win32gui.GetWindowText(hwnd)
                    
                    # 排除系统窗口
                    if class_name in ['Progman', 'WorkerW', 'Shell_TrayWnd', 'DwmWnd']:
                        return
                    
                    # 排除没有标题的窗口
                    if not window_title:
                        return
                    
                    # 排除某些特定的窗口类
                    if 'Windows.UI.Core' in class_name or 'ApplicationFrameWindow' in class_name:
                        return
                    
                    # 记录窗口类型
                    window_type = "全屏" if is_fullscreen else "最大化"
                    extra.append((hwnd, class_name, window_title, window_type))
        
        fullscreen_windows = []
        win32gui.EnumWindows(callback, fullscreen_windows)
        
        if fullscreen_windows:
            window_info = []
            for hwnd, class_name, window_title, window_type in fullscreen_windows:
                window_info.append(f"{window_type} - {class_name} - {window_title}")
            log.debug(f"检测到全屏/最大化窗口: {len(fullscreen_windows)}个 - {window_info}")
        
        return len(fullscreen_windows) > 0
    except Exception as e:
        log.error(f"检测全屏/最大化应用失败: {e}")
        return False

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
    t2 = None
    if log.on_DEBUG == True:
        t2 = start_thread(运行占用监控, "ResourceMonitor")
    t3 = start_thread(ram监听, "RamListener")
    t4 = start_thread(焦点监听, "FocusListener")
    
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
    for t in [t1, t2, t3]:
        if t and t.is_alive():
            log.info(f"正在等待 {t.name} 退出...")
            t.join(timeout=5)

    for title, p in list(active_ui_processes.items()):
        try:
            if p and p.poll() is None:
                _kill_process(p)
        except Exception:
            pass

    # 退出前设置为默认鼠标组
    try:
        from path_utils import resolve_path
        import toml
        MOUSE_BASE_PATH = resolve_path("mouses")
        default_config_path = os.path.join(MOUSE_BASE_PATH, "默认", "config.toml")
        if os.path.exists(default_config_path):
            config = toml.load(default_config_path)
            mouse_values = [config['mouses'].get(k, "") for k in CURSOR_ORDER_MAPPING]
            设置鼠标指针(mouse_values)
            log.info("已恢复为默认鼠标组")
        else:
            log.debug("默认鼠标组配置文件不存在，跳过恢复操作")
    except Exception as e:
        log.error(f"恢复默认鼠标组失败: {e}")

    log.info("程序已安全退出。")
