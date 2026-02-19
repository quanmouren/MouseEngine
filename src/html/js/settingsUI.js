window.addEventListener('DOMContentLoaded', function() {
    initSettingsPage();
});

function initSettingsPage() {
    const menuItems = document.querySelectorAll('.settings-nav-item');
    menuItems.forEach(item => {
        item.addEventListener('click', function() {
            menuItems.forEach(menuItem => {
                menuItem.classList.remove('active');
            });
            this.classList.add('active');
            const menuText = this.textContent;
            updateSettingsContent(menuText);
        });
    });
    loadSettings();
}

function updateSettingsContent(menuText) {
    const settingsTitle = document.querySelector('.settings-title');
    const settingsSection = document.querySelector('.settings-section');
    
    if (settingsTitle) {
        settingsTitle.textContent = menuText;
    }
    
    if (settingsSection) {
        switch (menuText) {
            case '基本设置':
                settingsSection.innerHTML = `
                    <div class="settings-section-title">应用设置</div>
                    <div class="settings-item">
                        <div class="settings-label">启动时自动运行</div>
                        <div class="settings-control">
                            <input type="checkbox" id="autoStart">
                        </div>
                    </div>
                    <div class="settings-item settings-item-double-row">
                        <div class="settings-label-row">
                            <div class="settings-label">Wallpaper Engine路径</div>
                        </div>
                        <div class="settings-control-row">
                            <input type="text" class="custom-input custom-input-stretch" placeholder="请输入路径">
                            <div class="settings-buttons">
                                <button class="settings-btn">自动获取</button>
                                <button class="settings-btn">预览</button>
                            </div>
                        </div>
                    </div>
                    <div class="settings-item">
                        <div class="settings-label">启用默认光标</div>
                        <div class="settings-control">
                            <input type="checkbox" id="enableDefaultCursor">
                        </div>
                    </div>
                `;
                break;
            case '高级设置':
                settingsSection.innerHTML = `
                    <div class="settings-section-title">高级选项</div>
                    <div class="settings-item">
                        <div class="settings-label">缓存清理</div>
                        <div class="settings-control">
                            <div class="header-btn">清理</div>
                        </div>
                    </div>
                `;
                break;
            case '关于':
                settingsSection.innerHTML = `
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
                        <div class="settings-value settings-link" onclick="showLicenseModal()">查看</div>
                    </div>
                    <div class="settings-item">
                        <div class="settings-label">第三方许可证</div>
                        <div class="settings-value settings-link" onclick="showThirdPartyLicenseModal()">查看</div>
                    </div>
                `;
                break;
        }
    }
}

function loadSettings() {
    const autoStart = document.getElementById('autoStart');
    if (autoStart) {
        autoStart.checked = false;
    }
}

function saveSettings() {
    console.log('设置已保存');
}

function showLicenseModal() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'licenseModal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title">许可证</h2>
                <span class="close" onclick="closeModal('licenseModal')">&times;</span>
            </div>
            <div class="modal-body">
                <pre>
111
                </pre>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    modal.style.display = 'block';
    window.onclick = function(event) {
        if (event.target == modal) {
            closeModal('licenseModal');
        }
    }
}

function showThirdPartyLicenseModal() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'thirdPartyLicenseModal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title">第三方许可证</h2>
                <span class="close" onclick="closeModal('thirdPartyLicenseModal')">&times;</span>
            </div>
            <div class="modal-body">
                <h3>第三方库许可证</h3>
                <p>本项目使用了以下第三方库：</p>
                <ul>
                    <li><strong>占位符</strong> - 占位符许可证</li>
                </ul>
                <p>123</p>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    modal.style.display = 'block';
    window.onclick = function(event) {
        if (event.target == modal) {
            closeModal('thirdPartyLicenseModal');
        }
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.removeChild(modal);
    }
}