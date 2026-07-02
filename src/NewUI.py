# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: BSD-3-Clause
import webview

from Tlog import TLog
from path_utils import resolve_path
from mainUIWeb import Api as WallpaperApi
from settingsUIWeb import SettingsApi
from mouseUI import EditMouseApi


log = TLog("NewUI")


class UnifiedApi(WallpaperApi, SettingsApi, EditMouseApi):
    def __init__(self):
        SettingsApi.__init__(self)
        EditMouseApi.__init__(self)
        self._window = None

    def set_window(self, window):
        self._window = window

    def exit_app(self):
        if self._window:
            self._window.destroy()


def run():
    api = UnifiedApi()
    html_file = resolve_path("html/NewUI.html")
    window = webview.create_window(
        "MouseEngine",
        html_file,
        js_api=api,
        width=1120,
        height=820,
        easy_drag=True,
        resizable=True,
        text_select=False
    )
    api.set_window(window)

    if log.on_DEBUG:
        webview.start(debug=True, http_server=True)
    else:
        webview.start(debug=False, http_server=True)


if __name__ == "__main__":
    run()
