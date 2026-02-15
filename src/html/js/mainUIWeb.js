// 定义测试备用数据
    const TEST_WALLPAPERS = [
        ['3450085161', 'cache\\3450085161.gif', 'Liquid Metal ROG', 'video'],
        ['3466484071', 'cache\\3466484071.jpg', 'Anime girl', 'video'],
        ['3484246124', 'cache\\3484246124.gif', 'Summer Miku - WALLHACK', 'scene'],
        ['3650880224', 'cache\\3650880224.gif', 'Blue Archive | Kei', 'Web']
    ];
    
    // 当前选中的壁纸 ID
    let currentWallpaperId = null;
    
    // 鼠标组图标缓存
    const mouseGroupIconsCache = {};

    // 初始化函数：自动调用Python API，3秒超时使用测试数据
    async function initApp() {
        try {
            console.log("1. 检查 pywebview 对象:", window.pywebview);
            
            if (!window.pywebview) {
                console.log("2. 等待 pywebview 就绪...（3秒超时）");
                await Promise.race([
                    new Promise(resolve => {
                        window.addEventListener('pywebviewready', resolve);
                    }),
                    // 3秒超时器
                    new Promise((_, reject) => {
                        setTimeout(() => reject(new Error("pywebview 3秒未就绪")), 3000);
                    })
                ]);
            }
            
            console.log("3. pywebview API:", window.pywebview.api);
            console.log("4. 调用 init 方法...");
            
            // 调用API获取数据
            let wallpapers = await window.pywebview.api.init();
            console.log("5. 获取到的API数据：", wallpapers);

            // 如果API返回空/无效数据，则使用测试列表
            if (!wallpapers || wallpapers.length === 0) {
                console.log("API返回数据为空，使用测试备用数据");
                wallpapers = TEST_WALLPAPERS;
            }
            
            renderWallpapers(wallpapers);
        } catch (error) {
            // 捕获所有异常
            console.error("初始化失败，切换到测试数据：", error);
            renderWallpapers(TEST_WALLPAPERS);
        }
    }

    // 初始化预览面板为默认状态
    function initPreviewPanel() {
        const previewImg = document.getElementById('previewImg');
        previewImg.src = '';
        previewImg.alt = '';
        previewImg.style.display = 'none';
        
        document.getElementById('detailTitle').textContent = '请选择壁纸';
        document.getElementById('detailSubtitle').textContent = '暂无信息';
        document.getElementById('detailType').textContent = '类型：-';
    }

    // 更新右侧预览面板
    function updatePreviewPanel(wallpaperData) {
        const [id, imagePath, name, type] = wallpaperData;
        
        // 如果类型为web或application，不执行更新操作
        if (type && (type.toLowerCase() === 'web' || type.toLowerCase() === 'application')) {
            return;
        }
        
        // 保存当前选中的壁纸 ID
        currentWallpaperId = id;
        
        // 更新预览图片
        const previewImg = document.getElementById('previewImg');
        if (imagePath) {
            previewImg.src = imagePath.replace(/\\/g, '/');
            previewImg.alt = name || '预览图';
            previewImg.style.display = 'block';
            // 图片加载失败时隐藏
            previewImg.onerror = function() {
                this.src = '';
                this.style.display = 'none';
            };
        } else {
            // 没有图片时隐藏
            previewImg.src = '';
            previewImg.alt = '';
            previewImg.style.display = 'none';
        }
        
        // 更新标题
        document.getElementById('detailTitle').textContent = name || '未知壁纸';
        
        // 更新副标题
        document.getElementById('detailSubtitle').textContent = `ID: ${id}`;
        
        // 更新类型
        document.getElementById('detailType').textContent = `类型：${type || '未知'}`;
        
        // 加载鼠标组列表并更新选择框
        loadMouseGroups();
    }

    // 渲染壁纸列表
    function renderWallpapers(wallpaperList) {
        const grid = document.getElementById('wallpaperGrid');
        grid.innerHTML = '';

        if (!wallpaperList || wallpaperList.length === 0) {
            grid.innerHTML = '<div class="error-placeholder">暂无壁纸数据</div>';
            return;
        }

        wallpaperList.forEach(item => {
            const [id, imagePath, name, type] = item;
            
            const itemEl = document.createElement('div');
            itemEl.className = 'wallpaper-item';
            itemEl.dataset.id = id;
            
            // 添加点击事件
            itemEl.addEventListener('click', () => {
                updatePreviewPanel(item);
            });

            // 缩略图容器
            const thumbEl = document.createElement('div');
            thumbEl.className = 'wallpaper-thumb';
            if (imagePath) {
                const img = document.createElement('img');
                // 兼容Windows路径
                img.src = imagePath.replace(/\\/g, '/');
                img.alt = name || '壁纸';
                // 图片加载失败的兜底
                img.onerror = function() {
                    this.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgwIiBoZWlnaHQ9IjE4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTgwIiBoZWlnaHQ9IjE4MCIgZmlsbD0iIzMzNDE1NSIvPjx0ZXh0IHg9IjkwIiB5PSI5MCIgZm9udC1mYW1pbHk9IkxlZnQgVUlUIiwgZm9udC1zaXplPSIxMiIgZmlsbD0iIzlhYjNjOCIgbGV0dGVyLXNwYWNpbmc9Im5vcm1hbCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+5Zu+54mH5Lu25Lq6PC90ZXh0Pjwvc3ZnPg==';
                };
                thumbEl.appendChild(img);
                
                // 如果类型为web或application，添加半透明红色覆盖层
                if (type && (type.toLowerCase() === 'web' || type.toLowerCase() === 'application')) {
                    const overlay = document.createElement('div');
                    overlay.style.position = 'absolute';
                    overlay.style.top = '0';
                    overlay.style.left = '0';
                    overlay.style.width = '100%';
                    overlay.style.height = '100%';
                    overlay.style.background = 'rgba(255, 0, 0, 0.5)';
                    overlay.style.display = 'flex';
                    overlay.style.alignItems = 'center';
                    overlay.style.justifyContent = 'center';
                    overlay.style.color = 'white';
                    overlay.style.fontSize = '12px';
                    overlay.style.fontWeight = 'bold';
                    overlay.style.textAlign = 'center';
                    overlay.style.padding = '10px';
                    overlay.textContent = type.toLowerCase() === 'web' ? '暂不支持Web壁纸' : '不支持应用程序壁纸';
                    thumbEl.appendChild(overlay);
                }
            } else {
                thumbEl.innerHTML = '<span style="color:#94a3b8; font-size:12px;">无图片</span>';
            }

            // 右上角鼠标组图标区域
            const mouseGroupIndicator = document.createElement('div');
            mouseGroupIndicator.className = 'mouse-group-indicator';
            mouseGroupIndicator.dataset.wallpaperId = id;
            thumbEl.appendChild(mouseGroupIndicator);

            // 壁纸名称
            const infoEl = document.createElement('div');
            infoEl.className = 'wallpaper-info';
            infoEl.textContent = name || `壁纸-${id}`;

            itemEl.appendChild(thumbEl);
            itemEl.appendChild(infoEl);
            grid.appendChild(itemEl);
        });
        
        // 加载鼠标组图标
        loadMouseGroupIndicators();
    }

    // 加载鼠标组列表并更新选择框
    async function loadMouseGroups() {
        if (!currentWallpaperId) {
            return;
        }
        
        try {
            // 获取鼠标组列表
            const mouseGroups = await window.pywebview.api.get_mouse_groups();
            console.log('获取到鼠标组列表:', mouseGroups);
            
            // 获取当前壁纸的绑定状态
            const currentBinding = await window.pywebview.api.get_wallpaper_binding(currentWallpaperId);
            console.log('当前壁纸绑定状态:', currentBinding);
            
            // 更新选择框
            const selectElement = document.querySelector('.custom-select');
            if (selectElement) {
                // 清空现有选项
                selectElement.innerHTML = '';
                
                // 添加默认选项
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = '请选择';
                selectElement.appendChild(defaultOption);
                
                // 添加"未绑定"选项
                const unbindOption = document.createElement('option');
                unbindOption.value = '未绑定';
                unbindOption.textContent = '未绑定';
                selectElement.appendChild(unbindOption);
                
                // 添加鼠标组选项
                mouseGroups.forEach(group => {
                    const option = document.createElement('option');
                    option.value = group;
                    option.textContent = group;
                    selectElement.appendChild(option);
                });
                
                // 设置当前选中值
                if (currentBinding) {
                    selectElement.value = currentBinding;
                    // 加载当前选中鼠标组的图标
                    await loadMouseGroupIcons(currentBinding);
                } else {
                    // 清空图标容器
                    const iconsContainer = document.querySelector('.icons-container');
                    if (iconsContainer) {
                        iconsContainer.innerHTML = '';
                        for (let i = 0; i < 15; i++) {
                            const iconItem = document.createElement('div');
                            iconItem.className = 'icon-item';
                            iconsContainer.appendChild(iconItem);
                        }
                    }
                }
                
                // 添加事件监听器
                selectElement.onchange = handleMouseGroupChange;
            }
        } catch (error) {
            console.error('加载鼠标组失败:', error);
        }
    }
    
    // 加载鼠标组图标
    async function loadMouseGroupIcons(groupName) {
        if (!groupName || groupName === "未绑定") {
            // 清空图标容器
            const iconsContainer = document.querySelector('.icons-container');
            if (iconsContainer) {
                iconsContainer.innerHTML = '';
                for (let i = 0; i < 15; i++) {
                    const iconItem = document.createElement('div');
                    iconItem.className = 'icon-item';
                    iconsContainer.appendChild(iconItem);
                }
            }
            return;
        }
        
        try {
            // 检查缓存
            let icons;
            if (mouseGroupIconsCache[groupName]) {
                icons = mouseGroupIconsCache[groupName];
                console.log('使用缓存的鼠标组图标:', groupName);
            } else {
                // 调用 API 获取鼠标组图标
                icons = await window.pywebview.api.get_mouse_group_icons(groupName);
                console.log('获取到鼠标组图标:', icons);
                // 缓存图标数据
                mouseGroupIconsCache[groupName] = icons;
            }
            
            // 更新图标容器
            const iconsContainer = document.querySelector('.icons-container');
            if (iconsContainer) {
                iconsContainer.innerHTML = '';
                
                icons.forEach(iconPath => {
                    const iconItem = document.createElement('div');
                    iconItem.className = 'icon-item';
                    
                    if (iconPath) {
                        const img = document.createElement('img');
                        img.src = iconPath;
                        img.alt = '图标';
                        img.style.width = '100%';
                        img.style.height = '100%';
                        img.style.objectFit = 'cover';
                        img.onerror = function() {
                            this.style.display = 'none';
                        };
                        iconItem.appendChild(img);
                    }
                    
                    iconsContainer.appendChild(iconItem);
                });
            }
        } catch (error) {
            console.error('加载鼠标组图标失败:', error);
        }
    }
    
    // 处理鼠标组选择变化
    async function handleMouseGroupChange(event) {
        if (!currentWallpaperId) {
            return;
        }
        
        const selectedGroup = event.target.value;
        if (!selectedGroup) {
            return;
        }
        
        // 立即更新 UI 状态，提高响应速度
        if (selectedGroup === "未绑定") {
            // 立即隐藏当前壁纸的小图标
            const indicator = document.querySelector(`.mouse-group-indicator[data-wallpaper-id="${currentWallpaperId}"]`);
            if (indicator) {
                indicator.style.display = 'none';
            }
        }
        
        try {
            // 调用 API 绑定鼠标组
            const result = await window.pywebview.api.bind_mouse_group(currentWallpaperId, selectedGroup);
            console.log('绑定鼠标组结果:', result);
            
            // 显示操作结果
            if (result.success) {
                console.log('操作成功:', result.message);
                // 加载鼠标组图标
                await loadMouseGroupIcons(selectedGroup);
                // 重新加载鼠标组图标指示
                await loadMouseGroupIndicators();
            } else {
                console.error('操作失败:', result.message);
            }
        } catch (error) {
            console.error('绑定鼠标组失败:', error);
        }
    }

    // 加载鼠标组图标指示
    async function loadMouseGroupIndicators() {
        try {
            // 获取所有壁纸项
            const indicators = document.querySelectorAll('.mouse-group-indicator');
            
            for (const indicator of indicators) {
                const wallpaperId = indicator.dataset.wallpaperId;
                if (!wallpaperId) continue;
                
                // 检查壁纸是否有对应的鼠标组绑定
                const groupName = await window.pywebview.api.get_wallpaper_binding(wallpaperId);
                
                if (groupName && groupName !== "未绑定") {
                    // 检查缓存
                    let icons;
                    if (mouseGroupIconsCache[groupName]) {
                        icons = mouseGroupIconsCache[groupName];
                    } else {
                        // 获取鼠标组的 Arrow 图标
                        icons = await window.pywebview.api.get_mouse_group_icons(groupName);
                        // 缓存图标数据
                        mouseGroupIconsCache[groupName] = icons;
                    }
                    
                    if (icons && icons.length > 0 && icons[0]) {
                        // 显示指示器
                        indicator.style.display = 'flex';
                        
                        // 清空现有内容
                        indicator.innerHTML = '';
                        
                        // 创建图标元素
                        const img = document.createElement('img');
                        img.src = icons[0]; // Arrow 图标在列表的第一个位置
                        img.alt = '鼠标组图标';
                        img.style.width = '24px';
                        img.style.height = '24px';
                        img.style.objectFit = 'cover';
                        img.onerror = function() {
                            this.style.display = 'none';
                        };
                        indicator.appendChild(img);
                    } else {
                        // 隐藏指示器
                        indicator.style.display = 'none';
                    }
                } else {
                    // 立即隐藏指示器，不等待
                    indicator.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('加载鼠标组图标指示失败:', error);
        }
    }

    // 加载播放列表
    async function loadPlaylist() {
        console.log('loadPlaylist 函数被调用');
        try {
            // 显示加载状态
            const playlistTitle = document.querySelector('.playlist-title');
            const playlistLoading = document.querySelector('.playlist-loading');
            if (playlistTitle) {
                playlistTitle.textContent = '当前播放列表: 加载中...';
            }
            if (playlistLoading) {
                playlistLoading.style.display = 'block';
            }
            
            // 检查 pywebview 对象是否存在
            console.log('开始加载播放列表');
            console.log('pywebview 对象:', window.pywebview);
            console.log('pywebview.api 对象:', window.pywebview ? window.pywebview.api : 'undefined');
            console.log('get_playlist 方法:', window.pywebview && window.pywebview.api ? window.pywebview.api.get_playlist : 'undefined');
            
            // 调用 API 获取播放列表数据
            const playlistData = await window.pywebview.api.get_playlist();
            console.log('获取到播放列表数据:', playlistData);
            
            // 渲染播放列表
            renderPlaylist(playlistData.items, playlistData.name);
        } catch (error) {
            console.error('加载播放列表失败:', error);
            console.error('错误堆栈:', error.stack);
            // 显示空播放列表
            renderPlaylist([], '');
        } finally {
            // 隐藏加载状态
            const playlistLoading = document.querySelector('.playlist-loading');
            if (playlistLoading) {
                playlistLoading.style.display = 'none';
            }
        }
    }
    
    // 测试函数
    function testPlaylist() {
        console.log('测试播放列表加载');
        loadPlaylist();
    }
    
    // 暴露测试函数到全局
    window.testPlaylist = testPlaylist;
    
    // 渲染播放列表
    function renderPlaylist(items, name) {
        const playlistContent = document.querySelector('.playlist-content');
        const playlistTitle = document.querySelector('.playlist-title');
        
        if (!playlistContent || !playlistTitle) {
            return;
        }
        
        // 清空现有内容
        playlistContent.innerHTML = '';
        
        // 更新播放列表标题和数量
        const count = items.length;
        playlistTitle.textContent = `当前播放列表: ${name || '未命名'} (共 ${count} 项)`;
        
        // 渲染播放列表项
        items.forEach((item, index) => {
            const [id, imagePath] = item;
            
            const playlistItem = document.createElement('div');
            playlistItem.className = 'playlist-item';
            playlistItem.dataset.id = id;
            playlistItem.dataset.index = index;
            
            // 添加点击事件
            playlistItem.addEventListener('click', () => {
                // 查找对应的壁纸数据并更新预览面板
                const wallpaperData = [id, imagePath, '', ''];
                updatePreviewPanel(wallpaperData);
            });
            
            // 如果有预览图，添加到播放列表项
            if (imagePath) {
                const img = document.createElement('img');
                img.src = imagePath.replace(/\\/g, '/');
                img.alt = `壁纸 ${id}`;
                img.style.width = '100%';
                img.style.height = '100%';
                img.style.objectFit = 'cover';
                img.onerror = function() {
                    // 图片加载失败时显示默认内容
                    this.parentElement.innerHTML = '<div class="playlist-item-no-image">无预览图</div>';
                };
                playlistItem.appendChild(img);
            } else {
                // 无预览图时显示默认内容
                const noImageDiv = document.createElement('div');
                noImageDiv.className = 'playlist-item-no-image';
                noImageDiv.textContent = '无预览图';
                playlistItem.appendChild(noImageDiv);
            }
            
            playlistContent.appendChild(playlistItem);
        });
        
        // 添加鼠标滚轮左右滚动功能
        addMouseWheelScroll(playlistContent);
    }
    
    // 添加鼠标滚轮左右滚动功能
    function addMouseWheelScroll(element) {
        let isScrolling = false;
        let currentPosition = 0;
        let targetPosition = 0;
        let startTime = 0;
        
        element.addEventListener('wheel', (event) => {
            event.preventDefault();
            
            // 计算目标滚动位置
            targetPosition = element.scrollLeft + event.deltaY * 2; // 调整滚动速度
            
            // 限制滚动范围
            targetPosition = Math.max(0, Math.min(targetPosition, element.scrollWidth - element.clientWidth));
            
            if (!isScrolling) {
                currentPosition = element.scrollLeft;
                startTime = performance.now();
                isScrolling = true;
                smoothScroll();
            }
        });
        
        // 平滑滚动函数
        function smoothScroll(currentTime = performance.now()) {
            const elapsed = currentTime - startTime;
            const duration = 200; // 滚动动画持续时间（毫秒）
            
            // 使用缓动函数
            const progress = Math.min(elapsed / duration, 1);
            const easeProgress = 1 - Math.pow(1 - progress, 3); // 缓出效果
            
            // 计算当前滚动位置
            const newPosition = currentPosition + (targetPosition - currentPosition) * easeProgress;
            element.scrollLeft = newPosition;
            
            // 检查是否需要继续滚动
            if (progress < 1 && Math.abs(newPosition - targetPosition) > 1) {
                requestAnimationFrame(smoothScroll);
            } else {
                // 确保滚动到精确位置
                element.scrollLeft = targetPosition;
                isScrolling = false;
            }
        }
    }

    // 页面加载后自动执行
    window.addEventListener('load', function() {
        initPreviewPanel();
        initApp();
        // 延迟加载播放列表，确保 pywebview 完全初始化
        console.log('页面加载完成，准备加载播放列表');
        setTimeout(function() {
            console.log('执行 loadPlaylist 函数');
            loadPlaylist();
        }, 1000); // 加载播放列表
    });