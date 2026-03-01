const CURSOR_KEYS = ["Arrow","Help","AppStarting","Wait","Crosshair","IBeam","Handwriting","No","SizeNS","SizeWE","SizeNWSE","SizeNESW","SizeAll","Hand","UpArrow"];
const DEFAULT_IMAGES = {
    "Arrow": "image/aero_arrow.png",
    "Help": "image/aero_helpsel.png",
    "AppStarting": "image/aero_working_xl.png",
    "Wait": "image/aero_busy_xl.png",
    "Crosshair": "image/cross_il.png",
    "IBeam": "image/beam_rl.png",
    "Handwriting": "image/aero_pen.png",
    "No": "image/aero_unavail.png",
    "SizeNS": "image/aero_ns.png",
    "SizeWE": "image/aero_ew.png",
    "SizeNWSE": "image/aero_nwse.png",
    "SizeNESW": "image/aero_nesw.png",
    "SizeAll": "image/aero_move.png",
    "Hand": "image/aero_link.png",
    "UpArrow": "image/aero_up.png"
};

let currentOriginalGroup = null;

document.addEventListener('DOMContentLoaded', async () => {
    renderRows();               // 右侧列表
    await renderPreviewGrid();   
    
    // 初始化悬浮窗事件监听器
    initModalListeners();

    if (window.pywebview) {
        await refreshGroups();
        await renderPreviewGrid(); // 刷新组列表后重新渲染列表
        await selectGroup('默认'); // 默认加载默认组
    } else {
        window.addEventListener('pywebviewready', async () => {
            await refreshGroups();
            await renderPreviewGrid(); // 刷新组列表后重新渲染列表
            await selectGroup('默认'); // 默认加载默认组
        });
    }
});

async function renderPreviewGrid() {
    const grid = document.getElementById('previewGrid');
    if (!grid) return;
    
    // 清空列表
    grid.innerHTML = '';
    
    // 获取所有鼠标组
    const groups = window.pywebview ? await pywebview.api.get_existing_groups() : ['默认组'];
    
    // 为每个组生成一个列表项
    for (const groupName of groups) {
        // 创建组卡片
        const groupCard = document.createElement('div');
        groupCard.className = 'grid-item';
        groupCard.dataset.group = groupName;
        
        // 组名称
        const nameLabel = document.createElement('div');
        nameLabel.className = 'group-name';
        nameLabel.textContent = groupName;
        groupCard.appendChild(nameLabel);
        
        // 加载组配置
        let groupConfig = {};
        if (window.pywebview) {
            try {
                groupConfig = await pywebview.api.load_group_config(groupName);
            } catch (e) {
                console.error('加载组配置失败:', e);
            }
        }
        
        // 主指针
        const mainSlot = document.createElement('div');
        mainSlot.className = 'cursor-slot main';
        const mainImg = document.createElement('img');
        mainImg.id = `grid-img-${groupName}-${CURSOR_KEYS[0]}`;
        mainImg.alt = CURSOR_KEYS[0];
        mainImg.onerror = function() {
            this.src = `data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 60 60"%3E%3Crect width="60" height="60" fill="%23334155"/%3E%3Ctext x="10" y="35" font-size="12" fill="%23fff"%3E${CURSOR_KEYS[0]}%3C/text%3E%3C/svg%3E`;
        };
        mainSlot.appendChild(mainImg);
        groupCard.appendChild(mainSlot);
        
        // 其他指针容器
        const slotsContainer = document.createElement('div');
        slotsContainer.className = 'cursor-slots-container';
        
        // 其他指针
        for (let i = 1; i < CURSOR_KEYS.length; i++) {
            const slot = document.createElement('div');
            slot.className = 'cursor-slot';
            const img = document.createElement('img');
            img.id = `grid-img-${groupName}-${CURSOR_KEYS[i]}`;
            img.alt = CURSOR_KEYS[i];
            img.onerror = function() {
                this.src = `data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40"%3E%3Crect width="40" height="40" fill="%23334155"/%3E%3Ctext x="5" y="25" font-size="10" fill="%23fff"%3E${CURSOR_KEYS[i]}%3C/text%3E%3C/svg%3E`;
            };
            slot.appendChild(img);
            slotsContainer.appendChild(slot);
        }
        
        groupCard.appendChild(slotsContainer);
        
        // 添加点击事件
        groupCard.addEventListener('click', async () => {
            await selectGroup(groupName);
        });
        
        // 添加到列表
        grid.appendChild(groupCard);
        
        // 加载预览图片
        for (const key of CURSOR_KEYS) {
            const imgElement = document.getElementById(`grid-img-${groupName}-${key}`);
            if (imgElement) {
                const cursorPath = groupConfig[key] || '';
                if (cursorPath && window.pywebview) {
                    try {
                        const previewPath = await pywebview.api.get_preview_base64(cursorPath);
                        if (previewPath) {
                            imgElement.src = previewPath;
                        } else {
                            if (groupName === '默认组') {
                                imgElement.src = DEFAULT_IMAGES[key];
                            } else {
                                imgElement.src = DEFAULT_IMAGES[key];
                            }
                        }
                    } catch (e) {
                        console.error('获取预览失败:', e);
                        imgElement.src = DEFAULT_IMAGES[key];
                    }
                } else {
                    imgElement.src = DEFAULT_IMAGES[key];
                }
            }
        }
    }
}

function renderRows() {
    const container = document.getElementById('cursorList');
    if (!container) return;
    
    container.innerHTML = CURSOR_KEYS.map(k => `
        <div class="position-row">
            <div class="thumb-preview" id="prev-${k}">
                <img src="${DEFAULT_IMAGES[k]}" alt="${k}">
            </div>
            <input id="input-${k}" class="position-input" readonly placeholder="${k}" value="">
            <button class="browse-button" onclick="handleBrowse('${k}')">浏览</button>
        </div>
    `).join('');
}

async function setPreviewImage(key, path) {
    // 如果path为空，使用默认图片
    const imagePath = path && path.trim() !== '' ? path : DEFAULT_IMAGES[key];
    
    if (window.pywebview && path && path !== DEFAULT_IMAGES[key]) {
        try {
            const previewPath = await pywebview.api.get_preview_base64(path);
            if (previewPath) {
                // 更新右侧缩略图
                const rightPreview = document.getElementById(`prev-${key}`);
                if (rightPreview) {
                    rightPreview.innerHTML = `<img src="${previewPath}" alt="${key}" onerror="this.src='${DEFAULT_IMAGES[key]}'">`;
                }
                // 只更新当前选中组的左侧列表图片
                if (currentOriginalGroup) {
                    const currentGroupImg = document.getElementById(`grid-img-${currentOriginalGroup}-${key}`);
                    if (currentGroupImg) {
                        currentGroupImg.src = previewPath;
                    }
                }
                return;
            }
        } catch (e) {
            console.warn("获取预览失败，使用直接路径", e);
        }
    }
    
    const rightPreview = document.getElementById(`prev-${key}`);
    if (rightPreview) {
        rightPreview.innerHTML = `<img src="${imagePath}" alt="${key}" onerror="this.src='${DEFAULT_IMAGES[key]}'">`;
    }
    if (currentOriginalGroup) {
        const currentGroupImg = document.getElementById(`grid-img-${currentOriginalGroup}-${key}`);
        if (currentGroupImg) {
            currentGroupImg.src = imagePath;
        }
    }
}

// 兼容旧的updatePreview调用
async function updatePreview(key, path) {
    await setPreviewImage(key, path);
}

async function refreshGroups() {
    if (!window.pywebview) return;
    const groups = await pywebview.api.get_existing_groups();
    const dropdown = document.getElementById('groupDropdown');
    dropdown.innerHTML = '';

    const newOpt = document.createElement('div');
    newOpt.className = 'dropdown-option';
    newOpt.innerText = '+ 新建鼠标组';
    newOpt.onclick = () => selectGroup(null);
    dropdown.appendChild(newOpt);

    groups.forEach(g => {
        const opt = document.createElement('div');
        opt.className = 'dropdown-option';
        opt.innerText = g;
        opt.onclick = () => selectGroup(g);
        dropdown.appendChild(opt);
    });
}

async function selectGroup(name) {
    currentOriginalGroup = name;
    document.getElementById('groupDropdown').style.display = 'none';

    // 更新标题
    const titleElement = document.getElementById('editorTitle');
    if (titleElement) {
        titleElement.textContent = name ? `编辑鼠标组：${name}` : '编辑鼠标组：新建组';
    }

    // 重置所有输入框和预览
    for (const k of CURSOR_KEYS) {
        document.getElementById(`input-${k}`).value = '';
        const rightPreview = document.getElementById(`prev-${k}`);
        if (rightPreview) {
            rightPreview.innerHTML = `<img src="${DEFAULT_IMAGES[k]}" alt="${k}">`;
        }
    }

    if (!name) {  // 新建组
        return;
    }

    // 加载组数据
    const data = await pywebview.api.load_group_config(name);
    for (const k of CURSOR_KEYS) {
        if (data[k] && data[k].trim() !== '') {
            document.getElementById(`input-${k}`).value = data[k];
            await setPreviewImage(k, data[k]);
        }
    }
}

// 保存数据
async function saveData() {
    if (!window.pywebview) {
        alert('此功能仅在应用内可用');
        return;
    }

    // 获取保存按钮并显示加载状态
    const saveButton = document.querySelector('.save-button');
    const originalButtonText = saveButton.textContent;
    saveButton.textContent = '保存中...';
    saveButton.disabled = true;

    try {
        const data = {};
        for (const key of CURSOR_KEYS) {
            data[key] = document.getElementById(`input-${key}`).value;
        }

        // 获取当前组名
        const titleElement = document.getElementById('editorTitle');
        let groupName = titleElement.textContent.replace('编辑鼠标组：', '');
        
        if (groupName === '新建组') {
            groupName = prompt('请输入新组名：');
            if (!groupName) {
                saveButton.textContent = originalButtonText;
                saveButton.disabled = false;
                return;
            }
            
            // 验证组名
            if (!validateGroupName(groupName)) {
                alert('组名不能包含特殊字符，且长度不能超过20个字符');
                saveButton.textContent = originalButtonText;
                saveButton.disabled = false;
                return;
            }
            
            // 检查组名是否已存在
            const existingGroups = await pywebview.api.get_existing_groups();
            if (existingGroups.includes(groupName)) {
                const confirmOverwrite = confirm('该组名已存在，是否覆盖？');
                if (!confirmOverwrite) {
                    saveButton.textContent = originalButtonText;
                    saveButton.disabled = false;
                    return;
                }
            }
        }

        // 验证组名
        if (!validateGroupName(groupName)) {
            alert('组名格式无效');
            saveButton.textContent = originalButtonText;
            saveButton.disabled = false;
            return;
        }

        const result = await pywebview.api.save_group_config(groupName, data, currentOriginalGroup);
        if (result.status === 'success') {
            // 更新当前组信息
            currentOriginalGroup = groupName;
            titleElement.textContent = `编辑鼠标组：${groupName}`;
            
            // 刷新组列表和预览网格
            await refreshGroups();
            await renderPreviewGrid();
        } else {
            // 显示错误消息
            alert(result.msg);
        }
    } catch (e) {
        console.error('保存失败', e);
        alert('保存失败，请重试');
    } finally {
        // 恢复保存按钮状态
        saveButton.textContent = originalButtonText;
        saveButton.disabled = false;
    }
}

// 验证组名
function validateGroupName(name) {
    if (!name || name.trim() === '') {
        return false;
    }
    if (name.length > 20) {
        return false;
    }
    // 检查是否包含特殊字符
    const regex = /^[\u4e00-\u9fa5a-zA-Z0-9_]+$/;
    return regex.test(name);
}

// 显示通知
function showNotification(message, type) {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 显示通知
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateY(0)';
    }, 10);
    
    // 3秒后隐藏通知
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// 浏览文件
async function handleBrowse(key) {
    if (!window.pywebview) {
        alert('此功能仅在应用内可用');
        return;
    }

    try {
        const path = await pywebview.api.open_file_dialog();
        if (path) {
            document.getElementById(`input-${key}`).value = path;
            await setPreviewImage(key, path);
        }
    } catch (e) {
        console.error('浏览失败', e);
    }
}

// 显示组名输入悬浮窗
function showGroupNameModal() {
    const modal = document.getElementById('groupNameModal');
    const input = document.getElementById('groupNameInput');
    
    // 清空输入框
    input.value = '';
    
    // 显示悬浮窗
    modal.style.display = 'flex';
    
    // 自动聚焦输入框
    setTimeout(() => {
        input.focus();
    }, 100);
}

// 隐藏组名输入悬浮窗
function hideGroupNameModal() {
    const modal = document.getElementById('groupNameModal');
    modal.style.display = 'none';
}

// 确认创建组
async function confirmCreateGroup() {
    const input = document.getElementById('groupNameInput');
    const groupName = input.value.trim();
    
    if (!groupName) {
        alert('组名不能为空');
        return;
    }

    // 验证组名
    if (!validateGroupName(groupName)) {
        alert('组名不能包含特殊字符，且长度不能超过20个字符');
        return;
    }

    // 检查组名是否已存在
    const existingGroups = await pywebview.api.get_existing_groups();
    if (existingGroups.includes(groupName)) {
        const confirmOverwrite = confirm('该组名已存在，是否覆盖？');
        if (!confirmOverwrite) {
            return;
        }
    }

    // 隐藏悬浮窗
    hideGroupNameModal();

    // 创建空白数据（15个空项）
    const emptyData = {};
    for (const key of CURSOR_KEYS) {
        emptyData[key] = '';
    }

    try {
        const result = await pywebview.api.save_group_config(groupName, emptyData);
        if (result.status === 'success') {
            // 刷新组列表和预览网格
            await refreshGroups();
            await renderPreviewGrid();
            // 选择新创建的组
            await selectGroup(groupName);
        } else {
            alert(result.msg);
        }
    } catch (e) {
        console.error('创建空白组失败', e);
        alert('创建空白组失败，请重试');
    }
}

// 新建空白组
function createEmptyGroup() {
    if (!window.pywebview) {
        alert('此功能仅在应用内可用');
        return;
    }

    // 显示组名输入悬浮窗
    showGroupNameModal();
}

// 导入组
async function importGroup() {
    if (!window.pywebview) {
        alert('此功能仅在应用内可用');
        return;
    }

    try {
        const result = await pywebview.api.导入组();
        if (result) {
            // 如果返回true，刷新组列表
            await refreshGroups();
            await renderPreviewGrid();
        }
        // 如果返回false，跳过刷新
    } catch (e) {
        console.error('导入组失败', e);
        alert('导入组失败，请重试');
    }
}

// 初始化悬浮窗事件监听器
function initModalListeners() {
    const modal = document.getElementById('groupNameModal');
    const cancelBtn = document.getElementById('cancelBtn');
    const confirmBtn = document.getElementById('confirmBtn');
    const input = document.getElementById('groupNameInput');

    // 取消按钮点击事件
    cancelBtn.addEventListener('click', hideGroupNameModal);

    // 确认按钮点击事件
    confirmBtn.addEventListener('click', confirmCreateGroup);

    // 点击弹窗外层取消
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            hideGroupNameModal();
        }
    });

    // 按下 Enter 键确认
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            confirmCreateGroup();
        }
    });

    // 按下 Escape 键取消
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideGroupNameModal();
        }
    });
}

// 显示下拉框
function showDropdown() {
    const dropdown = document.getElementById('groupDropdown');
    dropdown.style.display = 'block';
}

// 点击外部关闭下拉框
document.addEventListener('click', e => {
    if (!e.target.closest('.header-row')) {
        document.getElementById('groupDropdown').style.display = 'none';
    }
});