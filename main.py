import time
import os
import shutil
import toml
from src.Tlog import TLog
import toml
log = TLog("main")
from src.mouses import 触发刷新,保存组配置,wallpaper,add_wallpaper,delete_wallpaper
from src.getWallpaperConfig import 获取当前壁纸路径
from src.setMouse import 设置鼠标指针




#mouse_path = r"mouses"
username = "woshi"

# wallpaper_engine 配置路径
config_path = toml.load("config.toml")["path"]["wallpaper_engine_config"]
log.debug(f"wallpaper_engine配置地址: {config_path}")

#保存配置("测试","mouses",[r"C:\Users\woshi\Desktop\1.ani","","","","","","","","","","","","","","",""])

#查询路径 = r"D:/Application/STEAM/steamapps/workshop/content/431960/3306588730/scene.pkg"
#查询结果 = wallpaper(查询路径,"config.toml")

#add_wallpaper("测试",查询路径,"config.toml")


#delete_wallpaper(查询路径,"config.toml")
log.debug("触发刷新")
触发刷新(config_path, username, 1)


last_result = None
while True:
    current = 获取当前壁纸路径(config_path, username, 1)
    if current != last_result:
        last_result = current
        触发刷新(config_path, username, 1)
    time.sleep(1)

"""
while True:
    触发刷新(config_path, username, 1)
    time.sleep(1)
"""
