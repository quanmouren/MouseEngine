import customtkinter
import os
from tkinter import filedialog, messagebox 
import platform
import sys
import re 
import threading 
try:
    if platform.system() == "Windows":
        import winreg
    else:
        winreg = None
except ImportError:
    winreg = None

customtkinter.set_appearance_mode("Light") 
customtkinter.set_default_color_theme("blue") 

def find_steam_install_path():
    if platform.system() != "Windows" or winreg is None:
        return None
        
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        winreg.CloseKey(key)
        return steam_path.replace('/', '\\')
        
    except (FileNotFoundError, Exception):
        return None

def get_all_steam_library_paths(steam_main_path):
    library_paths = []
    if steam_main_path:
        library_paths.append(os.path.join(steam_main_path, "steamapps"))
        vdf_path = os.path.join(steam_main_path, "steamapps", "libraryfolders.vdf")
    else:
        return library_paths 

    if os.path.exists(vdf_path):
        try:
            with open(vdf_path, 'r', encoding='utf-8') as f:
                content = f.read()
            path_matches = re.findall(r'"\d+"\s+"(.+?)"', content)
            
            for path in path_matches:
                normalized_path = path.replace('\\\\', '\\').replace('/', '\\')
                library_paths.append(os.path.join(normalized_path, "steamapps"))
        except Exception as e:
            print(f"解析 libraryfolders.vdf 时出错: {e}")
    return library_paths

def find_wallpaper_engine_path_advanced():
    if platform.system() != "Windows":
        default_path = os.path.expanduser("~/.steam/steam/steamapps/common/wallpaper_engine")
        if os.path.exists(default_path) and os.path.exists(os.path.join(default_path, "wallpaper64.exe")):
            return default_path
        return None

    steam_main_path = find_steam_install_path()
    all_library_paths = get_all_steam_library_paths(steam_main_path)
    
    if not all_library_paths:
        common_paths = ["C:\\Program Files (x86)\\Steam", "C:\\Program Files\\Steam"]
        for path in common_paths:
            check_path = os.path.join(path, "steamapps", "common", "wallpaper_engine")
            if os.path.exists(os.path.join(check_path, "wallpaper64.exe")):
                 return check_path
        return None 

    for library_path in all_library_paths:
        we_path = os.path.join(library_path, "common", "wallpaper_engine")
        exe_path = os.path.join(we_path, "wallpaper64.exe")
        
        if os.path.exists(exe_path):
            return we_path
            
    return None

class WelcomeWindow(customtkinter.CTkToplevel):

    def __init__(self, master, on_path_selected_callback):
        super().__init__(master)
        self.master = master
        self.on_path_selected_callback = on_path_selected_callback
        self.animation_state = False
        
        self.WIN_WIDTH = 550
        self.WIN_HEIGHT = 280
        self.title("欢迎！应用程序配置向导")
        self.geometry(f"{self.WIN_WIDTH}x{self.WIN_HEIGHT}")
        self.resizable(False, False)
        
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width / 2) - (self.WIN_WIDTH / 2))
        y = int((screen_height / 2) - (self.WIN_HEIGHT / 2))
        self.geometry(f"+{x}+{y}")
        
        self.transient(master)  
        self.grab_set()         
        self.protocol("WM_DELETE_WINDOW", self._on_closing) 
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1, 2, 3), weight=1)

        self.header_frame = customtkinter.CTkFrame(self, fg_color="gray85", corner_radius=10)
        self.header_frame.grid(row=0, column=0, padx=25, pady=(25, 10), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.label_title = customtkinter.CTkLabel(
            self.header_frame, 
            text="✨ 欢迎使用 MouseEngine", 
            font=customtkinter.CTkFont(size=24, weight="bold"),
            text_color="#1F6AA5" 
        )
        self.label_title.grid(row=0, column=0, padx=20, pady=(15, 0))
        
        self.label_info = customtkinter.CTkLabel(
            self.header_frame, 
            text="程序首次运行，请指定 Wallpaper Engine 的安装位置。", 
            wraplength=480,
            text_color="gray30" 
        )
        self.label_info.grid(row=1, column=0, padx=20, pady=(0, 15))

        self.input_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, padx=25, pady=5, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.path_label = customtkinter.CTkLabel(
            self.input_frame, 
            text="Wallpaper Engine 根目录:",
            anchor="w",
            font=customtkinter.CTkFont(size=14, weight="bold")
        )
        self.path_label.grid(row=0, column=0, padx=5, pady=(5, 0), sticky="w")
        
        self.path_entry = customtkinter.CTkEntry(
            self.input_frame, 
            placeholder_text="输入路径，或使用下方的查找按钮", 
            width=480,
            height=35,
            corner_radius=8
        )
        self.path_entry.grid(row=1, column=0, padx=5, pady=(0, 10), sticky="ew")

        self.action_frame = customtkinter.CTkFrame(self.input_frame, fg_color="transparent")
        self.action_frame.grid(row=2, column=0, padx=5, pady=(0, 15), sticky="ew")
        self.action_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.auto_find_button = customtkinter.CTkButton(
            self.action_frame, 
            text="⚙️ 自动查找 (Steam)", 
            command=self._start_auto_find_thread,
            width=150,
            fg_color="#1F6AA5", 
            hover_color="#36A9E1"
        )
        self.auto_find_button.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        self.browse_button = customtkinter.CTkButton(
            self.action_frame, 
            text="📂 浏览文件夹", 
            command=self.browse_path,
            width=150,
            fg_color="gray50", 
            hover_color="gray30"
        )
        self.browse_button.grid(row=0, column=1, padx=5)

        self.continue_button = customtkinter.CTkButton(
            self.action_frame, 
            text="✅ 确认并继续", 
            command=self.confirm_path,
            width=150,
            fg_color="#1a8c3d", 
            hover_color="#22b950" 
        )
        self.continue_button.grid(row=0, column=2, padx=(10, 0), sticky="e")
        self.grid_rowconfigure(2, weight=1) 
        self._start_auto_find_thread(show_message=False)

    def _start_auto_find_thread(self, show_message=True):
        self.auto_find_button.configure(state="disabled", text="🔍 正在查找...")
        self.animation_state = True
        self._animate_find_button(1)
        threading.Thread(target=self._run_find_task, args=(show_message,)).start()

    def _run_find_task(self, show_message):
        found_path = find_wallpaper_engine_path_advanced()
        self.master.after(0, lambda: self._complete_auto_find(found_path, show_message))

    def _animate_find_button(self, count):
        if not self.animation_state:
            return
        colors = ["#36A9E1", "#1F6AA5"] 
        current_color = colors[count % len(colors)]
        self.auto_find_button.configure(fg_color=current_color)
        self.after_id = self.after(200, lambda: self._animate_find_button(count + 1))

    def _complete_auto_find(self, found_path, show_message):
        self.animation_state = False
        self.auto_find_button.configure(state="normal", text="⚙️ 自动查找 (Steam)", fg_color="#1F6AA5")
        if found_path:
            self.path_entry.delete(0, customtkinter.END)
            self.path_entry.insert(0, found_path)
            if show_message:
                messagebox.showinfo(title="查找成功", message="已通过 Steam 库文件自动找到 Wallpaper Engine 路径。") 
        elif show_message:
            messagebox.showwarning(title="查找失败", message="自动查找失败。请手动输入或浏览文件选择路径。")

    def browse_path(self):
        initial_dir = os.path.expanduser("~") if platform.system() != "Windows" else "C:\\"
        folder_path = filedialog.askdirectory(
            title="选择 Wallpaper Engine 根目录", 
            initialdir=initial_dir
        )
        if folder_path:
            self.path_entry.delete(0, customtkinter.END)
            self.path_entry.insert(0, folder_path)

    def confirm_path(self):
        path = self.path_entry.get().strip()
        
        if not path:
            messagebox.showerror(title="错误", message="请输入 Wallpaper Engine 的安装路径。")
            return
            
        validation_path = os.path.join(path, "wallpaper64.exe")
        if not os.path.exists(validation_path):
            messagebox.showerror(
                title="错误", 
                message=f"在所选路径中未找到关键文件 'wallpaper64.exe'。\n请确保路径指向 Wallpaper Engine 的根目录。",
            )
            return

        self.grab_release()
        self.on_path_selected_callback(path) 
        self.master.quit()

    def _on_closing(self):
        self.grab_release()
        self.on_path_selected_callback(None)
        self.master.quit()
class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("MouseEngine")
        self.geometry("1x1") 
        self.attributes('-alpha', 0)
        self.wallpaper_path = None
        self.show_welcome_ui()

    def show_welcome_ui(self):
        self.welcome_window = WelcomeWindow(self, self.set_path_and_stop)

    def set_path_and_stop(self, path):
        self.wallpaper_path = path

def get_wallpaper_engine_path_ui():
    app = App()
    app.mainloop()
    path = app.wallpaper_path
    app.destroy()
    return path

if __name__ == "__main__":
    final_path = get_wallpaper_engine_path_ui()
    
    if final_path:
        print(final_path)
    else:
        pass
        # sys.exit()