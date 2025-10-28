import os
import sys
import winreg
import ctypes
from ctypes import wintypes

def set_mouse(cursor_paths):
    """
    设置鼠标样式
    :param cursor_paths: 鼠标样式文件路径列表，顺序
    - cursor_paths[0]: 正常选择
    - cursor_paths[1]: 帮助选择
    - cursor_paths[2]: 后台运行
    - cursor_paths[3]: 忙
    - cursor_paths[4]: 精准选择
    - cursor_paths[5]: 文本选择
    - cursor_paths[6]: 手写
    - cursor_paths[7]: 不可用
    - cursor_paths[8]: 垂直调整大小
    - cursor_paths[9]: 水平调整大小
    - cursor_paths[10]: 沿对角线调整大小1
    - cursor_paths[11]: 沿对角线调整大小2
    - cursor_paths[12]: 移动
    - cursor_paths[13]: 候选（原映射中"PersonSelect"对应候选）
    - cursor_paths[14]: 链接选择
    - cursor_paths[15]: 位置选择

    :return: 成功返回True，失败返回False
    """
    def update_system_cursors():
        ctypes.windll.user32.SystemParametersInfoW(
            wintypes.UINT(0x0057),  # SPI_SETCURSORS
            wintypes.UINT(0),
            wintypes.LPVOID(None),
            wintypes.UINT(0x01)    # SPIF_SENDCHANGE：立即生效
        )
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
        "PersonSelect",   # 13: 候选（原映射中"PersonSelect"对应候选）
        "Hand",           # 14: 链接选择
        "UpArrow",        # 15: 位置选择
    ]
    base_reg_path = r"Control Panel\Cursors"
    try:
        base_key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            base_reg_path,
            0,
            winreg.KEY_SET_VALUE
        )
        for index, cursor_name in enumerate(CURSOR_ORDER_MAPPING):
            if index < len(cursor_paths) and cursor_paths[index]:
                cursor_path = cursor_paths[index]
                if os.path.exists(cursor_path):
                    winreg.SetValueEx(base_key, cursor_name, 0, winreg.REG_SZ, cursor_path)
                else:
                    print(f"警告：文件不存在 - {cursor_path}")
        winreg.CloseKey(base_key)
        update_system_cursors()
        return True
        
    except Exception as e:
        print(f"设置出错: {str(e)}")
        return False