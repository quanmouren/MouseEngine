/* Copyright (c) 2026, CIF3
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * 提供前台窗口、鼠标命中窗口、鼠标所在显示器等窗口 / 显示器探测功能。
 *
 * 公共 API：
 *   int get_fg_windows(ME_WindowInfo *out);
 *   int get_windows_at_mouse(ME_WindowInfo *out);
 *   int get_mouse_at_cursor(ME_MonitorInfo *out);
 *
 * 三个函数均返回：
 *   1 = 成功（结构体已填充）
 *   0 = 失败（参数无效、调用 WinAPI 失败等）
 *
 */

#define UNICODE
#define _UNICODE

#include <windows.h>
#include <stdint.h>

#define ME_TITLE_LEN 512
#define ME_CLASS_LEN 256
#define ME_DEVICE_NAME_LEN 32
#define ME_DISPLAY_NAME_LEN 128

#ifdef _WIN32
#define DLL_EXPORT __declspec(dllexport)
#else
#define DLL_EXPORT
#endif


typedef struct ME_WindowInfo {
    uint64_t hwnd;
    uint32_t pid;

    int32_t left;
    int32_t top;
    int32_t right;
    int32_t bottom;

    wchar_t title[ME_TITLE_LEN];
    wchar_t class_name[ME_CLASS_LEN];
} ME_WindowInfo;


typedef struct ME_MonitorInfo {
    uint64_t hmonitor;

    wchar_t device_name[ME_DEVICE_NAME_LEN];     // 例如 \\.\DISPLAY1
    wchar_t display_name[ME_DISPLAY_NAME_LEN];   // 例如 Generic PnP Monitor

    int32_t left;
    int32_t top;
    int32_t right;
    int32_t bottom;

    int32_t work_left;
    int32_t work_top;
    int32_t work_right;
    int32_t work_bottom;

    uint32_t dpi_x;
    uint32_t dpi_y;

    int32_t is_primary;
} ME_MonitorInfo;


typedef HRESULT(WINAPI *PFN_SetProcessDpiAwareness)(int value);
typedef HRESULT(WINAPI *PFN_GetDpiForMonitor)(
    HMONITOR hmonitor,
    int dpiType,
    UINT *dpiX,
    UINT *dpiY
);


static volatile LONG g_dpi_initialized = 0;
static PFN_GetDpiForMonitor g_GetDpiForMonitor = NULL;


static void safe_wcs_copy(wchar_t *dst, size_t dst_count, const wchar_t *src)
{
    if (!dst || dst_count == 0) {
        return;
    }

    dst[0] = L'\0';

    if (!src) {
        return;
    }

    wcsncpy_s(dst, dst_count, src, _TRUNCATE);
}


static void ensure_dpi_awareness(void)
{
    if (InterlockedCompareExchange(&g_dpi_initialized, 1, 0) != 0) {
        return;
    }

    HMODULE shcore = LoadLibraryW(L"shcore.dll");

    if (shcore) {
        PFN_SetProcessDpiAwareness SetProcessDpiAwarenessFunc =
            (PFN_SetProcessDpiAwareness)GetProcAddress(
                shcore,
                "SetProcessDpiAwareness"
            );

        g_GetDpiForMonitor =
            (PFN_GetDpiForMonitor)GetProcAddress(
                shcore,
                "GetDpiForMonitor"
            );

        if (SetProcessDpiAwarenessFunc) {
            // PROCESS_PER_MONITOR_DPI_AWARE = 2
            SetProcessDpiAwarenessFunc(2);
            return;
        }
    }

    SetProcessDPIAware();
}


static void clear_window_info(ME_WindowInfo *out)
{
    if (!out) {
        return;
    }

    ZeroMemory(out, sizeof(ME_WindowInfo));
}


static void clear_monitor_info(ME_MonitorInfo *out)
{
    if (!out) {
        return;
    }

    ZeroMemory(out, sizeof(ME_MonitorInfo));
}


static int fill_window_info(HWND hwnd, ME_WindowInfo *out)
{
    if (!out || !hwnd) {
        return 0;
    }

    clear_window_info(out);

    RECT rect;
    if (!GetWindowRect(hwnd, &rect)) {
        return 0;
    }

    DWORD pid = 0;
    GetWindowThreadProcessId(hwnd, &pid);

    wchar_t title[ME_TITLE_LEN];
    wchar_t class_name[ME_CLASS_LEN];

    ZeroMemory(title, sizeof(title));
    ZeroMemory(class_name, sizeof(class_name));

    GetWindowTextW(hwnd, title, ME_TITLE_LEN);
    GetClassNameW(hwnd, class_name, ME_CLASS_LEN);

    out->hwnd = (uint64_t)(uintptr_t)hwnd;
    out->pid = (uint32_t)pid;

    out->left = rect.left;
    out->top = rect.top;
    out->right = rect.right;
    out->bottom = rect.bottom;

    safe_wcs_copy(out->title, ME_TITLE_LEN, title);
    safe_wcs_copy(out->class_name, ME_CLASS_LEN, class_name);

    return 1;
}


static void get_monitor_dpi(HMONITOR hmonitor, uint32_t *dpi_x, uint32_t *dpi_y)
{
    if (!dpi_x || !dpi_y) {
        return;
    }

    *dpi_x = 96;
    *dpi_y = 96;

    if (!hmonitor || !g_GetDpiForMonitor) {
        return;
    }

    UINT x = 96;
    UINT y = 96;

    // MDT_EFFECTIVE_DPI = 0
    HRESULT hr = g_GetDpiForMonitor(hmonitor, 0, &x, &y);

    if (SUCCEEDED(hr)) {
        *dpi_x = (uint32_t)x;
        *dpi_y = (uint32_t)y;
    }
}


static int fill_monitor_info(HMONITOR hmonitor, ME_MonitorInfo *out)
{
    if (!out || !hmonitor) {
        return 0;
    }

    clear_monitor_info(out);

    MONITORINFOEXW info;
    ZeroMemory(&info, sizeof(info));
    info.cbSize = sizeof(info);

    if (!GetMonitorInfoW(hmonitor, (MONITORINFO *)&info)) {
        return 0;
    }

    DISPLAY_DEVICEW device;
    ZeroMemory(&device, sizeof(device));
    device.cb = sizeof(device);

    wchar_t display_name[ME_DISPLAY_NAME_LEN];
    ZeroMemory(display_name, sizeof(display_name));

    if (EnumDisplayDevicesW(info.szDevice, 0, &device, 0)) {
        safe_wcs_copy(display_name, ME_DISPLAY_NAME_LEN, device.DeviceString);
    } else {
        safe_wcs_copy(display_name, ME_DISPLAY_NAME_LEN, L"Unknown Monitor");
    }

    uint32_t dpi_x = 96;
    uint32_t dpi_y = 96;
    get_monitor_dpi(hmonitor, &dpi_x, &dpi_y);

    out->hmonitor = (uint64_t)(uintptr_t)hmonitor;

    safe_wcs_copy(out->device_name, ME_DEVICE_NAME_LEN, info.szDevice);
    safe_wcs_copy(out->display_name, ME_DISPLAY_NAME_LEN, display_name);

    out->left = info.rcMonitor.left;
    out->top = info.rcMonitor.top;
    out->right = info.rcMonitor.right;
    out->bottom = info.rcMonitor.bottom;

    out->work_left = info.rcWork.left;
    out->work_top = info.rcWork.top;
    out->work_right = info.rcWork.right;
    out->work_bottom = info.rcWork.bottom;

    out->dpi_x = dpi_x;
    out->dpi_y = dpi_y;

    out->is_primary = (info.dwFlags & MONITORINFOF_PRIMARY) ? 1 : 0;

    return 1;
}


DLL_EXPORT int get_fg_windows(ME_WindowInfo *out)
{
    ensure_dpi_awareness();

    if (!out) {
        return 0;
    }

    clear_window_info(out);

    HWND hwnd = GetForegroundWindow();

    if (!hwnd) {
        return 0;
    }

    return fill_window_info(hwnd, out);
}


DLL_EXPORT int get_windows_at_mouse(ME_WindowInfo *out)
{
    ensure_dpi_awareness();

    if (!out) {
        return 0;
    }

    clear_window_info(out);

    POINT point;

    if (!GetCursorPos(&point)) {
        return 0;
    }

    HWND hwnd = WindowFromPoint(point);

    if (!hwnd) {
        return 0;
    }

    HWND root = GetAncestor(hwnd, GA_ROOT);

    if (root) {
        hwnd = root;
    }

    return fill_window_info(hwnd, out);
}


DLL_EXPORT int get_mouse_at_cursor(ME_MonitorInfo *out)
{
    ensure_dpi_awareness();

    if (!out) {
        return 0;
    }

    clear_monitor_info(out);

    POINT point;

    if (!GetCursorPos(&point)) {
        return 0;
    }

    HMONITOR hmonitor = MonitorFromPoint(point, MONITOR_DEFAULTTONEAREST);

    if (!hmonitor) {
        return 0;
    }

    return fill_monitor_info(hmonitor, out);
}