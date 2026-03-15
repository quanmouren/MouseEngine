# Copyright (c) 2026, CIF3
# SPDX-License-Identifier: BSD-3-Clause
"""
测试用
"""

try:
    from screeninfo import get_monitors
    import pyautogui
except ImportError:
    # 库未安装时返回默认值
    def get_current_monitor_number():
        return 1
else:
    def get_current_monitor_number():
        """
        获取鼠标当前所在的显示器编号
        返回值: 显示器编号（从1开始），如果无法获取则返回1
        """
        try:
            # 获取所有显示器信息
            monitors = get_monitors()
            
            # 获取鼠标位置
            mouse_x, mouse_y = pyautogui.position()
            
            # 遍历显示器，判断鼠标位置
            for i, monitor in enumerate(monitors):
                if (monitor.x <= mouse_x < monitor.x + monitor.width and
                    monitor.y <= mouse_y < monitor.y + monitor.height):
                    return i + 1
            
            # 未找到时返回1（默认显示器）
            return 1
        except Exception:
            # 发生异常时返回1
            return 1

if __name__ == "__main__":
    
    # 测试函数
    monitor_num = get_current_monitor_number()
    print(f"当前鼠标所在显示器编号: {monitor_num}")
