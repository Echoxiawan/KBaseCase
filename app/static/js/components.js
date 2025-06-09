/**
 * 通用UI组件
 * 包含Toast通知、模态对话框、加载器等
 */

// Toast通知组件
const Toast = {
    /**
     * 创建并显示一个toast通知
     * @param {string} message - 通知消息
     * @param {string} type - 通知类型 (success, error, warning, info)
     * @param {number} duration - 显示时长(毫秒)
     */
    show: function(message, type = 'info', duration = 3000) {
        // 确保toast容器存在
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        
        // 创建toast元素
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        // 设置图标
        let icon = '💬';
        if (type === 'success') icon = '✅';
        else if (type === 'error') icon = '❌';
        else if (type === 'warning') icon = '⚠️';
        else if (type === 'info') icon = 'ℹ️';
        
        // 创建toast内容
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-icon">${icon}</span>
                <span>${message}</span>
            </div>
            <button class="toast-close">&times;</button>
        `;
        
        // 添加到容器
        container.appendChild(toast);
        
        // 设置关闭按钮事件
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            this.close(toast);
        });
        
        // 自动关闭
        if (duration > 0) {
            setTimeout(() => {
                this.close(toast);
            }, duration);
        }
        
        return toast;
    },
    
    /**
     * 关闭指定的toast
     * @param {HTMLElement} toast - 要关闭的toast元素
     */
    close: function(toast) {
        toast.style.animation = 'slideOut 0.3s forwards';
        setTimeout(() => {
            toast.remove();
        }, 300);
    },
    
    /**
     * 成功通知快捷方法
     * @param {string} message - 通知消息
     * @param {number} duration - 显示时长(毫秒)
     */
    success: function(message, duration = 3000) {
        return this.show(message, 'success', duration);
    },
    
    /**
     * 错误通知快捷方法
     * @param {string} message - 通知消息
     * @param {number} duration - 显示时长(毫秒)
     */
    error: function(message, duration = 3000) {
        return this.show(message, 'error', duration);
    },
    
    /**
     * 警告通知快捷方法
     * @param {string} message - 通知消息
     * @param {number} duration - 显示时长(毫秒)
     */
    warning: function(message, duration = 3000) {
        return this.show(message, 'warning', duration);
    },
    
    /**
     * 信息通知快捷方法
     * @param {string} message - 通知消息
     * @param {number} duration - 显示时长(毫秒)
     */
    info: function(message, duration = 3000) {
        return this.show(message, 'info', duration);
    }
};

// 模态对话框组件
const Modal = {
    /**
     * 创建并显示一个模态对话框
     * @param {Object} options - 配置选项
     * @param {string} options.title - 对话框标题
     * @param {string|HTMLElement} options.content - 对话框内容
     * @param {Array} options.buttons - 按钮配置数组
     * @param {boolean} options.closeOnOverlayClick - 点击遮罩层是否关闭对话框
     * @param {Function} options.onClose - 对话框关闭回调
     */
    show: function(options = {}) {
        const defaults = {
            title: '提示',
            content: '',
            buttons: [
                {
                    text: '确定',
                    type: 'primary',
                    handler: () => this.close()
                }
            ],
            closeOnOverlayClick: true,
            onClose: null
        };
        
        const settings = {...defaults, ...options};
        
        // 创建模态遮罩
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        
        // 创建模态框
        const modal = document.createElement('div');
        modal.className = 'modal';
        
        // 创建模态框头部
        const header = document.createElement('div');
        header.className = 'modal-header';
        header.innerHTML = `
            <h3 class="modal-title">${settings.title}</h3>
            <button class="modal-close">&times;</button>
        `;
        
        // 创建模态框内容
        const body = document.createElement('div');
        body.className = 'modal-body';
        
        if (typeof settings.content === 'string') {
            body.innerHTML = settings.content;
        } else if (settings.content instanceof HTMLElement) {
            body.appendChild(settings.content);
        }
        
        // 创建模态框底部
        const footer = document.createElement('div');
        footer.className = 'modal-footer';
        
        settings.buttons.forEach(btn => {
            const button = document.createElement('button');
            button.textContent = btn.text;
            button.className = btn.type === 'primary' ? 'button' : 'button ' + btn.type;
            
            if (btn.handler) {
                button.addEventListener('click', (e) => {
                    btn.handler(e, this);
                });
            }
            
            footer.appendChild(button);
        });
        
        // 组装模态框
        modal.appendChild(header);
        modal.appendChild(body);
        modal.appendChild(footer);
        overlay.appendChild(modal);
        
        // 添加到页面
        document.body.appendChild(overlay);
        
        // 绑定关闭按钮事件
        const closeBtn = modal.querySelector('.modal-close');
        closeBtn.addEventListener('click', () => {
            this.close(overlay, settings.onClose);
        });
        
        // 绑定遮罩点击事件
        if (settings.closeOnOverlayClick) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this.close(overlay, settings.onClose);
                }
            });
        }
        
        // 显示模态框
        setTimeout(() => {
            overlay.classList.add('active');
        }, 10);
        
        return overlay;
    },
    
    /**
     * 关闭指定的模态对话框
     * @param {HTMLElement} overlay - 要关闭的模态遮罩元素
     * @param {Function} callback - 关闭后的回调函数
     */
    close: function(overlay, callback) {
        if (!overlay) {
            overlay = document.querySelector('.modal-overlay.active');
            if (!overlay) return;
        }
        
        overlay.classList.remove('active');
        
        setTimeout(() => {
            overlay.remove();
            if (callback && typeof callback === 'function') {
                callback();
            }
        }, 300);
    },
    
    /**
     * 显示确认对话框
     * @param {string} message - 提示消息
     * @param {Function} onConfirm - 确认回调
     * @param {Function} onCancel - 取消回调
     * @param {string} title - 对话框标题
     */
    confirm: function(message, onConfirm, onCancel, title = '确认') {
        return this.show({
            title: title,
            content: message,
            buttons: [
                {
                    text: '取消',
                    type: 'default',
                    handler: (e, modal) => {
                        modal.close();
                        if (onCancel && typeof onCancel === 'function') {
                            onCancel();
                        }
                    }
                },
                {
                    text: '确定',
                    type: 'primary',
                    handler: (e, modal) => {
                        modal.close();
                        if (onConfirm && typeof onConfirm === 'function') {
                            onConfirm();
                        }
                    }
                }
            ]
        });
    },
    
    /**
     * 显示提示对话框
     * @param {string} message - 提示消息
     * @param {Function} onClose - 关闭回调
     * @param {string} title - 对话框标题
     */
    alert: function(message, onClose, title = '提示') {
        return this.show({
            title: title,
            content: message,
            buttons: [
                {
                    text: '确定',
                    type: 'primary',
                    handler: (e, modal) => {
                        modal.close();
                        if (onClose && typeof onClose === 'function') {
                            onClose();
                        }
                    }
                }
            ]
        });
    },
    
    /**
     * 显示输入对话框
     * @param {string} message - 提示消息
     * @param {Function} onInput - 输入回调
     * @param {string} defaultValue - 默认值
     * @param {string} title - 对话框标题
     */
    prompt: function(message, onInput, defaultValue = '', title = '请输入') {
        const content = document.createElement('div');
        content.innerHTML = `
            <p>${message}</p>
            <input type="text" class="modal-input" value="${defaultValue}" style="width: 100%; padding: 8px; margin-top: 10px;">
        `;
        
        return this.show({
            title: title,
            content: content,
            buttons: [
                {
                    text: '取消',
                    type: 'default',
                    handler: (e, modal) => {
                        modal.close();
                    }
                },
                {
                    text: '确定',
                    type: 'primary',
                    handler: (e, modal) => {
                        const input = content.querySelector('.modal-input');
                        const value = input.value;
                        modal.close();
                        if (onInput && typeof onInput === 'function') {
                            onInput(value);
                        }
                    }
                }
            ]
        });
    }
};

// 加载器组件
const Loader = {
    /**
     * 显示全屏加载动画
     * @param {string} message - 加载提示消息
     */
    show: function(message = '加载中...') {
        // 确保只有一个加载器
        this.hide();
        
        // 创建加载器容器
        const container = document.createElement('div');
        container.className = 'loader-container';
        container.id = 'global-loader';
        
        // 创建加载器
        container.innerHTML = `
            <div class="loader">
                <div></div><div></div><div></div><div></div>
            </div>
            <p style="margin-top: 20px; color: #666;">${message}</p>
        `;
        
        // 添加到页面
        document.body.appendChild(container);
        
        // 显示加载器
        setTimeout(() => {
            container.classList.add('active');
        }, 10);
        
        return container;
    },
    
    /**
     * 隐藏加载动画
     */
    hide: function() {
        const loader = document.getElementById('global-loader');
        if (loader) {
            loader.classList.remove('active');
            setTimeout(() => {
                loader.remove();
            }, 300);
        }
    },
    
    /**
     * 创建进度条
     * @param {HTMLElement} container - 容器元素
     * @param {number} initialValue - 初始进度值(0-100)
     */
    createProgressBar: function(container, initialValue = 0) {
        // 创建进度条容器
        const progressContainer = document.createElement('div');
        progressContainer.className = 'progress-container';
        
        // 创建进度条
        const progressBar = document.createElement('div');
        progressBar.className = 'progress-bar';
        progressBar.style.width = `${initialValue}%`;
        
        // 组装进度条
        progressContainer.appendChild(progressBar);
        container.appendChild(progressContainer);
        
        // 返回更新函数
        return function(value) {
            progressBar.style.width = `${value}%`;
        };
    }
};

// 拖放上传组件
const DropZone = {
    /**
     * 初始化拖放上传区域
     * @param {HTMLElement} element - 拖放区域元素
     * @param {Function} onDrop - 文件放置回调
     */
    init: function(element, onDrop) {
        if (!element) return;
        
        // 阻止默认拖放行为
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            element.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });
        
        // 高亮显示
        ['dragenter', 'dragover'].forEach(eventName => {
            element.addEventListener(eventName, highlight, false);
        });
        
        // 取消高亮
        ['dragleave', 'drop'].forEach(eventName => {
            element.addEventListener(eventName, unhighlight, false);
        });
        
        // 处理放置
        element.addEventListener('drop', handleDrop, false);
        
        // 阻止默认行为
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        // 高亮
        function highlight() {
            element.classList.add('active');
        }
        
        // 取消高亮
        function unhighlight() {
            element.classList.remove('active');
        }
        
        // 处理放置
        function handleDrop(e) {
            const files = e.dataTransfer.files;
            if (onDrop && typeof onDrop === 'function') {
                onDrop(files);
            }
        }
    }
};

// 搜索和筛选组件
const Filter = {
    /**
     * 初始化搜索栏
     * @param {HTMLElement} searchInput - 搜索输入框
     * @param {Array} items - 要筛选的项目数组
     * @param {Function} filterFn - 筛选函数
     * @param {Function} renderFn - 渲染函数
     */
    initSearch: function(searchInput, items, filterFn, renderFn) {
        if (!searchInput) return;
        
        searchInput.addEventListener('input', () => {
            const query = searchInput.value.trim().toLowerCase();
            const filtered = items.filter(item => filterFn(item, query));
            renderFn(filtered);
        });
    },
    
    /**
     * 初始化筛选按钮组
     * @param {NodeList} filterButtons - 筛选按钮集合
     * @param {Array} items - 要筛选的项目数组
     * @param {Function} filterFn - 筛选函数
     * @param {Function} renderFn - 渲染函数
     */
    initFilterButtons: function(filterButtons, items, filterFn, renderFn) {
        if (!filterButtons || !filterButtons.length) return;
        
        filterButtons.forEach(button => {
            button.addEventListener('click', () => {
                // 更新活动状态
                filterButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                // 获取筛选值
                const filterValue = button.getAttribute('data-filter');
                
                // 筛选和渲染
                const filtered = items.filter(item => filterFn(item, filterValue));
                renderFn(filtered);
            });
        });
    }
};

// 分页组件
const Pagination = {
    /**
     * 创建分页
     * @param {HTMLElement} container - 分页容器
     * @param {number} totalItems - 总项目数
     * @param {number} itemsPerPage - 每页项目数
     * @param {number} currentPage - 当前页码
     * @param {Function} onPageChange - 页码变化回调
     */
    create: function(container, totalItems, itemsPerPage, currentPage, onPageChange) {
        if (!container) return;
        
        // 计算总页数
        const totalPages = Math.ceil(totalItems / itemsPerPage);
        
        // 清空容器
        container.innerHTML = '';
        
        // 如果只有一页，不显示分页
        if (totalPages <= 1) return;
        
        // 创建分页容器
        const pagination = document.createElement('div');
        pagination.className = 'pagination';
        
        // 上一页按钮
        const prevButton = document.createElement('div');
        prevButton.className = `pagination-item ${currentPage === 1 ? 'disabled' : ''}`;
        prevButton.innerHTML = '&laquo;';
        prevButton.addEventListener('click', () => {
            if (currentPage > 1) {
                onPageChange(currentPage - 1);
            }
        });
        pagination.appendChild(prevButton);
        
        // 页码按钮
        let startPage = Math.max(1, currentPage - 2);
        let endPage = Math.min(totalPages, startPage + 4);
        
        if (endPage - startPage < 4) {
            startPage = Math.max(1, endPage - 4);
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const pageButton = document.createElement('div');
            pageButton.className = `pagination-item ${i === currentPage ? 'active' : ''}`;
            pageButton.textContent = i;
            pageButton.addEventListener('click', () => {
                onPageChange(i);
            });
            pagination.appendChild(pageButton);
        }
        
        // 下一页按钮
        const nextButton = document.createElement('div');
        nextButton.className = `pagination-item ${currentPage === totalPages ? 'disabled' : ''}`;
        nextButton.innerHTML = '&raquo;';
        nextButton.addEventListener('click', () => {
            if (currentPage < totalPages) {
                onPageChange(currentPage + 1);
            }
        });
        pagination.appendChild(nextButton);
        
        // 添加到容器
        container.appendChild(pagination);
    }
};

// 导出组件
window.UI = {
    Toast,
    Modal,
    Loader,
    DropZone,
    Filter,
    Pagination
}; 