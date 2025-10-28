from src.getWallpaperConfig import get_monitor_path
from src.setMouse import set_mouse
import time
import os
import shutil
import toml



def 触发刷新():
    path = get_monitor_path(config_path, username, monitor=1)

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
        config = toml.load(os.path.join("mouses", tf, "config.toml"))
        mouse_values = list(config['mouses'].values())
        set_mouse(mouse_values)




            
        
        


def 保存配置(name, folder_path, file_list):
    """
        保存配置文件
        :param name: 此配置名称
        :param folder_path: 配置文件夹路径
        :param file_list: 16个文件路径列表
    """
    if len(file_list) != 16:
        raise ValueError("file_list must contain exactly 16 items")
    
    target_folder = os.path.join(folder_path, name)
    os.makedirs(target_folder, exist_ok=True)
    
    copied_paths = []
    for file_path in file_list:
        if file_path and os.path.exists(file_path):
            file_name = os.path.basename(file_path)
            target_path = os.path.join(target_folder, file_name)
            shutil.copy2(file_path, target_path)
            copied_paths.append(target_path)
        else:
            copied_paths.append("")

    cursor_keys = [
        "Arrow", "Help", "AppStarting", "Wait", "Crosshair", "IBeam", 
        "Handwriting", "No", "SizeNS", "SizeWE", "SizeNWSE", "SizeNESW", 
        "SizeAll", "PersonSelect", "Hand", "UpArrow"
    ]

    toml_data = {"mouses": dict(zip(cursor_keys, copied_paths))}

    toml_path = os.path.join(target_folder, "config.toml")
    with open(toml_path, "w", encoding="utf-8") as f:
        toml.dump(toml_data, f)
    触发刷新()
    return target_folder
    


def wallpaper(query_path, config_path="config.toml"):
    """
    从查询路径中提取文件所在的最后一个文件夹名，检查其在config.toml的wallpaper项目中是否存在
    
    :param query_path: 待查询的文件路径字符串
    :param config_path: config.toml文件路径（默认当前目录）
    :return: 若存在则返回对应值，否则返回False
    """
    normalized_path = os.path.normpath(query_path)
    if os.path.isfile(normalized_path):
        file_dir = os.path.dirname(normalized_path)
    else:
        file_dir = normalized_path
    last_folder = os.path.basename(file_dir)
    if not last_folder:
        return False
    if not os.path.exists(config_path):
        default_config = {"wallpaper": {}}
        with open(config_path, 'w', encoding='utf-8') as f:
            toml.dump(default_config, f)
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = toml.load(f)
        if "wallpaper" not in config_data:
            config_data["wallpaper"] = {}
            with open(config_path, 'w', encoding='utf-8') as f:
                toml.dump(config_data, f)
        return config_data["wallpaper"].get(last_folder, False)
    
    except toml.TomlDecodeError:
        return False


def add_wallpaper(name, query_path, config_path="config.toml"):
    """
    从路径中提取文件所在的最后一个文件夹名，在config.toml的wallpaper表中添加键值对（文件夹名为键，name为值）
    
    :param name: 要保存的值
    :param query_path: 待处理的文件路径字符串
    :param config_path: 配置文件路径（默认当前目录的config.toml）
    :return: 成功返回True，失败返回False
    """
    normalized_path = os.path.normpath(query_path)
    if os.path.isfile(normalized_path):
        file_dir = os.path.dirname(normalized_path)
    else:
        file_dir = normalized_path 
    last_folder = os.path.basename(file_dir)
    
    if not last_folder:
        return False
    
    config_data = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = toml.load(f)
        except toml.TomlDecodeError:
            return False
    
    if "wallpaper" not in config_data:
        config_data["wallpaper"] = {}

    config_data["wallpaper"][last_folder] = name
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            toml.dump(config_data, f)
        return True
    except Exception:
        return False


def delete_wallpaper(query_path, config_path="config.toml"):
    """
    从路径中提取文件所在的最后一个文件夹名，删除config.toml的wallpaper表中对应键值对
    
    :param query_path: 待处理的文件路径字符串（文件或目录）
    :param config_path: 配置文件路径（默认当前目录的config.toml）
    :return: 成功删除返回True，未找到项目/操作失败返回False
    """
    normalized_path = os.path.normpath(query_path)
    if os.path.isfile(normalized_path):
        file_dir = os.path.dirname(normalized_path)
    else:
        file_dir = normalized_path
    last_folder = os.path.basename(file_dir)
    if not last_folder:
        return False 
    if not os.path.exists(config_path):
        return False 
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = toml.load(f)
    except toml.TomlDecodeError:
        return False 
    if "wallpaper" not in config_data or last_folder not in config_data["wallpaper"]:
        return False 
    del config_data["wallpaper"][last_folder]
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            toml.dump(config_data, f)
        return True
    except Exception:
        return False

mouse_path = r"mouses"
username = "woshi"

#wallpaper_engine 配置路径
config_path = r"D:\Application\STEAM\steamapps\common\wallpaper_engine\config.json"

#保存配置("测试","mouses",[r"C:\Users\woshi\Desktop\1.ani","","","","","","","","","","","","","","",""])

#查询路径 = r"D:/Application/STEAM/steamapps/workshop/content/431960/3306588730/scene.pkg"
#查询结果 = wallpaper(查询路径,"config.toml")
#print(查询结果)
#add_wallpaper("测试",查询路径,"config.toml")


#delete_wallpaper(查询路径,"config.toml")

触发刷新()