import os

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

CURSOR_TO_STRING_KEY = {
    "Arrow": "pointer",
    "Help": "help",
    "AppStarting": "working",
    "Wait": "busy",
    "Crosshair": "precision",
    "IBeam": "text",
    "Handwriting": "hand",
    "No": "unavailable",
    "SizeNS": "vert",
    "SizeWE": "horz",
    "SizeNWSE": "dgn1",
    "SizeNESW": "dgn2",
    "SizeAll": "move",
    "Hand": "link",
    "UpArrow": "alternate"
}

class INFParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.base_dir = os.path.dirname(file_path)
        self.sections = {}
        self.strings = {}
        self.current_section = None
        self._parse()
    
    def _parse(self):
        try:
            with open(self.file_path, 'r', encoding='gb2312') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith(';'):
                        continue
                    
                    if line.startswith('[') and line.endswith(']'):
                        section_name = line[1:-1].strip()
                        self.current_section = section_name
                        self.sections[section_name] = []
                    elif self.current_section:
                        self.sections[self.current_section].append(line)
            
            # 解析 Strings 节
            if 'Strings' in self.sections:
                for line in self.sections['Strings']:
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"')
                        self.strings[key] = value
        except Exception as e:
            print(f"解析文件时出错: {e}")
    
    def get_cursor_paths_in_order(self):
        cursor_paths = []
        
        for cursor_name in CURSOR_ORDER_MAPPING:
            file_name = None
            if cursor_name in CURSOR_TO_STRING_KEY:
                string_key = CURSOR_TO_STRING_KEY[cursor_name]
                if string_key in self.strings:
                    file_name = self.strings[string_key]
            
            if file_name:
                absolute_path = os.path.join(self.base_dir, file_name)
                cursor_paths.append(absolute_path)
            else:
                cursor_paths.append("")
        
        scheme_name = self.strings.get('SCHEME_NAME', '')
        return cursor_paths, scheme_name
    
    def get_scheme_name(self):
        """获取 SCHEME_NAME"""
        return self.strings.get('SCHEME_NAME', '')
