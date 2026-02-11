# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: BSD-3-Clause
import json
import os
from Tlog import TLog
import getpass


log = TLog("获取当前壁纸列表")

def 获取当前壁纸列表(config_path: str, user: str) -> list:
    """
    从 Wallpaper Engine 的 config.json 文件中提取每个显示器当前的壁纸信息。

    Args:
        config_path (str):
        user (str)

    Returns:
        list: 包含每个显示器壁纸信息的列表。
              结构为: [[当前加载, id, 播放列表, 加载列表名], ...]
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        log.error(f"错误：配置文件未找到，路径: {config_path}")
        return []
    except json.JSONDecodeError:
        log.error(f"错误：文件不是有效的 JSON 格式: {config_path}")
        return []
    except Exception as e:
        log.error(f"读取配置文件时发生未知错误: {e}")
        return []

    try:
        selected_wallpapers = config_data[user]['general']['wallpaperconfig']['selectedwallpapers']
    except KeyError as e:
        log.error(f"错误：无法在 JSON 中找到指定路径的键: {e}")
        return []
    
    result_list = []
    # XXX 未验证多显示器适配方法 
    for monitor_key in sorted(selected_wallpapers.keys(), key=lambda k: int(k) if str(k).isdigit() else str(k)):
        monitor_data = selected_wallpapers[monitor_key]

        try:
            file_path = monitor_data.get('file')
            items_list = monitor_data.get('playlist', {}).get('items', [])
            playlist_name = monitor_data.get('playlist', {}).get('name')
            
            wallpaper_id = ""
            if file_path:
                dir_path = os.path.dirname(file_path)
                dir_path_normalized = dir_path.replace('\\', '/')
                wallpaper_id = os.path.basename(dir_path_normalized)
            
            monitor_result = [
                file_path,
                wallpaper_id,
                items_list,
                playlist_name
            ]
            
            result_list.append(monitor_result)
            
        except Exception as e:
            log.warning(f"处理显示器 {monitor_key} 时发生错误，跳过: {e}")
            continue

    return result_list


if __name__ == '__main__':
    winUserName = getpass.getuser()

    log = TLog("获取当前壁纸路径")
    #config_path = toml.load("config.toml")["path"]["wallpaper_engine_config"]
    config_path = r"D:/Application/STEAM/steamapps/common/wallpaper_engine/config.json"
    _list = 获取当前壁纸列表(config_path, winUserName)
    log.val(_list)
    log.debug(f"{_list[0][1]}")
