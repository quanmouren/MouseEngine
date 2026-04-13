// upgradeConfirm.js

window.addEventListener('DOMContentLoaded', () => {
    loadOldVersions();
    
    document.getElementById('upgradeBtn').addEventListener('click', handleUpgrade);
    document.getElementById('skipBtn').addEventListener('click', handleSkip);
});

async function loadOldVersions() {
    if (typeof pywebview === 'undefined' || !pywebview.api) {
        setTimeout(loadOldVersions, 100);
        return;
    }

    try {
        // 获取当前版本
        const currentVersion = await pywebview.api.get_current_version();
        
        // 获取旧版本列表
        const versions = await pywebview.api.get_old_versions();
        
        // 更新标题为当前版本
        const oldVersionTitle = document.getElementById('oldVersionTitle');
        if (oldVersionTitle) {
            oldVersionTitle.textContent = `(${currentVersion})`;
        }
        
        renderVersionList(versions);
    } catch (e) {
        console.error('获取旧版本失败:', e);
        document.getElementById('versionList').innerHTML = '<p style="color: #ef4444;">加载失败</p>';
    }
}

function renderVersionList(versions) {
    const container = document.getElementById('versionList');
    
    if (!versions || versions.length === 0) {
        container.innerHTML = '<p style="color: #10b981; text-align: center;">没有发现旧版本</p>';
        document.getElementById('upgradeBtn').textContent = '确认';
        return;
    }

    // 更新提示文字中的旧版本号
    const oldVersionText = document.getElementById('oldVersionText');
    if (oldVersionText && versions[0].version) {
        oldVersionText.textContent = `(${versions[0].version})`;
    }

    // 不显示版本列表，只显示提示信息
    container.innerHTML = '';
}

async function handleUpgrade() {
    const btn = document.getElementById('upgradeBtn');
    const originalText = btn.textContent;
    btn.textContent = '正在清理...';
    btn.disabled = true;

    try {
        const result = await pywebview.api.cleanup_old_versions();
        
        if (result.success) {
            btn.textContent = '清理完成!';
            setTimeout(() => {
                if (pywebview.api.on_upgrade_clicked) {
                    pywebview.api.on_upgrade_clicked();
                } else {
                    pywebview.api.close_window();
                }
            }, 1000);
        } else {
            btn.textContent = '清理失败';
            btn.disabled = false;
            console.error('清理失败:', result.message);
        }
    } catch (e) {
        console.error('清理旧版本失败:', e);
        btn.textContent = '清理失败';
        btn.disabled = false;
    }
}

function handleSkip() {
    if (typeof pywebview !== 'undefined' && pywebview.api) {
        if (pywebview.api.on_skip_clicked) {
            pywebview.api.on_skip_clicked();
        } else {
            pywebview.api.close_window();
        }
    }
}
