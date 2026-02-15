# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: CC BY-NC-SA 4.0
import tkinter as tk
from tkinter import scrolledtext

class LuaCodeEditor:
    def __init__(self, parent):
        self.parent = parent
        self.root_frame = tk.Frame(parent, bg="#252526")

        self.line_numbers = tk.Text(
            self.root_frame,
            width=4,
            padx=2,
            pady=2,
            bg="#252526",
            fg="#888888",
            font=("Consolas", 12),
            state=tk.DISABLED,
            wrap=tk.NONE,
            relief=tk.FLAT
        )
        
        self.editor = scrolledtext.ScrolledText(
            self.root_frame,
            font=("Consolas", 12),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            undo=True,
            wrap=tk.NONE,
            relief=tk.FLAT,
            borderwidth=0
        )
        
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        self.editor.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.lua_keywords = {
            "and", "break", "do", "else", "elseif", "end", "false", "for",
            "function", "if", "in", "local", "nil", "not", "or", "repeat",
            "return", "then", "true", "until", "while"
        }
        self._init_highlight_tags()
        
        self._bind_events()
        
        self._update_line_numbers()

    def _init_highlight_tags(self):
        """初始化语法高亮标签"""
        # 关键字
        self.editor.tag_configure("keyword", foreground="#569cd6")
        # 字符串
        self.editor.tag_configure("string", foreground="#ce9178")
        # 注释
        self.editor.tag_configure("comment", foreground="#6a9955")
        # 数字
        self.editor.tag_configure("number", foreground="#b5cea8")
        # 函数名
        self.editor.tag_configure("function", foreground="#dcdcaa")

    def _bind_events(self):
        """绑定编辑器事件"""
        # Tab键插入4个空格
        self.editor.bind("<Tab>", self._handle_tab)
        # 实时更新行号
        self.editor.bind("<KeyRelease>", self._on_key_release)
        self.editor.bind("<MouseWheel>", self._update_line_numbers)
        # 自动缩进
        self.editor.bind("<Return>", self._handle_return)
        # 失去焦点时也更新行号
        self.editor.bind("<FocusOut>", self._update_line_numbers)

    def _handle_tab(self, event):
        """Tab键插入4个空格"""
        self.editor.insert(tk.INSERT, "    ")
        return "break"

    def _handle_return(self, event):
        """回车时自动缩进"""
        current_line = self.editor.get("insert linestart", "insert lineend")
        indent = len(current_line) - len(current_line.lstrip())
        self.editor.insert(tk.INSERT, "\n" + " " * indent)
        return "break"

    def _update_line_numbers(self, event=None):
        """更新行号显示"""
        line_count = int(self.editor.index(tk.END).split('.')[0]) - 1
        self.line_numbers.config(state=tk.NORMAL)
        self.line_numbers.delete("1.0", tk.END)
        self.line_numbers.insert(tk.END, "\n".join(str(i) for i in range(1, line_count + 1)))
        self.line_numbers.config(state=tk.DISABLED)
        self.line_numbers.yview_moveto(self.editor.yview()[0])

    def _highlight_code(self):
        for tag in ["keyword", "string", "comment", "number", "function"]:
            self.editor.tag_remove(tag, "1.0", tk.END)
        
        code = self.editor.get("1.0", tk.END)
        lines = code.split("\n")
        
        for line_idx, line in enumerate(lines):
            line_num = line_idx + 1
            pos = 0
            in_string = False
            string_quote = None
            in_comment = False
            
            while pos < len(line):
                if not in_string and not in_comment and line.startswith("--", pos):
                    start = f"{line_num}.{pos}"
                    end = f"{line_num}.{len(line)}"
                    self.editor.tag_add("comment", start, end)
                    break
                
                if not in_comment:
                    if not in_string and (line[pos] in ['"', "'"]):
                        in_string = True
                        string_quote = line[pos]
                        start = f"{line_num}.{pos}"
                        pos += 1
                        while pos < len(line) and line[pos] != string_quote:
                            pos += 1
                        if pos < len(line):
                            end = f"{line_num}.{pos + 1}"
                            self.editor.tag_add("string", start, end)
                            in_string = False
                            pos += 1
                        continue
                    elif in_string and line[pos] == string_quote:
                        end = f"{line_num}.{pos + 1}"
                        self.editor.tag_add("string", start, end)
                        in_string = False
                        pos += 1
                        continue
                
                if not in_string and not in_comment:
                    word_start = pos
                    while pos < len(line) and (line[pos].isalnum() or line[pos] == "_"):
                        pos += 1
                    if word_start < pos:
                        word = line[word_start:pos]
                        if word in self.lua_keywords:
                            start = f"{line_num}.{word_start}"
                            end = f"{line_num}.{pos}"
                            self.editor.tag_add("keyword", start, end)
                        elif word.isdigit() or (word.startswith('-') and word[1:].isdigit()):
                            start = f"{line_num}.{word_start}"
                            end = f"{line_num}.{pos}"
                            self.editor.tag_add("number", start, end)
                        elif (word_start > 8 and line[word_start-8:word_start] == "function "):
                            start = f"{line_num}.{word_start}"
                            end = f"{line_num}.{pos}"
                            self.editor.tag_add("function", start, end)
                    else:
                        pos += 1
                else:
                    pos += 1

    def _on_key_release(self, event):
        ignore_keys = ["Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"]
        if event.keysym not in ignore_keys:
            self._update_line_numbers()
            self.editor.after(100, self._highlight_code)

    def pack(self, **kwargs):
        self.root_frame.pack(** kwargs)

    def get_code(self):
        """获取编辑器中的代码"""
        return self.editor.get("1.0", tk.END)

    def set_code(self, code):
        """设置编辑器中的代码"""
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", code)
        self._update_line_numbers()
        self._highlight_code()

    def bind(self, *args, **kwargs):
        """事件绑定方法"""
        self.editor.bind(*args, **kwargs)

    def edit_modified(self, flag=None):
        """兼容原有代码的修改状态检测"""
        if flag is not None:
            self.editor.edit_modified(flag)
        return self.editor.edit_modified()


if __name__ == "__main__":
    # 创建主窗口
    root = tk.Tk()
    root.title("Lua 代码编辑器 - 测试")
    root.geometry("800x600")
    root.configure(bg="#1e1e1e")
    
    # 创建编辑器实例
    editor = LuaCodeEditor(root)
    editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # 预设测试用的 Lua 代码
    test_lua_code = '''-- Cur2D 编辑器测试代码
fps = 60
total_frames = 120

function on_render(current_frame)
    set_canvas(800, 600)
    set_hotspot(400, 300)
    load_png("bg", "assets/background.png")
    add_image("bg", 0, 0)
    
    local count = 123
    local neg_num = -456
    if current_frame < 60 then
        draw_rect(50, 50, 200, 100, "#FF0000", 10)
    end
end'''
    
    # 设置测试代码到编辑器
    editor.set_code(test_lua_code)
    
    # 运行主循环
    root.mainloop()