/* Copyright (c) 2026, CIF3
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * 为 MouseEngine 实现的快速、非持久化的 Windows 光标应用功能。
 *
 * 公共 API：
 *   int me_apply_system_cursors(
 *       const wchar_t **cursor_paths,
 *       int count,
 *       unsigned long *failed_index,
 *       unsigned long *last_error
 *   );
 *
 * cursor_paths 遵循 MouseEngine 中 Python 的 CURSOR_ORDER_MAPPING 顺序。
 * 空字符串会被跳过。SetSystemCursor 会接管成功设置的光标句柄，
 * 因此调用方在此调用之后不得再重复使用这些句柄。
 */

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#define ME_EXPORT __declspec(dllexport)

#define ME_OCR_NORMAL 32512
#define ME_OCR_IBEAM 32513
#define ME_OCR_WAIT 32514
#define ME_OCR_CROSS 32515
#define ME_OCR_UP 32516
#define ME_OCR_NWPEN 32631
#define ME_OCR_SIZENWSE 32642
#define ME_OCR_SIZENESW 32643
#define ME_OCR_SIZEWE 32644
#define ME_OCR_SIZENS 32645
#define ME_OCR_SIZEALL 32646
#define ME_OCR_NO 32648
#define ME_OCR_HAND 32649
#define ME_OCR_APPSTARTING 32650
#define ME_OCR_HELP 32651

static const DWORD CURSOR_IDS[] = {
    ME_OCR_NORMAL,      /* Arrow */
    ME_OCR_HELP,        /* Help */
    ME_OCR_APPSTARTING, /* AppStarting */
    ME_OCR_WAIT,        /* Wait */
    ME_OCR_CROSS,       /* Crosshair */
    ME_OCR_IBEAM,       /* IBeam */
    ME_OCR_NWPEN,       /* Handwriting / NWPen */
    ME_OCR_NO,          /* No */
    ME_OCR_SIZENS,      /* SizeNS */
    ME_OCR_SIZEWE,      /* SizeWE */
    ME_OCR_SIZENWSE,    /* SizeNWSE */
    ME_OCR_SIZENESW,    /* SizeNESW */
    ME_OCR_SIZEALL,     /* SizeAll */
    ME_OCR_HAND,        /* Hand */
    ME_OCR_UP           /* UpArrow */
};

ME_EXPORT int me_apply_system_cursors(
    const wchar_t **cursor_paths,
    int count,
    unsigned long *failed_index,
    unsigned long *last_error
) {
    int i;
    const int max_count = (int)(sizeof(CURSOR_IDS) / sizeof(CURSOR_IDS[0]));

    if (failed_index) {
        *failed_index = 0;
    }
    if (last_error) {
        *last_error = 0;
    }
    if (!cursor_paths || count < 0) {
        if (last_error) {
            *last_error = ERROR_INVALID_PARAMETER;
        }
        return 0;
    }
    if (count > max_count) {
        count = max_count;
    }

    for (i = 0; i < count; i++) {
        const wchar_t *path = cursor_paths[i];
        HCURSOR cursor;

        if (!path || !path[0]) {
            continue;
        }

        cursor = LoadCursorFromFileW(path);
        if (!cursor) {
            if (failed_index) {
                *failed_index = (unsigned long)i;
            }
            if (last_error) {
                *last_error = GetLastError();
            }
            return 0;
        }

        if (!SetSystemCursor(cursor, CURSOR_IDS[i])) {
            DWORD err = GetLastError();
            DestroyCursor(cursor);
            if (failed_index) {
                *failed_index = (unsigned long)i;
            }
            if (last_error) {
                *last_error = err;
            }
            return 0;
        }
    }

    return 1;
}

#endif
