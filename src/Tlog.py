# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: MIT
import datetime
import inspect
import sys
import re
import traceback

class TLog:
    def __init__(self, title="SYSTEM"):
        self.title = title
        self.on = True
        self.TF = True
        self.on_def = True
        self._time = True
        self.on_DEBUG = False
        self.level = 3

    def __color_text(self, text, is_error=False):
        res = str(text)
        tags = {"<f": "\033[0;35m",
                "<r": "\033[0;31m",
                "<b": "\033[0;34m",
                "<g": "\033[0;32m",
                "<_": "\033[4m",
                "<-": "\033[9m",
                "<i": "\033[3m",
                "<B": "\033[1m",
                "<!": "\033[1;31m",
                "<#!": "\033[41m"}
        for tag, code in tags.items(): res = res.replace(tag, code)
        if self.TF:
            res = res.replace("True", "\033[1;32mTrue\033[0m").replace("False", "\033[1;31mFalse\033[0m").replace("None", "\033[1;34mNone\033[0m")
        reset = "\033[0;31m" if is_error else "\033[0m"
        res = res.replace(">>", "[@BS]").replace(">", reset).replace("[@BS]", ">")
        if "<time" in res and self._time:
            res = res.replace("<time", f"\033[0;34m{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}\033[0m")
        return res

    def _get_info(self, frame):
        info = inspect.getframeinfo(frame)
        ts = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]" if self._time else ""
        class_name = f"{frame.f_locals['self'].__class__.__name__}." if 'self' in frame.f_locals else ""
        def_name = f",\033[0;34mdef:\033[0;35m{class_name}{info.function}\033[0m" if self.on_def and info.function != "<module>" else ""
        return ts, info.lineno, def_name

    def error(self, text):
        if self.on and self.level >= 1:
            frame = inspect.currentframe().f_back
            ts, line, df = self._get_info(frame)
            print(f"\033[0;34m{ts}\033[0;32m{self.title}\033[0m\033[1;31m ERROR [{line}]{df} >\033[0m\033[0;31m{self.__color_text(text, True)}\033[0m")
            
            if inspect.getframeinfo(frame).function != "<module>":
                filtered = {k: v for k, v in frame.f_locals.items() if not k.startswith("__") and k != 'self' and not inspect.ismodule(v) and not inspect.isfunction(v) and not inspect.isclass(v)}
                if filtered: print(f"    \033[0;33m└─ Local Vars:\033[0m {filtered}")
            
            if sys.exc_info()[0]: print("\033[0;31m" + traceback.format_exc() + "\033[0m")

    def info(self, text):
        if self.on and self.level >= 2:
            ts, _, _ = self._get_info(inspect.currentframe().f_back)
            print(f"\033[0;34m{ts}\033[0;32m{self.title} \033[1;32m>\033[0m{self.__color_text(text)}")

    def warning(self, text):
        if self.on and self.level >= 2:
            frame = inspect.currentframe().f_back
            ts, line, df = self._get_info(frame)
            print(f"\033[0;34m{ts}\033[0;32m{self.title}\033[0m\033[1;33m WARNING [{line}]{df} >\033[0m\033[0;33m{self.__color_text(text)}\033[0m")
            
            if inspect.getframeinfo(frame).function != "<module>":
                filtered = {k: v for k, v in frame.f_locals.items() if not k.startswith("__") and k != 'self' and not inspect.ismodule(v) and not inspect.isfunction(v) and not inspect.isclass(v)}
                if filtered: print(f"    \033[0;33m└─ Local Vars:\033[0m {filtered}")

    def debug(self, text):
        if self.on and self.on_DEBUG and self.level >= 3:
            ts, line, df = self._get_info(inspect.currentframe().f_back)
            print(f"\033[0;34m{ts}\033[0;32m{self.title}\033[0m\033[1;33m DEBUG [{line}]{df} \033[1;33m>\033[0m{self.__color_text(text)}")

    def val(self, var):
        if self.on and self.on_DEBUG and self.level >= 3:
            frame = inspect.currentframe().f_back
            ts, line, _ = self._get_info(frame)
            
            code_lines = inspect.getframeinfo(frame).code_context
            code_line = code_lines[0].strip() if code_lines else "unknown"
            var_name = re.search(r"val\((.*)\)", code_line).group(1) if "(" in code_line else "unknown"
            
            is_global = var_name in frame.f_globals and frame.f_globals[var_name] is var
            scope = "\033[0;33m[Global]\033[0m" if is_global else "\033[0;36m[Local]\033[0m"
            
            v_type = type(var).__name__
            extra = (f", len:{len(var)}" if hasattr(var, "__len__") and not isinstance(var, str) else "") + \
                    (f", hex:{hex(var)}" if isinstance(var, int) and not isinstance(var, bool) else "")
            
            header = f"\033[0;34m{ts}\033[0;32m{self.title} \033[0;36m[VAL] \033[1;33m[{line}]\033[0m"
            detail = f"{scope} \033[1;33m>\033[0m{var_name} (\033[0;35m{v_type}\033[0m{extra})"
            print(f"{header} {detail} = {self.__color_text(var)}")

    def code(self, obj):
        if self.on and self.on_DEBUG and self.level >= 3:
            try: print(f"\033[1;35m[SOURCE]\033[0m\n{inspect.getsource(obj)}")
            except: self.error("无法提取源码")


    INFO = info
    DEBUG = debug
    ERROR = error
    WARNING = warning


import re
if __name__ == "__main__":
    log = TLog('logTest')
    log.INFO('兼容测试：<-删除线> <_下划线> <i斜体> <g绿色> <r红色>')
    log.INFO('占位符 时间检测:<time')
    log.error("test")
    log.warning("test")
    log.DEBUG("test")
    log.val(log)
    def test():
        pass
    log.code(test)
