# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: BSD-3-Clause
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from path_utils import resolve_path

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

CURSOR_TYPE_ALIASES = {
    "Arrow": ["arrow", "pointer", "normal"],
    "Help": ["help"],
    "AppStarting": ["appstarting", "working", "work"],
    "Wait": ["wait", "busy"],
    "Crosshair": ["crosshair", "cross", "precision", "precisionhair"],
    "IBeam": ["ibeam", "beam", "text"],
    "Handwriting": ["handwriting", "hand", "pen", "nwpen"],
    "No": ["no", "unavailable"],
    "SizeNS": ["sizens", "ns", "vertical", "vert"],
    "SizeWE": ["sizewe", "we", "horizontal", "horz"],
    "SizeNWSE": ["sizenwse", "nwse", "dgn1", "diagonal1"],
    "SizeNESW": ["sizenesw", "nesw", "dgn2", "diagonal2"],
    "SizeAll": ["sizeall", "move"],
    "Hand": ["hand", "link"],
    "UpArrow": ["uparrow", "alternate", "loc"]
}

class INFParser:
    def __init__(self, file_path):
        self.file_path = resolve_path(file_path)
        self.base_dir = os.path.dirname(self.file_path)
        self.sections = {}
        self.strings = {}
        self.current_section = None
        self.cursor_mapping = {}
        self.alias_to_standard = {}
        self._build_alias_mapping()
        self._parse()
    
    def _build_alias_mapping(self):
        for standard_type, aliases in CURSOR_TYPE_ALIASES.items():
            for alias in aliases:
                self.alias_to_standard[alias.lower()] = standard_type
            self.alias_to_standard[standard_type.lower()] = standard_type
    
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
            
            if 'Strings' in self.sections:
                for line in self.sections['Strings']:
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"')
                        self.strings[key] = value
            
            self._build_cursor_mapping()
        except Exception as e:
            print(f"解析文件时出错: {e}")
    
    def _build_cursor_mapping(self):
        cursor_mapping = {}
        
        if 'Wreg' in self.sections:
            for line in self.sections['Wreg']:
                if 'Control Panel\\Cursors' in line and ',' in line:
                    parts = [p.strip().strip('"') for p in line.split(',')]
                    if len(parts) >= 5 and parts[2] and parts[2] != '':
                        cursor_type = parts[2]
                        cursor_path = parts[4]
                        
                        if cursor_path.startswith('%10%\\%CUR_DIR%\\'):
                            var_name = cursor_path[16:].strip('"')
                        elif cursor_path.startswith('%10%\\%CUR_DIR%'):
                            var_name = cursor_path[15:].strip('"')
                        else:
                            var_name = cursor_path.strip('%')
                        
                        var_name = var_name.strip('%')
                        
                        var_name_lower = var_name.lower()
                        found_value = None
                        for key, value in self.strings.items():
                            if key.lower() == var_name_lower:
                                found_value = value
                                break
                        
                        if found_value:
                            cursor_mapping[cursor_type] = found_value
                        else:
                            cursor_mapping[cursor_type] = var_name
        
        if not cursor_mapping:
            for cursor_type, aliases in CURSOR_TYPE_ALIASES.items():
                for alias in aliases:
                    if alias in self.strings:
                        cursor_mapping[cursor_type] = self.strings[alias]
                        break
        
        self.cursor_mapping = cursor_mapping
    
    def _find_cursor_file(self, cursor_type):
        cursor_type_lower = cursor_type.lower()
        
        for key, value in self.cursor_mapping.items():
            if key.lower() == cursor_type_lower:
                return value
            
            if key.lower() in self.alias_to_standard:
                standard_type = self.alias_to_standard[key.lower()]
                if standard_type.lower() == cursor_type_lower:
                    return value
        
        if cursor_type_lower in self.alias_to_standard:
            standard_type = self.alias_to_standard[cursor_type_lower]
            for key, value in self.cursor_mapping.items():
                if key.lower() == standard_type.lower():
                    return value
        
        for key, value in self.strings.items():
            if key.lower() in self.alias_to_standard:
                standard_type = self.alias_to_standard[key.lower()]
                if standard_type.lower() == cursor_type_lower:
                    return value
        
        return None
    
    def get_cursor_paths_in_order(self):
        cursor_paths = []
        
        for cursor_name in CURSOR_ORDER_MAPPING:
            file_name = self._find_cursor_file(cursor_name)
            
            if file_name:
                absolute_path = os.path.join(self.base_dir, file_name)
                if os.path.exists(absolute_path):
                    cursor_paths.append(absolute_path)
                else:
                    cursor_paths.append("")
            else:
                cursor_paths.append("")
        
        scheme_name = self.strings.get('SCHEME_NAME', '')
        return cursor_paths, scheme_name
    
    def get_scheme_name(self):
        return self.strings.get('SCHEME_NAME', '')
    
    def get_cursor_mapping(self):
        return self.cursor_mapping.copy()
