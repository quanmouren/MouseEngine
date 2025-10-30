from src.getWallpaperConfig import get_monitor_path
from src.setMouse import set_mouse
import time
import os
import shutil
import toml
from tkinter import *
from tkinter.ttk import *
import threading
from tkinterdnd2 import TkinterDnD, DND_FILES
import toml



def 获取mouses配置(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = toml.load(f)

        if 'mouses' not in data:
            return "错误：TOML文件中未找到[mouses]部分"
        
        mouses_section = data['mouses']
        return list(mouses_section.values())
    
    except FileNotFoundError:
        return f"错误：文件不存在 - {file_path}"
    except Exception as e:
        return f"处理错误：{str(e)}"

def 触发刷新():
    path = get_monitor_path(config_path, username, monitor=1)

    normalized_path = os.path.normpath(path)
    if os.path.isfile(normalized_path):
        file_dir = os.path.dirname(normalized_path)
    else:
        file_dir = normalized_path
    last_folder = os.path.basename(file_dir)
    if not last_folder:
        return False

    tf = wallpaper(last_folder)
    print(tf)
    if tf != False:
        config = toml.load(os.path.join("mouses", tf, "config.toml"))
        mouse_values = list(config['mouses'].values())
        set_mouse(mouse_values)
        return True
    return False

def 复制文件(src_path, dst_path, max_retries=3):
    """
    复制文件
    :param src_path: 源文件路径
    :param dst_path: 目标文件路径
    :param max_retries: 最大重试次数
    :return: 成功返回True，失败返回False
    """
    for attempt in range(max_retries):
        try:
            shutil.copy2(src_path, dst_path)
            return True
        except PermissionError:
            if attempt < max_retries - 1:
                print(f"文件被占用，等待重试... (尝试 {attempt + 1}/{max_retries})")
                time.sleep(0.5)  # 等待0.5秒后重试
            else:
                print(f"复制文件失败: {src_path} -> {dst_path}")
                return False
        except Exception as e:
            print(f"复制文件时出错: {e}")
            return False
    return False
            
def 保存配置(name, folder_path, file_list):
    """
        保存配置文件
        :param name: 此配置名称
        :param folder_path: 配置文件夹路径
        :param file_list: 16个文件路径列表
    """
    if len(file_list) != 16:
        raise ValueError("file_list must contain exactly 16 items")
    
    target_folder = os.path.join(folder_path, name)
    os.makedirs(target_folder, exist_ok=True)
    # 加载配置文件
    existing_config = {}
    config_path = os.path.join(target_folder, "config.toml")
    if os.path.exists(config_path):
        try:
            existing_config = toml.load(config_path)
        except:
            pass
    
    copied_paths = []
    for i, file_path in enumerate(file_list):
        if file_path and os.path.exists(file_path):
            file_name = os.path.basename(file_path)
            target_path = os.path.join(target_folder, file_name)
            
            # 检查文件是否来自现有的配置文件夹
            is_from_existing_config = False
            if existing_config and 'mouses' in existing_config:
                existing_values = list(existing_config['mouses'].values())
                if i < len(existing_values) and existing_values[i] == file_path:
                    is_from_existing_config = True
            
            # 如果文件来自现有配置，并且文件已经存在于目标位置，直接使用现有路径
            if is_from_existing_config and os.path.exists(file_path):
                copied_paths.append(file_path)
            else:
                if 复制文件(file_path, target_path):
                    copied_paths.append(target_path)
                else:
                    print(f"警告: 无法复制文件 {file_path}，使用空路径")
                    copied_paths.append("")
        else:
            copied_paths.append("")

    cursor_keys = [
        "Arrow", "Help", "AppStarting", "Wait", "Crosshair", "IBeam", 
        "Handwriting", "No", "SizeNS", "SizeWE", "SizeNWSE", "SizeNESW", 
        "SizeAll", "PersonSelect", "Hand", "UpArrow"
    ]

    toml_data = {"mouses": dict(zip(cursor_keys, copied_paths))}

    toml_path = os.path.join(target_folder, "config.toml")
    with open(toml_path, "w", encoding="utf-8") as f:
        toml.dump(toml_data, f)
    触发刷新()
    return target_folder
    
def 加载配置(name):
    """
    加载指定名称的配置
    :param name: 配置名称
    :return: 配置值列表或None
    """
    try:
        config_path = os.path.join("mouses", name, "config.toml")
        if os.path.exists(config_path):
            config = toml.load(config_path)
            return list(config['mouses'].values())
    except Exception as e:
        print(f"加载配置错误: {e}")
    return None

def wallpaper(query_path, config_path="config.toml"):
    """
    从查询路径中提取文件所在的最后一个文件夹名，检查其在config.toml的wallpaper项目中是否存在
    
    :param query_path: 待查询的文件路径字符串
    :param config_path: config.toml文件路径（默认当前目录）
    :return: 若存在则返回对应值，否则返回False
    """
    normalized_path = os.path.normpath(query_path)
    if os.path.isfile(normalized_path):
        file_dir = os.path.dirname(normalized_path)
    else:
        file_dir = normalized_path
    last_folder = os.path.basename(file_dir)
    if not last_folder:
        return False
    if not os.path.exists(config_path):
        default_config = {"wallpaper": {}}
        with open(config_path, 'w', encoding='utf-8') as f:
            toml.dump(default_config, f)
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = toml.load(f)
        if "wallpaper" not in config_data:
            config_data["wallpaper"] = {}
            with open(config_path, 'w', encoding='utf-8') as f:
                toml.dump(config_data, f)
        return config_data["wallpaper"].get(last_folder, False)
    
    except toml.TomlDecodeError:
        return False

def add_wallpaper(name, query_path, config_path="config.toml"):
    """
    从路径中提取文件所在的最后一个文件夹名，在config.toml的wallpaper表中添加键值对（文件夹名为键，name为值）
    
    :param name: 要保存的值
    :param query_path: 待处理的文件路径字符串
    :param config_path: 配置文件路径（默认当前目录的config.toml）
    :return: 成功返回True，失败返回False
    """
    normalized_path = os.path.normpath(query_path)
    if os.path.isfile(normalized_path):
        file_dir = os.path.dirname(normalized_path)
    else:
        file_dir = normalized_path 
    last_folder = os.path.basename(file_dir)
    
    if not last_folder:
        return False
    
    config_data = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = toml.load(f)
        except toml.TomlDecodeError:
            return False
    
    if "wallpaper" not in config_data:
        config_data["wallpaper"] = {}

    config_data["wallpaper"][last_folder] = name
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            toml.dump(config_data, f)
        return True
    except Exception:
        return False

def delete_wallpaper(query_path, config_path="config.toml"):
    """
    从路径中提取文件所在的最后一个文件夹名，删除config.toml的wallpaper表中对应键值对
    
    :param query_path: 待处理的文件路径字符串（文件或目录）
    :param config_path: 配置文件路径（默认当前目录的config.toml）
    :return: 成功删除返回True，未找到项目/操作失败返回False
    """
    normalized_path = os.path.normpath(query_path)
    if os.path.isfile(normalized_path):
        file_dir = os.path.dirname(normalized_path)
    else:
        file_dir = normalized_path
    last_folder = os.path.basename(file_dir)
    if not last_folder:
        return False 
    if not os.path.exists(config_path):
        return False 
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = toml.load(f)
    except toml.TomlDecodeError:
        return False 
    if "wallpaper" not in config_data or last_folder not in config_data["wallpaper"]:
        return False 
    del config_data["wallpaper"][last_folder]
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            toml.dump(config_data, f)
        return True
    except Exception:
        return False

def ui_设置():
    class Controller:
        ui: object
        def __init__(self):
            self.current_wallpaper_path = None
            self.current_wallpaper_folder = None
        
        def init(self, ui):
            """初始化UI实例"""
            self.ui = ui
            # 初始化时加载一次文件夹列表
            self.update_combobox_items()
            # 存储所有输入框的引用，保持顺序
            self.input_fields = [
                self.ui.tk_input_mhbvaeua,    # 1. 正常选择
                self.ui.tk_input_mhbw85ay,    # 2. 帮助选择
                self.ui.tk_input_mhbw86gs,    # 3. 后台运行
                self.ui.tk_input_mhbw8732,    # 4. 忙
                self.ui.tk_input_mhbw882r,    # 5. 精准选择
                self.ui.tk_input_mhbw890b,    # 6. 文本选择
                self.ui.tk_input_mhbw8amb,    # 7. 手写
                self.ui.tk_input_mhbw8c6w,    # 8. 不可用
                self.ui.tk_input_mhbw8dag,    # 9. 垂直调整大小
                self.ui.tk_input_mhbw8eir,    # 10. 水平调整大小
                self.ui.tk_input_mhbw8gbn,    # 11. 沿对角线调整1
                self.ui.tk_input_mhbw8h8g,    # 12. 沿对角线调整2
                self.ui.tk_input_mhbw8hzn,    # 13. 移动
                self.ui.tk_input_mhbw8jai,    # 14. 候选
                self.ui.tk_input_mhbw8k0c,    # 15. 链接选择
                self.ui.tk_input_mhbw8kq5     # 16. 位置选择
            ]
            
            # 为所有输入框启用拖放功能
            self.启用输入框拖放功能()
            
            # 初始化时自动加载当前壁纸配置
            self.自动加载当前壁纸配置()
        
        def 启用输入框拖放功能(self):
            """为所有输入框启用文件拖放功能"""
            for input_field in self.input_fields:
                self.设置输入框拖放(input_field)
        
        def 设置输入框拖放(self, widget):
            """为单个输入框设置文件拖放功能"""
            # 启用拖放
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind('<<Drop>>', lambda e: self.处理文件拖放(e, widget))
        
        def 处理文件拖放(self, event, widget):
            """处理文件拖放事件"""
            try:
                # 获取拖放的文件路径
                files = event.data
                # 处理文件路径格式
                if files.startswith('{') and files.endswith('}'):
                    files = files[1:-1]
                
                file_paths = files.split('} {')
                if file_paths:
                    first_file = file_paths[0]
                    # 清空输入框并填入文件路径
                    widget.delete(0, "end")
                    widget.insert(0, first_file)
                    print(f"已拖入文件: {first_file}")
            except Exception as e:
                print(f"处理拖放文件时出错: {e}")
        
        def 自动加载当前壁纸配置(self):
            """GUI启动时自动加载当前壁纸的配置"""
            try:
                # 获取当前壁纸路径
                path = get_monitor_path(config_path, username, monitor=1)
                self.current_wallpaper_path = path
                
                # 提取壁纸文件夹名
                normalized_path = os.path.normpath(path)
                if os.path.isfile(normalized_path):
                    file_dir = os.path.dirname(normalized_path)
                else:
                    file_dir = normalized_path
                last_folder = os.path.basename(file_dir)
                self.current_wallpaper_folder = last_folder
                
                # 查找对应的鼠标配置
                config_name = wallpaper(last_folder)
                
                self.ui.tk_label_mhbv638a.config(text=config_name if config_name else "未配置")
                self.ui.tk_label_mhbv71ow.config(text=last_folder)
                
                if config_name:
                    # 加载配置到输入框
                    self.加载配置到输入框(config_name)
                    # 设置下拉选择框为当前配置
                    self.ui.tk_select_box_mhbxbsjl.set(config_name)
                    # 同时更新组名输入框
                    self.ui.tk_input_mhbxbfoz.delete(0, "end")
                    self.ui.tk_input_mhbxbfoz.insert(0, config_name)
                else:
                    # 如果没有配置，清空下拉选择框和输入框
                    self.ui.tk_select_box_mhbxbsjl.set('')
                    self.ui.tk_input_mhbxbfoz.delete(0, "end")
                    
            except Exception as e:
                print(f"自动加载配置错误: {e}")
        
        def 加载配置到输入框(self, config_name):
            """加载指定配置到输入框"""
            values = 加载配置(config_name)
            if values:
                self.fill_input_fields(values)
        
        def 配置输入框鼠标右键(self, evt):
            """右键输入框时清空内容"""
            evt.widget.delete(0, "end")
        
        # 按钮的点击打印函数
        def 保存组点击(self, evt):
            print("===== 保存组按钮被点击 =====")
            # 获取组名
            group_name = self.ui.tk_input_mhbxbfoz.get().strip()
            if not group_name:
                print("错误：组名不能为空")
                return
                
            # 获取所有配置值
            values = self.get_input_values()
            
            # 打印文本框内容和当前列表
            print(f"组名输入框内容: '{group_name}'")
            print(f"当前16个输入框的值: {values}")
            
            try:
                # 保存配置
                保存配置(group_name, "mouses", values)
                print(f"配置已保存到: mouses/{group_name}")
                
                # 更新下拉框
                self.update_combobox_items()
                
            except Exception as e:
                print(f"保存配置错误: {e}")

        def 重命名点击(self, evt):
            print("===== 重命名按钮被点击 =====")
            old_name = self.ui.tk_select_box_mhbxbsjl.get().strip()
            new_name = self.ui.tk_input_mhbxbfoz.get().strip()
            
            if not old_name or not new_name:
                print("错误：原名称和新名称都不能为空")
                return
                
            if old_name == new_name:
                print("名称未改变")
                return
                
            try:
                old_path = os.path.join("mouses", old_name)
                new_path = os.path.join("mouses", new_name)
                
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                    print(f"重命名成功: {old_name} -> {new_name}")
                    
                    # 更新config.toml中的关联
                    if os.path.exists("config.toml"):
                        with open("config.toml", 'r', encoding='utf-8') as f:
                            config_data = toml.load(f)
                        
                        if "wallpaper" in config_data:
                            for key, value in config_data["wallpaper"].items():
                                if value == old_name:
                                    config_data["wallpaper"][key] = new_name
                            
                            with open("config.toml", 'w', encoding='utf-8') as f:
                                toml.dump(config_data, f)
                    
                    self.update_combobox_items()
                else:
                    print(f"错误：配置 '{old_name}' 不存在")
                    
            except Exception as e:
                print(f"重命名错误: {e}")

        def 删除组点击(self, evt):
            print("===== 删除组按钮被点击 =====")
            group_name = self.ui.tk_select_box_mhbxbsjl.get().strip()
            if not group_name:
                print("错误：请选择要删除的组")
                return
                
            try:
                group_path = os.path.join("mouses", group_name)
                if os.path.exists(group_path):
                    shutil.rmtree(group_path)
                    print(f"已删除配置组: {group_name}")
                    
                    # 清空输入框
                    self.ui.tk_input_mhbxbfoz.delete(0, "end")
                    
                    # 更新下拉框
                    self.update_combobox_items()
                else:
                    print(f"错误：配置 '{group_name}' 不存在")
                    
            except Exception as e:
                print(f"删除配置错误: {e}")

        def 保存对当前壁纸的配置点击(self, evt):
            print("===== 保存对当前壁纸的配置按钮被点击 =====")
            if not self.current_wallpaper_path:
                print("错误：未检测到当前壁纸")
                return
                
            group_name = self.ui.tk_input_mhbxbfoz.get().strip()
            if not group_name:
                print("错误：组名不能为空")
                return
                
            # 获取所有配置值
            values = self.get_input_values()
            
            try:
                # 保存配置到组
                保存配置(group_name, "mouses", values)
                
                # 关联当前壁纸与配置组
                if add_wallpaper(group_name, self.current_wallpaper_path):
                    print(f"已关联壁纸 '{self.current_wallpaper_folder}' 到配置组 '{group_name}'")
                    self.ui.tk_label_mhbv638a.config(text=group_name)
                else:
                    print("关联壁纸配置失败")
                    
            except Exception as e:
                print(f"保存壁纸配置错误: {e}")

        def 下拉选择框选择事件(self, event):
            """当下拉选择框选择变化时，将选择的内容填入到旁边的输入框中"""
            selected_value = self.ui.tk_select_box_mhbxbsjl.get()
            # 清空并填入选择的内容到旁边的输入框
            self.ui.tk_input_mhbxbfoz.delete(0, "end")
            self.ui.tk_input_mhbxbfoz.insert(0, selected_value)
            print(f"下拉选择框选择变化: '{selected_value}' 已填入输入框")
            
            # 加载选中配置到输入框
            if selected_value:
                self.加载配置到输入框(selected_value)
        
        def update_combobox_items(self):
            """更新下拉选择框选项为mouses文件夹下的文件夹名称，开头添加空项且保持当前选择"""
            # 保存当前选中的文本
            current_value = self.ui.tk_select_box_mhbxbsjl.get()
            
            # 检查mouses文件夹是否存在
            if not os.path.exists("mouses"):
                os.makedirs("mouses")  # 不存在则创建
            
            try:
                # 列出所有条目并筛选出文件夹
                items = [
                    item for item in os.listdir("mouses")
                    if os.path.isdir(os.path.join("mouses", item))
                ]
                
                # 在开头添加空项
                items = [""] + items  # 空字符串作为空项
                
                # 更新下拉框选项
                self.ui.tk_select_box_mhbxbsjl['values'] = items
                
                # 尝试恢复之前的选择
                if current_value in items:
                    self.ui.tk_select_box_mhbxbsjl.set(current_value)
                else:
                    self.ui.tk_select_box_mhbxbsjl.current(0)
                    
            except Exception as e:
                print(f"更新下拉框时出错: {e}")
        
        def fill_input_fields(self, values):
            """
            将包含16项的列表按顺序填入到输入框内
            
            参数:
                values: 包含16个元素的列表，将按顺序填充到对应的输入框
            """
            if len(values) != 16:
                print(f"错误：输入列表必须包含16项，实际收到{len(values)}项")
                return
                
            for i, value in enumerate(values):
                # 清空并填充每个输入框
                self.input_fields[i].delete(0, "end")
                self.input_fields[i].insert(0, str(value))
            print("输入框已按顺序填充完成")
        
        def get_input_values(self):
            """
            返回所有输入框内的内容，以列表形式输出
            
            返回:
                list: 按输入框顺序排列的内容列表
            """
            values = []
            for field in self.input_fields:
                values.append(field.get())
            print("已提取所有输入框内容")
            return values

    class WinGUI(TkinterDnD.Tk):  # 改为继承TkinterDnD.Tk以支持拖放
        def __init__(self):
            super().__init__()
            self.__win()
            self.tk_label_frame_mhbv7wyv = self.__tk_label_frame_mhbv7wyv(self)
            self.tk_input_mhbvaeua = self.__tk_input_mhbvaeua(self.tk_label_frame_mhbv7wyv) 
            self.tk_label_mhbvaku5 = self.__tk_label_mhbvaku5(self.tk_label_frame_mhbv7wyv) 
            self.tk_label_mhbvc6do = self.__tk_label_mhbvc6do(self.tk_label_frame_mhbv7wyv) 
            self.tk_label_mhbvc7ki = self.__tk_label_mhbvc7ki(self.tk_label_frame_mhbv7wyv) 
            self.tk_label_mhbvcce3 = self.__tk_label_mhbvcce3(self.tk_label_frame_mhbv7wyv) 
            self.tk_label_mhbvcd9p = self.__tk_label_mhbvcd9p(self.tk_label_frame_mhbv7wyv) 
            self.tk_label_mhbvce3v = self.__tk_label_mhbvce3v(self.tk_label_frame_mhbv7wyv) 
            self.tk_label_mhbvcf8m = self.__tk_label_mhbvcf8m(self.tk_label_frame_mhbv7wyv) 
            self.tk_label_mhbvcg9q = self.__tk_label_mhbvcg9q(self.tk_label_frame_mhbv7wyv) 
            self.tk_label_mhbvchcs = self.__tk_label_mhbvchcs(self.tk_label_frame_mhbv7wyv) 
            self.tk_label_mhbvcj42 = self.__tk_label_mhbvcj42(self.tk_label_frame_mhbv7wyv) 
            self.tk_label_mhbvgtn7 = self.__tk_label_mhbvgtn7(self.tk_label_frame_mhbv7wyv) 
            self.tk_label_mhbvk74o = self.__tk_label_mhbvk74o(self.tk_label_frame_mhbv7wyv) 
            self.tk_label_mhbvkh1f = self.__tk_label_mhbvkh1f(self.tk_label_frame_mhbv7wyv) 
            self.tk_label_mhbvktfs = self.__tk_label_mhbvktfs(self.tk_label_frame_mhbv7wyv) 
            self.tk_label_mhbvl7te = self.__tk_label_mhbvl7te(self.tk_label_frame_mhbv7wyv) 
            self.tk_label_mhbvlgdj = self.__tk_label_mhbvlgdj(self.tk_label_frame_mhbv7wyv) 
            self.tk_input_mhbw85ay = self.__tk_input_mhbw85ay(self.tk_label_frame_mhbv7wyv) 
            self.tk_input_mhbw86gs = self.__tk_input_mhbw86gs(self.tk_label_frame_mhbv7wyv) 
            self.tk_input_mhbw8732 = self.__tk_input_mhbw8732(self.tk_label_frame_mhbv7wyv) 
            self.tk_input_mhbw882r = self.__tk_input_mhbw882r(self.tk_label_frame_mhbv7wyv) 
            self.tk_input_mhbw890b = self.__tk_input_mhbw890b(self.tk_label_frame_mhbv7wyv) 
            self.tk_input_mhbw8amb = self.__tk_input_mhbw8amb(self.tk_label_frame_mhbv7wyv) 
            self.tk_input_mhbw8c6w = self.__tk_input_mhbw8c6w(self.tk_label_frame_mhbv7wyv) 
            self.tk_input_mhbw8dag = self.__tk_input_mhbw8dag(self.tk_label_frame_mhbv7wyv) 
            self.tk_input_mhbw8eir = self.__tk_input_mhbw8eir(self.tk_label_frame_mhbv7wyv) 
            self.tk_input_mhbw8gbn = self.__tk_input_mhbw8gbn(self.tk_label_frame_mhbv7wyv) 
            self.tk_input_mhbw8h8g = self.__tk_input_mhbw8h8g(self.tk_label_frame_mhbv7wyv) 
            self.tk_input_mhbw8hzn = self.__tk_input_mhbw8hzn(self.tk_label_frame_mhbv7wyv) 
            self.tk_input_mhbw8jai = self.__tk_input_mhbw8jai(self.tk_label_frame_mhbv7wyv) 
            self.tk_input_mhbw8k0c = self.__tk_input_mhbw8k0c(self.tk_label_frame_mhbv7wyv) 
            self.tk_input_mhbw8kq5 = self.__tk_input_mhbw8kq5(self.tk_label_frame_mhbv7wyv) 
            self.tk_label_frame_mhbv52wj = self.__tk_label_frame_mhbv52wj(self)
            self.tk_label_mhbv5t9j = self.__tk_label_mhbv5t9j(self.tk_label_frame_mhbv52wj) 
            self.tk_label_mhbv638a = self.__tk_label_mhbv638a(self.tk_label_frame_mhbv52wj) 
            self.tk_label_mhbv69eu = self.__tk_label_mhbv69eu(self.tk_label_frame_mhbv52wj) 
            self.tk_label_mhbv71ow = self.__tk_label_mhbv71ow(self.tk_label_frame_mhbv52wj) 
            self.tk_button_mhbx9o9a = self.__tk_button_mhbx9o9a(self)
            self.tk_input_mhbxbfoz = self.__tk_input_mhbxbfoz(self)
            self.tk_select_box_mhbxbsjl = self.__tk_select_box_mhbxbsjl(self)
            self.tk_button_mhbxdcc6 = self.__tk_button_mhbxdcc6(self)
            self.tk_button_mhbxf1ky = self.__tk_button_mhbxf1ky(self)
            self.tk_button_mhbxg7zg = self.__tk_button_mhbxg7zg(self)
        
        def __win(self):
            self.title("配置此壁纸")
            width = 874
            height = 596
            screenwidth = self.winfo_screenwidth()
            screenheight = self.winfo_screenheight()
            geometry = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
            self.geometry(geometry)
            self.resizable(width=False, height=False)
        
        def scrollbar_autohide(self, vbar, hbar, widget):
            """自动隐藏滚动条"""
            def show():
                if vbar: vbar.lift(widget)
                if hbar: hbar.lift(widget)
            def hide():
                if vbar: vbar.lower(widget)
                if hbar: hbar.lower(widget)
            hide()
            widget.bind("<Enter>", lambda e: show())
            if vbar: vbar.bind("<Enter>", lambda e: show())
            if vbar: vbar.bind("<Leave>", lambda e: hide())
            if hbar: hbar.bind("<Enter>", lambda e: show())
            if hbar: hbar.bind("<Leave>", lambda e: hide())
            widget.bind("<Leave>", lambda e: hide())
        
        def v_scrollbar(self, vbar, widget, x, y, w, h, pw, ph):
            widget.configure(yscrollcommand=vbar.set)
            vbar.config(command=widget.yview)
            vbar.place(relx=(w + x) / pw, rely=y / ph, relheight=h / ph, anchor='ne')
        
        def h_scrollbar(self, hbar, widget, x, y, w, h, pw, ph):
            widget.configure(xscrollcommand=hbar.set)
            hbar.config(command=widget.xview)
            hbar.place(relx=x / pw, rely=(y + h) / ph, relwidth=w / pw, anchor='sw')
        
        def create_bar(self, master, widget, is_vbar, is_hbar, x, y, w, h, pw, ph):
            vbar, hbar = None, None
            if is_vbar:
                vbar = Scrollbar(master)
                self.v_scrollbar(vbar, widget, x, y, w, h, pw, ph)
            if is_hbar:
                hbar = Scrollbar(master, orient="horizontal")
                self.h_scrollbar(hbar, widget, x, y, w, h, pw, ph)
            self.scrollbar_autohide(vbar, hbar, widget)
        
        def __tk_label_frame_mhbv7wyv(self, parent):
            frame = LabelFrame(parent, text="配置",)
            frame.place(x=418, y=0, width=445, height=586)
            return frame
        
        def __tk_input_mhbvaeua(self, parent):
            ipt = Entry(parent)
            ipt.place(x=98, y=5, width=271, height=30)
            # 启用拖放
            ipt.drop_target_register(DND_FILES)
            return ipt
        
        def __tk_label_mhbvaku5(self, parent):
            label = Label(parent, text="正常选择", anchor="center", )
            label.place(x=42, y=5, width=50, height=30)
            return label
        
        def __tk_label_mhbvc6do(self, parent):
            label = Label(parent, text="帮助选择", anchor="center", )
            label.place(x=42, y=39, width=50, height=30)
            return label
        
        def __tk_label_mhbvc7ki(self, parent):
            label = Label(parent, text="文本选择", anchor="center", )
            label.place(x=42, y=175, width=50, height=30)
            return label
        
        def __tk_label_mhbvcce3(self, parent):
            label = Label(parent, text="水平调整大小", anchor="center", )
            label.place(x=10, y=311, width=83, height=30)
            return label
        
        def __tk_label_mhbvcd9p(self, parent):
            label = Label(parent, text="手写", anchor="center", )
            label.place(x=42, y=209, width=50, height=30)
            return label
        
        def __tk_label_mhbvce3v(self, parent):
            label = Label(parent, text="后台运行", anchor="center", )
            label.place(x=42, y=73, width=50, height=30)
            return label
        
        def __tk_label_mhbvcf8m(self, parent):
            label = Label(parent, text="垂直调整大小", anchor="center", )
            label.place(x=10, y=277, width=83, height=30)
            return label
        
        def __tk_label_mhbvcg9q(self, parent):
            label = Label(parent, text="精准选择", anchor="center", )
            label.place(x=42, y=141, width=50, height=30)
            return label
        
        def __tk_label_mhbvchcs(self, parent):
            label = Label(parent, text="不可用", anchor="center", )
            label.place(x=42, y=243, width=50, height=30)
            return label
        
        def __tk_label_mhbvcj42(self, parent):
            label = Label(parent, text="忙", anchor="center", )
            label.place(x=42, y=107, width=50, height=30)
            return label
        
        def __tk_label_mhbvgtn7(self, parent):
            label = Label(parent, text="沿对角线调整1", anchor="center", )
            label.place(x=11, y=345, width=81, height=30)
            return label
        
        def __tk_label_mhbvk74o(self, parent):
            label = Label(parent, text="沿对角线调整2", anchor="center", )
            label.place(x=11, y=379, width=81, height=30)
            return label
        
        def __tk_label_mhbvkh1f(self, parent):
            label = Label(parent, text="移动", anchor="center", )
            label.place(x=42, y=413, width=50, height=30)
            return label
        
        def __tk_label_mhbvktfs(self, parent):
            label = Label(parent, text="候选", anchor="center", )
            label.place(x=42, y=447, width=50, height=30)
            return label
        
        def __tk_label_mhbvl7te(self, parent):
            label = Label(parent, text="链接选择", anchor="center", )
            label.place(x=42, y=481, width=50, height=30)
            return label
        
        def __tk_label_mhbvlgdj(self, parent):
            label = Label(parent, text="位置选择", anchor="center", )
            label.place(x=42, y=515, width=50, height=30)
            return label
        
        def __tk_input_mhbw85ay(self, parent):
            ipt = Entry(parent)
            ipt.place(x=98, y=39, width=271, height=30)
            ipt.drop_target_register(DND_FILES)
            return ipt
        
        def __tk_input_mhbw86gs(self, parent):
            ipt = Entry(parent)
            ipt.place(x=98, y=73, width=271, height=30)
            ipt.drop_target_register(DND_FILES)
            return ipt
        
        def __tk_input_mhbw8732(self, parent):
            ipt = Entry(parent)
            ipt.place(x=98, y=107, width=271, height=30)
            ipt.drop_target_register(DND_FILES)
            return ipt
        
        def __tk_input_mhbw882r(self, parent):
            ipt = Entry(parent)
            ipt.place(x=98, y=141, width=271, height=30)
            ipt.drop_target_register(DND_FILES)
            return ipt
        
        def __tk_input_mhbw890b(self, parent):
            ipt = Entry(parent)
            ipt.place(x=98, y=175, width=271, height=30)
            ipt.drop_target_register(DND_FILES)
            return ipt
        
        def __tk_input_mhbw8amb(self, parent):
            ipt = Entry(parent)
            ipt.place(x=98, y=209, width=271, height=30)
            ipt.drop_target_register(DND_FILES)
            return ipt
        
        def __tk_input_mhbw8c6w(self, parent):
            ipt = Entry(parent)
            ipt.place(x=98, y=243, width=271, height=30)
            ipt.drop_target_register(DND_FILES)
            return ipt
        
        def __tk_input_mhbw8dag(self, parent):
            ipt = Entry(parent)
            ipt.place(x=98, y=277, width=271, height=30)
            ipt.drop_target_register(DND_FILES)
            return ipt
        
        def __tk_input_mhbw8eir(self, parent):
            ipt = Entry(parent)
            ipt.place(x=98, y=311, width=271, height=30)
            ipt.drop_target_register(DND_FILES)
            return ipt
        
        def __tk_input_mhbw8gbn(self, parent):
            ipt = Entry(parent)
            ipt.place(x=98, y=345, width=271, height=30)
            ipt.drop_target_register(DND_FILES)
            return ipt
        
        def __tk_input_mhbw8h8g(self, parent):
            ipt = Entry(parent)
            ipt.place(x=98, y=379, width=271, height=30)
            ipt.drop_target_register(DND_FILES)
            return ipt
        
        def __tk_input_mhbw8hzn(self, parent):
            ipt = Entry(parent)
            ipt.place(x=98, y=413, width=271, height=30)
            ipt.drop_target_register(DND_FILES)
            return ipt
        
        def __tk_input_mhbw8jai(self, parent):
            ipt = Entry(parent)
            ipt.place(x=98, y=447, width=271, height=30)
            ipt.drop_target_register(DND_FILES)
            return ipt
        
        def __tk_input_mhbw8k0c(self, parent):
            ipt = Entry(parent)
            ipt.place(x=98, y=481, width=271, height=30)
            ipt.drop_target_register(DND_FILES)
            return ipt
        
        def __tk_input_mhbw8kq5(self, parent):
            ipt = Entry(parent)
            ipt.place(x=98, y=515, width=271, height=30)
            ipt.drop_target_register(DND_FILES)
            return ipt
        
        def __tk_label_frame_mhbv52wj(self, parent):
            frame = LabelFrame(parent, text="信息",)
            frame.place(x=12, y=0, width=399, height=95)
            return frame
        
        def __tk_label_mhbv5t9j(self, parent):
            label = Label(parent, text="当前壁纸：", anchor="center", )
            label.place(x=13, y=5, width=64, height=30)
            return label
        
        def __tk_label_mhbv638a(self, parent):
            label = Label(parent, text="标签", anchor="center", )
            label.place(x=86, y=5, width=311, height=30)
            return label
        
        def __tk_label_mhbv69eu(self, parent):
            label = Label(parent, text="编号：", anchor="center", )
            label.place(x=37, y=39, width=40, height=30)
            return label
        
        def __tk_label_mhbv71ow(self, parent):
            label = Label(parent, text="标签", anchor="center", )
            label.place(x=86, y=39, width=311, height=30)
            return label
        
        def __tk_button_mhbx9o9a(self, parent):
            btn = Button(parent, text="保存对当前壁纸的配置", takefocus=False,)
            btn.place(x=206, y=160, width=169, height=30)
            return btn
        
        def __tk_input_mhbxbfoz(self, parent):
            ipt = Entry(parent, )
            ipt.place(x=175, y=113, width=174, height=30)
            return ipt
        
        def __tk_select_box_mhbxbsjl(self, parent):
            cb = Combobox(parent, state="readonly", )
            cb.place(x=16, y=114, width=150, height=30)
            return cb
        
        def __tk_button_mhbxdcc6(self, parent):
            btn = Button(parent, text="重命名", takefocus=False,)
            btn.place(x=358, y=113, width=50, height=30)
            return btn
        
        def __tk_button_mhbxf1ky(self, parent):
            btn = Button(parent, text="保存组", takefocus=False,)
            btn.place(x=80, y=160, width=50, height=30)
            return btn
        
        def __tk_button_mhbxg7zg(self, parent):
            btn = Button(parent, text="删除组", takefocus=False,)
            btn.place(x=143, y=160, width=50, height=30)
            return btn

    class Win(WinGUI):
        def __init__(self, controller):
            self.ctl = controller
            super().__init__()
            self.__event_bind()
            self.__style_config()
            self.ctl.init(self)
        
        def __event_bind(self):
            # 绑定输入框右键事件
            self.tk_input_mhbvaeua.bind('<Button-3>', self.ctl.配置输入框鼠标右键)
            self.tk_input_mhbw85ay.bind('<Button-3>', self.ctl.配置输入框鼠标右键)
            self.tk_input_mhbw86gs.bind('<Button-3>', self.ctl.配置输入框鼠标右键)
            self.tk_input_mhbw8732.bind('<Button-3>', self.ctl.配置输入框鼠标右键)
            self.tk_input_mhbw882r.bind('<Button-3>', self.ctl.配置输入框鼠标右键)
            self.tk_input_mhbw890b.bind('<Button-3>', self.ctl.配置输入框鼠标右键)
            self.tk_input_mhbw8amb.bind('<Button-3>', self.ctl.配置输入框鼠标右键)
            self.tk_input_mhbw8c6w.bind('<Button-3>', self.ctl.配置输入框鼠标右键)
            self.tk_input_mhbw8dag.bind('<Button-3>', self.ctl.配置输入框鼠标右键)
            self.tk_input_mhbw8eir.bind('<Button-3>', self.ctl.配置输入框鼠标右键)
            self.tk_input_mhbw8gbn.bind('<Button-3>', self.ctl.配置输入框鼠标右键)
            self.tk_input_mhbw8h8g.bind('<Button-3>', self.ctl.配置输入框鼠标右键)
            self.tk_input_mhbw8hzn.bind('<Button-3>', self.ctl.配置输入框鼠标右键)
            self.tk_input_mhbw8jai.bind('<Button-3>', self.ctl.配置输入框鼠标右键)
            self.tk_input_mhbw8k0c.bind('<Button-3>', self.ctl.配置输入框鼠标右键)
            self.tk_input_mhbw8kq5.bind('<Button-3>', self.ctl.配置输入框鼠标右键)
            
            # 绑定输入框拖放事件
            self.tk_input_mhbvaeua.dnd_bind('<<Drop>>', lambda e: self.ctl.处理文件拖放(e, self.tk_input_mhbvaeua))
            self.tk_input_mhbw85ay.dnd_bind('<<Drop>>', lambda e: self.ctl.处理文件拖放(e, self.tk_input_mhbw85ay))
            self.tk_input_mhbw86gs.dnd_bind('<<Drop>>', lambda e: self.ctl.处理文件拖放(e, self.tk_input_mhbw86gs))
            self.tk_input_mhbw8732.dnd_bind('<<Drop>>', lambda e: self.ctl.处理文件拖放(e, self.tk_input_mhbw8732))
            self.tk_input_mhbw882r.dnd_bind('<<Drop>>', lambda e: self.ctl.处理文件拖放(e, self.tk_input_mhbw882r))
            self.tk_input_mhbw890b.dnd_bind('<<Drop>>', lambda e: self.ctl.处理文件拖放(e, self.tk_input_mhbw890b))
            self.tk_input_mhbw8amb.dnd_bind('<<Drop>>', lambda e: self.ctl.处理文件拖放(e, self.tk_input_mhbw8amb))
            self.tk_input_mhbw8c6w.dnd_bind('<<Drop>>', lambda e: self.ctl.处理文件拖放(e, self.tk_input_mhbw8c6w))
            self.tk_input_mhbw8dag.dnd_bind('<<Drop>>', lambda e: self.ctl.处理文件拖放(e, self.tk_input_mhbw8dag))
            self.tk_input_mhbw8eir.dnd_bind('<<Drop>>', lambda e: self.ctl.处理文件拖放(e, self.tk_input_mhbw8eir))
            self.tk_input_mhbw8gbn.dnd_bind('<<Drop>>', lambda e: self.ctl.处理文件拖放(e, self.tk_input_mhbw8gbn))
            self.tk_input_mhbw8h8g.dnd_bind('<<Drop>>', lambda e: self.ctl.处理文件拖放(e, self.tk_input_mhbw8h8g))
            self.tk_input_mhbw8hzn.dnd_bind('<<Drop>>', lambda e: self.ctl.处理文件拖放(e, self.tk_input_mhbw8hzn))
            self.tk_input_mhbw8jai.dnd_bind('<<Drop>>', lambda e: self.ctl.处理文件拖放(e, self.tk_input_mhbw8jai))
            self.tk_input_mhbw8k0c.dnd_bind('<<Drop>>', lambda e: self.ctl.处理文件拖放(e, self.tk_input_mhbw8k0c))
            self.tk_input_mhbw8kq5.dnd_bind('<<Drop>>', lambda e: self.ctl.处理文件拖放(e, self.tk_input_mhbw8kq5))
            
            # 绑定所有按钮点击事件
            self.tk_button_mhbx9o9a.bind('<Button-1>', self.ctl.保存对当前壁纸的配置点击)
            self.tk_button_mhbxdcc6.bind('<Button-1>', self.ctl.重命名点击)
            self.tk_button_mhbxf1ky.bind('<Button-1>', self.ctl.保存组点击)
            self.tk_button_mhbxg7zg.bind('<Button-1>', self.ctl.删除组点击)
            
            # 绑定下拉选择框选择事件
            self.tk_select_box_mhbxbsjl.bind('<<ComboboxSelected>>', self.ctl.下拉选择框选择事件)
        
        def __style_config(self):
            pass

    controller = Controller()
    win = Win(controller)
    
    # 测试提取数据
    print(controller.get_input_values())
    
    win.mainloop()









mouse_path = r"mouses"
username = "woshi"

#wallpaper_engine 配置路径
config_path = r"D:\Application\STEAM\steamapps\common\wallpaper_engine\config.json"

# 触发刷新确保启动时应用当前配置
触发刷新()

# 启动GUI
ui_设置()