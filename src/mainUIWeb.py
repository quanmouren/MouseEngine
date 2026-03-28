# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: BSD-3-Clause
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
import glob
from PIL import Image
from path_utils import resolve_path, get_project_root

# 引入项目根目录
PROJECT_ROOT = get_project_root()
log.info(f"项目根目录: {PROJECT_ROOT}")


MOUSE_BASE_PATH = resolve_path("mouses")
CONFIG_PATH = resolve_path("config.toml")
HTML_ROOT = resolve_path("html")
CACHE_BASE_DIR = resolve_path("html/cache")

# 导入鼠标组操作函数
try:
    from mouses import add_wallpaper, delete_wallpaper
except ImportError:
    log.error("无法导入 mouses 模块")
    add_wallpaper = None
    delete_wallpaper = None

# 导入图标转换函数
try:
    from ani_to_gif import get_ani_frames
    from cur_to_png import get_cur_image
except ImportError:
    log.error("无法导入图标转换模块")
    get_ani_frames = None
    get_cur_image = None

# 设置当前工作目录为项目根目录
os.chdir(PROJECT_ROOT)

def all_wallpapers(): 
    """
    从 config.toml 读取 Steam 路径，找到创意工坊壁纸文件夹
    """
    try:
        config_data = toml.load(CONFIG_PATH)
        we_config_path = config_data["path"]["wallpaper_engine_config"]
    except FileNotFoundError:
        log.error(f"错误：未找到配置文件 {CONFIG_PATH}")
        return []
    except KeyError as e:
        log.error(f"错误：配置文件中缺少键 {e}")
        return []

    steam_root = None
    normalized_path = os.path.normpath(we_config_path)
    path_parts = normalized_path.split(os.sep)
    
    try:
        steamapps_index = path_parts.index("steamapps")
        steam_root = os.sep.join(path_parts[:steamapps_index])
        if not steam_root.endswith(os.sep) and os.name == 'nt' and len(steam_root) == 2:
            steam_root += os.sep # 处理盘符根目录
    except ValueError:
        return []

    workshop_path = os.path.join(steam_root, "steamapps", "workshop", "content", "431960")
    
    if not os.path.exists(workshop_path):
        log.error(f"错误：创意工坊路径不存在 {workshop_path}")
        return []

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
        except Exception:
            continue
        
        if not type_value:
            continue
        
        try:
            modify_time = os.path.getmtime(folder_path)
        except Exception:
            continue
        
        wallpaper_info.append([folder_name, thumbnail_path, title, type_value, modify_time])

    wallpaper_info_sorted = sorted(wallpaper_info, key=lambda x: x[4])
    return [[item[0], item[1], item[2], item[3]] for item in wallpaper_info_sorted]

def 图片加缓存(original_list, cache_folder=CACHE_BASE_DIR):
    """
    将壁纸预览图复制到 HTML 缓存目录
    """
    try:
        os.makedirs(cache_folder, exist_ok=True)
    except Exception as e:
        return original_list
    
    processed_list = [item.copy() for item in original_list]
    for sub_list in processed_list:
        item_id = sub_list[0]
        original_path = sub_list[1]
        if not (isinstance(original_path, str) and os.path.exists(original_path)):
            continue

        file_ext = os.path.splitext(original_path)[1]
        cache_filename = f"{item_id}{file_ext}"
        cache_full_path = os.path.join(cache_folder, cache_filename)
        # 前端访问的相对路径
        cache_relative_path = os.path.join("cache", cache_filename).replace('\\', '/')
        
        if not os.path.exists(cache_full_path):
            try:
                shutil.copy2(original_path, cache_full_path)
            except Exception:
                continue
        
        sub_list[1] = cache_relative_path
    
    return processed_list

def get_available_mouse_groups() -> list:
    groups = []
    try:
        # 使用绝对路径搜索
        search_pattern = os.path.join(MOUSE_BASE_PATH, '*', 'config.toml')
        config_files = glob.glob(search_pattern)
        for file_path in config_files:
            group_name = os.path.basename(os.path.dirname(file_path))
            groups.append(group_name)
    except Exception as e:
        log.error(f"获取鼠标组列表失败：{e}")
    return sorted(groups)

def get_mouse_group_icons(group_name):
    icons = []
    try:
        group_dir = os.path.join(MOUSE_BASE_PATH, group_name)
        config_path = os.path.join(group_dir, "config.toml")
        if not os.path.exists(config_path):
            return icons
        
        config = toml.load(config_path)
        mouse_config = config.get('mouses', {})
        
        os.makedirs(CACHE_BASE_DIR, exist_ok=True)
        
        CURSOR_ORDER = ["Arrow", "Help", "AppStarting", "Wait", "Crosshair", "IBeam", 
                        "Handwriting", "No", "SizeNS", "SizeWE", "SizeNWSE", "SizeNESW", 
                        "SizeAll", "Hand", "UpArrow"]
        
        for cursor_name in CURSOR_ORDER:
            cursor_rel_path = mouse_config.get(cursor_name, "")
            if not cursor_rel_path:
                icons.append("")
                continue
            
            # 路径拼接逻辑：使用 resolve_path 统一处理路径
            cursor_path = resolve_path(cursor_rel_path)
            
            if not os.path.exists(cursor_path):
                icons.append("")
                continue
            
            cache_filename = f"{group_name}_{cursor_name}.png"
            cache_path = os.path.join(CACHE_BASE_DIR, cache_filename)
            
            try:
                if cursor_path.lower().endswith('.ani'):
                    if get_ani_frames:
                        frames = get_ani_frames(cursor_path)
                        if frames:
                            cache_filename = f"{group_name}_{cursor_name}.gif"
                            cache_path = os.path.join(CACHE_BASE_DIR, cache_filename)
                            frames[0].save(cache_path, save_all=True, append_images=frames[1:], 
                                           duration=100, loop=0, disposal=2)
                            icons.append(f"cache/{cache_filename}")
                        else: icons.append("")
                    else: icons.append("")
                elif cursor_path.lower().endswith('.cur'):
                    if get_cur_image:
                        img = get_cur_image(cursor_path)
                        if img:
                            img.thumbnail((64, 64))
                            img.save(cache_path, 'PNG')
                            icons.append(f"cache/{os.path.basename(cache_path)}")
                        else: icons.append("")
                    else: icons.append("")
                else:
                    shutil.copy2(cursor_path, cache_path)
                    icons.append(f"cache/{os.path.basename(cache_path)}")
            except Exception:
                icons.append("")
    except Exception as e:
        log.error(f"获取鼠标组图标失败：{e}")
    return icons

def load_wallpaper_bindings(path=CONFIG_PATH) -> dict:
    try:
        path = resolve_path(path)
        config = toml.load(path)
        return {str(k): v for k, v in config.get('wallpaper', {}).items()}
    except Exception:
        return {}

class Api:
    def init(self):
        wallpapers = all_wallpapers()
        wallpapers = 图片加缓存(wallpapers)
        return wallpapers
    
    def get_mouse_groups(self):
        return get_available_mouse_groups()
    
    def bind_mouse_group(self, wallpaper_id, group_name):
        try:
            if not wallpaper_id or not str(wallpaper_id).strip().isnumeric():
                return {"success": False, "message": "壁纸 ID 无效"}
            
            if not group_name:
                return {"success": True, "message": "请选择有效的鼠标组"}
            
            if group_name == "未绑定":
                if delete_wallpaper:
                    delete_wallpaper(wallpaper_id)
                    return {"success": True, "message": "成功解除绑定"}
                return {"success": False, "message": "解除绑定功能不可用"}
            else:
                if add_wallpaper:
                    add_wallpaper(group_name, wallpaper_id)
                    return {"success": True, "message": "成功绑定"}
                return {"success": False, "message": "绑定功能不可用"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def get_wallpaper_binding(self, wallpaper_id):
        bindings = load_wallpaper_bindings()
        return bindings.get(str(wallpaper_id), "未绑定")
    
    def get_mouse_group_icons(self, group_name):
        return get_mouse_group_icons(group_name)
    
    def get_playlist(self):
        try:
            import getpass
            from getWallpaperConfig import 获取当前壁纸列表
            
            config_data = toml.load(CONFIG_PATH)
            we_config_path = config_data["path"]["wallpaper_engine_config"]
            
            user = getpass.getuser()
            wallpaper_list = 获取当前壁纸列表(we_config_path, user)
            
            if not wallpaper_list:
                return {"items": [], "name": "", "monitors": []}
            
            monitor_count = len(wallpaper_list)
            
            if monitor_count == 1:
                monitor1_data = wallpaper_list[0]
                items_list = monitor1_data[2]
                playlist_name = monitor1_data[3]
                
                processed_items = []
                for item_path in items_list:
                    if not item_path: continue
                    dir_path = os.path.dirname(item_path)
                    wallpaper_id = os.path.basename(dir_path)
                    
                    preview_path = ""
                    for ext in ['jpg', 'png', 'gif']:
                        candidate = os.path.join(dir_path, f"preview.{ext}")
                        if os.path.exists(candidate):
                            preview_path = candidate
                            break
                    
                    if preview_path:
                        try:
                            os.makedirs(CACHE_BASE_DIR, exist_ok=True)
                            file_ext = os.path.splitext(preview_path)[1]
                            cache_filename = f"{wallpaper_id}{file_ext}"
                            cache_full_path = os.path.join(CACHE_BASE_DIR, cache_filename)
                            if not os.path.exists(cache_full_path):
                                shutil.copy2(preview_path, cache_full_path)
                            preview_path = f"cache/{cache_filename}"
                        except Exception: pass
                    
                    processed_items.append([wallpaper_id, preview_path])
                return {"items": processed_items, "name": playlist_name, "monitors": [{"name": playlist_name}]}
            else:
                monitors_info = []
                all_items_set = set()
                all_items_list = []
                
                for monitor_data in wallpaper_list:
                    playlist_name = monitor_data[3]
                    monitors_info.append({"name": playlist_name})
                    
                    items_list = monitor_data[2]
                    for item_path in items_list:
                        if not item_path: continue
                        dir_path = os.path.dirname(item_path)
                        wallpaper_id = os.path.basename(dir_path)
                        
                        if wallpaper_id not in all_items_set:
                            all_items_set.add(wallpaper_id)
                            
                            preview_path = ""
                            for ext in ['jpg', 'png', 'gif']:
                                candidate = os.path.join(dir_path, f"preview.{ext}")
                                if os.path.exists(candidate):
                                    preview_path = candidate
                                    break
                            
                            if preview_path:
                                try:
                                    os.makedirs(CACHE_BASE_DIR, exist_ok=True)
                                    file_ext = os.path.splitext(preview_path)[1]
                                    cache_filename = f"{wallpaper_id}{file_ext}"
                                    cache_full_path = os.path.join(CACHE_BASE_DIR, cache_filename)
                                    if not os.path.exists(cache_full_path):
                                        shutil.copy2(preview_path, cache_full_path)
                                    preview_path = f"cache/{cache_filename}"
                                except Exception: pass
                            
                            all_items_list.append([wallpaper_id, preview_path])
                
                return {"items": all_items_list, "name": "", "monitors": monitors_info}
        except Exception as e:
            log.error(f"获取播放列表失败：{e}")
            return {"items": [], "name": "", "monitors": []}

    def exit_app(self):
        safe_exit()

api = Api()
# 使用绝对路径指向 HTML 文件
main_html_path = resolve_path("html/mainUIWeb.html")

win = webview.create_window(
    "MouseEngine",
    main_html_path,
    js_api=api,
    width=1000,
    height=900,
    easy_drag=True
)

def safe_exit():
    try:
        if win:
            win.destroy()
        log.info("Web UI 已安全退出")
    except Exception as e:
        log.error(f"退出 Web UI 时出错：{e}")

if log.on_DEBUG:
    webview.start(debug=True, http_server=True)
else:
    webview.start(debug=False, http_server=True)