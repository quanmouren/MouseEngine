import winreg
import ctypes
from ctypes import wintypes
import toml
import os
import sys
from Tlog import TLog

log = TLog("设置鼠标指针")
CURSOR_ORDER_MAPPING = [
    "Arrow",          # 0: 正常选择
    "Help",           # 1: 帮助选择
    "AppStarting",    # 2: 后台运行
    "Wait",           # 3: 忙
    "Crosshair",      # 4: 精准选择
    "IBeam",          # 5: 文本选择
    "Handwriting",    # 6: 手写
    "No",             # 7: 不可用
    "SizeNS",         # 8: 垂直调整大小
    "SizeWE",         # 9: 水平调整大小
    "SizeNWSE",       # 10: 沿对角线调整大小1
    "SizeNESW",       # 11: 沿对角线调整大小2
    "SizeAll",        # 12: 移动
    "Hand",           # 13: 链接选择
    "UpArrow"         # 14: 位置选择
]

def APP_ROOT() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = APP_ROOT()
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.toml")

MOUSES_DIR = os.path.join(PROJECT_ROOT, "mouses")
DEFAULT_GROUP_NAME = "默认"
DEFAULT_GROUP_DIR = os.path.join(MOUSES_DIR, DEFAULT_GROUP_NAME)
DEFAULT_GROUP_CONFIG = os.path.join(DEFAULT_GROUP_DIR, "config.toml")


def _safe_toml_load(path: str) -> dict:
    try:
        if not os.path.exists(path):
            log.error(f"TOML 不存在: {path}")
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return toml.load(f)
    except Exception as e:
        log.error(f"TOML 读取失败: {path} -> {e}")
        return {}


def 读取配置() -> bool:
    cfg = _safe_toml_load(CONFIG_PATH)
    c = cfg.get("config", {}) if isinstance(cfg, dict) else {}
    return bool(c.get("enable_default_icon_group", False))


def _abs_from_project(path_str: str) -> str:
    s = str(path_str).strip().replace("/", "\\")
    if not s:
        return ""
    if os.path.isabs(s):
        return os.path.abspath(s)
    return os.path.abspath(os.path.join(PROJECT_ROOT, s))


def 获取默认图标路径(index: int) -> str | None:
    if not os.path.isdir(DEFAULT_GROUP_DIR):
        log.error(f"默认光标组不存在: mouses\\{DEFAULT_GROUP_NAME}")
        return None

    cfg = _safe_toml_load(DEFAULT_GROUP_CONFIG)
    mouses_cfg = cfg.get("mouses", {}) if isinstance(cfg, dict) else {}

    if not (0 <= index < len(CURSOR_ORDER_MAPPING)):
        return None

    cursor_name = CURSOR_ORDER_MAPPING[index]
    rel = mouses_cfg.get(cursor_name)
    if not rel:
        return None

    rel = str(rel).strip().replace("/", "\\")
    if rel.lower().startswith("mouses\\"):
        abs_path = _abs_from_project(rel)
    else:
        abs_path = os.path.abspath(os.path.join(DEFAULT_GROUP_DIR, rel))

    return abs_path if os.path.exists(abs_path) else None


def 设置鼠标指针(cursor_paths):
    log.debug(f"收到样式: {cursor_paths}")

    enable_default = 读取配置()
    if enable_default:
        log.debug(f"默认鼠标组已启用：mouses\\{DEFAULT_GROUP_NAME}")
    else:
        log.debug("默认鼠标组未启用")

    def update_system_cursors():
        # SPI_SETCURSORS: 0x0057
        # SPIF_SENDCHANGE: 0x01（广播变更）
        ctypes.windll.user32.SystemParametersInfoW(
            wintypes.UINT(0x0057),
            wintypes.UINT(0),
            wintypes.LPVOID(None),
            wintypes.UINT(0x01)
        )

    base_reg_path = r"Control Panel\Cursors"

    try:
        base_key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            base_reg_path,
            0,
            winreg.KEY_SET_VALUE
        )

        for index, cursor_name in enumerate(CURSOR_ORDER_MAPPING):
            cursor_path = None

            original_path = None
            if isinstance(cursor_paths, (list, tuple)) and index < len(cursor_paths):
                original_path = cursor_paths[index]
            if original_path is None or str(original_path).strip() == "":
                if enable_default:
                    default_path = 获取默认图标路径(index)
                    if default_path:
                        log.debug(f"使用默认光标 {cursor_name}: {default_path}")
                        cursor_path = default_path
                    else:
                        log.debug(f"默认光标缺失，跳过: {cursor_name}")
                else:
                    log.debug(f"未提供光标且未启用默认组，跳过: {cursor_name}")
            else:
                candidate_path = _abs_from_project(original_path)
                log.debug(f"处理光标 {cursor_name}: {candidate_path}")

                if os.path.exists(candidate_path):
                    cursor_path = candidate_path
                else:
                    log.error(f"文件不存在 - {candidate_path}")
                    if enable_default:
                        default_path = 获取默认图标路径(index)
                        if default_path:
                            log.debug(f"使用默认光标 {cursor_name} 替代: {default_path}")
                            cursor_path = default_path

            # 写注册表
            if cursor_path and str(cursor_path).strip():
                winreg.SetValueEx(base_key, cursor_name, 0, winreg.REG_SZ, cursor_path)
            else:
                log.debug(f"跳过空光标设置: {cursor_name}")

        winreg.CloseKey(base_key)
        update_system_cursors()
        return True

    except Exception as e:
        log.error(f"设置出错: {e}")
        return False


if __name__ == "__main__":
    设置鼠标指针([""] * 16)
    #设置鼠标指针(["mouses\\芙宁娜\\1.ani", "mouses\\芙宁娜\\111.ani", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])
