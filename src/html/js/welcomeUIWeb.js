// 等待 DOM 加载完成
window.onload = function() {
    const autoFindBtn = document.getElementById('autoFindBtn');
    const browseBtn = document.getElementById('browseBtn');
    const continueBtn = document.getElementById('continueBtn');
    const pathInput = document.getElementById('pathInput');
    const folderInput = document.getElementById('folderInput');
    
    // 检查 pywebview 是否可用
    function checkPyWebView() {
        return typeof window.pywebview !== 'undefined' && window.pywebview.api;
    }
    
    // 更新确认按钮状态
    function updateContinueButton(isValid) {
        if (isValid) {
            continueBtn.disabled = false;
            continueBtn.classList.remove('btn-disabled');
            continueBtn.classList.add('btn-success');
        } else {
            continueBtn.disabled = true;
            continueBtn.classList.remove('btn-success');
            continueBtn.classList.add('btn-disabled');
        }
    }
    
    // 添加输入框事件监听
    let debounceTimer;
    pathInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            handlePathValidation.call(this);
        }, 500); // 500ms防抖
    });
    
    // 文件夹选择事件
    folderInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            const folderPath = e.target.files[0].webkitRelativePath.split('/')[0];
            const fullPath = e.target.files[0].path;
            const path = fullPath.substring(0, fullPath.indexOf(folderPath));
            pathInput.value = path;
            // 验证路径并设置样式
            handlePathValidation.call(pathInput);
        }
    });
    
    // 自动查找按钮点击事件
    autoFindBtn.addEventListener('click', function() {
        if (!checkPyWebView()) {
            return;
        }
        
        autoFindBtn.disabled = true;
        autoFindBtn.textContent = '🔍 正在查找...\n(steam)  ';
        autoFindBtn.classList.add('loading');
        
        // 调用 Python 端的自动查找方法
        window.pywebview.api.auto_find_wallpaper_engine().then(function(result) {
            autoFindBtn.disabled = false;
            autoFindBtn.textContent = '⚙️ 自动查找 (Steam)';
            autoFindBtn.classList.remove('loading');
            
            if (result.success && result.path) {
                pathInput.value = result.path;
                // 验证路径并设置样式
                handlePathValidation.call(pathInput);
            }
        }).catch(function(error) {
            autoFindBtn.disabled = false;
            autoFindBtn.textContent = '⚙️ 自动查找 (Steam)';
            autoFindBtn.classList.remove('loading');
        });
    });
    
    // 浏览文件夹按钮点击事件
    browseBtn.addEventListener('click', function() {
        // 使用 HTML5 的文件选择功能
        folderInput.click();
    });
    
    // 确认并继续按钮点击事件
    continueBtn.addEventListener('click', function() {
        const path = pathInput.value.trim();
        
        if (!path) {
            return;
        }
        
        if (!checkPyWebView()) {
            return;
        }
        
        window.pywebview.api.validate_path(path).then(function(result) {
            if (result.success) {
                window.pywebview.api.confirm_path(path);
            }
        }).catch(function(error) {
        });
    });
    
    // 路径验证函数
    function handlePathValidation() {
        const pathInput = this;
        const path = pathInput.value.trim();
        
        if (!path) {
            // 清空路径时恢复默认状态
            pathInput.classList.remove('valid', 'invalid');
            updateContinueButton(false);
            return;
        }
        
        if (!checkPyWebView()) {
            return;
        }
        
        // 调用 Python 端的路径验证方法
        window.pywebview.api.validate_path(path).then(function(result) {
            // 根据验证结果设置样式类
            if (result.success) {
                pathInput.classList.remove('invalid');
                pathInput.classList.add('valid');
                updateContinueButton(true);
            } else {
                pathInput.classList.remove('valid');
                pathInput.classList.add('invalid');
                updateContinueButton(false);
            }
        }).catch(function(error) {
            console.error("验证路径失败:", error);
            pathInput.classList.remove('valid');
            pathInput.classList.add('invalid');
            updateContinueButton(false);
        });
    }
    
    // 初始化确认按钮状态
    updateContinueButton(false);
    
    // 页面加载时自动执行一次查找
    setTimeout(function() {
        if (checkPyWebView()) {
            autoFindBtn.click();
        }
    }, 500);
};
