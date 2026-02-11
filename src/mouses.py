# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: BSD-3-Clause
import os
import shutil
import toml
try:
    import portalocker
except ImportError:
    portalocker = None
    print("警告：未安装 portalocker，可能出现并发文件访问问题.请运行 'pip install portalocker'")





from Tlog import TLog
from getWallpaperConfig import 获取当前壁纸列表
from setMouse import 设置鼠标指针, CURSOR_ORDER_MAPPING

from screeninfo import get_monitors
import pyautogui

log = TLog("mouses")

CONFIG_PATH = "config.toml"
MOUSE_BASE_PATH = "mouses"

def load_toml_config(path=CONFIG_PATH):
    """加载顶层 config.toml 文件"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return toml.load(f)
    except FileNotFoundError:
        log.error(f"配置文件未找到: {path}")
        return {}
    except Exception as e:
        log.error(f"加载主配置文件失败: {e}")
        return {}

def wallpaper(wallpaper_id: str, config_path=CONFIG_PATH) -> str:
    """根据壁纸 ID 获取对应的鼠标组名称"""
    config = load_toml_config(config_path)
    return config.get('wallpaper', {}).get(wallpaper_id, False)

def get_current_monitor_index_minimal():
    """
    获取鼠标当前所在的显示器索引（从 0 开始）。
    """
    try:
        current_x, current_y = pyautogui.position()
        monitors = get_monitors()
        for i, monitor in enumerate(monitors):
            if monitor.x <= current_x < monitor.x + monitor.width and \
               monitor.y <= current_y < monitor.y + monitor.height:
                return i
        return 0
    except Exception as e:
        log.error(f"获取当前显示器索引失败: {e}")
        return 0

def 触发刷新(config_path, username, monitor=None):
    """
    根据当前显示器壁纸应用鼠标配置。
    :param config_path: wallpaper_engine 配置路径
    :param username: 用户名
    :param monitor: (可选) 显示器编号 (1-based)。如果为 None，则自动检测。
    """
    if monitor is None:
        monitor_index = get_current_monitor_index_minimal()
    else:
        monitor_index = monitor - 1

    # 获取所有壁纸数据
    all_wallpapers = 获取当前壁纸列表(config_path, username)
    if not all_wallpapers:
        log.error("无法获取壁纸配置，触发刷新失败。")
        return False
        
    # 获取当前显示器的壁纸数据
    if 0 <= monitor_index < len(all_wallpapers):
        path, last_folder, _, _ = all_wallpapers[monitor_index] 
    else:
        log.error(f"无效的显示器索引: {monitor_index}，使用第一个显示器的数据。")
        path, last_folder, _, _ = all_wallpapers[0] if all_wallpapers else (None, None, None, None)

    if not last_folder:
        log.info("当前壁纸ID为空，尝试应用默认配置。")
        # 尝试应用默认
        group_name = None
    else:
        # 查找对应的鼠标组
        group_name = wallpaper(last_folder, CONFIG_PATH)
    
    # 应用配置逻辑
    target_config_path = None
    
    if group_name:
        target_config_path = os.path.join(MOUSE_BASE_PATH, group_name, "config.toml")
        if not os.path.exists(target_config_path):
            log.debug(f"绑定组 '{group_name}' 配置文件不存在，尝试回退到默认。")
            target_config_path = None
    
    # 回退到默认配置
    if not target_config_path:
        default_path = os.path.join(MOUSE_BASE_PATH, "默认", "config.toml")
        if os.path.exists(default_path):
            target_config_path = default_path
            log.debug("使用默认鼠标组配置。")
    
    if target_config_path:
        try:
            config = toml.load(target_config_path)
            # 按照 CURSOR_ORDER_MAPPING 顺序提取路径
            mouse_values = [config['mouses'].get(k, "") for k in CURSOR_ORDER_MAPPING]
            设置鼠标指针(mouse_values)
            if group_name:
                log.info(f"成功应用鼠标组: {group_name}")
            return True
        except Exception as e:
            log.error(f"应用鼠标配置失败: {e}")
            return False
            
    return False


def 保存组配置(name, folder_path, file_list):
    """
    保存配置文件。
    :param name: 此配置名称
    :param folder_path: 配置文件夹路径
    :param file_list: 15个文件路径列表
    """
    if len(file_list) != 15:
        log.error(f"file_list 长度不符: {len(file_list)} (期望 15)")
        raise ValueError(f"file_list must contain exactly 15 items")

    target_folder = os.path.join(folder_path, name)
    os.makedirs(target_folder, exist_ok=True)
    log.debug(f"目标文件夹路径: {target_folder}")
    
    mouse_config = {}
    
    for i, file_path_input in enumerate(file_list):
        cursor_name = CURSOR_ORDER_MAPPING[i]
        
        # 处理空路径
        if not file_path_input or not file_path_input.strip():
            mouse_config[cursor_name] = ""
            continue

        try:
            source_path = os.path.abspath(file_path_input)
            
            if not os.path.exists(source_path):
                log.error(f"源文件不存在，跳过: {source_path}")
                mouse_config[cursor_name] = ""
                continue

            file_name = os.path.basename(source_path)
            target_path = os.path.join(target_folder, file_name)
            target_path_abs = os.path.abspath(target_path)

            is_same_file = False
            if os.path.exists(target_path_abs):
                try:
                    if os.path.samefile(source_path, target_path_abs):
                        is_same_file = True
                except OSError:
                    pass

            if not is_same_file:
                shutil.copy2(source_path, target_path)
                log.debug(f"已复制文件: {file_name}")
            else:
                log.debug(f"文件已存在且相同，跳过复制: {file_name}")
            
            mouse_config[cursor_name] = target_path

        except Exception as e:
            log.error(f"处理文件 {cursor_name} 失败: {e}")
            mouse_config[cursor_name] = ""

    config_data = {'mouses': mouse_config}
    config_file_path = os.path.join(target_folder, "config.toml")
    
    # 写入配置文件
    try:
        if portalocker:
            with portalocker.Lock(config_file_path, 'w', encoding='utf-8') as f:
                toml.dump(config_data, f)
        else:
            with open(config_file_path, 'w', encoding='utf-8') as f:
                toml.dump(config_data, f)
                
        log.info(f"配置保存成功: {config_file_path}")
        return target_folder
    except Exception as e:
        log.error(f"保存配置失败: {e}")
        return False


def old_add_wallpaper(name, query_path, config_path=CONFIG_PATH):
    """
    绑定壁纸 ID 到 config.toml。
    """
    log.debug(f"add_wallpaper: name={name}, path={query_path}")
    
    normalized_path = os.path.normpath(query_path)
    if os.path.isfile(normalized_path):
        file_dir = os.path.dirname(normalized_path)
    else:
        file_dir = normalized_path
    last_folder = os.path.basename(file_dir)
    
    if not last_folder:
        log.error("无法提取壁纸 ID。")
        return False
    
    # 读取现有配置
    config_data = load_toml_config(config_path)
    if "wallpaper" not in config_data:
        config_data["wallpaper"] = {}

    config_data["wallpaper"][last_folder] = name
    
    # 写入配置
    try:
        if portalocker:
            with portalocker.Lock(config_path, 'w', encoding='utf-8') as f:
                toml.dump(config_data, f)
        else:
            with open(config_path, 'w', encoding='utf-8') as f:
                toml.dump(config_data, f)
        
        log.info(f"配置写入成功: {last_folder} -> {name}")
        return True
    except Exception as e:
        log.error(f"配置写入失败: {e}")
        return False

def add_wallpaper(name, ID, config_path=CONFIG_PATH):
    """
    绑定壁纸 ID 到 config.toml。
    """
    log.debug(f"add_wallpaper: name={name}, ID={ID}")
    
    # 读取现有配置
    config_data = load_toml_config(config_path)
    if "wallpaper" not in config_data:
        config_data["wallpaper"] = {}

    config_data["wallpaper"][ID] = name
    
    # 写入配置
    try:
        if portalocker:
            with portalocker.Lock(config_path, 'w', encoding='utf-8') as f:
                toml.dump(config_data, f)
        else:
            with open(config_path, 'w', encoding='utf-8') as f:
                toml.dump(config_data, f)
        
        log.info(f"配置写入成功: {ID} -> {name}")
        return True
    except Exception as e:
        log.error(f"配置写入失败: {e}")
        return False


def delete_wallpaper(query_path, config_path=CONFIG_PATH):
    """
    删除 config.toml 中的绑定。
    """
    normalized_path = os.path.normpath(query_path)
    if os.path.isfile(normalized_path):
        file_dir = os.path.dirname(normalized_path)
    else:
        file_dir = normalized_path
    last_folder = os.path.basename(file_dir)
    
    if not last_folder:
        return False
        
    config_data = load_toml_config(config_path)
    
    if "wallpaper" not in config_data or last_folder not in config_data["wallpaper"]:
        log.debug("绑定不存在，无需删除。")
        return True

    del config_data["wallpaper"][last_folder]
    
    # 写入配置
    try:
        if portalocker:
            with portalocker.Lock(config_path, 'w', encoding='utf-8') as f:
                toml.dump(config_data, f)
        else:
            with open(config_path, 'w', encoding='utf-8') as f:
                toml.dump(config_data, f)
                
        log.info("配置删除成功。")
        return True
    except Exception as e:
        log.error(f"配置删除失败: {e}")
        return False

def 删除鼠标组(group_name, base_path=MOUSE_BASE_PATH):
    """删除整个鼠标组文件夹"""
    if group_name == "默认":
        log.error("禁止删除默认组")
        return False
        
    target_folder = os.path.join(base_path, group_name)
    if not os.path.exists(target_folder):
        return True
        
    try:
        shutil.rmtree(target_folder)
        log.info(f"删除鼠标组成功: {group_name}")
        return True
    except Exception as e:
        log.error(f"删除鼠标组失败: {e}")
        return False


if __name__ == "__main__":
    add_wallpaper("表1", "testdfghj")
    pass