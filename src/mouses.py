import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.Tlog import TLog
from src.getWallpaperConfig import 获取当前壁纸
from src.setMouse import 设置鼠标指针
import time
from screeninfo import get_monitors
import pyautogui

import shutil
import toml


from src.Tlog import TLog
import toml
log = TLog("mouses")



def 触发刷新(config_path,username,monitor):
    """
        触发刷新
        :param config_path: wallpaper_engine 配置路径
        :param username: 用户名
        :param monitor: 显示器编号
    """
    path = 获取当前壁纸(config_path, username, monitor)[0]

    normalized_path = os.path.normpath(path)
    if os.path.isfile(normalized_path):
        file_dir = os.path.dirname(normalized_path)
    else:
        file_dir = normalized_path
    last_folder = os.path.basename(file_dir)
    if not last_folder:
        return False

    tf = wallpaper(last_folder)
    if tf != False:
        config_file_path = os.path.join("mouses", tf, "config.toml")
        # 检查配置文件是否存在
        if os.path.exists(config_file_path):
            config = toml.load(config_file_path)
            mouse_values = list(config['mouses'].values())
            设置鼠标指针(mouse_values)
        else:
            log.debug(f"配置文件不存在: {config_file_path}")
            # 如果没有对应的配置文件，尝试使用默认配置
            default_config_path = os.path.join("mouses", "默认", "config.toml")
            if os.path.exists(default_config_path):
                log.debug(f"使用默认配置: {default_config_path}")
                config = toml.load(default_config_path)
                mouse_values = list(config['mouses'].values())
                设置鼠标指针(mouse_values)
    else:
        # 如果 wallpaper() 返回 False，直接使用默认配置
        default_config_path = os.path.join("mouses", "默认", "config.toml")
        if os.path.exists(default_config_path):
            log.debug(f"使用默认配置: {default_config_path}")
            config = toml.load(default_config_path)
            mouse_values = list(config['mouses'].values())
            设置鼠标指针(mouse_values)



            
        
        


def 保存组配置(name, folder_path, file_list):
    """
        保存配置文件
        :param name: 此配置名称
        :param folder_path: 配置文件夹路径
        :param file_list: 16个文件路径列表
    """
    if len(file_list) != 15:
        log.debug("file_list 长度不符")
        raise ValueError("file_list must contain exactly 15 items")
    
    target_folder = os.path.join(folder_path, name)
    log.debug(f"目标文件夹路径: {target_folder}")
    os.makedirs(target_folder, exist_ok=True)
    
    copied_paths = []
    for idx, file_path in enumerate(file_list):
        log.debug(f"处理第 {idx+1} 个文件: {file_path}")
        if file_path and os.path.exists(file_path):
            file_name = os.path.basename(file_path)
            target_path = os.path.join(target_folder, file_name)
            shutil.copy2(file_path, target_path)
            copied_paths.append(target_path)
            log.debug(f"已复制文件到: {target_path}")
        else:
            copied_paths.append("")
            log.debug("文件路径为空或不存在，跳过复制")

    cursor_keys = [
        "Arrow", "Help", "AppStarting", "Wait", "Crosshair", "IBeam", 
        "Handwriting", "No", "SizeNS", "SizeWE", "SizeNWSE", "SizeNESW", 
        "SizeAll", "Hand", "UpArrow"
    ]

    toml_data = {"mouses": dict(zip(cursor_keys, copied_paths))}
    log.debug("生成 TOML 数据")

    toml_path = os.path.join(target_folder, "config.toml")
    log.debug(f"准备写入 TOML 文件: {toml_path}")
    with open(toml_path, "w", encoding="utf-8") as f:
        toml.dump(toml_data, f)
    log.debug("TOML 文件写入完成")
    #触发刷新()
    #log.debug("触发刷新完成")
    return target_folder
    
 


def add_wallpaper(name, query_path, config_path="config.toml"):
    """
    从路径中提取文件所在的最后一个文件夹名，在config.toml的wallpaper表中添加键值对（文件夹名为键，name为值）
    
    :param name: 要保存的值
    :param query_path: 待处理的文件路径字符串
    :param config_path: 配置文件路径（默认当前目录的config.toml）
    :return: 成功返回True，失败返回False
    """
    log.debug(f"add_wallpaper() 开始，name={name}, query_path={query_path}, config_path={config_path}")
    normalized_path = os.path.normpath(query_path)
    log.debug(f"标准化路径: {normalized_path}")
    if os.path.isfile(normalized_path):
        file_dir = os.path.dirname(normalized_path)
        log.debug(f"路径指向文件，提取目录: {file_dir}")
    else:
        file_dir = normalized_path
        log.debug(f"路径指向目录: {file_dir}")
    last_folder = os.path.basename(file_dir)
    log.debug(f"提取最后一级文件夹名: {last_folder}")
    
    if not last_folder:
        log.debug("最后一级文件夹名为空，返回False")
        return False
    
    config_data = {}
    if os.path.exists(config_path):
        try:
            log.debug(f"配置文件存在，尝试读取: {config_path}")
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = toml.load(f)
            log.debug("配置文件读取成功")
        except toml.TomlDecodeError:
            log.debug("TOML 解析失败，返回False")
            return False
    
    if "wallpaper" not in config_data:
        log.debug("wallpaper 节点不存在，准备初始化空字典")
        config_data["wallpaper"] = {}

    config_data["wallpaper"][last_folder] = name
    log.debug(f"准备写入配置: wallpaper.{last_folder} = {name}")
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            toml.dump(config_data, f)
        log.debug("配置写入成功，返回True")
        return True
    except Exception as e:
        log.debug(f"配置写入失败，异常: {e}，返回False")
        return False


def delete_wallpaper(query_path, config_path="config.toml"):
    """
    从路径中提取文件所在的最后一个文件夹名，删除config.toml的wallpaper表中对应键值对
    
    :param query_path: 待处理的文件路径字符串（文件或目录）
    :param config_path: 配置文件路径（默认当前目录的config.toml）
    :return: 成功删除返回True，未找到项目/操作失败返回False
    """
    log.debug(f"delete_wallpaper() 开始，query_path={query_path}, config_path={config_path}")
    normalized_path = os.path.normpath(query_path)
    log.debug(f"标准化路径: {normalized_path}")
    if os.path.isfile(normalized_path):
        file_dir = os.path.dirname(normalized_path)
        log.debug(f"路径指向文件，提取目录: {file_dir}")
    else:
        file_dir = normalized_path
        log.debug(f"路径指向目录: {file_dir}")
    last_folder = os.path.basename(file_dir)
    log.debug(f"提取最后一级文件夹名: {last_folder}")
    if not last_folder:
        log.debug("最后一级文件夹名为空，返回False")
        return False 
    if not os.path.exists(config_path):
        log.debug(f"配置文件不存在，返回False")
        return False 
    try:
        log.debug(f"尝试读取配置文件: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = toml.load(f)
        log.debug("配置文件读取成功")
    except toml.TomlDecodeError:
        log.debug("TOML 解析失败，返回False")
        return False 
    if "wallpaper" not in config_data or last_folder not in config_data["wallpaper"]:
        log.debug(f"wallpaper 节点或键 {last_folder} 不存在，返回False")
        return False 
    log.debug(f"准备删除配置键: wallpaper.{last_folder}")
    del config_data["wallpaper"][last_folder]
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            toml.dump(config_data, f)
        log.debug("配置删除成功，,回True")
        return True
    except Exception as e:
        log.debug(f"配置写入失败，异常: {e}，返回False")
        return False


def get_current_monitor_index_minimal():
    """返回鼠标当前所在的显示器索引"""
    
    x, y = pyautogui.position()
    for i, m in enumerate(get_monitors()):
        if m.x <= x < (m.x + m.width) and m.y <= y < (m.y + m.height):
            return i
            
    return -1



if __name__ == "__main__":
    wallpaper("2992022633")
    print(wallpaper("2992022633"))



