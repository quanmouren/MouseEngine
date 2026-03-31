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
        
        // 添加右键点击事件
        groupCard.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            showContextMenu(e, groupName);
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
        <div class="position-row" oncontextmenu="showInputContextMenu(event, '${k}')">
            <div class="thumb-preview" id="prev-${k}">
                <img src="${DEFAULT_IMAGES[k]}" alt="${k}">
            </div>
            <input id="input-${k}" class="position-input" placeholder="${k}" value="">
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

    for (const k of CURSOR_KEYS) {
        const input = document.getElementById(`input-${k}`);
        input.value = '';

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
        const input = document.getElementById(`input-${k}`);
        if (data[k] && data[k].trim() !== '') {
            input.value = data[k];
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
            const input = document.getElementById(`input-${key}`);
            input.value = path;
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
    // 组名输入弹窗
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

    // 重命名弹窗
    const renameModal = document.getElementById('renameModal');
    const renameCancelBtn = document.getElementById('renameCancelBtn');
    const renameConfirmBtn = document.getElementById('renameConfirmBtn');
    const renameInput = document.getElementById('renameInput');

    // 取消按钮点击事件
    renameCancelBtn.addEventListener('click', hideRenameModal);

    // 确认按钮点击事件
    renameConfirmBtn.addEventListener('click', confirmRenameGroup);

    // 点击弹窗外层取消
    renameModal.addEventListener('click', (e) => {
        if (e.target === renameModal) {
            hideRenameModal();
        }
    });

    // 按下 Enter 键确认
    renameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            confirmRenameGroup();
        }
    });

    // 按下 Escape 键取消
    renameInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideRenameModal();
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
    // 点击外部关闭右键菜单
    if (!e.target.closest('.context-menu') && !e.target.closest('.grid-item')) {
        hideContextMenu();
    }
    if (!e.target.closest('#inputContextMenu')) {
        hideInputContextMenu();
    }
});

// 显示右键菜单
function showContextMenu(e, groupName) {
    const contextMenu = document.getElementById('contextMenu');
    const deleteItem = document.getElementById('deleteGroupItem');
    
    // 计算菜单位置，考虑content-left区域的滚动偏移
    const contentLeft = document.querySelector('.content-left');
    const rect = e.currentTarget.getBoundingClientRect();
    const scrollLeft = contentLeft ? contentLeft.scrollLeft : 0;
    const scrollTop = contentLeft ? contentLeft.scrollTop : 0;
    
    // 获取content-left的位置
    const contentLeftRect = contentLeft ? contentLeft.getBoundingClientRect() : { left: 0, top: 0 };
    
    let left = e.clientX;
    let top = e.clientY;
    
    // 检查菜单是否会超出视口
    const menuWidth = contextMenu.offsetWidth || 200;
    const menuHeight = contextMenu.offsetHeight || 50;
    
    if (left + menuWidth > window.innerWidth) {
        left = window.innerWidth - menuWidth;
    }
    
    if (top + menuHeight > window.innerHeight) {
        top = window.innerHeight - menuHeight;
    }
    
    // 确保菜单在视口内
    left = Math.max(0, left);
    top = Math.max(0, top);
    
    // 设置菜单位置
    contextMenu.style.left = left + 'px';
    contextMenu.style.top = top + 'px';
    contextMenu.style.position = 'fixed';
    
    const renameItem = document.getElementById('renameGroupItem');
    
    // 如果是默认组，禁用删除选项
    if (groupName === '默认组') {
        deleteItem.classList.add('disabled');
        deleteItem.onclick = null;
    } else {
        deleteItem.classList.remove('disabled');
        deleteItem.onclick = () => handleDeleteGroup(groupName);
    }
    
    // 为所有组添加重命名选项
    renameItem.classList.remove('disabled');
    renameItem.onclick = () => handleRenameGroup(groupName);
    
    // 显示菜单
    contextMenu.style.display = 'block';
    
    // 添加滚动事件监听器，滚动时关闭菜单
    if (contentLeft) {
        contentLeft.addEventListener('scroll', hideContextMenu);
    }
    
    // 添加鼠标离开事件监听器，离开画面时关闭菜单
    document.addEventListener('mouseleave', hideContextMenu);
}

// 更新右键菜单位置
function updateContextMenuPosition() {
    const contextMenu = document.getElementById('contextMenu');
    if (contextMenu.style.display === 'block') {
        // 保持菜单在视口中的相对位置
        const rect = contextMenu.getBoundingClientRect();
        let left = rect.left;
        let top = rect.top;
        
        // 检查菜单是否会超出视口
        const menuWidth = contextMenu.offsetWidth || 200;
        const menuHeight = contextMenu.offsetHeight || 50;
        
        if (left + menuWidth > window.innerWidth) {
            left = window.innerWidth - menuWidth;
        }
        
        if (top + menuHeight > window.innerHeight) {
            top = window.innerHeight - menuHeight;
        }
        
        // 确保菜单在视口内
        left = Math.max(0, left);
        top = Math.max(0, top);
        
        contextMenu.style.left = left + 'px';
        contextMenu.style.top = top + 'px';
    }
}

// 隐藏右键菜单
function hideContextMenu() {
    const contextMenu = document.getElementById('contextMenu');
    contextMenu.style.display = 'none';
    
    // 移除事件监听器
    const contentLeft = document.querySelector('.content-left');
    if (contentLeft) {
        contentLeft.removeEventListener('scroll', hideContextMenu);
    }
    document.removeEventListener('mouseleave', hideContextMenu);
}

// 显示输入框右键菜单
function showInputContextMenu(e, key) {
    e.preventDefault();
    const contextMenu = document.getElementById('inputContextMenu');
    contextMenu.style.left = `${e.clientX}px`;
    contextMenu.style.top = `${e.clientY}px`;
    contextMenu.style.display = 'block';

    const clearItem = document.getElementById('clearInputItem');
    clearItem.onclick = () => clearInput(key);
}

// 隐藏输入框右键菜单
function hideInputContextMenu() {
    const contextMenu = document.getElementById('inputContextMenu');
    if (contextMenu) {
        contextMenu.style.display = 'none';
    }
}

// 清空输入框内容
async function clearInput(key) {
    const input = document.getElementById(`input-${key}`);
    if (input) {
        input.value = '';
    }
    await setPreviewImage(key, '');
    hideInputContextMenu();
}

// 处理删除组操作
async function handleDeleteGroup(groupName) {
    if (!window.pywebview) {
        alert('此功能仅在应用内可用');
        hideContextMenu();
        return;
    }
    
    try {
        // 调用Python API删除组
        const result = await pywebview.api.delete_group(groupName);
        if (result.status === 'success') {
            // 刷新组列表和预览网格
            await refreshGroups();
            await renderPreviewGrid();
            
            // 如果当前选中的是被删除的组，切换到默认组
            if (currentOriginalGroup === groupName) {
                await selectGroup('默认组');
            }
            
            showNotification('删除成功', 'success');
        } else {
            showNotification(result.msg, 'error');
        }
    } catch (e) {
        console.error('删除组失败', e);
        showNotification('删除失败，请重试', 'error');
    } finally {
        hideContextMenu();
    }
}

// 处理重命名组操作
function handleRenameGroup(groupName) {
    if (!window.pywebview) {
        alert('此功能仅在应用内可用');
        hideContextMenu();
        return;
    }
    
    // 显示重命名弹窗
    showRenameModal(groupName);
    hideContextMenu();
}

// 显示重命名弹窗
function showRenameModal(groupName) {
    const modal = document.getElementById('renameModal');
    const input = document.getElementById('renameInput');
    
    // 设置输入框默认值为当前组名
    input.value = groupName;
    
    // 存储当前组名，用于后续操作
    modal.dataset.groupName = groupName;
    
    // 显示弹窗
    modal.style.display = 'flex';
    
    // 自动聚焦输入框
    setTimeout(() => {
        input.focus();
        // 选中输入框内容，方便直接修改
        input.select();
    }, 100);
}

// 隐藏重命名弹窗
function hideRenameModal() {
    const modal = document.getElementById('renameModal');
    modal.style.display = 'none';
}

// 确认重命名组
async function confirmRenameGroup() {
    const modal = document.getElementById('renameModal');
    const input = document.getElementById('renameInput');
    const newGroupName = input.value.trim();
    const oldGroupName = modal.dataset.groupName;
    
    if (!newGroupName) {
        alert('组名不能为空');
        return;
    }
    
    // 验证组名
    if (!validateGroupName(newGroupName)) {
        alert('组名不能包含特殊字符，且长度不能超过20个字符');
        return;
    }
    
    // 检查组名是否已存在
    const existingGroups = await pywebview.api.get_existing_groups();
    if (existingGroups.includes(newGroupName) && newGroupName !== oldGroupName) {
        const confirmOverwrite = confirm('该组名已存在，是否覆盖？');
        if (!confirmOverwrite) {
            return;
        }
    }
    
    // 隐藏弹窗
    hideRenameModal();
    
    try {
        // 调用Python API重命名组
        const result = await pywebview.api.rename_group(oldGroupName, newGroupName);
        if (result.status === 'success') {
            // 刷新组列表和预览网格
            await refreshGroups();
            await renderPreviewGrid();
            
            // 如果当前选中的是被重命名的组，切换到新组名
            if (currentOriginalGroup === oldGroupName) {
                await selectGroup(newGroupName);
            }
            
            showNotification('重命名成功', 'success');
        } else {
            showNotification(result.msg, 'error');
        }
    } catch (e) {
        console.error('重命名组失败', e);
        showNotification('重命名失败，请重试', 'error');
    }
}