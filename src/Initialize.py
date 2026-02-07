# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: BSD-3-Clause
import os
import sys
from Tlog import TLog
log = TLog("初始化")
from WelcomeUI import get_wallpaper_engine_path_ui
def initialize_config():
    config_path = "config.toml"
    if os.path.exists(config_path):
        return
    wallpaper_path = get_wallpaper_engine_path_ui()
    if wallpaper_path is None:
        log.error("未选择壁纸引擎路径,初始化结束")
        sys.exit()
    config_content = f"""[wallpaper]

[path]
wallpaper_engine_config = "{wallpaper_path.replace('\\', '/')}/config.json"

[config]
enable_default_icon_group = true
"""
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_content)
        print(f"配置文件已创建：{config_path}")
    except Exception as e:
        raise RuntimeError(f"创建配置文件失败：{e}") from e
def test():
    pass
if __name__ == "__main__":
    initialize_config()