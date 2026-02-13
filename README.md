# MouseEngine

MouseEngine 是一个 **基于 Wallpaper Engine 的 Windows 鼠标指针自动切换工具**。
它能够根据当前显示器所使用的壁纸，**自动切换对应的鼠标指针主题**，默认回退、系统托盘常驻运行。

![Logo](./docs/images/1.jpg "MouseEngine Logo")

---

## ✨ 功能特性

- 🎨 **壁纸驱动鼠标指针切换**
  - 读取 Wallpaper Engine 当前壁纸项目 ID
  - 根据配置和播放列表自动切换鼠标指针主题

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
3. 启动线程监控获取活跃壁纸
4. 在 `config.toml` 中查找对应的鼠标主题
5. 调用 Windows API 应用鼠标指针
6. 若无匹配项，根据设置决定是否使用默认主题

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
   ├─ ani_to_gif.py          # 处理ani格式转换
   ├─ cur_to_png.py          # 处理cur格式转换
   │
   ├─ getActiveWallpaper.py  # 获取活跃壁纸
   ├─ getWallpaperConfig.py  # 壁纸配置解析
   ├─ setMouse.py            # 鼠标指针切换逻辑
   ├─ mouses.py              # 显示器与主题解析
   │
   ├─ mainUI.py              # 主界面
   ├─ playlistUI.py          # 鼠标主题绑定界面
   ├─ settingsUI.py          # 设置界面
   ├─ WelcomeUI.py           # 欢迎界面
   ├─ mainUIWeb.py           # 正在测试的新界面
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
- 确认在“有桌面会话”的环境运行
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

## 🚧 开发进度和问题
### 🔄 开发中功能
- 适配 Web 类型壁纸（当前开发中，暂未支持）

### ❌ 不支持/无计划功能
- EXE 类型壁纸（暂无支持计划）

### 🛠 核心开发任务
- 使用 WebView 重构全量 UI 界面
- 核心功能模块（对的，还没写）

---

## 📜 许可证与第三方声明

本项目采用**组合授权模型 (Combined Licensing Model)**，不同功能模块遵循不同的开源协议。

### 1. 授权划分
为了平衡原创保护与社区集成，本项目代码划分为以下部分：

| 模块类型 | 涵盖内容 | 采用协议 | 限制说明 |
| :--- | :--- | :--- | :--- |
| **核心逻辑** | 独创算法、核心业务流、项目特有功能 | **[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh)** | 署名、**禁止商用**、相同方式共享 |
| **联动接口** | 与 Wallpaper Engine 交互、Wallpaper Engine 相关UI、进程监控、系统句柄操作 | **[BSD 3-Clause](https://opensource.org/licenses/BSD-3-Clause)** | 宽松授权 |
| **通用工具** | 独立的小型辅助工具函数 | **[MIT](https://opensource.org/licenses/MIT)** | 极度宽松 |

> **注**：具体每个文件的授权情况，请参阅各文件头部的 `SPDX-License-Identifier` 标注。

---

### 2. 版本变更说明
本项目自 **Alpha 2.0** 版本起进行了协议调整：
* **Alpha 2.0 及后续版本**：采用上述组合授权模型。
* **Alpha 1.2 及更早版本**：仍遵循原有的 **[BSD 3-Clause](https://opensource.org/licenses/BSD-3-Clause)** 协议。如果您使用的是旧版本代码，原有权利继续有效且不可撤销。

---

### 3. 免责声明与第三方权利
* **壁纸内容**：本软件联动功能仅用于识别和获取壁纸元数据。所有壁纸资产（图片、视频、ID 等）的版权归其在 Steam 创意工坊上的原作者所有。
* **官方关联**：本项目为个人开发，与 Wallpaper Engine 或 Steam 官方无任何隶属或背书关系。
* **软件使用**：本软件按“原样”提供，不附带任何形式的保证。作者不对因使用本软件导致的任何系统损害或法律纠纷负责。

更多详情，请阅读完整的 **[LICENSE](./LICENSE)** 文件。

- 本项目许可证：`LICENSE`
- 第三方依赖清单：`THIRD_PARTY_NOTICES.txt`
- 第三方许可证原文：`docs/licenses/`

---

### 4. 本项目中“不受 CC BY-NC-SA 4.0 限制”的内容

以下内容并非本人原创，其使用遵循各自独立的许可协议，不受本项目 CC BY-NC-SA 4.0 协议限制：


---

### 5. 对本许可证的解释与开发者权益说明
#### 许可协议的不可撤销性说明：
本项目部分内容采用的 CC BY-NC-SA 4.0 协议为不可撤销的公共许可：
- 公众获得的“非商业使用、修改、分享”权利永久有效，本人不会收回已发布版本的授权；
- 本人可停止更新项目，但已发布的版本仍受协议约束。

#### 对开发者：
* **自由开发**：使用 CC BY-NC-SA 4.0 协议的内容只要不用于商用、盈利，您可以随意 fork、魔改、集成或分发本项目的衍生版本，无需额外征得本人许可。

* **功能保障**：关于与 Wallpaper Engine 联动相关内容均使用 BSD 3-Clause 许可证，包括主main、UI、及所需的必要组件，对于此内容您可以随意更改。

* **一言以蔽之**：只要不盈利你随便改

---

## 🤝 贡献与反馈

欢迎提交 Issue / Pull Request。  
如果你遇到问题，建议附上运行日志与 `config.toml`（注意隐藏隐私路径）。
