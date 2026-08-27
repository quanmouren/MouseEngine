# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: BSD-3-Clause

import ctypes
import json
import os
import shutil
import time
from contextlib import contextmanager
from ctypes import wintypes

from Tlog import TLog
from path_utils import resolve_path

log = TLog("DebugUI")

CACHE_DIR = resolve_path("html/cache")

DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE = -3
DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4


def _enable_dpi_awareness():
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(
            ctypes.c_void_p(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
        )
        return
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


user32 = ctypes.windll.user32
try:
    shcore = ctypes.windll.shcore
except Exception:
    shcore = None


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", wintypes.WCHAR * 32),
    ]


class DISPLAY_DEVICEW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("DeviceName", wintypes.WCHAR * 32),
        ("DeviceString", wintypes.WCHAR * 128),
        ("StateFlags", wintypes.DWORD),
        ("DeviceID", wintypes.WCHAR * 128),
        ("DeviceKey", wintypes.WCHAR * 128),
    ]


MONITORINFOF_PRIMARY = 0x00000001
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79
MONITOR_DEFAULTTONEAREST = 0x00000002
GA_ROOT = 2

MonitorEnumProc = ctypes.WINFUNCTYPE(
    wintypes.BOOL,
    wintypes.HMONITOR,
    wintypes.HDC,
    ctypes.POINTER(RECT),
    wintypes.LPARAM,
)

EnumWindowsProc = ctypes.WINFUNCTYPE(
    wintypes.BOOL,
    wintypes.HWND,
    wintypes.LPARAM,
)


def _bind_winapi():
    user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
    user32.GetCursorPos.restype = wintypes.BOOL

    user32.MonitorFromPoint.argtypes = [POINT, wintypes.DWORD]
    user32.MonitorFromPoint.restype = wintypes.HMONITOR

    user32.WindowFromPoint.argtypes = [POINT]
    user32.WindowFromPoint.restype = wintypes.HWND

    user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetAncestor.restype = wintypes.HWND

    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = wintypes.HWND

    user32.EnumDisplayMonitors.argtypes = [
        wintypes.HDC,
        ctypes.POINTER(RECT),
        MonitorEnumProc,
        wintypes.LPARAM,
    ]
    user32.EnumDisplayMonitors.restype = wintypes.BOOL

    user32.GetMonitorInfoW.argtypes = [
        wintypes.HMONITOR,
        ctypes.POINTER(MONITORINFOEXW),
    ]
    user32.GetMonitorInfoW.restype = wintypes.BOOL

    user32.EnumDisplayDevicesW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(DISPLAY_DEVICEW),
        wintypes.DWORD,
    ]
    user32.EnumDisplayDevicesW.restype = wintypes.BOOL

    user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL

    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL

    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.IsIconic.restype = wintypes.BOOL

    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL

    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int

    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int

    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetClassNameW.restype = ctypes.c_int

    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD),
    ]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD


_bind_winapi()


def _push_per_monitor_dpi():
    try:
        set_ctx = user32.SetThreadDpiAwarenessContext
        set_ctx.argtypes = [ctypes.c_void_p]
        set_ctx.restype = ctypes.c_void_p
        return set_ctx(ctypes.c_void_p(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2))
    except Exception:
        return None


def _pop_dpi(prev):
    if prev is None:
        return
    try:
        user32.SetThreadDpiAwarenessContext(prev)
    except Exception:
        pass


@contextmanager
def _per_monitor_dpi():
    prev = _push_per_monitor_dpi()
    try:
        yield
    finally:
        _pop_dpi(prev)


def _rect_tuple(rect):
    return [rect.left, rect.top, rect.right, rect.bottom]


def _rect_intersects(a, b):
    return not (
        a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3]
    )


def _get_virtual_screen_rect():
    left = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    top = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
    width = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
    height = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
    return [left, top, left + width, top + height]


def _virtual_rect_from_monitors(monitors):
    if not monitors:
        return [0, 0, 0, 0]
    left = min(m["rect"][0] for m in monitors)
    top = min(m["rect"][1] for m in monitors)
    right = max(m["rect"][2] for m in monitors)
    bottom = max(m["rect"][3] for m in monitors)
    return [left, top, right, bottom]


def _get_display_device_string(device_name):
    dd = DISPLAY_DEVICEW()
    dd.cb = ctypes.sizeof(DISPLAY_DEVICEW)
    ok = user32.EnumDisplayDevicesW(device_name, 0, ctypes.byref(dd), 0)
    if ok and dd.DeviceString:
        return dd.DeviceString
    return "Unknown Monitor"


def _get_display_device_id(device_name):
    dd = DISPLAY_DEVICEW()
    dd.cb = ctypes.sizeof(DISPLAY_DEVICEW)
    ok = user32.EnumDisplayDevicesW(device_name, 0, ctypes.byref(dd), 0)
    if ok and dd.DeviceID:
        return dd.DeviceID
    return ""


def _get_monitor_dpi(hmonitor):
    if shcore is None:
        return 96, 96
    try:
        dpi_x = wintypes.UINT()
        dpi_y = wintypes.UINT()
        result = shcore.GetDpiForMonitor(
            hmonitor, 0, ctypes.byref(dpi_x), ctypes.byref(dpi_y)
        )
        if result == 0:
            return int(dpi_x.value), int(dpi_y.value)
    except Exception:
        pass
    return 96, 96


def _get_window_text(hwnd):
    if not hwnd:
        return ""
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value.strip()


def _get_window_class_name(hwnd):
    if not hwnd:
        return ""
    buffer = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buffer, 256)
    return buffer.value.strip()


def _get_window_pid(hwnd):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return int(pid.value)


def _get_window_rect(hwnd):
    rect = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None
    r = _rect_tuple(rect)
    if (r[2] - r[0]) <= 0 or (r[3] - r[1]) <= 0:
        return None
    return r


def _window_data(hwnd, z_no=0):
    if not hwnd:
        return None
    rect = _get_window_rect(hwnd)
    if rect is None:
        return None
    return {
        "hwnd": int(hwnd),
        "z_no": z_no,
        "title": _get_window_text(hwnd),
        "class_name": _get_window_class_name(hwnd),
        "pid": _get_window_pid(hwnd),
        "rect": rect,
    }


def _enumerate_monitors():
    monitors = []

    def callback(hmonitor, hdc, lprc_monitor, lparam):
        info = MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(MONITORINFOEXW)
        if user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
            device_name = info.szDevice
            dpi_x, dpi_y = _get_monitor_dpi(hmonitor)
            monitors.append(
                {
                    "hmonitor": int(hmonitor),
                    "device_name": device_name,
                    "device_id": _get_display_device_id(device_name),
                    "display_name": _get_display_device_string(device_name),
                    "rect": _rect_tuple(info.rcMonitor),
                    "work_rect": _rect_tuple(info.rcWork),
                    "primary": bool(info.dwFlags & MONITORINFOF_PRIMARY),
                    "dpi_x": dpi_x,
                    "dpi_y": dpi_y,
                }
            )
        return True

    proc = MonitorEnumProc(callback)
    user32.EnumDisplayMonitors(None, None, proc, 0)

    monitors.sort(key=lambda m: (m["rect"][1], m["rect"][0]))
    for i, m in enumerate(monitors, 1):
        m["visual_no"] = i
    return monitors


def _enumerate_windows(virtual_rect):
    windows = []
    current_pid = os.getpid()

    def callback(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        if user32.IsIconic(hwnd):
            return True
        pid = _get_window_pid(hwnd)
        if pid == current_pid:
            return True
        title = _get_window_text(hwnd)
        if not title:
            return True
        rect = _get_window_rect(hwnd)
        if rect is None:
            return True
        if not _rect_intersects(rect, virtual_rect):
            return True
        windows.append(
            {
                "hwnd": int(hwnd),
                "z_no": len(windows) + 1,
                "title": title,
                "class_name": _get_window_class_name(hwnd),
                "pid": pid,
                "rect": rect,
            }
        )
        return True

    proc = EnumWindowsProc(callback)
    user32.EnumWindows(proc, 0)
    return windows


def _get_cursor_point():
    point = POINT()
    if user32.GetCursorPos(ctypes.byref(point)):
        return point
    return None


def _get_mouse_monitor(monitors, point):
    hmonitor = user32.MonitorFromPoint(point, MONITOR_DEFAULTTONEAREST)
    if hmonitor:
        for m in monitors:
            if m["hmonitor"] == int(hmonitor):
                return m
    for m in monitors:
        r = m["rect"]
        if r[0] <= point.x < r[2] and r[1] <= point.y < r[3]:
            return m
    return None


def _get_mouse_window(point):
    hwnd = user32.WindowFromPoint(point)
    if not hwnd:
        return None
    root = user32.GetAncestor(hwnd, GA_ROOT)
    if root:
        hwnd = root
    return _window_data(int(hwnd))


def _get_foreground_window():
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None
    return _window_data(int(hwnd))


_wallpaper_thumb_map = {}
_last_thumb_scan = 0.0


def _get_playliststate_items():
    try:
        from getActiveWallpaper import call_playliststate_details
        details = call_playliststate_details()
        if isinstance(details, dict):
            return details.get("items") or []
    except Exception as e:
        log.error(f"获取显示器壁纸详情失败: {e}")
    return []


def _match_wallpaper_item(monitor, items):
    try:
        from getActiveWallpaper import find_mouse_playliststate_item
        probe = {
            "hmonitor": monitor.get("hmonitor"),
            "device_name": monitor.get("device_name"),
            "rect": monitor.get("rect"),
            "is_primary": monitor.get("primary"),
        }
        return find_mouse_playliststate_item(probe, {"items": items})
    except Exception:
        return None


def _refresh_wallpaper_thumb_map():
    global _wallpaper_thumb_map, _last_thumb_scan
    now = time.time()
    if _wallpaper_thumb_map and now - _last_thumb_scan < 10.0:
        return _wallpaper_thumb_map
    try:
        from mainUIWeb import all_wallpapers
        wallpapers = all_wallpapers()
        _wallpaper_thumb_map = {}
        for w in wallpapers:
            if len(w) > 1 and w[0] and w[1]:
                _wallpaper_thumb_map[str(w[0])] = w[1]
    except Exception as e:
        log.error(f"获取壁纸缩略图失败: {e}")
    _last_thumb_scan = now
    return _wallpaper_thumb_map


def _cache_thumb(wallpaper_id, abs_thumb):
    if not wallpaper_id or not abs_thumb or not os.path.exists(abs_thumb):
        return ""
    ext = os.path.splitext(abs_thumb)[1] or ".jpg"
    cache_name = "debug_" + str(wallpaper_id) + ext
    cache_path = os.path.join(CACHE_DIR, cache_name)
    try:
        if not os.path.exists(cache_path):
            os.makedirs(CACHE_DIR, exist_ok=True)
            shutil.copy2(abs_thumb, cache_path)
        return "cache/" + cache_name
    except Exception as e:
        log.error(f"缓存壁纸缩略图失败: {e}")
        return ""


_binding_cache = {}
_last_binding_scan = 0.0


def _load_binding_info():
    global _binding_cache, _last_binding_scan
    now = time.time()
    if _binding_cache and now - _last_binding_scan < 2.0:
        return _binding_cache
    try:
        import toml
        cfg_path = resolve_path("config.toml")
        cfg = {}
        if os.path.exists(cfg_path):
            cfg = toml.load(cfg_path)
        _binding_cache = {
            "wallpaper_map": {str(k): v for k, v in (cfg.get("wallpaper", {}) or {}).items()},
            "specified_mouse_group": str(
                (cfg.get("config", {}) or {}).get("specified_mouse_group", "") or ""
            ).strip(),
            "enable_default": bool(
                (cfg.get("config", {}) or {}).get("enable_default_icon_group", False)
            ),
            "pause_on_fullscreen": bool(
                (cfg.get("config", {}) or {}).get("pause_on_fullscreen", False)
            ),
            "program_whitelist": {
                str(k): v for k, v in (cfg.get("program_whitelist", {}) or {}).items()
            },
        }
    except Exception as e:
        log.error(f"读取绑定配置失败: {e}")
        _binding_cache = {}
    _last_binding_scan = now
    return _binding_cache


def _get_process_name(pid):
    if not pid:
        return ""
    try:
        import psutil
        return psutil.Process(int(pid)).name()
    except Exception:
        return ""


def _effective_group_for_monitor(wallpaper_id, binding, foreground_process):
    wallpaper_map = binding.get("wallpaper_map", {})
    whitelist = binding.get("program_whitelist", {})
    specified = binding.get("specified_mouse_group", "")
    enable_default = binding.get("enable_default", False)

    whitelist_group = (
        str(whitelist.get(foreground_process, "") or "") if foreground_process else ""
    )

    if specified and not whitelist_group:
        return specified, "specified"
    if whitelist_group:
        return whitelist_group, "whitelist"
    bound = str(wallpaper_map.get(wallpaper_id, "") or "")
    if bound:
        return bound, "wallpaper"
    if enable_default:
        return "默认", "default"
    return "", "none"


def _is_fullscreen_app_running():
    try:
        screen_w = user32.GetSystemMetrics(0)  # SM_CXSCREEN
        screen_h = user32.GetSystemMetrics(1)  # SM_CYSCREEN
        hits = []

        def callback(hwnd, lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
            rect = _get_window_rect(hwnd)
            if rect is None:
                return True
            w = rect[2] - rect[0]
            h = rect[3] - rect[1]
            is_fullscreen = (
                w == screen_w and h == screen_h and rect[0] == 0 and rect[1] == 0
            )
            is_maximized = (
                w >= screen_w - 20
                and h >= screen_h - 20
                and rect[0] <= 10
                and rect[1] <= 10
            )
            if is_fullscreen or is_maximized:
                class_name = _get_window_class_name(hwnd)
                title = _get_window_text(hwnd)
                if class_name in ("Progman", "WorkerW", "Shell_TrayWnd", "DwmWnd"):
                    return True
                if not title:
                    return True
                if "Windows.UI.Core" in class_name or "ApplicationFrameWindow" in class_name:
                    return True
                hits.append(hwnd)
            return True

        proc = EnumWindowsProc(callback)
        user32.EnumWindows(proc, 0)
        return len(hits) > 0
    except Exception as e:
        log.error(f"检测全屏失败: {e}")
        return False


def _build_decision(binding, foreground_process, mouse_monitor, fullscreen_active):
    wallpaper_map = binding.get("wallpaper_map", {})
    whitelist = binding.get("program_whitelist", {})
    specified = binding.get("specified_mouse_group", "")
    enable_default = binding.get("enable_default", False)
    pause_on_fullscreen = binding.get("pause_on_fullscreen", False)

    wallpaper_id = (
        str(mouse_monitor.get("wallpaper_id", "") or "") if mouse_monitor else ""
    )
    whitelist_group = (
        str(whitelist.get(foreground_process, "") or "") if foreground_process else ""
    )

    monitor_info = (
        {
            "visual_no": mouse_monitor.get("visual_no"),
            "device_name": mouse_monitor.get("device_name", ""),
            "wallpaper_id": wallpaper_id,
        }
        if mouse_monitor
        else {}
    )

    spec = bool(specified and not whitelist_group)
    wl = bool(whitelist_group)
    bound = str(wallpaper_map.get(wallpaper_id, "") or "")
    wp = bool(bound)
    fs = bool(pause_on_fullscreen and fullscreen_active)

    nodes = [
        {
            "key": "pause",
            "name": "① 全局暂停",
            "status": "unknown",
            "condition": "pause_flag（主进程运行时状态）",
            "yes": {"label": "跳过刷新", "taken": False},
            "no": {"label": "继续（假设未暂停）", "taken": True},
        },
        {
            "key": "fullscreen",
            "name": "② 全屏暂停",
            "status": "active",
            "condition": "pause_on_fullscreen=" + ("是" if pause_on_fullscreen else "否")
            + " · 检测到全屏=" + ("是" if fullscreen_active else "否"),
            "yes": {"label": "跳过刷新", "taken": fs},
            "no": {"label": "继续", "taken": not fs},
        },
        {
            "key": "specified",
            "name": "③ 指定光标组",
            "status": "active",
            "condition": "specified=" + ("「" + specified + "」" if specified else "空")
            + " · 进程在白名单=" + ("是" if whitelist_group else "否"),
            "yes": {"label": "使用「" + (specified or "指定组") + "」", "taken": spec},
            "no": {"label": "继续", "taken": not spec},
        },
        {
            "key": "whitelist",
            "name": "④ 程序白名单",
            "status": "active",
            "condition": "前台进程「" + (foreground_process or "未知") + "」",
            "yes": {"label": "使用「" + whitelist_group + "」", "taken": wl},
            "no": {"label": "继续", "taken": not wl},
        },
        {
            "key": "wallpaper",
            "name": "⑤ 壁纸匹配",
            "status": "active",
            "condition": "壁纸 ID " + (wallpaper_id or "无"),
            "yes": {"label": "使用「" + (bound or "绑定组") + "」", "taken": wp},
            "no": {"label": "继续", "taken": not wp},
        },
        {
            "key": "default",
            "name": "⑥ 默认组",
            "status": "active",
            "condition": "enable_default=" + ("是" if enable_default else "否"),
            "yes": {"label": "使用「默认」", "taken": enable_default},
            "no": {"label": "不应用", "taken": not enable_default},
        },
    ]

    if fs:
        final_group, final_source = "", "fullscreen_skip"
    elif spec:
        final_group, final_source = specified, "specified"
    elif wl:
        final_group, final_source = whitelist_group, "whitelist"
    elif wp:
        final_group, final_source = bound, "wallpaper"
    elif enable_default:
        final_group, final_source = "默认", "default"
    else:
        final_group, final_source = "", "none"

    return {
        "monitor": monitor_info,
        "foreground_process": foreground_process,
        "nodes": nodes,
        "final_group": final_group,
        "final_source": final_source,
    }


def _load_we_config():
    result = {"monitormap": {}, "selected_ids": {}, "mtime": 0.0}
    try:
        import getpass
        import toml
        cfg = toml.load(resolve_path("config.toml"))
        we_path = cfg.get("path", {}).get("wallpaper_engine_config", "")
        if not we_path or not os.path.exists(we_path):
            return result
        result["mtime"] = os.path.getmtime(we_path)
        data = json.load(open(we_path, "r", encoding="utf-8"))
        user = getpass.getuser()
        general = data.get(user, {}).get("general", {})
        mm = general.get("user", {}).get("monitormap", {})
        result["monitormap"] = {
            str(k): v for k, v in mm.items() if isinstance(v, dict)
        }
        selected = general.get("wallpaperconfig", {}).get("selectedwallpapers", {})
        for k, v in selected.items():
            if isinstance(v, dict):
                fp = str(v.get("file", "") or "")
                if fp:
                    result["selected_ids"][str(k)] = os.path.basename(
                        os.path.dirname(fp.replace(chr(92), "/"))
                    )
    except Exception as e:
        log.error(f"读取 Wallpaper Engine 配置失败: {e}")
    return result


def _get_playliststate_mtime():
    try:
        from getActiveWallpaper import get_wallpaper_engine_root_from_config
        root = str(get_wallpaper_engine_root_from_config())
        bin_path = os.path.join(root, "bin", "playliststate.bin")
        if os.path.exists(bin_path):
            return os.path.getmtime(bin_path)
    except Exception as e:
        log.error(f"获取 playliststate.bin mtime 失败: {e}")
    return 0.0


def _get_monitor_current_ids():
    try:
        from getActiveWallpaper import load_playliststate_reader, resolve_wallpaper_engine_root
        dll = load_playliststate_reader()
        root = resolve_wallpaper_engine_root(None)
        dll.we_get_monitor_current_ids_json.argtypes = [ctypes.c_char_p]
        dll.we_get_monitor_current_ids_json.restype = ctypes.c_void_p
        ptr = dll.we_get_monitor_current_ids_json(str(root).encode("utf-8"))
        if not ptr:
            return {}
        try:
            raw = ctypes.string_at(ptr).decode("utf-8", errors="replace")
        finally:
            dll.we_free_string(ptr)
        result = json.loads(raw)
        return result if isinstance(result, dict) else {}
    except Exception as e:
        log.error(f"获取显示器当前壁纸ID失败: {e}")
        return {}


def _resolve_monitor_location(device_id, device_name, monitormap):
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


def _build_monitors():
    monitors = _enumerate_monitors()
    thumb_map = _refresh_wallpaper_thumb_map()
    wallpaper_map = _load_binding_info().get("wallpaper_map", {})
    we_config = _load_we_config()
    monitormap = we_config.get("monitormap", {})
    config_ids = we_config.get("selected_ids", {})
    config_mtime = we_config.get("mtime", 0.0)
    playlist_mtime = _get_playliststate_mtime()
    current_ids = _get_monitor_current_ids()
    items = _get_playliststate_items()


    prefer_config = config_mtime >= playlist_mtime

    source_map = {}
    for item in items:
        we_key = str(item.get("we_monitor") or "")
        if we_key:
            source_map[we_key] = str(item.get("wallpaper_source") or "")

    for m in monitors:
        location = _resolve_monitor_location(
            m.get("device_id", ""), m.get("device_name", ""), monitormap
        )
        wallpaper_id = ""
        wallpaper_source = ""
        if location >= 0:
            we_key = "Monitor" + str(location)
            if prefer_config and config_ids.get(we_key):
                wallpaper_id = str(config_ids.get(we_key, ""))
                wallpaper_source = "config.json"
            else:
                wallpaper_id = str(current_ids.get(we_key, "") or "")
                wallpaper_source = source_map.get(we_key, "dll")
        else:
            item = _match_wallpaper_item(m, items)
            if item:
                wallpaper_id = str(item.get("current_id") or "")
                wallpaper_source = str(item.get("wallpaper_source") or "")
        m["wallpaper_id"] = wallpaper_id
        m["wallpaper_source"] = wallpaper_source
        m["mouse_group"] = str(wallpaper_map.get(wallpaper_id, "") or "")
        m["thumbnail"] = (
            _cache_thumb(wallpaper_id, thumb_map.get(wallpaper_id, ""))
            if wallpaper_id
            else ""
        )
    return monitors


def _build_realtime(monitors):
    point = _get_cursor_point()
    mouse_monitor = None
    mouse_window = None
    foreground = _get_foreground_window()
    mouse = None
    if point is not None:
        mouse = [int(point.x), int(point.y)]
        mouse_monitor = _get_mouse_monitor(monitors, point)
        mouse_window = _get_mouse_window(point)
    return {
        "mouse": mouse,
        "mouse_monitor": mouse_monitor,
        "mouse_window": mouse_window,
        "foreground_window": foreground,
    }


class DebugApi:

    def __init__(self):
        self._monitors = []
        self._windows = []
        self._virtual_rect = [0, 0, 0, 0]
        self._fullscreen_active = False
        self._last_monitor = 0.0
        self._last_window = 0.0
        self._monitor_interval = 1.0
        self._window_interval = 1.0

    def get_snapshot(self):
        now = time.perf_counter()

        with _per_monitor_dpi():
            if now - self._last_monitor >= self._monitor_interval:
                try:
                    self._monitors = _build_monitors()
                    self._virtual_rect = _virtual_rect_from_monitors(self._monitors)
                except Exception as e:
                    log.error(f"刷新显示器失败: {e}")
                self._last_monitor = now

            if now - self._last_window >= self._window_interval:
                try:
                    self._windows = _enumerate_windows(self._virtual_rect)
                    self._fullscreen_active = _is_fullscreen_app_running()
                except Exception as e:
                    log.error(f"刷新窗口失败: {e}")
                self._last_window = now

            realtime = _build_realtime(self._monitors)

            binding = _load_binding_info()
            foreground_process = _get_process_name(
                realtime["foreground_window"].get("pid")
                if realtime.get("foreground_window")
                else 0
            )
            for m in self._monitors:
                effective_group, effective_source = _effective_group_for_monitor(
                    m.get("wallpaper_id", ""), binding, foreground_process
                )
                m["effective_group"] = effective_group
                m["effective_source"] = effective_source

            decision = _build_decision(
                binding,
                foreground_process,
                realtime.get("mouse_monitor"),
                self._fullscreen_active,
            )
            decision["wallpaper_reader"] = "playliststate_reader.dll"
            decision["fetched_at"] = time.time()

        return {
            "monitors": self._monitors,
            "windows": self._windows,
            "realtime": realtime,
            "virtual_rect": self._virtual_rect,
            "wallpaper_reader": "playliststate_reader.dll",
            "fetched_at": time.time(),
            "binding": {
                "foreground_process": foreground_process,
                "whitelist_group": str(
                    binding.get("program_whitelist", {}).get(foreground_process, "") or ""
                ),
                "specified_mouse_group": binding.get("specified_mouse_group", ""),
                "enable_default": binding.get("enable_default", False),
                "pause_on_fullscreen": binding.get("pause_on_fullscreen", False),
                "fullscreen_active": self._fullscreen_active,
            },
            "decision": decision,
        }


if __name__ == "__main__":
    import webview

    _enable_dpi_awareness()  # 仅单独运行 debugUI.py 时设置进程级 DPI

    api = DebugApi()
    window = webview.create_window(
        "MouseEngine Debug",
        resolve_path("html/debugUI.html"),
        js_api=api,
        width=1200,
        height=800,
        easy_drag=True,
    )
    if log.on_DEBUG:
        webview.start(debug=True, http_server=True)
    else:
        webview.start(debug=False, http_server=True)
