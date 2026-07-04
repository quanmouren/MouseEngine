# MouseEngine

**Language / 语言**: [简体中文](../README.md) | English | [日本語](./README_JA.md)

MouseEngine is a **Windows cursor auto-switching tool for Wallpaper Engine**.

It reads the Wallpaper Engine wallpaper currently active on your display and automatically switches to the matching cursor theme.

![Logo](./images/logo.jpg "MouseEngine Logo")

---

## Features

- **Wallpaper-driven cursor switching**: Reads the current Wallpaper Engine wallpaper ID and applies the bound cursor group automatically.
- **Cursor group management**: Create, import, and edit cursor themes. Supports `.cur` and `.ani` cursor files.
- **Wallpaper binding UI**: Bind Wallpaper Engine wallpapers to cursor groups through a visual interface.
- **Program whitelist**: Bind cursor groups to specific applications. Whitelist rules take priority over wallpaper rules.
- **Default fallback**: Fall back to a default cursor group when a wallpaper is not bound or a cursor theme is invalid.
- **System tray resident mode**: Open configuration pages, pause/resume switching, adjust settings, and exit safely from the tray menu.
- **Multi-language UI**: Currently supports Simplified Chinese, English, and Japanese.

---

## How It Works

1. Reads Wallpaper Engine's `config.json`.
2. Gets the wallpaper project ID currently active on the display.
3. Looks up the matching cursor group in `config.toml`.
4. If the foreground program matches the whitelist, the whitelist cursor group is used first.
5. Applies the cursor theme through Windows APIs.
6. If no rule matches, the app uses the default cursor group depending on the current settings.

---

## Quick Start

### 1. Download and Extract

Download the release package from GitHub Releases:

[MouseEngine-V1.0](https://github.com/quanmouren/MouseEngine/releases/download/V1.0/MouseEngine-V1.0-windows-x64.zip)

After downloading, extract the package to the directory where you want to keep MouseEngine. A normal user directory or a dedicated tools directory is recommended. Avoid system directories that require administrator permission to write files.

### 2. First Launch

Double-click `MouseEngine.exe` in the extracted directory.

![Welcome UI](./images/UI1_en.png)

On first launch, MouseEngine will try to locate your Wallpaper Engine installation path automatically. After confirming the path, click "Confirm and continue". The app will then run in the background and stay in the system tray.

Right-click the `MouseEngine` tray icon to open the main menu.

![Menu](./images/menu_en.png)

### 3. Configure Cursor Groups

Click `Configure cursor groups` in the tray menu.

![Cursor Group UI](./images/UI2_en.png)

Here you can create, import, and edit cursor groups. Each cursor group represents a Windows cursor theme.

### 4. Bind Wallpapers to Cursor Groups

Click `Bind cursor groups` in the tray menu.

![Binding UI](./images/UI3_en.png)

Installed Wallpaper Engine wallpapers are shown on the left. Select a wallpaper, then bind the cursor group you want to use on the right.

### 5. Settings

Click `Settings` in the tray menu.

![Settings UI](./images/UI4_en.png)

The settings page lets you configure the Wallpaper Engine path, startup behavior, default cursor group, fullscreen pause, language, and program whitelist.

---

## Usage Tips

- Keep a default cursor group configured. It can be used as a fallback when a wallpaper is not bound or a cursor theme has missing files.
- MouseEngine must run in a Windows desktop session. The tray menu and cursor switching depend on the Windows desktop environment.
- The current version does not support automatic online updates. Download new versions manually from GitHub Releases.

---

## Run From Source

For developers or users who want to run MouseEngine directly from source.

### 1. Clone the Repository

```bash
git clone https://github.com/quanmouren/MouseEngine.git
cd MouseEngine
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the App

```bash
cd src
python main.py
```

---

## Project Structure

```text
MouseEngine/
|
├─ README.md                         # Chinese project documentation
├─ LICENSE.txt                       # Project license notice
├─ FINAL_THIRD_PARTY_NOTICES.txt     # Third-party dependency license notices
├─ requirements.txt                  # Python dependencies
├─ docs/
│  ├─ README_EN.md                   # English project documentation
│  ├─ README_JA.md                   # Japanese project documentation
│  └─ images/                        # Documentation images
|
└─ src/                              # App runtime directory
   ├─ main.py                        # Main entry: wallpaper monitoring, tray menu, pause/exit
   ├─ Initialize.py                  # First-launch initialization and config repair
   ├─ WelcomeUI.py                   # First-launch wizard and old-version cleanup confirmation
   ├─ mainUIWeb.py                   # Wallpaper and cursor group binding UI API
   ├─ mouseUI.py                     # Cursor group editor API
   ├─ settingsUIWeb.py               # Settings UI API
   ├─ getActiveWallpaper.py          # Gets the currently active wallpaper
   ├─ getWallpaperConfig.py          # Parses Wallpaper Engine configuration
   ├─ setMouse.py                    # Applies Windows cursor themes
   ├─ mouses.py                      # Cursor group save/load and display mapping
   ├─ i18n_utils.py                  # Python-side language and tray translation utilities
   ├─ path_utils.py                  # Unified path handling for source and packaged builds
   ├─ Tlog.py                        # Logging module
   ├─ ani_to_gif.py                  # Converts `.ani` cursors for preview
   ├─ cur_to_png.py                  # Converts `.cur` cursors for preview
   ├─ config.toml                    # Main configuration file
   ├─ temp_storage.toml              # Runtime temporary state
   ├─ version.toml                   # App version information
   |
   ├─ mouses/                        # Cursor group folders
   ├─ html/                          # Web UI files
   ├─ lib/                           # Helper libraries
   ├─ projects/                      # 2D editor projects
   └─ ui/                            # 2D editor UI
```

---

## Configuration

### 1. Wallpaper Engine Config Path

The `[path]` section in `config.toml` stores the path to Wallpaper Engine's `config.json`:

```toml
[path]
wallpaper_engine_config = "D:/Steam/steamapps/common/wallpaper_engine/config.json"
```

The first-launch wizard and the Settings page can write this path automatically through auto-detection or folder selection.

### 2. Wallpaper ID to Cursor Theme Mapping

```toml
[wallpaper]
3406760593 = "Dark Theme"
3409595232 = "Light Theme"
```

- The left side is the Wallpaper Engine project ID.
- The right side is the folder name under `mouses/<theme name>/`.

### 3. Basic Settings

```toml
[config]
enable_default_icon_group = true
pause_on_fullscreen = false
show_more_menu = false
language = "zh-CN"
```

- `enable_default_icon_group`: Enables the default cursor group when no rule matches.
- `pause_on_fullscreen`: Pauses cursor switching when a fullscreen program is detected.
- `show_more_menu`: Shows additional tray menu items.
- `language`: UI language. Currently supports `zh-CN`, `en`, and `ja`.

### 4. Program Whitelist

```toml
[program_whitelist]
"Code.exe" = "Default"
"Photoshop.exe" = "Design Cursor"
```

- The left side is the process name.
- The right side is the cursor group name.
- When the current foreground program matches the whitelist, the whitelist rule is used before wallpaper rules.

---

## Cursor Theme Structure

Each cursor theme is a folder, for example:

```text
mouses/Dark Theme/
└─ config.toml
```

Example:

```toml
[mouses]
Arrow = "arrow.cur"
Hand = "hand.cur"
Wait = "wait.ani"
```

More cursor entries can be added depending on your theme. Values may be absolute paths or relative paths.

---

## FAQ

### Q1: The system tray icon does not appear. What should I check?

- Make sure the app is running in a Windows desktop session.
- If running from source, make sure `pystray` and `Pillow` are installed.
- Check whether security software is blocking the tray program.
- If using the packaged version, make sure the extracted directory is complete and you did not copy only `MouseEngine.exe`.

### Q2: Why do I see `portalocker not installed`?

This is an optional warning indicating that the file lock library is not installed. Single-instance usage usually works without it.

To remove the warning:

```bash
pip install portalocker
```

### Q3: Why does the cursor not change after the wallpaper changes?

- Make sure the Wallpaper Engine path is correct.
- Make sure the target wallpaper has been bound to a cursor group.
- Make sure the `.cur` and `.ani` files in the cursor group have valid paths.
- If the current foreground program matches the whitelist, the whitelist rule takes priority over wallpaper rules.

### Q4: How do I switch the UI language?

Open the Settings page and select `Simplified Chinese`, `English`, or `Japanese` in the language option.

### Q5: Does MouseEngine update itself automatically?

No. The current version does not support automatic online updates. Download the latest release package from GitHub Releases and replace the old version manually.

---

## License and Third-Party Notices

This project uses a **combined licensing model**. Different modules follow different licenses.

### 1. License Scope

To balance original work protection and community integration, this project is divided into the following parts:

| Module type | Scope | License | Notes |
| :--- | :--- | :--- | :--- |
| **Core logic** | Original algorithms, core workflows, and project-specific features | **MouseEngine Non-Commercial License** | Free projects, personal projects, learning, research, and open-source non-commercial projects may use it freely. Commercial use requires permission from the author. |
| **Integration interfaces** | Wallpaper Engine integration, related UI, process monitoring, and system handle operations | **[BSD 3-Clause](https://opensource.org/licenses/BSD-3-Clause)** | Permissive license |
| **Utility modules** | Independent small helper modules | **[MIT](https://opensource.org/licenses/MIT)** | Highly permissive license |

> Note: The license of each file is identified by its `SPDX-License-Identifier` header. If a file does not clearly state MIT, BSD 3-Clause, or another license, it is licensed under the MouseEngine Non-Commercial License by default.

### 2. Version and License Changes

This project changed its license starting from **Alpha 2.0**, and deprecated **CC BY-NC-SA 4.0** for core logic starting from **V1.0**:

- **V1.0 and later**: Uses the combined licensing model above. Core logic is licensed under the MouseEngine Non-Commercial License.
- **Alpha 2.0 through versions before V1.0**: Some core logic was licensed under **[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)**. Already published CC-licensed code remains licensed under that license, and the granted rights are not withdrawn.
- **Alpha 1.2 and earlier**: Remain under the **[BSD 3-Clause](https://opensource.org/licenses/BSD-3-Clause)** license. Permissions granted under previous licenses remain valid and are not withdrawn.

### 3. Disclaimers and Third-Party Rights

- **Wallpaper content**: MouseEngine only identifies and reads wallpaper metadata. All wallpaper assets, including images, videos, IDs, and media, belong to their respective authors on Steam Workshop.
- **No official affiliation**: This project is a personal project and is not affiliated with or endorsed by Wallpaper Engine, Steam, or Valve.
- **Software use**: This software is provided "as is", without warranty of any kind. The author is not liable for any system damage or legal disputes caused by using this software.

For details, read [LICENSE.txt](../LICENSE.txt).

- Project license: [`LICENSE.txt`](../LICENSE.txt)
- Third-party notices: [`FINAL_THIRD_PARTY_NOTICES.txt`](../FINAL_THIRD_PARTY_NOTICES.txt)

### 4. Plain-Language Summary

- You are welcome to use, study, modify, fork, and share MouseEngine for free, personal, learning, research, and open-source non-commercial projects.
- Commercial use of the core logic requires permission from the author.
- Files marked as MIT or BSD 3-Clause may be used according to those file-level licenses.
- Third-party libraries remain governed by their own licenses.
- Licenses already granted for previously published versions are not withdrawn.

In short: **you can use and modify it freely as long as you are not using it for profit. Commercial use requires permission.**

---

## Contributions and Feedback

Issues and pull requests are welcome.

When reporting a problem, please include runtime logs and `config.toml` if possible. Remember to hide private paths or personal information.

---

## Star History

<div align="center">
  <img src="https://api.star-history.com/svg?repos=quanmouren/MouseEngine&type=Date" width="100%">
</div>
