# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: BSD-3-Clause
import webview
import os
import shutil
import toml
import base64
import io
import signal
from PIL import Image

from mouses import 保存组配置, CURSOR_ORDER_MAPPING
from Tlog import TLog

try:
    from ani_to_gif import get_ani_frames
except ImportError:
    get_ani_frames = None

try:
    from cur_to_png import get_cur_image
except ImportError:
    get_cur_image = None


log = TLog("EditMouse")

MOUSE_BASE_PATH = "mouses"
CURSOR_KEYS = CURSOR_ORDER_MAPPING[:]


class EditMouseApi:
    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

    def get_existing_groups(self):
        os.makedirs(MOUSE_BASE_PATH, exist_ok=True)
        return [
            d for d in os.listdir(MOUSE_BASE_PATH)
            if os.path.isdir(os.path.join(MOUSE_BASE_PATH, d))
        ]

    def load_group_config(self, group_name):
        path = os.path.join(MOUSE_BASE_PATH, group_name, "config.toml")
        empty = {k: "" for k in CURSOR_KEYS}

        if not os.path.exists(path):
            # 检查是否为默认组，如果是，尝试加载默认组配置
            if group_name == "默认组":
                default_path = os.path.join(MOUSE_BASE_PATH, "默认", "config.toml")
                if os.path.exists(default_path):
                    try:
                        data = toml.load(default_path).get("mouses", {})
                        return {k: data.get(k, "") for k in CURSOR_KEYS}
                    except Exception:
                        return empty
            return empty

        try:
            data = toml.load(path).get("mouses", {})
            return {k: data.get(k, "") for k in CURSOR_KEYS}
        except Exception:
            return empty

    def open_file_dialog(self):
        res = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=('Cursor Files (*.cur;*.ani)',)
        )
        return res[0] if res else ""

    def get_preview_base64(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return ""

        try:
            import hashlib
            # 缓存文件夹
            cache_folder = "html/cache"
            os.makedirs(cache_folder, exist_ok=True)
            
            # 生成基于文件路径的唯一哈希值
            file_hash = hashlib.md5(file_path.encode()).hexdigest()
            ext = os.path.splitext(file_path)[1].lower()
            
            # 根据文件类型确定缓存文件格式
            if ext == ".ani":
                cache_filename = f"preview_{file_hash}.gif"
            else:
                cache_filename = f"preview_{file_hash}.png"
            
            cache_path = os.path.join(cache_folder, cache_filename)
            cache_relative_path = os.path.join("cache", cache_filename).replace('\\', '/')
            
            # 如果缓存文件已存在，直接返回路径
            if os.path.exists(cache_path):
                return cache_relative_path
            
            # 处理不同类型的光标文件
            if ext == ".ani" and get_ani_frames:
                frames = get_ani_frames(file_path)
                if frames:
                    frames[0].save(
                        cache_path,
                        format="GIF",
                        save_all=True,
                        append_images=frames[1:],
                        duration=100,
                        loop=0,
                        disposal=2
                    )
                    return cache_relative_path

            if ext == ".cur" and get_cur_image:
                img = get_cur_image(file_path)
                if img:
                    img.save(cache_path, format="PNG")
                    return cache_relative_path

            # 处理其他图像格式
            img = Image.open(file_path).convert("RGBA")
            img.save(cache_path, format="PNG")
            return cache_relative_path

        except Exception as e:
            log.debug(f"预览生成失败: {e}")
            return ""

    def save_group_config(self, group_name, cursor_data, original_name=None):
        if not group_name.strip():
            return {"status": "error", "msg": "组名不能为空"}

        try:
            if original_name and original_name != group_name:
                src = os.path.join(MOUSE_BASE_PATH, original_name)
                dst = os.path.join(MOUSE_BASE_PATH, group_name)
                if os.path.exists(src) and not os.path.exists(dst):
                    shutil.copytree(src, dst)

            file_list = [cursor_data.get(k, "") for k in CURSOR_KEYS]

            保存组配置(
                name=group_name,
                folder_path=MOUSE_BASE_PATH,
                file_list=file_list
            )

            return {
                "status": "success",
                "msg": f"组 [{group_name}] 已保存"
            }

        except Exception as e:
            log.error(f"保存组失败: {e}")
            return {"status": "error", "msg": str(e)}


def on_window_closed():
    """窗口关闭时的回调函数"""
    log.info("鼠标组编辑器窗口已关闭")

if __name__ == "__main__":
    api = EditMouseApi()
    window = webview.create_window(
        "鼠标组编辑器",
        "html/mouseUI.html",
        js_api=api,
        width=900,
        height=765
    )
    api.set_window(window)
    
    # 注册窗口关闭回调
    window.events.closed += on_window_closed
    
    # 处理信号
    def signal_handler(signum, frame):
        log.info(f"收到信号 {signum}，正在关闭窗口...")
        if window:
            window.destroy()
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    log.info("鼠标组编辑器已启动")
    webview.start(debug=True)
    log.info("鼠标组编辑器已退出")
