// settingsUI.js

window.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    // 初始加载第一页的数据
    startLoadingSequence();
    
    // 添加输入框事件监听
    const pathInput = document.querySelector('.custom-input-stretch');
    if (pathInput) {
        // 防抖函数
        let debounceTimer;
        pathInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                handlePathValidation.call(this);
            }, 500); // 500ms防抖
        });
    }
});

// 异步加载序列：逐个触发 Python 函数并等待返回
async function startLoadingSequence() {
    if (typeof pywebview === 'undefined' || !pywebview.api) {
        setTimeout(startLoadingSequence, 100);
        return;
    }

    console.log("开始按序加载设置...");

    try {
        // 1. 获取自启动状态
        const autoStart = await pywebview.api.get_auto_start();
        const autoStartEl = document.getElementById('autoStart');
        if (autoStartEl) autoStartEl.checked = autoStart;

        // 2. 获取路径
        const wpPath = await pywebview.api.get_wp_path();
        const pathInput = document.querySelector('.custom-input-stretch');
        if (pathInput) pathInput.value = wpPath;

        // 3. 获取光标设置
        const cursorStatus = await pywebview.api.get_cursor_status();
        const cursorEl = document.getElementById('enableDefaultCursor');
        if (cursorEl) cursorEl.checked = cursorStatus;
        
        // 4. 获取全屏暂停状态
        const fullscreenPauseStatus = await pywebview.api.全屏暂停状态();
        const fullscreenPauseEl = document.getElementById('enableFullscreenPause');
        if (fullscreenPauseEl) fullscreenPauseEl.checked = fullscreenPauseStatus;
        
        console.log("所有配置项加载完成");
    } catch (e) {
        console.error("加载配置失败:", e);
    }
}

function initNavigation() {
    const menuItems = document.querySelectorAll('.settings-nav-item');
    menuItems.forEach(item => {
        item.addEventListener('click', function() {
            menuItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            updateSettingsContent(this.textContent.trim());
        });
    });
}

function updateSettingsContent(menuText) {
    const settingsTitle = document.querySelector('.settings-title');
    const settingsSection = document.querySelector('.settings-section');
    
    if (settingsTitle) settingsTitle.textContent = menuText;
    
    // 清空当前内容并根据菜单名重新渲染
    switch (menuText) {
        case '基本设置':
            renderBasicSettings(settingsSection);
            startLoadingSequence(); // 重新填充数据
            break;
        case '高级设置':
            renderAdvancedSettings(settingsSection);
            break;
        case '关于':
            renderAboutSettings(settingsSection);
            break;
    }
}

// --- 页面渲染模板 ---

function renderBasicSettings(container) {
    container.innerHTML = `
        <div class="settings-section-title">应用设置</div>
        <div class="settings-item">
            <div class="settings-label">启动时自动运行</div>
            <div class="settings-control"><input type="checkbox" id="autoStart"></div>
        </div>
        <div class="settings-item settings-item-double-row">
            <div class="settings-label-row"><div class="settings-label">Wallpaper Engine路径</div></div>
            <div class="settings-control-row">
                <input type="text" class="custom-input custom-input-stretch" placeholder="请输入路径">
                <div class="settings-buttons">
                    <button class="settings-btn" onclick="handleAutoGet()">自动获取</button>
                    <button class="settings-btn" onclick="handlePreview()">预览</button>
                </div>
            </div>
        </div>
        <div class="settings-item">
            <div class="settings-label">启用默认光标</div>
            <div class="settings-control"><input type="checkbox" id="enableDefaultCursor"></div>
        </div>
        <div class="settings-item">
            <div class="settings-label">启动全屏暂停</div>
            <div class="settings-control"><input type="checkbox" id="enableFullscreenPause" onchange="handleFullscreenPauseChange(this.checked)"></div>
        </div>
    `;
}

function renderAdvancedSettings(container) {
    container.innerHTML = `
        <div class="settings-section-title">高级选项</div>
        <div class="settings-item">
            <div class="settings-label">缓存清理</div>
            <div class="settings-control">
                <button class="settings-btn" onclick="handleClearCache(this)">清理</button>
            </div>
        </div>
    `;
}

function renderAboutSettings(container) {
    container.innerHTML = `
        <div class="settings-section-title">关于 MouseEngine</div>
        <div class="settings-item">
            <div class="settings-label">版本</div>
            <div class="settings-value">Alpha2.2</div>
        </div>
        <div class="settings-item">
            <div class="settings-label">开发者</div>
            <div class="settings-value">CIF3</div>
        </div>
        <div class="settings-item">
            <div class="settings-label">版权</div>
            <div class="settings-value">© 2026 CIF3</div>
        </div>
        <div class="settings-item">
            <div class="settings-label">许可证</div>
            <div class="settings-value settings-link" onclick="showModal('license')">查看</div>
        </div>
    `;
}

// --- 交互逻辑 ---

async function handlePreview() {
    try {
        const pathInput = document.querySelector('.custom-input-stretch');
        const currentPath = pathInput.value;
        
        // 调用路径预览选择方法，获取用户选择的路径
        const selectedPath = await pywebview.api.路径预览选择(currentPath);
        
        if (selectedPath) {
            // 将选择的路径填入输入框
            pathInput.value = selectedPath;
            // 触发输入框的验证和保存
            handlePathValidation.call(pathInput);
        }
    } catch (e) {
        console.error("选择路径失败:", e);
    }
}

async function handleAutoGet() {
    try {
        const path = await pywebview.api.自动查找路径();
        if (path) {
            const pathInput = document.querySelector('.custom-input-stretch');
            if (pathInput) {
                pathInput.value = path;
                // 自动获取路径后也进行验证
                handlePathValidation.call(pathInput);
            }
        }
    } catch (e) {
        console.error("自动获取路径失败:", e);
    }
}

async function handlePathValidation() {
    const pathInput = this;
    const path = pathInput.value.trim();
    
    if (!path) {
        // 清空路径时恢复默认边框颜色
        pathInput.style.borderColor = '';
        return;
    }
    
    try {
        const isValid = await pywebview.api.验证路径(path);
        // 根据验证结果设置边框颜色
        if (isValid) {
            pathInput.style.borderColor = '#4CAF50'; // 绿色，表示有效
        } else {
            pathInput.style.borderColor = '#F44336'; // 红色，表示无效
        }
    } catch (e) {
        console.error("验证路径失败:", e);
        pathInput.style.borderColor = '#F44336'; // 红色，表示错误
    }
}

async function handleFullscreenPauseChange(checked) {
    try {
        await pywebview.api.全屏暂停(checked);
        console.log("全屏暂停状态已更新为:", checked);
    } catch (e) {
        console.error("更新全屏暂停状态失败:", e);
    }
}

async function handleClearCache(button) {
    // 保存原始文本
    const originalText = button.textContent;
    // 替换为正在清理
    button.textContent = "正在清理...";
    // 禁用按钮
    button.disabled = true;
    
    try {
        // 调用清理缓存方法
        const success = await pywebview.api.清理缓存();
        // 替换为清理完成
        button.textContent = "清理完成";
        console.log("缓存清理完成");
    } catch (e) {
        console.error("清理缓存失败:", e);
        button.textContent = "清理失败";
    } finally {
        // 3秒后恢复按钮状态
        setTimeout(() => {
            button.textContent = originalText;
            button.disabled = false;
        }, 3000);
    }
}

function showModal(type) {
    // 简单实现模态框逻辑
    const content = type === 'license' ? "MIT License..." : "Third Party...";
    alert(content); 
}