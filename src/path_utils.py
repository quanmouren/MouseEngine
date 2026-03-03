# Copyright (c) 2026, CIF3
# SPDX-License-Identifier: MIT
import os
import sys

def get_project_root() -> str:
    """
    获取项目根目录路径
    处理不同环境下的路径问题，包括开发环境、打包环境和_internal目录环境
    """
    # 检查是否是打包环境
    if getattr(sys, 'frozen', False):
        # 在打包环境中，返回exe文件所在的目录
        return os.path.dirname(os.path.abspath(sys.executable))
    
    # 获取当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 检查是否在_internal目录中
    if '_internal' in current_dir:
        # 如果在_internal目录中，返回上一级目录
        return os.path.dirname(current_dir)
    
    # 否则返回当前目录
    return current_dir

def resolve_path(path: str) -> str:
    """
    解析路径
    - 如果是绝对路径，直接返回
    - 如果是相对路径，基于项目根目录拼接为绝对路径
    """
    if not path:
        return path
    
    # 检查是否为绝对路径
    if os.path.isabs(path):
        return os.path.abspath(path)
    
    # 相对路径，基于项目根目录拼接
    project_root = get_project_root()
    return os.path.abspath(os.path.join(project_root, path))
