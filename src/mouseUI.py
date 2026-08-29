# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: BSD-3-Clause
import webview
import os
import shutil
import toml
import base64
import io
import signal
import threading
from PIL import Image
from lib.INFParser import INFParser
from mouses import 保存组配置, CURSOR_ORDER_MAPPING, read_group_meta, build_group_meta, 导出组, 导入组包, MOUSE_GROUP_PACK_EXT
from setMouse import 设置鼠标指针
from Tlog import TLog
from path_utils import resolve_path
from i18n_utils import get_language

try:
    from ani_to_gif import get_ani_frames
except ImportError:
    get_ani_frames = None

try:
    from cur_to_png import get_cur_image
except ImportError:
    get_cur_image = None


log = TLog("EditMouse")

MOUSE_BASE_PATH = resolve_path("mouses")
CURSOR_KEYS = CURSOR_ORDER_MAPPING[:]
CONFIG_PATH = resolve_path("config.toml")


class EditMouseApi:
    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

    def get_language(self):
        return get_language()

    def get_existing_groups(self):
        os.makedirs(MOUSE_BASE_PATH, exist_ok=True)
        return [
            d for d in os.listdir(MOUSE_BASE_PATH)
            if os.path.isdir(os.path.join(MOUSE_BASE_PATH, d))
        ]

    def get_group_meta(self, group_name):
        """
        获取鼠标组元数据。
        返回字典: { author, url, created_date, added_date }
        author / url 为空字符串时表示未填写，前端可不显示。
        """
        empty = {
            "author": "",
            "url": "",
            "created_date": "",
            "added_date": "",
        }
        if not group_name:
            return empty

        config_path = os.path.join(MOUSE_BASE_PATH, group_name, "config.toml")
        meta = read_group_meta(config_path)
        if not meta:
            return empty

        return {
            "author": str(meta.get("author", "") or ""),
            "url": str(meta.get("url", "") or ""),
            "created_date": str(meta.get("created_date", "") or ""),
            "added_date": str(meta.get("added_date", "") or ""),
        }

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
        import threading
        done = threading.Event()
        result_box = [None]
        
        def worker():
            try:
                res = self._window.create_file_dialog(
                    webview.OPEN_DIALOG,
                    allow_multiple=False,
                    file_types=('Cursor Files (*.cur;*.ani)',)
                )
                result_box[0] = res[0] if res else ""
            except Exception as e:
                log.error(f"文件选择失败: {e}")
                result_box[0] = ""
            finally:
                done.set()
        
        threading.Thread(target=worker, daemon=True).start()
        done.wait()
        return result_box[0]

    def _build_or_reuse_preview(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return ""

        try:
            import hashlib
            cache_folder = resolve_path("html/cache")
            os.makedirs(cache_folder, exist_ok=True)

            file_hash = hashlib.md5(file_path.encode()).hexdigest()
            ext = os.path.splitext(file_path)[1].lower()

            if ext == ".ani":
                cache_filename = f"preview_{file_hash}.gif"
            else:
                cache_filename = f"preview_{file_hash}.webp"
            cache_path = os.path.join(cache_folder, cache_filename)
            cache_relative_path = os.path.join("cache", cache_filename).replace('\\', '/')

            try:
                src_mtime = os.path.getmtime(file_path)
                if os.path.exists(cache_path) and os.path.getmtime(cache_path) >= src_mtime:
                    return cache_relative_path
            except OSError:
                pass

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
                        disposal=2,
                    )
                    try:
                        os.utime(cache_path, (src_mtime, src_mtime))
                    except OSError:
                        pass
                    return cache_relative_path

            if ext == ".cur" and get_cur_image:
                img = get_cur_image(file_path)
                if img:
                    tmp = cache_path + ".tmp"
                    img.save(tmp, format="WEBP", quality=80, method=4)
                    os.replace(tmp, cache_path)
                    try:
                        os.utime(cache_path, (src_mtime, src_mtime))
                    except OSError:
                        pass
                    return cache_relative_path

            img = Image.open(file_path).convert("RGBA")
            tmp = cache_path + ".tmp"
            img.save(tmp, format="WEBP", quality=80, method=4)
            os.replace(tmp, cache_path)
            try:
                os.utime(cache_path, (src_mtime, src_mtime))
            except OSError:
                pass
            return cache_relative_path
        except Exception as e:
            log.debug(f"预览生成失败: {file_path} - {e}")
            return ""

    def get_preview_base64(self, file_path):
        return self._build_or_reuse_preview(file_path)

    def get_all_cursor_previews(self, groups_config):
        if not isinstance(groups_config, dict):
            return {}
        result = {}
        for group_name, cursor_map in groups_config.items():
            if not isinstance(cursor_map, dict):
                result[group_name] = {}
                continue
            group_out = {}
            for key, path in cursor_map.items():
                if path:
                    group_out[key] = self._build_or_reuse_preview(path)
                else:
                    group_out[key] = ""
            result[group_name] = group_out
        return result

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

    def delete_group(self, group_name):
        if group_name == "默认组":
            return {"status": "error", "msg": "默认组无法删除"}

        try:
            from mouses import 删除鼠标组
            success = 删除鼠标组(group_name)
            if success:
                return {"status": "success", "msg": f"组 [{group_name}] 已删除"}
            else:
                return {"status": "error", "msg": f"删除组 [{group_name}] 失败"}
        except Exception as e:
            log.error(f"删除组失败: {e}")
            return {"status": "error", "msg": str(e)}

    def rename_group(self, old_group_name, new_group_name):
        if old_group_name == "默认组":
            return {"status": "error", "msg": "默认组无法重命名"}

        if old_group_name == new_group_name:
            return {"status": "success", "msg": "组名未变更"}

        try:
            from mouses import 重命名鼠标组
            success = 重命名鼠标组(old_group_name, new_group_name)
            if success:
                return {"status": "success", "msg": f"组 [{old_group_name}] 已重命名为 [{new_group_name}]"}
            else:
                return {"status": "error", "msg": f"重命名组 [{old_group_name}] 失败"}
        except Exception as e:
            log.error(f"重命名组失败: {e}")
            return {"status": "error", "msg": str(e)}

    def apply_group(self, group_name):
        if not group_name:
            return {"status": "error", "msg": "组名不能为空"}

        group_config_path = os.path.join(MOUSE_BASE_PATH, group_name, "config.toml")
        if not os.path.exists(group_config_path):
            return {"status": "error", "msg": f"组 [{group_name}] 配置不存在"}

        try:
            group_config = toml.load(group_config_path)
            mouses_section = group_config.get("mouses", {})
            if not isinstance(mouses_section, dict):
                return {"status": "error", "msg": "鼠标组配置格式无效"}

            cursor_paths = [mouses_section.get(key, "") for key in CURSOR_KEYS]
            if not 设置鼠标指针(cursor_paths):
                return {"status": "error", "msg": "应用鼠标组失败"}

            if os.path.exists(CONFIG_PATH):
                config_data = toml.load(CONFIG_PATH)
            else:
                config_data = {}
            config_data.setdefault("config", {})
            config_data["config"]["specified_mouse_group"] = group_name
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                toml.dump(config_data, f)

            return {"status": "success", "msg": f"已应用组 [{group_name}]"}
        except Exception as e:
            log.error(f"应用组失败: {e}")
            return {"status": "error", "msg": str(e)}

    def export_group(self, group_name):
        """
        导出鼠标组为 .mepack (zip) 文件。
        - 默认组允许导出
        - 通过 webview SAVE_DIALOG 让用户选择保存位置
        - 用户取消对话框返回 status=cancelled
        """
        if not group_name or not group_name.strip():
            return {"status": "error", "msg": "组名不能为空"}

        group_folder = os.path.join(MOUSE_BASE_PATH, group_name)
        if not os.path.isdir(group_folder):
            return {"status": "error", "msg": f"组 [{group_name}] 不存在"}

        import threading
        done = threading.Event()
        result_box = [None]

        def worker():
            try:
                default_filename = f"{group_name}{MOUSE_GROUP_PACK_EXT}"
                res = self._window.create_file_dialog(
                    webview.SAVE_DIALOG,
                    directory="",
                    save_filename=default_filename,
                    file_types=(f"MouseEngine 鼠标组包 (*{MOUSE_GROUP_PACK_EXT})",)
                )
                if not res:
                    result_box[0] = {"status": "cancelled", "msg": "已取消导出"}
                    return

                target_path = res[0] if isinstance(res, (list, tuple)) else res
                if not target_path:
                    result_box[0] = {"status": "cancelled", "msg": "已取消导出"}
                    return

                success, msg = 导出组(group_name, target_path)
                if success:
                    result_box[0] = {"status": "success", "msg": f"已导出组 [{group_name}] → {msg}"}
                else:
                    result_box[0] = {"status": "error", "msg": f"导出失败: {msg}"}
            except Exception as e:
                log.error(f"导出组失败: {e}")
                result_box[0] = {"status": "error", "msg": str(e)}
            finally:
                done.set()

        threading.Thread(target=worker, daemon=True).start()
        done.wait()
        return result_box[0]

    def 导入组(self):
        """
        导入鼠标组（统一入口）。
        - 文件对话框同时支持 .inf 和 .mepack
        - 选中后按扩展名二次分流：
            * .mepack -> mouses.导入组包
            * 其他   -> 原有 INFParser 流程
        返回 {status, msg, group_name?}：
            status: 'success' / 'cancelled' / 'error'
        """
        import threading
        done = threading.Event()
        result_box = [None]

        def worker():
            try:
                # 二次判断的第一步：弹文件对话框，让用户选类型
                # pywebview 期望 file_types 是 list of strings，每个 string 形如 "描述 (*.ext)"
                res = self._window.create_file_dialog(
                    webview.OPEN_DIALOG,
                    allow_multiple=False,
                    file_types=(
                        f"MouseEngine 鼠标组包 (*{MOUSE_GROUP_PACK_EXT})",
                        "INF 主题 (*.inf)",
                    )
                )
                if not res:
                    result_box[0] = {"status": "cancelled", "msg": "已取消导入"}
                    return

                file_path = res[0] if isinstance(res, (list, tuple)) else res
                if not file_path:
                    result_box[0] = {"status": "cancelled", "msg": "已取消导入"}
                    return

                # 二次判断的第二步：按扩展名二次分流
                ext = os.path.splitext(file_path)[1].lower()
                if ext == MOUSE_GROUP_PACK_EXT:
                    # 分流到 .mepack 导入
                    success, msg, group_name = 导入组包(file_path)
                    if success:
                        result_box[0] = {
                            "status": "success",
                            "msg": msg,
                            "group_name": group_name,
                        }
                    else:
                        result_box[0] = {"status": "error", "msg": f"导入失败: {msg}"}
                    return

                # 默认按 INF 流程处理
                parser = INFParser(file_path)
                cursor_paths, scheme_name = parser.get_cursor_paths_in_order()
                log.val(f"cursor_paths: {cursor_paths}")
                log.val(f"scheme_name: {scheme_name}")
                if scheme_name and cursor_paths != ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '']:
                    保存组配置(scheme_name, "mouses", cursor_paths, is_import=True)
                    result_box[0] = {
                        "status": "success",
                        "msg": f"已导入组 [{scheme_name}]",
                        "group_name": scheme_name,
                    }
                else:
                    log.error(f"导入组失败: 为空组 ({file_path})")
                    result_box[0] = {"status": "error", "msg": "INF 解析失败或为空组"}
            except Exception as e:
                log.error(f"导入组失败: {e}")
                result_box[0] = {"status": "error", "msg": str(e)}
            finally:
                done.set()

        threading.Thread(target=worker, daemon=True).start()
        done.wait()
        return result_box[0]


def on_window_closed():
    """窗口关闭时的回调函数"""
    log.info("鼠标组编辑器窗口已关闭")

if __name__ == "__main__":
    api = EditMouseApi()
    # 获取 HTML 文件的绝对路径
    import os
    html_file = resolve_path("html/mouseUI.html")
    window = webview.create_window(
        "MouseEngine-鼠标组编辑器",
        html_file,
        js_api=api,
        width=900,
        height=765,
        easy_drag=True,
        resizable=True,
        text_select=False
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
    if log.on_DEBUG:
        webview.start(debug=True)
    else:
        webview.start()

    log.info("鼠标组编辑器已退出")
