(function () {
    const SUPPORTED_LANGUAGES = ["zh-CN", "en", "ja"];
    const DEFAULT_LANGUAGE = "zh-CN";
    const SYNC_INTERVAL_MS = 1000;

    const dictionaries = {
        "zh-CN": {
            "__name": "简体中文",
            "settings": "设置",
            "mouseGroups": "鼠标组",
            "wallpaperBinding": "壁纸绑定",
            "basicSettings": "基本设置",
            "advancedSettings": "高级设置",
            "programWhitelist": "程序白名单",
            "about": "关于",
            "appSettings": "应用设置",
            "language": "语言",
            "runAtStartup": "启动时自动运行",
            "wallpaperEnginePath": "Wallpaper Engine 路径",
            "enterPath": "请输入路径",
            "autoGet": "自动获取",
            "preview": "预览",
            "enableDefaultCursor": "启用默认光标",
            "pauseOnFullscreen": "启动全屏暂停",
            "strictWindowCheck": "严格窗口判定",
            "performanceImpactHigh": "性能影响大",
            "advancedOptions": "高级选项",
            "cacheCleanup": "缓存清理",
            "clear": "清理",
            "clearing": "正在清理...",
            "clearDone": "清理完成",
            "clearFailed": "清理失败",
            "loadFailed": "加载失败",
            "noOldVersions": "没有发现旧版本",
            "appNotStarted": "未启动应用",
            "setDefaultWindowsCursor": "将默认组设置为 Windows 默认光标",
            "setDefault": "设置默认",
            "setting": "正在设置...",
            "setSuccess": "设置成功",
            "setFailed": "设置失败",
            "showMoreMenu": "显示更多菜单内容",
            "useNewMenu": "使用新版菜单",
            "aboutMouseEngine": "关于 MouseEngine",
            "version": "版本",
            "loading": "加载中...",
            "developer": "开发者",
            "copyright": "版权",
            "license": "许可证",
            "thirdPartyLibraries": "第三方库",
            "view": "查看",
            "programExceptionRules": "程序例外规则",
            "application": "应用程序",
            "selectApplication": "选择应用程序",
            "selectFromRunning": "从运行中选择",
            "cursorGroup": "鼠标组",
            "selectCursorGroup": "选择鼠标组",
            "operation": "操作",
            "addBinding": "添加绑定",
            "currentBindings": "当前绑定",
            "noBindings": "暂无绑定",
            "edit": "编辑",
            "delete": "删除",
            "selectRunningApplication": "选择运行中的应用程序",
            "showCurrentPlaylistOnly": "仅显示当前播放列表",
            "selectWallpaper": "请选择壁纸",
            "noInfo": "暂无信息",
            "type": "类型",
            "select": "请选择",
            "currentPlaylistLoading": "当前播放列表: 加载中...",
            "currentPlaylist": "当前播放列表: {name} (共 {count} 项)",
            "multiplePlaylists": "多个播放列表（{names}）(共 {count} 项)",
            "unnamed": "未命名",
            "noWallpaperData": "暂无壁纸数据",
            "unknownWallpaper": "未知壁纸",
            "unknown": "未知",
            "unbound": "未绑定",
            "unsupportedWebWallpaper": "暂不支持 Web 壁纸",
            "unsupportedApplicationWallpaper": "不支持应用程序壁纸",
            "noImage": "无图片",
            "noPreview": "无预览图",
            "mouseGroupEditor": "MouseEngine-鼠标组编辑器",
            "mouseGroupEditorSuffix": "鼠标组编辑器",
            "applyGroup": "应用该组",
            "applyGroupSuccess": "已应用该组",
            "applyGroupFailed": "应用该组失败",
            "importGroup": "导入组",
            "newGroup": "新建组",
            "editMouseGroup": "编辑鼠标组",
            "saveCurrentGroup": "保存当前组",
            "newMouseGroup": "新建鼠标组",
            "cancel": "取消",
            "confirm": "确认",
            "rename": "重命名",
            "deleteThisGroup": "删除此组",
            "empty": "清空",
            "renameMouseGroup": "重命名鼠标组",
            "enterGroupName": "请输入组名",
            "enterNewGroupName": "请输入新组名",
            "browse": "浏览",
            "saveInProgress": "保存中...",
            "thisFeatureAppOnly": "此功能仅在应用内可用",
            "groupNameEmpty": "组名不能为空",
            "invalidGroupName": "组名不能包含特殊字符，且长度不能超过20个字符",
            "invalidGroupNameShort": "组名格式无效",
            "groupExistsOverwrite": "该组名已存在，是否覆盖？",
            "saveFailed": "保存失败，请重试",
            "deleteSuccess": "删除成功",
            "deleteFailed": "删除失败，请重试",
            "renameSuccess": "重命名成功",
            "renameFailed": "重命名失败，请重试",
            "importFailed": "导入组失败，请重试",
            "createFailed": "创建空白组失败，请重试",
            "welcomeTitle": "欢迎！应用程序配置向导",
            "welcomeHeading": "欢迎使用 MouseEngine",
            "welcomeSubtitle": "程序首次运行，请指定 Wallpaper Engine 的安装位置。",
            "wallpaperEngineRoot": "Wallpaper Engine 根目录:",
            "autoFindSteam": "自动查找 (Steam)",
            "autoFindingSteam": "正在查找... (Steam)",
            "browseFolder": "浏览文件夹",
            "confirmAndContinue": "确认并继续",
            "useDefaultWindowsCursor": "使用 Windows 默认光标创建默认光标组",
            "enterPathOrFind": "输入路径，或使用下方的查找按钮",
            "autoUpdate": "自动更新",
            "autoUpdateTitle": "MouseEngine 自动更新",
            "autoUpdateSubtitle": "检查并安装最新版本",
            "currentVersion": "当前版本",
            "latestVersion": "最新版本",
            "checking": "检查中...",
            "checkingUpdate": "正在检查更新...",
            "readyToDownload": "准备下载...",
            "releaseNotes": "更新内容",
            "downloadOptions": "选择下载版本",
            "checkUpdate": "检查更新",
            "close": "关闭",
            "downloadAndInstall": "下载并安装",
            "skip": "跳过",
            "updateAvailable": "发现新版本 {version}",
            "checkFailed": "检查失败: {error}",
            "upToDate": "当前已是最新版本",
            "downloadFailed": "下载失败，请稍后重试",
            "downloadDoneInstalling": "下载完成，正在安装...",
            "installDoneRestarting": "更新已安装，程序将重启...",
            "installFailedManual": "安装失败，请手动更新",
            "recommended": "推荐",
            "upgrade": "版本升级",
            "oneClickUpdate": "一键更新",
            "oldVersionFound": "程序找到了之前安装过的旧版本，是否一键更新？",
            "tip": "温馨提示",
            "clickOneClickUpgradePrefix": "点击\"一键升级\"将自动删除旧版本",
            "keepConfig": "，但保留原先的配置文件。",
            "oneClickUpgrade": "一键升级"
        },
        "en": {
            "__name": "English",
            "settings": "Settings",
            "mouseGroups": "Mouse Groups",
            "wallpaperBinding": "Wallpaper Binding",
            "basicSettings": "Basic Settings",
            "advancedSettings": "Advanced Settings",
            "programWhitelist": "Program Whitelist",
            "about": "About",
            "appSettings": "Application Settings",
            "language": "Language",
            "runAtStartup": "Run at startup",
            "wallpaperEnginePath": "Wallpaper Engine Path",
            "enterPath": "Enter path",
            "autoGet": "Auto Detect",
            "preview": "Browse",
            "enableDefaultCursor": "Enable default cursor",
            "pauseOnFullscreen": "Pause in fullscreen",
            "strictWindowCheck": "Strict window matching",
            "performanceImpactHigh": "High performance impact",
            "advancedOptions": "Advanced Options",
            "cacheCleanup": "Cache cleanup",
            "clear": "Clear",
            "clearing": "Clearing...",
            "clearDone": "Cleared",
            "clearFailed": "Clear failed",
            "loadFailed": "Load failed",
            "noOldVersions": "No older versions found",
            "appNotStarted": "App is not running",
            "setDefaultWindowsCursor": "Set default group as Windows default cursor",
            "setDefault": "Set Default",
            "setting": "Setting...",
            "setSuccess": "Set successfully",
            "setFailed": "Set failed",
            "showMoreMenu": "Show more menu content",
            "useNewMenu": "Use new menu",
            "aboutMouseEngine": "About MouseEngine",
            "version": "Version",
            "loading": "Loading...",
            "developer": "Developer",
            "copyright": "Copyright",
            "license": "License",
            "thirdPartyLibraries": "Third-party Libraries",
            "view": "View",
            "programExceptionRules": "Program exception rules",
            "application": "Application",
            "selectApplication": "Select application",
            "selectFromRunning": "Select from running apps",
            "cursorGroup": "Mouse group",
            "selectCursorGroup": "Select mouse group",
            "operation": "Action",
            "addBinding": "Add Binding",
            "currentBindings": "Current Bindings",
            "noBindings": "No bindings",
            "edit": "Edit",
            "delete": "Delete",
            "selectRunningApplication": "Select running application",
            "showCurrentPlaylistOnly": "Show current playlist only",
            "selectWallpaper": "Please select a wallpaper",
            "noInfo": "No information",
            "type": "Type",
            "select": "Please select",
            "currentPlaylistLoading": "Current playlist: Loading...",
            "currentPlaylist": "Current playlist: {name} ({count} items)",
            "multiplePlaylists": "Multiple playlists ({names}) ({count} items)",
            "unnamed": "Unnamed",
            "noWallpaperData": "No wallpaper data",
            "unknownWallpaper": "Unknown wallpaper",
            "unknown": "Unknown",
            "unbound": "Unbound",
            "unsupportedWebWallpaper": "Web wallpapers are not supported yet",
            "unsupportedApplicationWallpaper": "Application wallpapers are not supported",
            "noImage": "No image",
            "noPreview": "No preview",
            "mouseGroupEditor": "MouseEngine-Mouse Group Editor",
            "mouseGroupEditorSuffix": "Mouse Group Editor",
            "applyGroup": "Apply This Group",
            "applyGroupSuccess": "Group applied",
            "applyGroupFailed": "Failed to apply group",
            "importGroup": "Import Group",
            "newGroup": "New Group",
            "editMouseGroup": "Edit Mouse Group",
            "saveCurrentGroup": "Save Current Group",
            "newMouseGroup": "New Mouse Group",
            "cancel": "Cancel",
            "confirm": "Confirm",
            "rename": "Rename",
            "deleteThisGroup": "Delete this group",
            "empty": "Clear",
            "renameMouseGroup": "Rename Mouse Group",
            "enterGroupName": "Enter group name",
            "enterNewGroupName": "Enter new group name",
            "browse": "Browse",
            "saveInProgress": "Saving...",
            "thisFeatureAppOnly": "This feature is available only in the app",
            "groupNameEmpty": "Group name cannot be empty",
            "invalidGroupName": "Group name cannot contain special characters and must be 20 characters or fewer",
            "invalidGroupNameShort": "Invalid group name",
            "groupExistsOverwrite": "This group name already exists. Overwrite it?",
            "saveFailed": "Save failed, please try again",
            "deleteSuccess": "Deleted",
            "deleteFailed": "Delete failed, please try again",
            "renameSuccess": "Renamed",
            "renameFailed": "Rename failed, please try again",
            "importFailed": "Import failed, please try again",
            "createFailed": "Create failed, please try again",
            "welcomeTitle": "Welcome! Application Setup Wizard",
            "welcomeHeading": "Welcome to MouseEngine",
            "welcomeSubtitle": "First run: please choose the Wallpaper Engine installation location.",
            "wallpaperEngineRoot": "Wallpaper Engine root folder:",
            "autoFindSteam": "Auto Detect (Steam)",
            "autoFindingSteam": "Detecting... (Steam)",
            "browseFolder": "Browse Folder",
            "confirmAndContinue": "Confirm and Continue",
            "useDefaultWindowsCursor": "Create the default cursor group from Windows defaults",
            "enterPathOrFind": "Enter a path, or use the detection buttons below",
            "autoUpdate": "Auto Update",
            "autoUpdateTitle": "MouseEngine Auto Update",
            "autoUpdateSubtitle": "Check for and install the latest version",
            "currentVersion": "Current Version",
            "latestVersion": "Latest Version",
            "checking": "Checking...",
            "checkingUpdate": "Checking for updates...",
            "readyToDownload": "Ready to download...",
            "releaseNotes": "Release Notes",
            "downloadOptions": "Select Download Version",
            "checkUpdate": "Check Updates",
            "close": "Close",
            "downloadAndInstall": "Download and Install",
            "skip": "Skip",
            "updateAvailable": "New version found: {version}",
            "checkFailed": "Check failed: {error}",
            "upToDate": "You are already on the latest version",
            "downloadFailed": "Download failed, please try again later",
            "downloadDoneInstalling": "Download complete, installing...",
            "installDoneRestarting": "Update installed, restarting...",
            "installFailedManual": "Installation failed, please update manually",
            "recommended": "Recommended",
            "upgrade": "Version Upgrade",
            "oneClickUpdate": "One-click Update",
            "oldVersionFound": "An older installed version was found. Update with one click?",
            "tip": "Tip",
            "clickOneClickUpgradePrefix": "Click \"One-click Upgrade\" to automatically delete the old version",
            "keepConfig": ", while keeping your existing configuration files.",
            "oneClickUpgrade": "One-click Upgrade"
        },
        "ja": {
            "__name": "日本語",
            "settings": "設定",
            "mouseGroups": "カーソルグループ",
            "wallpaperBinding": "壁紙の紐付け",
            "basicSettings": "基本設定",
            "advancedSettings": "詳細設定",
            "programWhitelist": "プログラムホワイトリスト",
            "about": "情報",
            "appSettings": "アプリ設定",
            "language": "言語",
            "runAtStartup": "起動時に自動実行",
            "wallpaperEnginePath": "Wallpaper Engine のパス",
            "enterPath": "パスを入力してください",
            "autoGet": "自動取得",
            "preview": "参照",
            "enableDefaultCursor": "デフォルトカーソルを有効にする",
            "pauseOnFullscreen": "フルスクリーン時に一時停止",
            "strictWindowCheck": "厳密なウィンドウ判定",
            "performanceImpactHigh": "性能への影響大",
            "advancedOptions": "詳細オプション",
            "cacheCleanup": "キャッシュ削除",
            "clear": "削除",
            "clearing": "削除中...",
            "clearDone": "削除完了",
            "clearFailed": "削除失敗",
            "loadFailed": "読み込みに失敗しました",
            "noOldVersions": "古いバージョンは見つかりませんでした",
            "appNotStarted": "アプリが起動していません",
            "setDefaultWindowsCursor": "デフォルトグループを Windows の既定カーソルに設定",
            "setDefault": "既定に設定",
            "setting": "設定中...",
            "setSuccess": "設定しました",
            "setFailed": "設定に失敗しました",
            "showMoreMenu": "追加メニュー項目を表示",
            "useNewMenu": "新しいメニューを使用",
            "aboutMouseEngine": "MouseEngine について",
            "version": "バージョン",
            "loading": "読み込み中...",
            "developer": "開発者",
            "copyright": "著作権",
            "license": "ライセンス",
            "thirdPartyLibraries": "サードパーティライブラリ",
            "view": "表示",
            "programExceptionRules": "プログラム例外ルール",
            "application": "アプリケーション",
            "selectApplication": "アプリケーションを選択",
            "selectFromRunning": "実行中から選択",
            "cursorGroup": "カーソルグループ",
            "selectCursorGroup": "カーソルグループを選択",
            "operation": "操作",
            "addBinding": "紐づけを追加",
            "currentBindings": "現在の紐づけ",
            "noBindings": "紐づけはありません",
            "edit": "編集",
            "delete": "削除",
            "selectRunningApplication": "実行中のアプリケーションを選択",
            "showCurrentPlaylistOnly": "現在のプレイリストのみ表示",
            "selectWallpaper": "壁紙を選択してください",
            "noInfo": "情報がありません",
            "type": "種類",
            "select": "選択してください",
            "currentPlaylistLoading": "現在のプレイリスト: 読み込み中...",
            "currentPlaylist": "現在のプレイリスト: {name} ({count} 件)",
            "multiplePlaylists": "複数のプレイリスト ({names}) ({count} 件)",
            "unnamed": "名称未設定",
            "noWallpaperData": "壁紙データがありません",
            "unknownWallpaper": "不明な壁紙",
            "unknown": "不明",
            "unbound": "未紐づけ",
            "unsupportedWebWallpaper": "Web 壁紙はまだサポートされていません",
            "unsupportedApplicationWallpaper": "アプリケーション壁紙はサポートされていません",
            "noImage": "画像なし",
            "noPreview": "プレビューなし",
            "mouseGroupEditor": "MouseEngine-カーソルグループエディタ",
            "mouseGroupEditorSuffix": "カーソルグループエディタ",
            "applyGroup": "このグループを適用",
            "applyGroupSuccess": "グループを適用しました",
            "applyGroupFailed": "グループの適用に失敗しました",
            "importGroup": "グループをインポート",
            "newGroup": "新規グループ",
            "editMouseGroup": "カーソルグループを編集",
            "saveCurrentGroup": "現在のグループを保存",
            "newMouseGroup": "新しいカーソルグループ",
            "cancel": "キャンセル",
            "confirm": "確認",
            "rename": "名前を変更",
            "deleteThisGroup": "このグループを削除",
            "empty": "クリア",
            "renameMouseGroup": "カーソルグループ名を変更",
            "enterGroupName": "グループ名を入力してください",
            "enterNewGroupName": "新しいグループ名を入力してください",
            "browse": "参照",
            "saveInProgress": "保存中...",
            "thisFeatureAppOnly": "この機能はアプリ内でのみ使用できます",
            "groupNameEmpty": "グループ名は空にできません",
            "invalidGroupName": "グループ名に特殊文字は使用できません。20 文字以内にしてください",
            "invalidGroupNameShort": "グループ名の形式が無効です",
            "groupExistsOverwrite": "このグループ名は既に存在します。上書きしますか？",
            "saveFailed": "保存に失敗しました。もう一度お試しください",
            "deleteSuccess": "削除しました",
            "deleteFailed": "削除に失敗しました。もう一度お試しください",
            "renameSuccess": "名前を変更しました",
            "renameFailed": "名前の変更に失敗しました。もう一度お試しください",
            "importFailed": "グループのインポートに失敗しました。もう一度お試しください",
            "createFailed": "空のグループ作成に失敗しました。もう一度お試しください",
            "welcomeTitle": "ようこそ！アプリ設定ウィザード",
            "welcomeHeading": "MouseEngine へようこそ",
            "welcomeSubtitle": "初回起動です。Wallpaper Engine のインストール場所を指定してください。",
            "wallpaperEngineRoot": "Wallpaper Engine ルートフォルダ:",
            "autoFindSteam": "自動検索 (Steam)",
            "autoFindingSteam": "検索中... (Steam)",
            "browseFolder": "フォルダを参照",
            "confirmAndContinue": "確認して続行",
            "useDefaultWindowsCursor": "Windows 既定カーソルからデフォルトグループを作成",
            "enterPathOrFind": "パスを入力するか、下の検索ボタンを使用してください",
            "autoUpdate": "自動更新",
            "autoUpdateTitle": "MouseEngine 自動更新",
            "autoUpdateSubtitle": "最新バージョンを確認してインストール",
            "currentVersion": "現在のバージョン",
            "latestVersion": "最新バージョン",
            "checking": "確認中...",
            "checkingUpdate": "更新を確認中...",
            "readyToDownload": "ダウンロード準備中...",
            "releaseNotes": "リリースノート",
            "downloadOptions": "ダウンロードするバージョンを選択",
            "checkUpdate": "更新を確認",
            "close": "閉じる",
            "downloadAndInstall": "ダウンロードしてインストール",
            "skip": "スキップ",
            "updateAvailable": "新しいバージョンが見つかりました: {version}",
            "checkFailed": "確認に失敗しました: {error}",
            "upToDate": "現在のバージョンは最新です",
            "downloadFailed": "ダウンロードに失敗しました。後でもう一度お試しください",
            "downloadDoneInstalling": "ダウンロード完了。インストール中...",
            "installDoneRestarting": "更新をインストールしました。再起動します...",
            "installFailedManual": "インストールに失敗しました。手動で更新してください",
            "recommended": "推奨",
            "upgrade": "バージョンアップグレード",
            "oneClickUpdate": "ワンクリック更新",
            "oldVersionFound": "以前インストールされた古いバージョンが見つかりました。ワンクリックで更新しますか？",
            "tip": "ヒント",
            "clickOneClickUpgradePrefix": "「ワンクリックアップグレード」をクリックすると古いバージョンを自動で削除します",
            "keepConfig": "、既存の設定ファイルは保持されます。",
            "oneClickUpgrade": "ワンクリックアップグレード"
        }
    };

    const textToKey = {};
    for (const dict of Object.values(dictionaries)) {
        for (const [key, value] of Object.entries(dict)) {
            if (!key.startsWith("__") && typeof value === "string" && !value.includes("{")) {
                textToKey[normalize(value)] = key;
            }
        }
    }
    Object.assign(textToKey, {
        "Wallpaper Engine路径": "wallpaperEnginePath",
        "暂不支持Web壁纸": "unsupportedWebWallpaper",
        "类型：-": "type",
        "Type: -": "type",
        "種類：-": "type"
    });

    let language = normalizeLanguage(localStorage.getItem("mouseengine.language"));
    let observer = null;
    let applying = false;
    let syncTimer = null;

    function normalizeLanguage(value) {
        return SUPPORTED_LANGUAGES.includes(value) ? value : DEFAULT_LANGUAGE;
    }

    function normalize(text) {
        return (text || "").replace(/\s+/g, " ").trim();
    }

    function currentDictionary() {
        return dictionaries[language] || dictionaries[DEFAULT_LANGUAGE];
    }

    function format(template, params) {
        return String(template).replace(/\{(\w+)\}/g, (_, key) => params && params[key] !== undefined ? params[key] : "");
    }

    function t(key, params) {
        const dict = currentDictionary();
        return format(dict[key] || dictionaries[DEFAULT_LANGUAGE][key] || key, params);
    }

    function translateFreeText(text) {
        const raw = normalize(text);
        if (!raw) return text;

        let match = raw.match(/^(类型|Type|種類)[:：]\s*(.+)$/);
        if (match) return `${t("type")}：${match[2]}`;

        const key = textToKey[raw];
        if (key === "type") return `${t("type")}：-`;
        return key ? t(key) : text;
    }

    function translateElement(el) {
        if (el.nodeType !== Node.ELEMENT_NODE) return;

        if (el.dataset.i18n) {
            el.textContent = t(el.dataset.i18n);
        }
        if (el.dataset.i18nPrefix && el.dataset.i18nValue !== undefined) {
            el.textContent = `${t(el.dataset.i18nPrefix)}：${el.dataset.i18nValue}`;
        }
        if (el.dataset.i18nPlaceholder) {
            el.setAttribute("placeholder", t(el.dataset.i18nPlaceholder));
        }
        if (el.dataset.i18nTitle) {
            el.setAttribute("title", t(el.dataset.i18nTitle));
        }
        if (el.dataset.i18nAlt) {
            el.setAttribute("alt", t(el.dataset.i18nAlt));
        }
        if (el.placeholder) {
            el.placeholder = translateFreeText(el.placeholder);
        }
        if (el.alt) {
            el.alt = translateFreeText(el.alt);
        }
        for (const child of el.childNodes) {
            if (child.nodeType === Node.TEXT_NODE) {
                const translated = translateFreeText(child.nodeValue);
                if (translated !== child.nodeValue) child.nodeValue = translated;
            }
        }
    }

    function applyI18n(root) {
        if (applying) return;
        applying = true;
        try {
            document.documentElement.lang = language;
            const scope = root && root.querySelectorAll ? root : document;
            if (scope.nodeType === Node.ELEMENT_NODE) translateElement(scope);
            scope.querySelectorAll("*").forEach(translateElement);
            window.dispatchEvent(new CustomEvent("mouseengine-language-applied", { detail: { language } }));
        } finally {
            applying = false;
        }
    }

    async function readApiLanguage() {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.get_language) {
            return normalizeLanguage(await window.pywebview.api.get_language());
        }
        return language;
    }

    async function loadLanguage() {
        try {
            language = await readApiLanguage();
        } catch (e) {
            language = normalizeLanguage(localStorage.getItem("mouseengine.language"));
        }
        localStorage.setItem("mouseengine.language", language);
        applyI18n(document);
        return language;
    }

    async function setLanguage(nextLanguage) {
        const normalized = normalizeLanguage(nextLanguage);
        language = normalized;
        localStorage.setItem("mouseengine.language", language);
        try {
            if (window.pywebview && window.pywebview.api && window.pywebview.api.set_language) {
                await window.pywebview.api.set_language(language);
            }
        } catch (e) {
        }
        applyI18n(document);
        return true;
    }

    async function syncLanguageFromConfig() {
        try {
            const apiLanguage = await readApiLanguage();
            if (apiLanguage !== language) {
                language = apiLanguage;
                localStorage.setItem("mouseengine.language", language);
                applyI18n(document);
            }
        } catch (e) {
        }
    }

    function observe() {
        if (observer) observer.disconnect();
        observer = new MutationObserver((mutations) => {
            if (applying) return;
            for (const mutation of mutations) {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) applyI18n(node);
                });
                if (mutation.type === "characterData" && mutation.target.parentElement) {
                    applyI18n(mutation.target.parentElement);
                }
            }
        });
        observer.observe(document.documentElement, { childList: true, subtree: true, characterData: true });
    }

    function startSyncTimer() {
        if (syncTimer) return;
        syncTimer = window.setInterval(syncLanguageFromConfig, SYNC_INTERVAL_MS);
    }

    window.MouseEngineI18n = {
        languages: SUPPORTED_LANGUAGES,
        languageNames: Object.fromEntries(SUPPORTED_LANGUAGES.map((code) => [code, dictionaries[code].__name])),
        t,
        apply: applyI18n,
        load: loadLanguage,
        setLanguage,
        getLanguage: () => language
    };

    document.addEventListener("DOMContentLoaded", () => {
        observe();
        loadLanguage();
        startSyncTimer();
    });
    window.addEventListener("pywebviewready", () => {
        loadLanguage();
        startSyncTimer();
    });
})();
