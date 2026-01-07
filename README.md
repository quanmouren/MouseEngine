# MouseEngine

MouseEngine 是一个 **基于 Wallpaper Engine 的 Windows 鼠标指针自动切换工具**。
它能够根据当前显示器所使用的壁纸，**自动切换对应的鼠标指针主题**，并支持多显示器、默认回退、系统托盘常驻运行。

---

## ✨ 功能特性

- 🎨 **壁纸驱动鼠标指针切换**
  - 读取 Wallpaper Engine 当前壁纸项目 ID
  - 根据配置自动切换鼠标指针主题

- 🖥 **多显示器支持**
  - 自动识别当前鼠标所在显示器
  - 每个显示器可使用不同壁纸 → 不同鼠标主题

- ♻ **默认回退机制**
  - 未配置映射时，可自动使用默认鼠标指针组

- ⚙ **可视化设置界面**
  - Wallpaper Engine 路径配置
  - 默认鼠标指针开关
  - 播放列表快速配置与设置

- 📌 **系统托盘常驻**
  - 后台监听壁纸变化
  - 托盘菜单快速打开配置 / 设置
  - 安全退出

---

## 🧩 工作原理简述

1. 读取 Wallpaper Engine 的 `config.json`
2. 获取当前显示器正在使用的壁纸项目 ID
3. 在 `config.toml` 中查找对应的鼠标主题
4. 调用 Windows API 应用鼠标指针
5. 若无匹配项，根据设置决定是否使用默认主题

---

## 🚀 快速部署

> 适合第一次使用 / 只想快速跑起来

### 1) 克隆仓库

```bash
git clone https://github.com/yourname/MouseEngine.git
cd MouseEngine
```

### 2) 安装依赖

```bash
pip install -r requirements.txt
```


### 3) 启动程序

```bash
cd src
python main.py
```

---

## 🔧 详细部署说明（进阶）

### 📁 项目目录结构（参考）

```text
MouseEngine/
│
├─ LICENSE
├─ README.md
├─ requirements.txt
├─ THIRD_PARTY_NOTICES.txt
│
├─ docs/
│  └─ licenses/              # 第三方依赖许可证原文
│
└─ src/                      # ⭐ 唯一运行目录
   ├─ main.py                # 主入口（监听 / 托盘）
   ├─ config.toml            # 主配置文件
   ├─ Initialize.py          # 初始化与配置修复
   ├─ Tlog.py                # 日志模块
   │
   ├─ getWallpaperConfig.py  # 壁纸配置解析
   ├─ setMouse.py            # 鼠标指针切换逻辑
   ├─ mouses.py              # 显示器与主题解析
   │
   ├─ mainUI.py              # 主界面
   ├─ playlistUI.py          # 鼠标主题绑定界面
   ├─ settingsUI.py          # 设置界面
   ├─ WelcomeUI.py           # 欢迎界面
   │
   ├─ image/                 # 内置图像资源
   └─ mouses/                # 鼠标指针目录

```

---

## ⚙ 配置说明（config.toml）

### 1) Wallpaper Engine 配置文件路径

在 `config.toml` 中设置 Wallpaper Engine 的 `config.json` 路径：

```toml
[path]
wallpaper_engine_config = "D:/Steam/steamapps/common/wallpaper_engine/config.json"
```

你也可以通过「设置」界面的“自动查找 / 浏览文件夹”按钮填写并写入。

---

### 2) 默认鼠标指针回退

当当前壁纸 ID 未映射到任何自定义主题时，是否回退到 `mouses/默认/`：

```toml
[config]
enable_default_icon_group = true
```

---

### 3) 壁纸 ID → 鼠标主题映射

```toml
[wallpaper]
3406760593 = "深色主题"
3409595232 = "浅色主题"
```

说明：
- 左边是 Wallpaper Engine 的项目 ID
- 右边是 `mouses/<主题名>/` 的文件夹名

---

## 🖱 鼠标主题结构说明

每个鼠标主题是一个文件夹，例如：

```text
mouses/深色主题/
└─ config.toml
```

示例：

```toml
[mouses]
Arrow = "arrow.cur"
Hand = "hand.cur"
Wait = "wait.ani"
```

（实际可按你的主题配置扩展更多项）

---

## 🧪 常见问题（FAQ）

### Q1：系统托盘没有显示？
- 确认已安装 `pystray` 和 `Pillow`
- 确认在“有桌面会话”的环境运行（不是无桌面 / 远程服务环境）
- 使用同一个 Python/venv 运行 `main.py`

### Q2：提示 `portalocker not installed`？
- 这是可选警告：表示未安装文件锁库
- 单实例使用通常可以忽略
- 安装即可消除：

```bash
pip install portalocker
```

### Q3：日志提示“未找到壁纸 ID 对应主题”，鼠标不变？
- 在 `config.toml` 的 `[wallpaper]` 中添加该壁纸 ID 的映射
- 或开启 `[config] enable_default_icon_group = true` 作为回退

---

## 📜 许可证与第三方声明

- 本项目许可证：`LICENSE`
- 第三方依赖清单：`THIRD_PARTY_NOTICES.txt`
- 第三方许可证原文：`docs/licenses/`

---

## 🤝 贡献与反馈

欢迎提交 Issue / Pull Request。  
如果你遇到问题，建议附上运行日志与 `config.toml`（注意隐藏隐私路径）。