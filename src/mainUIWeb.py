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

# 鼠标组基础路径
MOUSE_BASE_PATH = "mouses"

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

def get_available_mouse_groups() -> list:
    """
    获取可用的鼠标组列表
    
    Returns:
        list: 鼠标组名称列表
    """
    groups = []
    try:
        config_files = glob.glob(os.path.join(MOUSE_BASE_PATH, '*', 'config.toml'))
        for file_path in config_files:
            group_name = os.path.basename(os.path.dirname(file_path))
            groups.append(group_name)
        log.debug(f"获取到鼠标组列表：{groups}")
    except Exception as e:
        log.error(f"获取鼠标组列表失败：{e}")
    return sorted(groups)

def get_mouse_group_icons(group_name):
    """
    获取鼠标组的图标路径列表，将 ani 和 cur 文件转换为可预览格式
    
    Args:
        group_name: 鼠标组名称
    
    Returns:
        list: 图标路径列表
    """
    icons = []
    try:
        # 读取鼠标组配置文件
        config_path = os.path.join(MOUSE_BASE_PATH, group_name, "config.toml")
        if not os.path.exists(config_path):
            log.error(f"鼠标组配置文件不存在：{config_path}")
            return icons
        
        config = toml.load(config_path)
        mouse_config = config.get('mouses', {})
        
        # 确保缓存文件夹存在
        cache_folder = "cache"
        os.makedirs(cache_folder, exist_ok=True)
        
        # 光标名称顺序
        CURSOR_ORDER = [
            "Arrow", "Help", "AppStarting", "Wait", "Crosshair", "IBeam", 
            "Handwriting", "No", "SizeNS", "SizeWE", "SizeNWSE", "SizeNESW", 
            "SizeAll", "Hand", "UpArrow"
        ]
        
        # 处理每个光标
        for cursor_name in CURSOR_ORDER:
            cursor_path = mouse_config.get(cursor_name, "")
            if not cursor_path:
                icons.append("")
                continue
            
            # 确保路径是绝对路径
            if not os.path.isabs(cursor_path):
                cursor_path = os.path.join(BASE_DIR, cursor_path)
            
            if not os.path.exists(cursor_path):
                icons.append("")
                continue
            
            # 生成缓存文件名
            cache_filename = f"{group_name}_{cursor_name}.png"
            cache_path = os.path.join(cache_folder, cache_filename)
            
            # 转换并保存到缓存
            try:
                if cursor_path.endswith('.ani'):
                    if get_ani_frames:
                        frames = get_ani_frames(cursor_path)
                        if frames and len(frames) > 0:
                            # 将 ani 转换为 gif
                            cache_filename = f"{group_name}_{cursor_name}.gif"
                            cache_path = os.path.join(cache_folder, cache_filename)
                            frames[0].save(
                                cache_path,
                                save_all=True,
                                append_images=frames[1:],
                                duration=100,
                                loop=0,
                                disposal=2
                            )
                            icons.append(cache_path.replace('\\', '/'))
                        else:
                            icons.append("")
                    else:
                        icons.append("")
                elif cursor_path.endswith('.cur'):
                    if get_cur_image:
                        img = get_cur_image(cursor_path)
                        if img:
                            img.thumbnail((64, 64))
                            img.save(cache_path, 'PNG')
                            icons.append(cache_path.replace('\\', '/'))
                        else:
                            icons.append("")
                    else:
                        icons.append("")
                else:
                    # 其他格式直接复制到缓存
                    shutil.copy2(cursor_path, cache_path)
                    icons.append(cache_path.replace('\\', '/'))
            except Exception as e:
                log.error(f"转换图标失败 {cursor_path}：{e}")
                icons.append("")
        
        log.debug(f"获取到鼠标组 {group_name} 的图标列表：{icons}")
    except Exception as e:
        log.error(f"获取鼠标组图标失败：{e}")
    return icons

def load_wallpaper_bindings(path="config.toml") -> dict:
    """
    加载壁纸绑定配置
    
    Args:
        path: 配置文件路径
    
    Returns:
        dict: 壁纸 ID 到鼠标组名称的映射
    """
    try:
        config = toml.load(path)
        bindings = {str(k): v for k, v in config.get('wallpaper', {}).items()}
        log.debug(f"加载到壁纸绑定配置：{bindings}")
        return bindings
    except Exception as e:
        log.error(f"加载壁纸绑定配置失败: {e}")
        return {}

class Api:
    def init(self):
        wallpapers = all_wallpapers()
        wallpapers = 图片加缓存(wallpapers)
        try:
            log.debug(f"初始化返回壁纸列表：{len(wallpapers)} 项")
        except Exception:
            pass
        return wallpapers
    
    def get_mouse_groups(self):
        """
        获取可用的鼠标组列表
        
        Returns:
            list: 鼠标组名称列表
        """
        groups = get_available_mouse_groups()
        log.debug(f"返回鼠标组列表：{groups}")
        return groups
    
    def bind_mouse_group(self, wallpaper_id, group_name):
        """
        绑定或解除绑定鼠标组
        
        Args:
            wallpaper_id: 壁纸 ID
            group_name: 鼠标组名称，"未绑定"表示解除绑定，空字符串表示"请选择"
        
        Returns:
            dict: 操作结果
        """
        try:
            if not wallpaper_id or not wallpaper_id.strip().isnumeric():
                log.error(f"无效的壁纸 ID：{wallpaper_id}")
                return {"success": False, "message": "壁纸 ID 无效"}
            
            # 处理选择"请选择"的情况
            if not group_name or group_name == "":
                log.info(f"选择了'请选择'，不执行任何操作")
                return {"success": True, "message": "请选择有效的鼠标组"}
            
            if group_name == "未绑定":
                if delete_wallpaper:
                    delete_wallpaper(wallpaper_id)
                    log.info(f"成功解除壁纸 ID: {wallpaper_id} 的鼠标组绑定")
                    return {"success": True, "message": "成功解除绑定"}
                else:
                    log.error("delete_wallpaper 函数不可用")
                    return {"success": False, "message": "解除绑定功能不可用"}
            else:
                if add_wallpaper:
                    add_wallpaper(group_name, wallpaper_id)
                    log.info(f"成功将壁纸 ID: {wallpaper_id} 绑定到鼠标组: {group_name}")
                    return {"success": True, "message": "成功绑定"}
                else:
                    log.error("add_wallpaper 函数不可用")
                    return {"success": False, "message": "绑定功能不可用"}
        except Exception as e:
            log.error(f"绑定鼠标组失败：{e}")
            return {"success": False, "message": str(e)}
    
    def get_wallpaper_binding(self, wallpaper_id):
        """
        获取壁纸的当前鼠标组绑定
        
        Args:
            wallpaper_id: 壁纸 ID
        
        Returns:
            str: 鼠标组名称，"未绑定"表示未绑定
        """
        try:
            bindings = load_wallpaper_bindings()
            group_name = bindings.get(str(wallpaper_id), "未绑定")
            log.debug(f"壁纸 ID: {wallpaper_id} 的绑定：{group_name}")
            return group_name
        except Exception as e:
            log.error(f"获取壁纸绑定失败：{e}")
            return "未绑定"
    
    def get_mouse_group_icons(self, group_name):
        """
        获取鼠标组的图标路径列表
        
        Args:
            group_name: 鼠标组名称
        
        Returns:
            list: 图标路径列表
        """
        icons = get_mouse_group_icons(group_name)
        log.debug(f"返回鼠标组 {group_name} 的图标列表：{icons}")
        return icons
    
    def get_playlist(self):
        """
        获取当前播放列表数据
        
        Returns:
            dict: 包含播放列表项和名称的字典
        """
        try:
            import getpass
            import toml
            from getWallpaperConfig import 获取当前壁纸列表
            
            # 读取配置文件路径
            config_data = toml.load("config.toml")
            we_config_path = config_data["path"]["wallpaper_engine_config"]
            
            # 获取当前壁纸列表
            user = getpass.getuser()
            wallpaper_list = 获取当前壁纸列表(we_config_path, user)
            
            if not wallpaper_list:
                log.error("无法获取壁纸列表")
                return {"items": [], "name": ""}
            
            # 仅使用显示器1（列表第一项）的数据
            monitor1_data = wallpaper_list[0]
            items_list = monitor1_data[2]  # 播放列表项列表
            playlist_name = monitor1_data[3]  # 播放列表名称
            
            # 处理播放列表项，获取每个项的预览图路径
            processed_items = []
            for item_path in items_list:
                if not item_path:
                    continue
                
                # 提取壁纸ID
                dir_path = os.path.dirname(item_path)
                wallpaper_id = os.path.basename(dir_path)
                
                # 查找预览图路径
                preview_path = ""
                for ext in ['jpg', 'png', 'gif']:
                    candidate_path = os.path.join(dir_path, f"preview.{ext}")
                    if os.path.exists(candidate_path):
                        preview_path = candidate_path
                        break
                
                # 处理预览图路径，添加到缓存
                if preview_path:
                    try:
                        os.makedirs("cache", exist_ok=True)
                        file_ext = os.path.splitext(preview_path)[1]
                        cache_filename = f"{wallpaper_id}{file_ext}"
                        cache_full_path = os.path.join("cache", cache_filename)
                        if not os.path.exists(cache_full_path):
                            import shutil
                            shutil.copy2(preview_path, cache_full_path)
                        preview_path = os.path.join("cache", cache_filename)
                    except Exception as e:
                        log.error(f"处理预览图失败：{e}")
                
                processed_items.append([wallpaper_id, preview_path])
            
            try:
                log.debug(f"返回播放列表数据：{len(processed_items)} 项")
            except Exception:
                pass
            return {"items": processed_items, "name": playlist_name}
        except Exception as e:
            log.error(f"获取播放列表失败：{e}")
            return {"items": [], "name": ""}
    
    def test_playlist(self):
        """
        测试播放列表加载
        
        Returns:
            dict: 测试结果
        """
        try:
            log.debug("测试播放列表加载")
            result = self.get_playlist()
            log.debug(f"测试播放列表加载结果：{result}")
            return {"success": True, "data": result}
        except Exception as e:
            log.error(f"测试播放列表加载失败：{e}")
            return {"success": False, "error": str(e)}





api = Api()
win = webview.create_window(
    "MouseEngine",
    "mainUIWeb.html",
    js_api=api,
    width=1000,
    height=900,
    #resizable=False,  # 禁止用户调整窗口大小
    easy_drag=True    # 支持通过任意区域拖动窗口
)

# 安全退出功能
def safe_exit():
    """安全退出 Web UI"""
    try:
        if win:
            win.destroy()
        log.info("Web UI 已安全退出")
    except Exception as e:
        log.error(f"退出 Web UI 时出错：{e}")

# 在 Api 类中添加退出方法
api.exit_app = safe_exit

webview.start(
    debug=True,
    http_server=True
)

