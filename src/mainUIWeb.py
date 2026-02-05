import webview
from threading import Thread
from Tlog import TLog
log = TLog("MouseEngineWebUI")
import os
import toml
from typing import List, Tuple
import json
import time
import base64
from pathlib import Path
import shutil
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

def all_wallpapers(): 
    """
    从 config.toml 读取 Steam 路径，找到创意工坊壁纸文件夹，
    收集每个文件夹名、区分大小写的缩略图路径、title、type，
    
    Returns:
        List[List[str]]: [["文件夹名", "缩略图绝对路径", "title值", "type值"], ...]
    """
    # 获取wp配置文件路径
    try:
        config_data = toml.load("config.toml")
        we_config_path = config_data["path"]["wallpaper_engine_config"]
    except FileNotFoundError:
        log.error(f"错误：未找到 config.toml 文件")
        return []
    except KeyError as e:
        log.error(f"错误：config.toml 中缺少键 {e}")
        return []
    except Exception as e:
        log.error(f"读取 config.toml 时出错：{e}")
        return []

    steam_root = None
    normalized_path = os.path.normpath(we_config_path)
    path_parts = normalized_path.split(os.sep)
    
    try:
        steamapps_index = path_parts.index("steamapps")
        steam_root = os.sep.join(path_parts[:steamapps_index])
    except ValueError:
        return []
        # 拼接创意工坊路径
    workshop_path = os.path.join(
        steam_root,
        "steamapps",
        "workshop",
        "content",
        "431960"
    )
    
    if not os.path.exists(workshop_path):
        log.error(f"错误：创意工坊路径不存在 {workshop_path}")
        return []

    # 收集信息
    wallpaper_info = []
    for folder_name in os.listdir(workshop_path):
        folder_path = os.path.join(workshop_path, folder_name)
        
        if not os.path.isdir(folder_path):
            continue
        
        real_folder_path = os.path.realpath(folder_path)
        
        thumbnail_path = ""
        preview_jpg = os.path.join(real_folder_path, "preview.jpg")
        preview_gif = os.path.join(real_folder_path, "preview.gif")
        
        if os.path.exists(preview_jpg):
            thumbnail_path = os.path.abspath(preview_jpg)
        elif os.path.exists(preview_gif):
            thumbnail_path = os.path.abspath(preview_gif)
        
        project_json_path = os.path.join(real_folder_path, "project.json")
        title = ""
        type_value = ""
        try:
            with open(project_json_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
                title = project_data.get("title", "")
                type_value = project_data.get("type", "")
        except FileNotFoundError:
            log.debug(f"{folder_name} 中未找到 project.json 文件")
        except json.JSONDecodeError:
            log.debug(f"{folder_name} 中的 project.json 格式错误")
        except Exception as e:
            log.debug(f"读取 {folder_name} 的 project.json 出错：{e}")
        
        if not type_value:
            log.debug(f"{folder_name} 无有效type值，跳过该壁纸")
            continue
        
        try:
            modify_time = os.path.getmtime(folder_path)
        except Exception as e:
            print(f"警告：无法获取 {folder_name} 的修改时间，跳过：{e}")
            continue
        
        wallpaper_info.append([
            folder_name, 
            thumbnail_path, 
            title, 
            type_value, 
            modify_time
        ])

    # 按修改时间排序
    wallpaper_info_sorted = sorted(wallpaper_info, key=lambda x: x[4])
    final_list = [[item[0], item[1], item[2], item[3]] for item in wallpaper_info_sorted]

    return final_list

def 图片加缓存(original_list, cache_folder="cache"):
    try:
        os.makedirs(cache_folder, exist_ok=True)
    except Exception as e:
        return original_list
    
    processed_list = [item.copy() for item in original_list]
    
    for sub_list in processed_list:
        item_id = sub_list[0]
        original_path = sub_list[1]
        if not (isinstance(original_path, str) and os.path.exists(original_path) and os.path.isfile(original_path)):
            continue

        file_ext = os.path.splitext(original_path)[1]
        cache_filename = f"{item_id}{file_ext}"
        cache_full_path = os.path.join(cache_folder, cache_filename)
        cache_relative_path = os.path.join(cache_folder, cache_filename)
        
        if not os.path.exists(cache_full_path):
            try:
                shutil.copy2(original_path, cache_full_path)
            except (PermissionError, FileNotFoundError):
                continue
            except Exception as e:
                log.error(f"文件复制失败 [{item_id}]：{e}")
                continue
        
        # 更新路径
        sub_list[1] = cache_relative_path
    
    return processed_list

class Api:
    def init(self):
        wallpapers = all_wallpapers()
        wallpapers = 图片加缓存(wallpapers)
        print(wallpapers)
        return wallpapers





api = Api()
win = webview.create_window("MouseEngine", "mainUIWeb.html", js_api=api)

webview.start(
    debug=True,
    http_server=True
)

