# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: BSD-3-Clause
import os
import sys
from Tlog import TLog
log = TLog("初始化")
from WelcomeUI import get_wallpaper_engine_path_ui, check_other_versions_in_startup
from path_utils import resolve_path

def initialize_config():
    config_path = resolve_path("config.toml")
    if os.path.exists(config_path):
        return
    wallpaper_path, use_default_cursor = get_wallpaper_engine_path_ui()
    if wallpaper_path is None:
        log.error("未选择壁纸引擎路径,初始化结束")
        sys.exit()
    config_content = f"""[wallpaper]

[path]
wallpaper_engine_config = "{wallpaper_path.replace('\\', '/')}/config.json"

[config]
enable_default_icon_group = true
pause_on_fullscreen = false

[program_whitelist]
"""
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_content)
        print(f"配置文件已创建：{config_path}")
    except Exception as e:
        raise RuntimeError(f"创建配置文件失败：{e}") from e

    initialize_folders(use_default_cursor)


def initialize_folders(use_default_cursor=True):
    mouses_path = resolve_path("mouses")
    os.makedirs(mouses_path, exist_ok=True)
    print(f"已创建 mouses 文件夹：{mouses_path}")
    
    default_path = os.path.join(mouses_path, "默认")
    os.makedirs(default_path, exist_ok=True)
    print(f"已创建默认文件夹：{default_path}")


    if use_default_cursor:
        config_path = os.path.join(default_path, "config.toml")
        if not os.path.exists(config_path):
            cursor_files = {
                "Arrow": "aero_arrow.cur",
                "Help": "aero_helpsel.cur",
                "AppStarting": "aero_working.ani",
                "Wait": "aero_busy.ani",
                "Crosshair": "cross_i.cur",
                "IBeam": "beam_i.cur",
                "Handwriting": "aero_pen.cur",
                "No": "aero_unavail.cur",
                "SizeNS": "aero_ns.cur",
                "SizeWE": "aero_ew.cur",
                "SizeNWSE": "aero_nwse.cur",
                "SizeNESW": "aero_nesw.cur",
                "SizeAll": "aero_move.cur",
                "Hand": "aero_link.cur",
                "UpArrow": "aero_up.cur"
            }
            
            windows_cursors_path = os.path.join(os.environ.get("WINDIR", "C:\Windows"), "Cursors")
            
            config_content = "[mouses]\n"
            for cursor_name, cursor_file in cursor_files.items():
                cursor_path = os.path.join(windows_cursors_path, cursor_file)
                if os.path.exists(cursor_path):
                    cursor_path = cursor_path.replace('\\', '\\\\')
                    config_content += f'{cursor_name} = "{cursor_path}"\n'
                else:
                    config_content += f'{cursor_name} = ""\n'
            
            try:
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(config_content)
                print(f"已创建默认光标配置文件：{config_path}")
                print(f"已配置 {len(cursor_files)} 个光标文件路径")
            except Exception as e:
                log.error(f"创建默认光标配置文件失败：{e}")
    else:
        config_path = os.path.join(default_path, "config.toml")
        if not os.path.exists(config_path):
            config_content = '''[mouses]
Arrow = ""
Help = ""
AppStarting = ""
Wait = ""
Crosshair = ""
IBeam = ""
Handwriting = ""
No = ""
SizeNS = ""
SizeWE = ""
SizeNWSE = ""
SizeNESW = ""
SizeAll = ""
Hand = ""
UpArrow = ""
'''
            try:
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(config_content)
                print(f"已创建默认光标配置文件：{config_path}")
            except Exception as e:
                log.error(f"创建默认光标配置文件失败：{e}")


if __name__ == "__main__":
    log.val(check_other_versions_in_startup())
    initialize_config()
