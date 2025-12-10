import datetime
import inspect
class TLog:
    def __init__(self, title):
        self.title = title
        self.on = True
        self.TF = True
        self.on_def = True
        self._time = True
        self.on_DEBUG = True
        self.level = 2
    def __color_text(self, text, endColor="W"):
        text = f"{text}"
        text = text.replace("<f", "\033[0;35m")
        text = text.replace("<r", "\033[0;31m")
        text = text.replace("<b", "\033[0;34m")
        text = text.replace("<g", "\033[0;32m")
        if self.TF:
            text = text.replace("True", "\033[1;32mTrue\033[0m")
            text = text.replace("False", "\033[1;31mFalse\033[0m")
            text = text.replace("None", "\033[1;34mNone\033[0m")
        text = text.replace("<_", "\033[4m")
        text = text.replace("<-", "\033[9m")
        text = text.replace("<i", "\033[3m")
        text = text.replace("<B", "\033[1m")
        if endColor == "error":
            text = text.replace(">", "\033[0;31m")
            text = text.replace("<!", "\033[1;31m")
            text = text.replace("<#!", "\033[41m")
        text = text.replace(">>", "[@backslash]")
        text = text.replace(">", "\033[0m")
        text = text.replace("[@backslash]", ">")
        text = text.replace("<time", f"\033[0;34m{datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]}\033[0m")
        return text
    def DEBUG(self, text):
        if self.on and self.on_DEBUG and self.level >= 1:
            if self._time:
                timestamp = f"[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]"
            else:
                timestamp = ""
            current_frame = inspect.currentframe()
            (filename, line_number, func_name, lines, index) = inspect.getframeinfo(current_frame.f_back)
            if func_name != "<module>" and self.on_def:
                def_name = f",\033[0;34mdef:\033[0;35m{func_name}\033[0m"
            else:
                def_name = ""
            text = self.__color_text(text)
            print(f"\033[0;34m{timestamp}\033[0;32m{self.title}\033[0m\033[1;33m DEBUG [{line_number}]{def_name} \033[1;33m>\033[0m{text}")
    def INFO(self, text):
        if self.on and self.level >= 2:
            if self._time:
                timestamp = f"[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]"
            else:
                timestamp = ""
            text = self.__color_text(text)
            print(f"\033[0;34m{timestamp}\033[0;32m{self.title} \033[1;32m>\033[0m{text}")
    def ERROR(self, text):
        if self.on and self.level >= 0:
            if self._time:
                timestamp = f"[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]"
            else:
                timestamp = ""
            current_frame = inspect.currentframe()
            (filename, line_number, func_name, lines, index) = inspect.getframeinfo(current_frame.f_back)
            if func_name != "<module>" and self.on_def:
                def_name = f",\033[0;34mdef:\033[0;35m{func_name}\033[0m"
            else:
                def_name = ""
            text = self.__color_text(text,'error')
            print(f"\033[0;34m{timestamp}\033[0;32m{self.title}\033[0m\033[1;31m ERROR [{line_number}]{def_name} >\033[0m\033[0;31m{text}\033[0m")
    error = ERROR
    debug = DEBUG
    info = INFO

if __name__ == '__main__':
    log = TLog('标题')
    log.INFO('文本')
    def 函数名称():
        log = TLog('')
        log.DEBUG('显示函数')
    函数名称()
    log.on_def = False
    log = TLog('')
    log.ERROR('默认文本 <!亮色> <#!底亮>')
    log.INFO('颜色 <-删除线> <_下划线> <i斜体> <b粗体> <g绿色> <r红色> <f地址> <B粗体>')
    log.INFO('占位符 时间:<time')
