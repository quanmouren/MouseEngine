# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: BSD-3-Clause
import customtkinter as ctk
import os
import sys
import toml
import time
import threading
import platform
import subprocess
import tkinter.messagebox as tk_messagebox
from tkinter import filedialog

from Tlog import TLog


log = TLog("SettingsUI")


CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.toml")
if not os.path.exists(CONFIG_PATH):
    CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.toml")

try:
    WIN_USERNAME = os.getlogin()
except Exception:
    WIN_USERNAME = ""

REPO_ROOT = os.path.dirname(os.path.abspath(CONFIG_PATH))
LICENSE_PATH = os.path.join(REPO_ROOT, "LICENSE")
THIRD_PARTY_NOTICES_PATH = os.path.join(REPO_ROOT, "THIRD_PARTY_NOTICES.txt")
DOCS_LICENSES_DIR = os.path.join(REPO_ROOT, "docs", "licenses")


# ---- 主题 ----
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class UIStyle:
    OUTER_PAD = 18
    INNER_PAD = 16
    PAGE_PAD_X = 16
    PAGE_PAD_Y = 16
    CARD_PAD_X = 16
    CARD_PAD_Y = 14
    CARD_GAP = 12

    R_OUTER = 18
    R_PANEL = 16
    R_CARD = 16
    R_INPUT = 12

    MUTED_TEXT = ("gray40", "gray70")


def _read_toml(path: str) -> dict:
    try:
        if not os.path.exists(path):
            return {}
        return toml.load(path)
    except Exception as e:
        log.error(f"读取 toml 失败: {e}")
        return {}


def _atomic_write_text(path: str, text: str) -> None:
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    tmp_path = os.path.join(folder, f".{os.path.basename(path)}.tmp_{int(time.time()*1000)}")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp_path, path)


def _update_toml_key(path: str, section: str, key: str, value):
    data = _read_toml(path)
    if section not in data or not isinstance(data.get(section), dict):
        data[section] = {}
    data[section][key] = value
    try:
        _atomic_write_text(path, toml.dumps(data))
        return True, ""
    except Exception as e:
        return False, str(e)


def _get_toml_value(path: str, section: str, key: str, default=None):
    data = _read_toml(path)
    try:
        return data.get(section, {}).get(key, default)
    except Exception:
        return default


def _open_in_system(path: str):
    try:
        if not path:
            tk_messagebox.showwarning("路径为空", "未提供要打开的路径。")
            return

        abspath = os.path.abspath(path)
        if not os.path.exists(abspath):
            tk_messagebox.showwarning("不存在", f"路径不存在：\n{abspath}")
            return

        system = platform.system()
        if system == "Windows":
            os.startfile(abspath)
        elif system == "Darwin":
            subprocess.run(["open", abspath], check=False)
        else:
            subprocess.run(["xdg-open", abspath], check=False)
    except Exception as e:
        tk_messagebox.showerror("打开失败", f"无法打开：\n{path}\n\n原因：{e}")


try:
    if platform.system() == "Windows":
        import winreg
    else:
        winreg = None
except ImportError:
    winreg = None


def _normalize_win_path(p: str) -> str:
    return p.replace("\\\\", "\\").replace("/", "\\")


def find_steam_install_path() -> str | None:
    if platform.system() != "Windows" or winreg is None:
        return None
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        winreg.CloseKey(key)
        return _normalize_win_path(steam_path)
    except Exception:
        return None


def get_all_steam_library_paths(steam_main_path: str | None) -> list[str]:
    if not steam_main_path:
        return []
    library_paths = [os.path.join(steam_main_path, "steamapps")]

    vdf_path = os.path.join(steam_main_path, "steamapps", "libraryfolders.vdf")
    if not os.path.exists(vdf_path):
        return library_paths

    try:
        with open(vdf_path, "r", encoding="utf-8") as f:
            content = f.read()
        import re

        path_matches = re.findall(r'"\d+"\s+"(.+?)"', content)
        for p in path_matches:
            normalized = _normalize_win_path(p)
            library_paths.append(os.path.join(normalized, "steamapps"))
    except Exception as e:
        log.error(f"解析 libraryfolders.vdf 失败: {e}")

    return library_paths


def find_wallpaper_engine_root() -> str | None:
    if platform.system() != "Windows":
        default_path = os.path.expanduser("~/.steam/steam/steamapps/common/wallpaper_engine")
        return default_path if os.path.isdir(default_path) else None

    steam_main_path = find_steam_install_path()
    library_paths = get_all_steam_library_paths(steam_main_path)

    if not library_paths:
        library_paths = [
            r"C:\Program Files (x86)\Steam\steamapps",
            r"C:\Program Files\Steam\steamapps",
        ]

    for steamapps in library_paths:
        we_root = os.path.join(steamapps, "common", "wallpaper_engine")
        if os.path.isdir(we_root):
            return we_root

    return None


def guess_wallpaper_engine_config_json(root: str) -> str:
    return os.path.join(root, "config.json")


class PageLayout(ctk.CTkFrame):
    def __init__(self, master, title: str, desc: str):
        super().__init__(master, corner_radius=UIStyle.R_PANEL)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, corner_radius=UIStyle.R_PANEL, fg_color="transparent")
        header.grid(row=0, column=0, padx=UIStyle.PAGE_PAD_X, pady=(UIStyle.PAGE_PAD_Y, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text=title, font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header, text=desc, text_color=UIStyle.MUTED_TEXT, font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, pady=(2, 0), sticky="w")

        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=UIStyle.R_PANEL, fg_color="transparent")
        self.scroll.grid(row=1, column=0, padx=UIStyle.PAGE_PAD_X, pady=(0, UIStyle.PAGE_PAD_Y), sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)

        self._row = 0

    def add_card(self, title: str, subtitle: str):
        card = ctk.CTkFrame(self.scroll, corner_radius=UIStyle.R_CARD)
        card.grid(row=self._row, column=0, sticky="ew", pady=(0, UIStyle.CARD_GAP))
        card.grid_columnconfigure(0, weight=1)
        self._row += 1

        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=UIStyle.CARD_PAD_X, pady=(UIStyle.CARD_PAD_Y, 2), sticky="w"
        )
        ctk.CTkLabel(
            card, text=subtitle, text_color=UIStyle.MUTED_TEXT, font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, padx=UIStyle.CARD_PAD_X, pady=(0, 10), sticky="w")

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.grid(row=2, column=0, padx=UIStyle.CARD_PAD_X, pady=(0, UIStyle.CARD_PAD_Y), sticky="ew")
        content.grid_columnconfigure(0, weight=1)
        return card, content


class SettingsUIMixin:
    def _build_settings_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.panel = ctk.CTkFrame(self, corner_radius=UIStyle.R_OUTER)
        self.panel.grid(row=0, column=0, padx=UIStyle.OUTER_PAD, pady=UIStyle.OUTER_PAD, sticky="nsew")
        self.panel.grid_rowconfigure(1, weight=1)
        self.panel.grid_columnconfigure(0, weight=1)

        self._build_header(self.panel)

        body = ctk.CTkFrame(self.panel, fg_color="transparent")
        body.grid(row=1, column=0, padx=UIStyle.INNER_PAD, pady=UIStyle.INNER_PAD, sticky="nsew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        self._build_sidebar(body)
        self._build_pages(body)
        self._build_footer(self.panel)

        self._switch_page("general")
        self._load_values_from_toml()

    def _build_header(self, parent):
        header = ctk.CTkFrame(parent, corner_radius=UIStyle.R_PANEL)
        header.grid(row=0, column=0, padx=UIStyle.INNER_PAD, pady=(UIStyle.INNER_PAD, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="⚙️ 设置", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, padx=16, pady=(14, 2), sticky="w"
        )
        ctk.CTkLabel(
            header,
            text="软件基础设置",
            text_color=UIStyle.MUTED_TEXT,
            font=ctk.CTkFont(size=13),
        ).grid(row=1, column=0, padx=16, pady=(0, 14), sticky="w")

    def _build_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, width=240, corner_radius=UIStyle.R_PANEL)
        sidebar.grid(row=0, column=0, padx=(0, 12), sticky="nsw")
        sidebar.grid_rowconfigure(99, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        self._nav_font = ctk.CTkFont(size=13, weight="normal")
        self._nav_font_active = ctk.CTkFont(size=13, weight="bold")

        self.nav_buttons = {}
        self.nav_buttons["general"] = self._make_nav_button(sidebar, 1, "常规", "general")
        self.nav_buttons["mouse"] = self._make_nav_button(sidebar, 2, "鼠标指针", "mouse")
        self.nav_buttons["about"] = self._make_nav_button(sidebar, 3, "关于", "about")

    def _make_nav_button(self, parent, row: int, text: str, page: str):
        btn = ctk.CTkButton(
            parent,
            text=text,
            anchor="w",
            height=40,
            corner_radius=UIStyle.R_INPUT,
            font=self._nav_font,
            command=lambda: self._switch_page(page),
        )
        btn.grid(row=row, column=0, padx=14, pady=6, sticky="ew")
        return btn

    def _build_pages(self, parent):
        self.pages_container = ctk.CTkFrame(parent, corner_radius=UIStyle.R_PANEL, fg_color="transparent")
        self.pages_container.grid(row=0, column=1, sticky="nsew")
        self.pages_container.grid_rowconfigure(0, weight=1)
        self.pages_container.grid_columnconfigure(0, weight=1)

        self.pages = {
            "general": self._page_general(self.pages_container),
            "mouse": self._page_mouse(self.pages_container),
            "about": self._page_about(self.pages_container),
        }

    def _build_footer(self, parent):
        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.grid(row=2, column=0, padx=UIStyle.INNER_PAD, pady=(0, UIStyle.INNER_PAD), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        btns = ctk.CTkFrame(footer, fg_color="transparent")
        btns.grid(row=0, column=1, sticky="e")

        self.ui_btn_close = ctk.CTkButton(
            btns, text="关闭", height=38, corner_radius=UIStyle.R_INPUT, command=self._on_close
        )
        self.ui_btn_close.grid(row=0, column=0)

    def _page_general(self, parent):
        page = PageLayout(parent, "常规", "")

        _, content = page.add_card("📄 Wallpaper Engine 配置文件位置", "")
        self.ui_we_config_path_entry = ctk.CTkEntry(content, height=38, corner_radius=UIStyle.R_INPUT)
        self.ui_we_config_path_entry.grid(row=0, column=0, sticky="ew")

        btnrow = ctk.CTkFrame(content, fg_color="transparent")
        btnrow.grid(row=1, column=0, pady=(10, 0), sticky="ew")
        btnrow.grid_columnconfigure((0, 1), weight=1)

        self.ui_btn_auto_find_we = ctk.CTkButton(
            btnrow,
            text="⚙️ 自动查找",
            height=36,
            corner_radius=UIStyle.R_INPUT,
            command=lambda: self._start_auto_find_we(show_message=True),
        )
        self.ui_btn_auto_find_we.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.ui_btn_browse_we_folder = ctk.CTkButton(
            btnrow,
            text="📂 浏览文件夹",
            height=36,
            corner_radius=UIStyle.R_INPUT,
            command=self._on_browse_we_folder,
        )
        self.ui_btn_browse_we_folder.grid(row=0, column=1, sticky="ew")

        return page

    def _page_mouse(self, parent):
        page = PageLayout(parent, "鼠标指针", "")

        _, content = page.add_card(
            "默认鼠标指针",
            "此功能将会决定在当前壁纸没用组或组中没有指定鼠标指针时，是否使用默认鼠标指针",
        )

        row = ctk.CTkFrame(content, fg_color="transparent")
        row.grid(row=0, column=0, sticky="ew")
        row.grid_columnconfigure(0, weight=1)

        self.var_enable_default_icon_group = ctk.BooleanVar(value=False)
        self.ui_switch_enable_default_icon_group = ctk.CTkSwitch(
            row,
            text="启用默认鼠标指针",
            variable=self.var_enable_default_icon_group,
            command=self._on_toggle_default_icon_group,
        )
        self.ui_switch_enable_default_icon_group.grid(row=0, column=0, sticky="w")

        return page

    def _page_about(self, parent):
        page = PageLayout(parent, "关于", "")

        _, c1 = page.add_card("MouseEngine", "基础信息")
        ctk.CTkLabel(
            c1,
            text=f"当前用户：{WIN_USERNAME}",
            justify="left",
            anchor="w",
            text_color=UIStyle.MUTED_TEXT,
            font=ctk.CTkFont(size=12),
        ).grid(row=0, column=0, sticky="w")

        _, c2 = page.add_card("📜 许可证", "本许可证位置：LICENSE")
        ctk.CTkButton(
            c2,
            text="📄 打开 LICENSE",
            height=36,
            corner_radius=UIStyle.R_INPUT,
            command=lambda: _open_in_system(LICENSE_PATH),
        ).grid(row=0, column=0, sticky="w")

        _, c3 = page.add_card("📦 第三方清单", "第三方清单：THIRD_PARTY_NOTICES.txt；原版内容目录：docs\\licenses")
        row3 = ctk.CTkFrame(c3, fg_color="transparent")
        row3.grid(row=0, column=0, sticky="ew")
        row3.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            row3,
            text="📄 打开 THIRD_PARTY_NOTICES.txt",
            height=36,
            corner_radius=UIStyle.R_INPUT,
            command=lambda: _open_in_system(THIRD_PARTY_NOTICES_PATH),
        ).grid(row=0, column=0, padx=(0, 10), sticky="ew")

        ctk.CTkButton(
            row3,
            text="📂 打开 docs\\licenses",
            height=36,
            corner_radius=UIStyle.R_INPUT,
            command=lambda: _open_in_system(DOCS_LICENSES_DIR),
        ).grid(row=0, column=1, sticky="ew")

        return page

    def _switch_page(self, page_key: str):
        for frame in self.pages.values():
            frame.grid_forget()
        self.pages[page_key].grid(row=0, column=0, sticky="nsew")

        for k, btn in self.nav_buttons.items():
            btn.configure(font=self._nav_font_active if k == page_key else self._nav_font)

    def _load_values_from_toml(self):
        we_cfg = _get_toml_value(CONFIG_PATH, "path", "wallpaper_engine_config", "")
        self.ui_we_config_path_entry.delete(0, "end")
        self.ui_we_config_path_entry.insert(0, str(we_cfg or ""))

        enable_default = _get_toml_value(CONFIG_PATH, "config", "enable_default_icon_group", False)
        self.var_enable_default_icon_group.set(bool(enable_default))

    def _set_we_buttons_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.ui_btn_auto_find_we.configure(state=state)
        self.ui_btn_browse_we_folder.configure(state=state)

    def _start_auto_find_we(self, show_message: bool = True):
        self._set_we_buttons_enabled(False)
        t = threading.Thread(target=self._auto_find_worker, args=(show_message,), daemon=True)
        t.start()

    def _auto_find_worker(self, show_message: bool):
        root = find_wallpaper_engine_root()
        self.after(0, lambda: self._auto_find_done(root, show_message))

    def _auto_find_done(self, root: str | None, show_message: bool):
        try:
            if not root:
                if show_message:
                    tk_messagebox.showwarning("查找失败", "未能自动找到 Wallpaper Engine 安装目录，请手动选择。")
                return

            config_json = guess_wallpaper_engine_config_json(root)
            self.ui_we_config_path_entry.delete(0, "end")
            self.ui_we_config_path_entry.insert(0, config_json)

            ok, err = _update_toml_key(CONFIG_PATH, "path", "wallpaper_engine_config", config_json)
            if not ok:
                tk_messagebox.showerror("写入失败", f"写入 config.toml 失败：{err}")
                return

            if show_message:
                tk_messagebox.showinfo("查找成功", "")
        finally:
            self._set_we_buttons_enabled(True)

    def _on_browse_we_folder(self):
        self._set_we_buttons_enabled(False)
        try:
            current = self.ui_we_config_path_entry.get().strip()
            initial_dir = os.path.dirname(current) if current else ""
            if not initial_dir or not os.path.isdir(initial_dir):
                initial_dir = os.path.dirname(CONFIG_PATH)

            folder = filedialog.askdirectory(
                title="选择 Wallpaper Engine 根目录（wallpaper_engine）",
                initialdir=initial_dir,
            )
            if not folder:
                return

            config_json = guess_wallpaper_engine_config_json(folder)
            self.ui_we_config_path_entry.delete(0, "end")
            self.ui_we_config_path_entry.insert(0, config_json)

            ok, err = _update_toml_key(CONFIG_PATH, "path", "wallpaper_engine_config", config_json)
            if not ok:
                tk_messagebox.showerror("写入失败", f"写入 config.toml 失败：{err}")
                return

            tk_messagebox.showinfo("已更新", "")
        except Exception as e:
            tk_messagebox.showerror("错误", f"选择文件夹失败：{e}")
        finally:
            self._set_we_buttons_enabled(True)

    def _on_toggle_default_icon_group(self):
        v = bool(self.var_enable_default_icon_group.get())
        ok, err = _update_toml_key(CONFIG_PATH, "config", "enable_default_icon_group", v)
        if not ok:
            tk_messagebox.showerror("写入失败", f"写入 config.toml 失败：{err}")
            self.var_enable_default_icon_group.set(not v)

    def _on_close(self):
        self.destroy()


class SettingsWindow(ctk.CTkToplevel, SettingsUIMixin):
    def __init__(self, master=None):
        super().__init__(master=master)
        self.title("设置 MouseEngine")
        self.geometry("980x620")
        self.minsize(920, 560)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_settings_ui()


class SettingsApp(ctk.CTk, SettingsUIMixin):
    def __init__(self):
        super().__init__()
        self.title("设置 MouseEngine")
        self.geometry("980x620")
        # 设置窗口图标
        try:
            self.iconbitmap("icon300.ico")
        except Exception:
            pass 
        self.minsize(920, 560)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_settings_ui()


def open_settings_window(master=None):
    if master is None:
        app = SettingsApp()
        app.mainloop()
        return app

    win = SettingsWindow(master=master)
    try:
        win.lift()
        win.focus_force()
    except Exception:
        pass
    return win


def run():
    open_settings_window(master=None)


if __name__ == "__main__":
    run()
