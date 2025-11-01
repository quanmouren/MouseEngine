import winreg
import ctypes
from ctypes import wintypes
import toml
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.Tlog import TLog
log = TLog("设置鼠标指针")

# 光标类型映射到Windows注册表键名
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
    "UpArrow"          # 14: 位置选择
]

# 读取配置文件
def 读取配置():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.toml")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = toml.load(f)
            return config.get('config', {}).get('enable_default_icon_group', False)
    except Exception as e:
        log.error(f"读取配置文件失败: {str(e)}")
        return False

# 获取默认图标路径（从配置文件读取）
def 获取默认图标路径(index):
    # 获取默认配置文件路径
    default_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mouses", "默认", "config.toml")
    
    try:
        # 读取配置文件
        with open(default_config_path, 'r', encoding='utf-8') as f:
            config = toml.load(f)
        
        # 检查配置是否包含mouses部分
        if 'mouses' in config:
            mouses_config = config['mouses']
            # 使用CURSOR_ORDER_MAPPING获取光标名称
            if 0 <= index < len(CURSOR_ORDER_MAPPING):
                cursor_name = CURSOR_ORDER_MAPPING[index]
                if cursor_name in mouses_config:
                    # 获取配置中的路径
                    relative_path = mouses_config[cursor_name]
                    # 将相对路径转换为绝对路径
                    if relative_path.startswith("mouses\\"):
                        # 相对于项目根目录的路径
                        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), relative_path)
                    else:
                        # 相对于默认文件夹的路径
                        return os.path.join(os.path.dirname(default_config_path), relative_path)
    except Exception as e:
        log.error(f"读取默认配置文件失败: {str(e)}")
    
    return None

def 设置鼠标指针(cursor_paths):
    log.debug(f"收到样式: {cursor_paths}")
    # 读取配置
    enable_default = 读取配置()
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
    - cursor_paths[13]: 链接选择
    - cursor_paths[14]: 位置选择

    :return: 成功返回True，失败返回False
    """
    def update_system_cursors():
        ctypes.windll.user32.SystemParametersInfoW(
            wintypes.UINT(0x0057),  # SPI_SETCURSORS
            wintypes.UINT(0),
            wintypes.LPVOID(None),
            wintypes.UINT(0x01)    # SPIF_SENDCHANGE：立即生效
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
            # 优先使用提供的鼠标指针
            if index < len(cursor_paths) and cursor_paths[index]:
                candidate_path = os.path.abspath(cursor_paths[index])
                log.debug(f"处理光标 {cursor_name}: {candidate_path}")
                if os.path.exists(candidate_path):
                    cursor_path = candidate_path
                else:
                    #print(f"警告：文件不存在 - {candidate_path}")
                    log.error(f"文件不存在 - {candidate_path}")
                    # 尝试使用默认文件作为替代
                    if enable_default:
                        default_path = 获取默认图标路径(index)
                        if default_path and os.path.exists(default_path):
                            log.debug(f"<r ! >使用默认光标 {cursor_name} 替代: {default_path}")
                            cursor_path = default_path
            # 如果启用了默认图标组且当前没有提供鼠标指针，使用默认配置
            elif enable_default:
                default_path = 获取默认图标路径(index)
                if default_path and os.path.exists(default_path):
                    log.debug(f"<r ! >使用默认光标 {cursor_name}: {default_path}")
                    cursor_path = default_path
                else:
                    log.error(f"默认光标不存在或索引无效: {index}")
            
            # 如果找到了有效的光标路径，则设置
            if cursor_path:
                winreg.SetValueEx(base_key, cursor_name, 0, winreg.REG_SZ, cursor_path)
        winreg.CloseKey(base_key)
        update_system_cursors()
        return True
        
    except Exception as e:
        print(f"设置出错: {str(e)}")
        return False


if __name__ == "__main__":
    设置鼠标指针(["mouses\\芙宁娜\\1.ani", "mouses\\芙宁娜\\111.ani", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])