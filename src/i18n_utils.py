# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: BSD-3-Clause
import os
import toml

from path_utils import resolve_path


SUPPORTED_LANGUAGES = {"zh-CN", "en", "ja"}
DEFAULT_LANGUAGE = "zh-CN"


def _load_config():
    config_path = resolve_path("config.toml")
    if os.path.exists(config_path):
        return toml.load(config_path)
    return {}


def get_language():
    try:
        config_data = _load_config()
        language = config_data.get("config", {}).get("language", DEFAULT_LANGUAGE)
        return language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    except Exception:
        return DEFAULT_LANGUAGE


def set_language(language):
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE

    config_path = resolve_path("config.toml")
    config_data = _load_config()
    config_data.setdefault("config", {})
    config_data["config"]["language"] = language

    with open(config_path, "w", encoding="utf-8") as f:
        toml.dump(config_data, f)

    return True


def tr(key):
    language = get_language()
    translations = {
        "zh-CN": {
            "tray_title": "光标引擎",
            "tray_title_paused": "光标引擎 (已暂停)",
            "configure_mouse_groups": "配置鼠标组",
            "bind_mouse_groups": "绑定鼠标组",
            "settings": "设置",
            "pause": "暂停",
            "resume": "解除暂停",
            "exit": "退出",
            "set_last_focus_default": "将上一焦点窗口设为默认",
        },
        "en": {
            "tray_title": "MouseEngine",
            "tray_title_paused": "MouseEngine (Paused)",
            "configure_mouse_groups": "Configure mouse groups",
            "bind_mouse_groups": "Bind mouse groups",
            "settings": "Settings",
            "pause": "Pause",
            "resume": "Resume",
            "exit": "Exit",
            "set_last_focus_default": "Set previous focused window as default",
        },
        "ja": {
            "tray_title": "MouseEngine",
            "tray_title_paused": "MouseEngine (一時停止中)",
            "configure_mouse_groups": "カーソルグループを設定",
            "bind_mouse_groups": "カーソルグループを紐づけ",
            "settings": "設定",
            "pause": "一時停止",
            "resume": "再開",
            "exit": "終了",
            "set_last_focus_default": "直前のフォーカスウィンドウを既定に設定",
        },
    }
    return translations.get(language, translations[DEFAULT_LANGUAGE]).get(
        key,
        translations[DEFAULT_LANGUAGE].get(key, key),
    )
