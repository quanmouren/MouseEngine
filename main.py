import threading
import time
import random
from src.Tlog import TLog 
import inspect
import os
import time
import getpass
import toml
from src.getWallpaperConfig import 获取当前壁纸 
from src.mouses import get_current_monitor_index_minimal 
from src.setMouse import 设置鼠标指针 
import psutil



PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH = "config.toml"

MOUSE_THEMES_DIR = "mouses" 

CURSOR_ORDER_MAPPING = [
    "Arrow", "Help", "AppStarting", "Wait", "Crosshair", "IBeam", 
    "Handwriting", "No", "SizeNS", "SizeWE", "SizeNWSE", "SizeNESW", 
    "SizeAll", "Hand", "UpArrow"
]

log = TLog("main")


def 获得函数名():
    frame = inspect.currentframe()
    if frame is not None and frame.f_back is not None:
        return frame.f_back.f_code.co_name
    log.error("无法获取函数名")
    return None


def 触发刷新():
    """
    根据当前鼠标所在显示器的壁纸 ID，自动加载并应用对应的鼠标指针主题。
    """
    log = TLog("触发刷新")
    winUserName = getpass.getuser()
    
    try:
        main_config = toml.load(CONFIG_FILE_PATH)
        config_path_we = main_config.get("path", {}).get("wallpaper_engine_config", "")
        enable_default = main_config.get("config", {}).get("enable_default_icon_group", False)
        wallpaper_map = main_config.get("wallpaper", {})
    except FileNotFoundError:
        log.error(f"读取主配置文件失败: {CONFIG_FILE_PATH} 未找到。")
        return False
    except Exception as e:
        log.error(f"读取主配置文件失败: {e}")
        return False
        

    monitor_index = get_current_monitor_index_minimal()
    log.debug(f"当前鼠标位于显示器索引: {monitor_index}")
    
    try:
        wallpaper_info = 获取当前壁纸(config_path_we, winUserName)
        if 0 <= monitor_index < len(wallpaper_info):
            当前鼠标指针id = wallpaper_info[monitor_index][1] 
        else:
            log.error(f"获取当前壁纸信息失败，索引 {monitor_index} 超出范围。")
            当前鼠标指针id = None
    except Exception as e:
        log.error(f"获取当前壁纸信息异常: {e}")
        当前鼠标指针id = None

    log.debug(f"当前鼠标指针id: {当前鼠标指针id}")
    
    
    target_theme_name = None
    
    if 当前鼠标指针id:
        target_theme_name = wallpaper_map.get(str(当前鼠标指针id))

    if target_theme_name:
        log.info(f"找到对应主题名称: {target_theme_name}")
        theme_config_path = os.path.join(MOUSE_THEMES_DIR, target_theme_name, "config.toml")
    else:
        log.info(f"未找到壁纸 ID {当前鼠标指针id} 对应的自定义主题。")
        theme_config_path = None
        
    
    if theme_config_path and os.path.exists(theme_config_path):
        config_to_load = theme_config_path
        log.debug(f"加载自定义主题配置: {config_to_load}")
    elif enable_default:
        config_to_load = os.path.join(MOUSE_THEMES_DIR, "默认", "config.toml")
        log.info(f"启用默认图标组，加载默认配置: {config_to_load}")
    else:
        log.info("未找到主题配置，且未启用默认图标组，跳过设置。")
        return True 
    
    if not os.path.exists(config_to_load):
        log.error(f"配置文件不存在: {config_to_load}。无法设置鼠标指针。")
        return False

    try:
        theme_config = toml.load(config_to_load)
        mouse_config = theme_config.get("mouses", {})

        cursor_paths_list = []
        for key in CURSOR_ORDER_MAPPING:
            path = mouse_config.get(key, "")
            cursor_paths_list.append(path)
            
        log.debug(f"生成的 cursor_paths 列表长度: {len(cursor_paths_list)}")
        
        if 设置鼠标指针(cursor_paths_list):
            log.info("鼠标指针主题设置成功。")
            return True
        else:
            log.error("设置鼠标指针主题失败。")
            return False
            
    except Exception as e:
        log.error(f"处理鼠标主题配置或设置指针失败: {e}")
        return False

def json监听():
    log = TLog(获得函数名())
    winUserName = getpass.getuser()
    
    try:
        config_data = toml.load(CONFIG_FILE_PATH)
        config_path = config_data.get("path", {}).get("wallpaper_engine_config", "")
    except FileNotFoundError:
        log.error(f"错误：{CONFIG_FILE_PATH} 文件未找到。请检查路径。")
        return
    except KeyError:
        log.error("错误：config.toml 缺少必要的 'path' -> 'wallpaper_engine_config' 键。")
        return

    wallpaperConfig = 获取当前壁纸(config_path, winUserName)
    
    current_state = {index: project[1] for index, project in enumerate(wallpaperConfig)}

    log.info("初始壁纸状态:")
    for index, project_id in current_state.items():
        log.info(f"显示器{index}: {project_id}")
    
    触发刷新()

    try:
        while True:
            log.debug("正在监听...")
            latest_wallpaperConfig = 获取当前壁纸(config_path, winUserName)
            
            for index, project in enumerate(latest_wallpaperConfig):
                latest_project_id = project[1]
                
                if index in current_state:
                    previous_project_id = current_state[index]
                    
                    if latest_project_id != previous_project_id:
                        log.info(f"显示器 {index} 壁纸已更换 (ID: {previous_project_id} ->> {latest_project_id})")
                        current_state[index] = latest_project_id
                        触发刷新()
                else:
                    log.info(f"发现新的显示器 {index}，项目ID: {latest_project_id}")
                    current_state[index] = latest_project_id
                    触发刷新()
            
            
            time.sleep(1)


    except KeyboardInterrupt:
        log.info("监听线程停止。")
    except Exception as e:
        log.info(f"监听过程中发生错误: {e}")


def 运行占用监控():
    if not psutil:
        return 
        
    CURRENT_PROCESS = psutil.Process(os.getpid())
    MONITOR_INTERVAL = 3
    monitor_log = TLog(获得函数名()) 
    last_metrics = None 
    last_monitor_time = time.time()
    try:
        while True:
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
                            return "<r" # 红色标签
                        elif current_val < last_val:
                            return "<g" # 绿色标签
                        else:
                            return "" # 无色标签

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
                except Exception as e:
                    monitor_log.error(f"获取性能数据时发生错误: {e}")
                    
                last_monitor_time = current_time

            time.sleep(max(0, MONITOR_INTERVAL - (time.time() - current_time))) 

    except KeyboardInterrupt:
        monitor_log.info("监控线程停止。")
        
    monitor_log.info("监控任务结束。")



t1 = threading.Thread(target=json监听)
t2 = threading.Thread(target=运行占用监控)

t1.start()
t2.start()


t1.join()
t2.join()