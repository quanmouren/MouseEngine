import os
from tkinter import *
from tkinter.ttk import *

class Controller:
    ui: object
    def __init__(self):
        pass
    
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
    
    def 配置输入框鼠标右键(self, evt):
        """右键输入框时清空内容"""
        evt.widget.delete(0, "end")
    
    # 按钮的点击打印函数
    def 保存组点击(self, evt):
        print("===== 保存组按钮被点击 =====")
        # 获取下拉选择框旁边的输入框内容（组名）
        group_name = self.ui.tk_input_mhbxbfoz.get()
        # 获取所有配置值
        values = self.get_input_values()
        
        # 打印文本框内容和当前列表
        print(f"组名输入框内容: '{group_name}'")
        print(f"当前16个输入框的值: {values}")
        
        # 获取下拉框当前选择的值
        current_selection = self.ui.tk_select_box_mhbxbsjl.get()
        print(f"下拉框当前选择: '{current_selection}'")
        
        # 获取下拉框所有选项
        all_options = list(self.ui.tk_select_box_mhbxbsjl['values'])
        print(f"下拉框所有选项: {all_options}")
        
        self.update_combobox_items()  # 保存组按钮点击时更新下拉框

    def 重命名点击(self, evt):
        print("===== 重命名按钮被点击 =====")
        self.update_combobox_items()  # 重命名按钮点击时更新下拉框

    def 删除组点击(self, evt):
        print("===== 删除组按钮被点击 =====")
        self.update_combobox_items()  # 删除组按钮点击时更新下拉框

    def 下拉选择框选择事件(self, event):
        """当下拉选择框选择变化时，将选择的内容填入到旁边的输入框中"""
        selected_value = self.ui.tk_select_box_mhbxbsjl.get()
        # 清空并填入选择的内容到旁边的输入框
        self.ui.tk_input_mhbxbfoz.delete(0, "end")
        self.ui.tk_input_mhbxbfoz.insert(0, selected_value)
        print(f"下拉选择框选择变化: '{selected_value}' 已填入输入框")
    
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
                # 如果之前的选项仍存在，则选中它
                self.ui.tk_select_box_mhbxbsjl.set(current_value)
            else:
                # 如果之前的选项已不存在，默认选中空项
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

class WinGUI(Tk):
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
        ipt = Entry(parent, )
        ipt.place(x=98, y=5, width=271, height=30)
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
        ipt = Entry(parent, )
        ipt.place(x=98, y=39, width=271, height=30)
        return ipt
    
    def __tk_input_mhbw86gs(self, parent):
        ipt = Entry(parent, )
        ipt.place(x=98, y=73, width=271, height=30)
        return ipt
    
    def __tk_input_mhbw8732(self, parent):
        ipt = Entry(parent, )
        ipt.place(x=98, y=107, width=271, height=30)
        return ipt
    
    def __tk_input_mhbw882r(self, parent):
        ipt = Entry(parent, )
        ipt.place(x=98, y=141, width=271, height=30)
        return ipt
    
    def __tk_input_mhbw890b(self, parent):
        ipt = Entry(parent, )
        ipt.place(x=98, y=175, width=271, height=30)
        return ipt
    
    def __tk_input_mhbw8amb(self, parent):
        ipt = Entry(parent, )
        ipt.place(x=98, y=209, width=271, height=30)
        return ipt
    
    def __tk_input_mhbw8c6w(self, parent):
        ipt = Entry(parent, )
        ipt.place(x=98, y=243, width=271, height=30)
        return ipt
    
    def __tk_input_mhbw8dag(self, parent):
        ipt = Entry(parent, )
        ipt.place(x=98, y=277, width=271, height=30)
        return ipt
    
    def __tk_input_mhbw8eir(self, parent):
        ipt = Entry(parent, )
        ipt.place(x=98, y=311, width=271, height=30)
        return ipt
    
    def __tk_input_mhbw8gbn(self, parent):
        ipt = Entry(parent, )
        ipt.place(x=98, y=345, width=271, height=30)
        return ipt
    
    def __tk_input_mhbw8h8g(self, parent):
        ipt = Entry(parent, )
        ipt.place(x=98, y=379, width=271, height=30)
        return ipt
    
    def __tk_input_mhbw8hzn(self, parent):
        ipt = Entry(parent, )
        ipt.place(x=98, y=413, width=271, height=30)
        return ipt
    
    def __tk_input_mhbw8jai(self, parent):
        ipt = Entry(parent, )
        ipt.place(x=98, y=447, width=271, height=30)
        return ipt
    
    def __tk_input_mhbw8k0c(self, parent):
        ipt = Entry(parent, )
        ipt.place(x=98, y=481, width=271, height=30)
        return ipt
    
    def __tk_input_mhbw8kq5(self, parent):
        ipt = Entry(parent, )
        ipt.place(x=98, y=515, width=271, height=30)
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
        
        # 绑定所有按钮点击事件
        self.tk_button_mhbx9o9a.bind('<Button-1>', self.ctl.保存组点击)
        self.tk_button_mhbxdcc6.bind('<Button-1>', self.ctl.重命名点击)
        self.tk_button_mhbxf1ky.bind('<Button-1>', self.ctl.保存组点击)
        self.tk_button_mhbxg7zg.bind('<Button-1>', self.ctl.删除组点击)
        
        # 绑定下拉选择框选择事件
        self.tk_select_box_mhbxbsjl.bind('<<ComboboxSelected>>', self.ctl.下拉选择框选择事件)
    
    def __style_config(self):
        pass

if __name__ == "__main__":
    controller = Controller()
    win = Win(controller)
    
    # 示例：可以这样调用填充和提取函数
    # 测试填充16项数据
    test_data = [f"值{i+1}" for i in range(16)]
    controller.fill_input_fields(test_data)
    
    # 测试提取数据
    print(controller.get_input_values())
    
    win.mainloop()