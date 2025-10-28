import json
import os

def get_monitor_path(config_path, user, monitor):
    """
    从Wallpaper Engine配置文件中获取指定Monitor的壁纸文件路径
    :param config_path: Wallpaper Engine配置文件路径
    :param user: 用户名
    :param monitor: 显示器编号
    :return: 壁纸文件路径，如果没有找到则返回None
    """
    try:
        if not os.path.exists(config_path):
            print(f"配置文件不存在: {config_path}")
            return None
        with open(config_path, 'r', encoding='utf-8') as file:
            config_data = json.load(file)
        wallpaper_path = config_data.get(user, {}).get('general', {}).get(
            'wallpaperconfig', {}).get('selectedwallpapers', {}).get(f"Monitor{monitor}", {}).get('file')
        
        return wallpaper_path
        
    except Exception as e:
        print(f"读取配置文件时出错: {e}")
        return None