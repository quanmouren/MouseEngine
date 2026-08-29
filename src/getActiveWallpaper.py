# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

import ctypes
import getpass
import json
import time
from pathlib import Path
from typing import Any

import toml

from Tlog import TLog
from path_utils import resolve_path


log = TLog("获取当前活跃壁纸")

CONFIG_FILE_PATH = Path(resolve_path("config.toml"))
DEFAULT_MOUSE_PROBE_DLL = Path(resolve_path("mouse_probe.dll"))
DEFAULT_PLAYLISTSTATE_READER_DLL = Path(resolve_path("playliststate_reader.dll"))

ME_DEVICE_NAME_LEN = 32
ME_DISPLAY_NAME_LEN = 128

_last_ids: set[str] = set()
_last_check_time = 0.0
_mouse_probe_dll: ctypes.CDLL | None = None
_playliststate_reader_dll: ctypes.CDLL | None = None


class ME_MonitorInfo(ctypes.Structure):
    _fields_ = [
        ("hmonitor", ctypes.c_uint64),
        ("device_name", ctypes.c_wchar * ME_DEVICE_NAME_LEN),
        ("display_name", ctypes.c_wchar * ME_DISPLAY_NAME_LEN),
        ("left", ctypes.c_int32),
        ("top", ctypes.c_int32),
        ("right", ctypes.c_int32),
        ("bottom", ctypes.c_int32),
        ("work_left", ctypes.c_int32),
        ("work_top", ctypes.c_int32),
        ("work_right", ctypes.c_int32),
        ("work_bottom", ctypes.c_int32),
        ("dpi_x", ctypes.c_uint32),
        ("dpi_y", ctypes.c_uint32),
        ("is_primary", ctypes.c_int32),
    ]


def _resolve_path(path: str | Path) -> Path:
    return Path(resolve_path(str(path)))


def load_main_config(config_path: str | Path = CONFIG_FILE_PATH) -> dict[str, Any]:
    resolved_config_path = _resolve_path(config_path)
    if not resolved_config_path.exists():
        raise FileNotFoundError(f"找不到主配置文件: {resolved_config_path}")
    return toml.load(resolved_config_path)


def get_wallpaper_engine_root_from_config(
    config_path: str | Path = CONFIG_FILE_PATH,
) -> Path:
    config_data = load_main_config(config_path)
    wallpaper_config = str(
        config_data.get("path", {}).get("wallpaper_engine_config", "") or ""
    ).strip()
    if not wallpaper_config:
        raise RuntimeError("config.toml 缺少 [path].wallpaper_engine_config")

    wallpaper_config_path = _resolve_path(wallpaper_config)
    if wallpaper_config_path.name.lower() == "config.json":
        return wallpaper_config_path.parent
    return wallpaper_config_path


def resolve_wallpaper_engine_root(
    wallpaper_engine_root: str | Path | None = None,
) -> Path:
    if wallpaper_engine_root is None:
        return get_wallpaper_engine_root_from_config()
    return _resolve_path(wallpaper_engine_root)


def load_mouse_probe(
    dll_path: str | Path | ctypes.CDLL = DEFAULT_MOUSE_PROBE_DLL,
) -> ctypes.CDLL:
    global _mouse_probe_dll

    if isinstance(dll_path, ctypes.CDLL):
        return dll_path
    if _mouse_probe_dll is not None and _resolve_path(dll_path) == DEFAULT_MOUSE_PROBE_DLL:
        return _mouse_probe_dll

    resolved_dll_path = _resolve_path(dll_path)
    if not resolved_dll_path.exists():
        raise FileNotFoundError(f"找不到 mouse_probe.dll: {resolved_dll_path}")

    dll = ctypes.CDLL(str(resolved_dll_path))
    dll.get_mouse_at_cursor.argtypes = [ctypes.POINTER(ME_MonitorInfo)]
    dll.get_mouse_at_cursor.restype = ctypes.c_int

    if resolved_dll_path == DEFAULT_MOUSE_PROBE_DLL:
        _mouse_probe_dll = dll
    return dll


def load_playliststate_reader(
    dll_path: str | Path | ctypes.CDLL = DEFAULT_PLAYLISTSTATE_READER_DLL,
) -> ctypes.CDLL:
    global _playliststate_reader_dll

    if isinstance(dll_path, ctypes.CDLL):
        return dll_path
    if (
        _playliststate_reader_dll is not None
        and _resolve_path(dll_path) == DEFAULT_PLAYLISTSTATE_READER_DLL
    ):
        return _playliststate_reader_dll

    resolved_dll_path = _resolve_path(dll_path)
    if not resolved_dll_path.exists():
        raise FileNotFoundError(
            f"找不到 playliststate_reader.dll: {resolved_dll_path}"
        )

    dll = ctypes.CDLL(str(resolved_dll_path))
    dll.we_get_monitor_details_json.argtypes = [ctypes.c_char_p]
    dll.we_get_monitor_details_json.restype = ctypes.c_void_p
    dll.we_free_string.argtypes = [ctypes.c_void_p]
    dll.we_free_string.restype = None

    if resolved_dll_path == DEFAULT_PLAYLISTSTATE_READER_DLL:
        _playliststate_reader_dll = dll
    return dll


def monitor_info_to_dict(info: ME_MonitorInfo) -> dict[str, Any]:
    return {
        "hmonitor": int(info.hmonitor),
        "device_name": info.device_name,
        "display_name": info.display_name,
        "rect": [int(info.left), int(info.top), int(info.right), int(info.bottom)],
        "work_rect": [
            int(info.work_left),
            int(info.work_top),
            int(info.work_right),
            int(info.work_bottom),
        ],
        "dpi": [int(info.dpi_x), int(info.dpi_y)],
        "is_primary": bool(info.is_primary),
    }


def get_mouse_monitor(
    mouse_probe_dll: str | Path | ctypes.CDLL = DEFAULT_MOUSE_PROBE_DLL,
) -> dict[str, Any]:
    dll = load_mouse_probe(mouse_probe_dll)
    info = ME_MonitorInfo()
    ok = dll.get_mouse_at_cursor(ctypes.byref(info))
    if not ok:
        raise RuntimeError("get_mouse_at_cursor 调用失败")
    return monitor_info_to_dict(info)


def get_mouse_monitor_python_fallback() -> dict[str, Any]:
    try:
        import pyautogui
        from screeninfo import get_monitors
    except Exception as e:
        raise RuntimeError(f"Python 鼠标显示器兜底不可用: {e}") from e

    mouse_x, mouse_y = pyautogui.position()
    monitors = list(get_monitors())
    if not monitors:
        raise RuntimeError("Python 鼠标显示器兜底未获取到显示器列表")

    for index, monitor in enumerate(monitors):
        left = int(monitor.x)
        top = int(monitor.y)
        right = left + int(monitor.width)
        bottom = top + int(monitor.height)
        if left <= mouse_x < right and top <= mouse_y < bottom:
            return {
                "hmonitor": 0,
                "device_name": str(getattr(monitor, "name", "") or ""),
                "display_name": str(getattr(monitor, "name", "") or ""),
                "rect": [left, top, right, bottom],
                "is_primary": bool(getattr(monitor, "is_primary", False)),
                "index": index,
                "fallback_source": "pyautogui_screeninfo",
            }

    monitor = monitors[0]
    left = int(monitor.x)
    top = int(monitor.y)
    return {
        "hmonitor": 0,
        "device_name": str(getattr(monitor, "name", "") or ""),
        "display_name": str(getattr(monitor, "name", "") or ""),
        "rect": [left, top, left + int(monitor.width), top + int(monitor.height)],
        "is_primary": bool(getattr(monitor, "is_primary", False)),
        "index": 0,
        "fallback_source": "pyautogui_screeninfo_first_monitor",
    }


def call_playliststate_details(
    wallpaper_engine_root: str | Path | None = None,
    playliststate_reader_dll: str | Path | ctypes.CDLL = DEFAULT_PLAYLISTSTATE_READER_DLL,
) -> dict[str, Any]:
    dll = load_playliststate_reader(playliststate_reader_dll)
    root = resolve_wallpaper_engine_root(wallpaper_engine_root)
    ptr = dll.we_get_monitor_details_json(str(root).encode("utf-8"))
    if not ptr:
        raise RuntimeError("we_get_monitor_details_json 返回了空指针 NULL")

    try:
        raw_json = ctypes.string_at(ptr).decode("utf-8", errors="replace")
    finally:
        dll.we_free_string(ptr)

    result = json.loads(raw_json)
    if isinstance(result, dict) and "error" in result:
        raise RuntimeError(f"playliststate_reader.dll error: {result['error']}")
    return result


def normalize_device_name(value: str) -> str:
    return str(value or "").replace("\\", "/").lower()


def normalize_rect(value: Any) -> list[int]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return []
    try:
        return [int(v) for v in value]
    except Exception:
        return []


def rects_match_across_dpi(a: list[int], b: list[int]) -> bool:
    if not a or not b:
        return False
    aw = abs(a[2] - a[0])
    ah = abs(a[3] - a[1])
    bw = abs(b[2] - b[0])
    bh = abs(b[3] - b[1])
    if not aw or not ah or not bw or not bh:
        return False

    same_anchor = (
        (a[0] == b[0] == 0)
        or (a[2] == b[2] == 0)
        or (a[1] == b[1] == 0)
        or (a[3] == b[3] == 0)
    )
    same_aspect = abs((aw / ah) - (bw / bh)) < 0.03
    return same_anchor and same_aspect


def find_mouse_playliststate_item(
    mouse_monitor: dict[str, Any],
    playliststate_details: dict[str, Any],
) -> dict[str, Any]:
    items = list(playliststate_details.get("items") or [])
    mouse_hmonitor = int(mouse_monitor.get("hmonitor") or 0)
    mouse_device = normalize_device_name(mouse_monitor.get("device_name", ""))
    mouse_rect = normalize_rect(mouse_monitor.get("rect"))
    mouse_is_primary = mouse_monitor.get("is_primary")

    for item in items:
        if mouse_hmonitor and int(item.get("hmon") or 0) == mouse_hmonitor:
            return item

    for item in items:
        if mouse_device and normalize_device_name(item.get("device_name", "")) == mouse_device:
            return item

    for item in items:
        if mouse_rect and normalize_rect(item.get("rect")) == mouse_rect:
            return item

    for item in items:
        item_rect = normalize_rect(item.get("rect"))
        if mouse_rect and rects_match_across_dpi(mouse_rect, item_rect):
            return item

    primary_matches = [
        item for item in items
        if mouse_is_primary is not None and bool(item.get("is_primary")) == bool(mouse_is_primary)
    ]
    if len(primary_matches) == 1:
        return primary_matches[0]

    if len(items) == 1:
        return items[0]

    raise RuntimeError("无法把鼠标所在显示器匹配到 playliststate_reader.dll 的显示器详情")


_we_monitormap_cache: dict[str, Any] = {}
_we_monitormap_cache_time = 0.0


def _get_we_monitormap() -> dict[str, Any]:
    """读取 Wallpaper Engine config.json 的 monitormap（key -> {location, timestamp, ...}）。
    带短缓存5秒
    """
    global _we_monitormap_cache, _we_monitormap_cache_time
    now = time.time()
    if _we_monitormap_cache and now - _we_monitormap_cache_time < 5.0:
        return _we_monitormap_cache
    try:
        cfg = toml.load(CONFIG_FILE_PATH)
        we_path = str(cfg.get("path", {}).get("wallpaper_engine_config", "") or "").strip()
        if not we_path or not Path(we_path).exists():
            _we_monitormap_cache = {}
        else:
            data = json.load(open(we_path, "r", encoding="utf-8"))
            user = getpass.getuser()
            mm = data.get(user, {}).get("general", {}).get("user", {}).get("monitormap", {})
            _we_monitormap_cache = {
                str(k): v for k, v in mm.items() if isinstance(v, dict)
            }
    except Exception as e:
        log.error(f"读取 monitormap 失败: {e}")
        _we_monitormap_cache = {}
    _we_monitormap_cache_time = now
    return _we_monitormap_cache


def _resolve_we_monitor_location(device_id: str, device_name: str, monitormap: dict[str, Any]) -> int:
    """用硬件型号（DeviceID 里的型号名）+ 最新 timestamp 解析显示器对应的 WE location"""
    if not monitormap:
        return -1
    norm_name = str(device_name or "").replace(chr(92), "/")
    model = ""
    parts = str(device_id or "").split(chr(92))
    if len(parts) >= 2:
        model = parts[1]
    best = None
    for key, val in monitormap.items():
        if not isinstance(val, dict):
            continue
        matched = (norm_name and key == norm_name) or (model and model in key)
        if not matched:
            continue
        ts = val.get("timestamp", 0) or 0
        if best is None or ts > best[0]:
            best = (ts, val)
    if best is not None:
        try:
            return int(best[1].get("location", -1))
        except Exception:
            pass
    return -1


def load_monitor_current_ids(
    wallpaper_engine_root: str | Path | None = None,
    playliststate_reader_dll: str | Path | ctypes.CDLL = DEFAULT_PLAYLISTSTATE_READER_DLL,
) -> dict[str, str]:
    """调用 DLL we_get_monitor_current_ids_json，返回 {MonitorN: current_id}。"""
    dll = load_playliststate_reader(playliststate_reader_dll)
    root = resolve_wallpaper_engine_root(wallpaper_engine_root)
    dll.we_get_monitor_current_ids_json.argtypes = [ctypes.c_char_p]
    dll.we_get_monitor_current_ids_json.restype = ctypes.c_void_p
    ptr = dll.we_get_monitor_current_ids_json(str(root).encode("utf-8"))
    if not ptr:
        return {}
    try:
        raw_json = ctypes.string_at(ptr).decode("utf-8", errors="replace")
    finally:
        dll.we_free_string(ptr)
    result = json.loads(raw_json)
    if isinstance(result, dict) and "error" in result:
        raise RuntimeError(f"playliststate_reader.dll error: {result['error']}")
    return result if isinstance(result, dict) else {}


_we_selected_ids_cache: dict[str, str] = {}
_we_selected_ids_mtime = 0.0


def _get_we_config_selected_ids() -> tuple[dict[str, str], float]:
    global _we_selected_ids_cache, _we_selected_ids_mtime
    try:
        cfg = toml.load(CONFIG_FILE_PATH)
        we_path = str(cfg.get("path", {}).get("wallpaper_engine_config", "") or "").strip()
    except Exception as e:
        log.error(f"读取 config.toml 失败: {e}")
        return {}, 0.0

    if not we_path or not Path(we_path).exists():
        _we_selected_ids_cache = {}
        _we_selected_ids_mtime = 0.0
        return {}, 0.0

    try:
        mtime = Path(we_path).stat().st_mtime
    except OSError as e:
        log.error(f"获取 config.json mtime 失败: {e}")
        return {}, 0.0

    if _we_selected_ids_cache and mtime == _we_selected_ids_mtime:
        return _we_selected_ids_cache, mtime

    try:
        data = json.load(open(we_path, "r", encoding="utf-8"))
        user = getpass.getuser()
        general = data.get(user, {}).get("general", {})
        selected = general.get("wallpaperconfig", {}).get("selectedwallpapers", {})
        ids: dict[str, str] = {}
        for k, v in selected.items():
            if isinstance(v, dict):
                fp = str(v.get("file", "") or "")
                if fp:
                    ids[str(k)] = Path(fp.replace(chr(92), "/")).parent.name
        _we_selected_ids_cache = ids
        _we_selected_ids_mtime = mtime
    except Exception as e:
        log.error(f"读取 wallpaperconfig.selectedwallpapers 失败: {e}")
        _we_selected_ids_cache = {}
        _we_selected_ids_mtime = mtime
    return _we_selected_ids_cache, _we_selected_ids_mtime


def _get_playliststate_mtime() -> float:
    try:
        root = get_wallpaper_engine_root_from_config()
        bin_path = Path(root) / "bin" / "playliststate.bin"
        if bin_path.exists():
            return bin_path.stat().st_mtime
    except Exception as e:
        log.error(f"获取 playliststate.bin mtime 失败: {e}")
    return 0.0


def get_mouse_playliststate_detail(
    wallpaper_engine_root: str | Path | None = None,
    mouse_probe_dll: str | Path | ctypes.CDLL = DEFAULT_MOUSE_PROBE_DLL,
    playliststate_reader_dll: str | Path | ctypes.CDLL = DEFAULT_PLAYLISTSTATE_READER_DLL,
) -> dict[str, Any]:
    details = call_playliststate_details(wallpaper_engine_root, playliststate_reader_dll)
    try:
        mouse_monitor = get_mouse_monitor(mouse_probe_dll)
    except Exception as e:
        mouse_monitor = get_mouse_monitor_python_fallback()
        mouse_monitor["mouse_probe_error"] = str(e)
    item = find_mouse_playliststate_item(mouse_monitor, details)

    device_id = str(item.get("device_id") or "") if item else ""
    monitormap = _get_we_monitormap()
    location = _resolve_we_monitor_location(
        device_id, mouse_monitor.get("device_name", ""), monitormap
    )
    if location >= 0:
        we_key = "Monitor" + str(location)
        config_ids, config_mtime = _get_we_config_selected_ids()
        if config_mtime >= _get_playliststate_mtime() and config_ids.get(we_key):
            current_id = str(config_ids.get(we_key, ""))
        else:
            current_ids = load_monitor_current_ids(wallpaper_engine_root, playliststate_reader_dll)
            current_id = str(current_ids.get(we_key, "") or "")
    else:
        current_id = str(item.get("current_id") or "") if item else ""

    return {
        "mouse_monitor": mouse_monitor,
        "playliststate_item": item,
        "current_id": current_id,
    }


def getPlayliststateID_for_monitor(
    mouse_monitor: dict[str, Any],
    wallpaper_engine_root: str | Path | None = None,
    playliststate_reader_dll: str | Path | ctypes.CDLL = DEFAULT_PLAYLISTSTATE_READER_DLL,
) -> str:
    details = call_playliststate_details(wallpaper_engine_root, playliststate_reader_dll)
    item = find_mouse_playliststate_item(mouse_monitor, details)
    current_id = str(item.get("current_id") or "")
    if not current_id:
        raise RuntimeError("鼠标所在显示器没有 current_id")
    return current_id


def getPlayliststateID(
    wallpaper_engine_root: str | Path | None = None,
    mouse_probe_dll: str | Path | ctypes.CDLL = DEFAULT_MOUSE_PROBE_DLL,
    playliststate_reader_dll: str | Path | ctypes.CDLL = DEFAULT_PLAYLISTSTATE_READER_DLL,
) -> str:
    detail = get_mouse_playliststate_detail(
        wallpaper_engine_root,
        mouse_probe_dll,
        playliststate_reader_dll,
    )
    current_id = detail["current_id"]
    if not current_id:
        raise RuntimeError("鼠标所在显示器没有 current_id")
    return current_id


def _extract_current_ids(playliststate_details: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for item in playliststate_details.get("items") or []:
        current_id = str(item.get("current_id") or "").strip()
        if current_id:
            ids.add(current_id)
    return ids


def get_active_ids() -> set[str]:
    """
    获取当前活跃的 Wallpaper Engine 壁纸 ID。

    数据来源是 playliststate_reader.dll 读取的 playliststate.bin，不再扫描进程句柄。
    """
    global _last_ids, _last_check_time

    current_time = time.time()
    if current_time - _last_check_time < 1.0:
        return _last_ids.copy()

    try:
        details = call_playliststate_details()
        active_ids = _extract_current_ids(details)
        _last_ids = active_ids
        _last_check_time = current_time
        return active_ids.copy()
    except Exception as e:
        log.error(f"获取壁纸ID失败: {e}")
        return _last_ids.copy()


if __name__ == "__main__":
    for i in range(100):
        start_time = time.perf_counter()
        tempval = get_active_ids()
        end_time = time.perf_counter()

        log.val(tempval)
        log.debug(f"第{i + 1:02d}次执行 - 执行时间: {end_time - start_time:.4f}秒")

        time.sleep(0.5)
