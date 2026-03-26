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
        // 获取自启动状态
        const autoStart = await pywebview.api.get_auto_start();
        const autoStartEl = document.getElementById('autoStart');
        if (autoStartEl) {
            autoStartEl.checked = autoStart;
            // 添加 change 事件监听器
            autoStartEl.addEventListener('change', function() {
                handleAutoStartChange(this.checked);
            });
        }

        // 获取路径
        const wpPath = await pywebview.api.get_wp_path();
        const pathInput = document.querySelector('.custom-input-stretch');
        if (pathInput) pathInput.value = wpPath;

        // 获取光标设置
        const cursorStatus = await pywebview.api.get_enable_default_icon_group();
        const cursorEl = document.getElementById('enableDefaultCursor');
        if (cursorEl) {
            cursorEl.checked = cursorStatus;
            // 添加 change 事件监听器
            cursorEl.addEventListener('change', function() {
                handleEnableDefaultCursorChange(this.checked);
            });
        }
        
        // 获取全屏暂停状态
        const fullscreenPauseStatus = await pywebview.api.全屏暂停状态();
        const fullscreenPauseEl = document.getElementById('enableFullscreenPause');
        if (fullscreenPauseEl) fullscreenPauseEl.checked = fullscreenPauseStatus;
        
        // 获取严格窗口判定状态
        const strictWindowCheckStatus = await pywebview.api.严格窗口判定状态();
        const strictWindowCheckEl = document.getElementById('strictWindowCheck');
        if (strictWindowCheckEl) strictWindowCheckEl.checked = strictWindowCheckStatus;
        
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
            startLoadingSequence(); // 重新填充数据
            break;
        case '程序白名单':
            renderProgramWhitelistSettings(settingsSection);
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
            <div class="settings-control"><input type="checkbox" id="autoStart" onchange="handleAutoStartChange(this.checked)"></div>
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
            <div class="settings-control"><input type="checkbox" id="enableDefaultCursor" onchange="handleEnableDefaultCursorChange(this.checked)"></div>
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
        <div class="settings-item settings-item-developing">
            <div class="developing-overlay">
                <span>此功能处于开发状态</span>
            </div>
            <div class="settings-label-container">
                <div class="settings-label">严格的窗口判定 <span class="beta-badge">Beta</span></div>
                <div class="settings-sub-label">用于程序白名单，进入或离开窗口时立即切换</div>
            </div>
            <div class="settings-control"><input type="checkbox" id="strictWindowCheck" onchange="handleStrictWindowCheckChange(this.checked)"></div>
        </div>
        <div class="settings-item">
            <div class="settings-label-container">
                <div class="settings-label">将默认组设置为Windows默认光标</div>
            </div>
            <div class="settings-control">
                <button class="settings-btn" onclick="handleRestoreDefaultCursor()">设置默认</button>
            </div>
        </div>
    `;
}

function renderAboutSettings(container) {
    container.innerHTML = `
        <div class="settings-section-title">关于 MouseEngine</div>
        <div class="settings-item">
            <div class="settings-label">版本</div>
            <div class="settings-value">Beta1.1</div>
        </div>
        <div class="settings-item">
            <div class="settings-label">开发者</div>
            <div class="settings-value">CIF3</div>
        </div>
        <div class="settings-item">
            <div class="settings-label">版权</div>
            <div class="settings-value">© 2025-${new Date().getFullYear()} CIF3</div>
        </div>
        <div class="settings-item">
            <div class="settings-label">许可证</div>
            <div class="settings-value settings-link" onclick="showModal('license')">查看</div>
        </div>
        <div class="settings-item">
            <div class="settings-label">第三方库</div>
            <div class="settings-value settings-link" onclick="showModal('thirdparty')">查看</div>
        </div>
    `;
}

function renderProgramWhitelistSettings(container) {
    container.innerHTML = `
        <div class="settings-section-title">程序例外规则</div>
        <div class="settings-item">
            <div class="settings-label">应用程序</div>
            <div class="settings-control">
                <input type="text" class="custom-input" id="programInput" placeholder="选择应用程序" readonly>
                <button class="settings-btn" onclick="selectFromRunning()">从运行中选择</button>
            </div>
        </div>
        <div class="settings-item">
            <div class="settings-label">光标组</div>
            <div class="settings-control">
                <select class="custom-input" id="cursorGroupSelect">
                    <option value="">选择光标组</option>
                </select>
            </div>
        </div>
        <div class="settings-item">
            <div class="settings-label">操作</div>
            <div class="settings-control">
                <button class="settings-btn" onclick="addWhitelistEntry()">添加绑定</button>
            </div>
        </div>
        <div class="settings-divider"></div>
        <div class="settings-section-title">当前绑定</div>
        <div id="whitelistEntries" class="whitelist-entries">
            <div class="whitelist-empty">暂无绑定</div>
        </div>
    `;
    
    // 加载白名单数据
    loadWhitelistData();
    // 加载光标组数据
    loadCursorGroups();
}

async function loadWhitelistData() {
    try {
        if (typeof pywebview === 'undefined' || !pywebview.api) {
            setTimeout(loadWhitelistData, 100);
            return;
        }
        
        const whitelist = await pywebview.api.get_program_whitelist();
        const container = document.getElementById('whitelistEntries');
        
        if (whitelist && Object.keys(whitelist).length > 0) {
            container.innerHTML = '';
            Object.entries(whitelist).forEach(([program, cursorGroup]) => {
                const entry = document.createElement('div');
                entry.className = 'whitelist-entry';
                entry.innerHTML = `
                    <div class="whitelist-program">${program}</div>
                    <div class="whitelist-cursor">${cursorGroup}</div>
                    <div class="whitelist-actions">
                        <button class="settings-btn settings-btn-small" onclick="editWhitelistEntry('${program}')">编辑</button>
                        <button class="settings-btn settings-btn-small" onclick="deleteWhitelistEntry('${program}')">删除</button>
                    </div>
                `;
                container.appendChild(entry);
            });
        } else {
            container.innerHTML = '<div class="whitelist-empty">暂无绑定</div>';
        }
    } catch (e) {
        console.error("加载白名单数据失败:", e);
    }
}

async function loadCursorGroups() {
    try {
        if (typeof pywebview === 'undefined' || !pywebview.api) {
            setTimeout(loadCursorGroups, 100);
            return;
        }
        
        const cursorGroups = await pywebview.api.get_cursor_groups();
        const select = document.getElementById('cursorGroupSelect');
        
        select.innerHTML = '<option value="">选择光标组</option>';
        cursorGroups.forEach(group => {
            const option = document.createElement('option');
            option.value = group;
            option.textContent = group;
            select.appendChild(option);
        });
    } catch (e) {
        console.error("加载光标组数据失败:", e);
    }
}



async function addWhitelistEntry() {
    const program = document.getElementById('programInput').value;
    const cursorGroup = document.getElementById('cursorGroupSelect').value;
    
    if (!program || !cursorGroup) {
        console.log('请选择应用程序和光标组');
        return;
    }
    
    try {
        if (typeof pywebview === 'undefined' || !pywebview.api) {
            console.log('请先启动应用程序');
            return;
        }
        
        await pywebview.api.add_program_whitelist(program, cursorGroup);
        console.log('绑定成功');
        // 重新加载数据
        loadWhitelistData();
        // 清空选择
        document.getElementById('programInput').value = '';
        document.getElementById('cursorGroupSelect').value = '';
    } catch (e) {
        console.error("添加绑定失败:", e);
    }
}



async function editWhitelistEntry(program) {
    try {
        if (typeof pywebview === 'undefined' || !pywebview.api) {
            console.log('请先启动应用程序');
            return;
        }
        
        const whitelist = await pywebview.api.get_program_whitelist();
        const currentGroup = whitelist[program];
        
        if (currentGroup) {
            document.getElementById('programInput').value = program;
            document.getElementById('cursorGroupSelect').value = currentGroup;
        }
    } catch (e) {
        console.error("编辑绑定失败:", e);
    }
}

async function deleteWhitelistEntry(program) {
    try {
        if (typeof pywebview === 'undefined' || !pywebview.api) {
            console.log('请先启动应用程序');
            return;
        }
        
        await pywebview.api.delete_program_whitelist(program);
        console.log('删除绑定成功');
        // 重新加载数据
        loadWhitelistData();
    } catch (e) {
        console.error("删除绑定失败:", e);
    }
}

async function selectFromRunning() {
    try {
        if (typeof pywebview === 'undefined' || !pywebview.api) {
            console.log('请先启动应用程序');
            return;
        }
        
        const windows = await pywebview.api.get_all_windows();
        if (!windows || windows.length === 0) {
            console.log('未找到运行中的窗口');
            return;
        }
        
        // 创建选择对话框
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        
        const modalContent = document.createElement('div');
        modalContent.className = 'modal-content';
        modalContent.innerHTML = `
            <div class="modal-header">
                <h3>选择运行中的应用程序</h3>
            </div>
            <div class="modal-body scrollable">
                <div class="running-windows-list">
                    ${windows.map(window => `
                        <div class="running-window-item" onclick="selectWindow('${window.process_name}')">
                            <div class="running-window-title">${window.title}</div>
                            <div class="running-window-process">${window.process_name}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
        
        // 点击模态框外部关闭
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });
    } catch (e) {
        console.error("获取运行中窗口失败:", e);
    }
}

function selectWindow(processName) {
    const input = document.getElementById('programInput');
    input.value = processName;
    
    // 关闭模态框
    const modal = document.querySelector('.modal-overlay');
    if (modal) {
        document.body.removeChild(modal);
    }
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

async function handleStrictWindowCheckChange(checked) {
    try {
        await pywebview.api.严格窗口判定(checked);
        console.log("严格窗口判定状态已更新为:", checked);
    } catch (e) {
        console.error("更新严格窗口判定状态失败:", e);
    }
}

async function handleEnableDefaultCursorChange(checked) {
    try {
        await pywebview.api.set_enable_default_icon_group(checked);
        console.log("默认图标组状态已更新为:", checked);
    } catch (e) {
        console.error("更新默认图标组状态失败:", e);
    }
}

async function handleAutoStartChange(checked) {
    try {
        await pywebview.api.set_auto_start(checked);
        console.log("自启动状态已更新为:", checked);
    } catch (e) {
        console.error("更新自启动状态失败:", e);
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

async function handleRestoreDefaultCursor() {
    // 获取按钮元素
    const button = event.target;
    // 保存原始文本
    const originalText = button.textContent;
    // 替换为正在设置
    button.textContent = "正在设置...";
    // 禁用按钮
    button.disabled = true;
    
    try {
        if (typeof pywebview === 'undefined' || !pywebview.api) {
            console.log('请先启动应用程序');
            button.textContent = "未启动应用";
            // 3秒后恢复按钮状态
            setTimeout(() => {
                button.textContent = originalText;
                button.disabled = false;
            }, 3000);
            return;
        }
        
        const success = await pywebview.api.设置默认组为Windows默认光标();
        if (success) {
            console.log('已将默认组设置为Windows默认光标');
            button.textContent = "设置成功";
        } else {
            console.log('设置默认组失败');
            button.textContent = "设置失败";
        }
    } catch (e) {
        console.error('设置默认组失败:', e);
        button.textContent = "设置失败";
    } finally {
        // 3秒后恢复按钮状态
        setTimeout(() => {
            button.textContent = originalText;
            button.disabled = false;
        }, 3000);
    }
}

function showModal(type) {
    // 创建模态框元素
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    
    // 创建模态框内容
    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content';
    
    // 设置模态框内容
    if (type === 'license') {
        modalContent.innerHTML = `
            <div class="modal-header">
                <h3>许可证</h3>
            </div>
            <div class="modal-body scrollable">
                <h3># Project Licensing Notice</h3>
                <p></p>
                <p>Copyright (c) 2025, CIF3. All rights reserved.</p>
                <p></p>
                <p>This project is distributed under a combined licensing model:</p>
                <p></p>
                <h4>## 1. Core Logic & Original Features</h4>
                <p>The core functionality, original algorithms, and unique features of this software are licensed under:</p>
                <p>Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)</p>
                <p><code>https://creativecommons.org/licenses/by-nc-sa/4.0/</code></p>
                <p></p>
                <h4>## 2. Wallpaper Engine Integration & API Modules</h4>
                <p>The modules specifically designed for interacting with Wallpaper Engine, process monitoring (psutil-based logic), and system handle operations are licensed under:</p>
                <p>The BSD 3-Clause License</p>
                <p><code>https://opensource.org/licenses/BSD-3-Clause</code></p>
                <p></p>
                <h4>## 3. Third-Party Support or Miscellaneous Modules</h4>
                <p>Certain files in this project are licensed under:</p>
                <p>The MIT License (MIT)</p>
                <p><code>https://opensource.org/licenses/MIT</code></p>
                <p></p>
                <p>(See individual file headers for the specific license governing each file.)</p>
                <p></p>
                <h4>---</h4>
                <p></p>
                <h4>## BSD 3-Clause License Text (for Integration Modules)</h4>
                <p>Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:</p>
                <p>1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.</p>
                <p>2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.</p>
                <p>3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.</p>
                <p></p>
                <h4>---</h4>
                <p></p>
                <h4>## Important Exceptions & Disclaimers</h4>
                <p>- WALLPAPER CONTENT: This project identifies and retrieves metadata of wallpapers. All wallpaper assets, IDs, and media remain the property of their respective copyright holders on Steam Workshop.</p>
                <p>- THIRD-PARTY LIBRARIES: Libraries such as 'psutil' are subject to their own respective licenses.</p>
                <p>- NO ENDORSEMENT: This project is not affiliated with or endorsed by Wallpaper Engine or Steam.</p>
                <p></p>
                <h4>---</h4>
                <p></p>
                <p>Note: This project changed its license starting from Alpha2.0.</p>
                <p>Alpha2.0 and later: Licensed under CC BY-NC-SA 4.0 (Core) & BSD 3-Clause (Integration). Commercial use without authorization is prohibited.</p>
                <p>Alpha1.2 and earlier: Remains under BSD 3-Clause. Permissions granted under the previous license for older versions are still valid.</p>
            </div>
        `;
    } else if (type === 'thirdparty') {
        modalContent.innerHTML = `
            <div class="modal-header">
                <h3>第三方库</h3>
            </div>
            <div class="modal-body scrollable" id="thirdPartyContent">
                <p>加载中...</p>
            </div>
        `;
        
        // 加载第三方库许可证信息
        if (typeof pywebview !== 'undefined' && pywebview.api) {
            pywebview.api.get_third_party_notices().then(content => {
                const contentDiv = document.getElementById('thirdPartyContent');
                if (contentDiv) {
                    // 将文本内容转换为HTML，保留换行
                    const htmlContent = content.replace(/\n/g, '<br>');
                    contentDiv.innerHTML = `<pre style="white-space: pre-wrap; font-family: monospace;">${content}</pre>`;
                }
            }).catch(error => {
                console.error('获取第三方库信息失败:', error);
                const contentDiv = document.getElementById('thirdPartyContent');
                if (contentDiv) {
                    contentDiv.innerHTML = '<p>获取第三方库信息失败</p>';
                }
            });
        }
    }
    
    // 将内容添加到模态框
    modal.appendChild(modalContent);
    
    // 添加到文档
    document.body.appendChild(modal);
    
    // 点击模态框外部关闭
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    });
}