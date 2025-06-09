// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initApp();
});

// 初始化应用程序
function initApp() {
    // 根据当前页面加载相应的功能
    const currentPath = window.location.pathname;
    
    if (currentPath === '/' || currentPath === '/index.html') {
        // 首页/用例生成页面
        // 注意：首页的loadTestCaseBatches已经在index.html中重写
        // 这里不再需要调用loadTestCaseBatches()
    } else if (currentPath.includes('/testcase.html')) {
        // 测试用例页面
        const urlParams = new URLSearchParams(window.location.search);
        const batchId = urlParams.get('batch_id');
        if (batchId) {
            initTestCasePage(batchId);
        }
    } else if (currentPath.includes('/knowledge.html')) {
        // 知识库页面
        loadKnowledgeFiles();
    }
    
    // 绑定全局事件
    bindGlobalEvents();
}

// 绑定全局事件
function bindGlobalEvents() {
    // 文件上传表单提交
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            uploadDocument();
        });
    }
    
    // 知识库文件上传表单提交
    const knowledgeUploadForm = document.getElementById('knowledge-upload-form');
    if (knowledgeUploadForm) {
        knowledgeUploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            uploadKnowledgeFile();
        });
    }
}

// 初始化测试用例页面
function initTestCasePage(batchId) {
    // 全局测试用例数据
    window.testCaseData = {
        batchId: batchId,
        testCases: [],
        filteredTestCases: [],
        selectedTestCases: new Set(),
        currentPage: 1,
        itemsPerPage: 10,
        currentFilter: 'all',
        currentSort: 'title-asc',
        searchQuery: ''
    };
    
    // 加载测试用例
    loadTestCases(batchId);
    
    // 绑定搜索事件
    const searchInput = document.getElementById('testcase-search');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            // 更新搜索查询
            window.testCaseData.searchQuery = searchInput.value.trim().toLowerCase();
            window.testCaseData.currentPage = 1;  // 重置页码
            applyTestCaseFilters();
        });
    }
    
    // 绑定排序事件
    const sortSelect = document.getElementById('testcase-sort');
    if (sortSelect) {
        sortSelect.addEventListener('change', () => {
            // 更新排序方式
            window.testCaseData.currentSort = sortSelect.value;
            applyTestCaseFilters();
        });
    }
    
    // 绑定筛选事件
    const filterButtons = document.querySelectorAll('.filter-item');
    if (filterButtons.length) {
        filterButtons.forEach(button => {
            button.addEventListener('click', () => {
                // 更新筛选器
                filterButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                window.testCaseData.currentFilter = button.getAttribute('data-filter');
                window.testCaseData.currentPage = 1;  // 重置页码
                applyTestCaseFilters();
            });
        });
    }
    
    // 绑定批量操作事件
    bindBatchOperations();
}

// 绑定批量操作事件
function bindBatchOperations() {
    // 全选按钮
    const selectAllBtn = document.getElementById('select-all-btn');
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', () => {
            const checkboxes = document.querySelectorAll('.testcase-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = true;
                const testCaseId = parseInt(checkbox.getAttribute('data-id'));
                window.testCaseData.selectedTestCases.add(testCaseId);
            });
            updateBatchButtons();
        });
    }
    
    // 取消全选按钮
    const deselectAllBtn = document.getElementById('deselect-all-btn');
    if (deselectAllBtn) {
        deselectAllBtn.addEventListener('click', () => {
            const checkboxes = document.querySelectorAll('.testcase-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = false;
            });
            window.testCaseData.selectedTestCases.clear();
            updateBatchButtons();
        });
    }
    
    // 批量通过按钮
    const batchApproveBtn = document.getElementById('batch-approve-btn');
    if (batchApproveBtn) {
        batchApproveBtn.addEventListener('click', () => {
            batchApproveTestCases();
        });
    }
    
    // 批量拒绝按钮
    const batchRejectBtn = document.getElementById('batch-reject-btn');
    if (batchRejectBtn) {
        batchRejectBtn.addEventListener('click', () => {
            batchRejectTestCases();
        });
    }
}

// 更新批量操作按钮状态
function updateBatchButtons() {
    const selectAllBtn = document.getElementById('select-all-btn');
    const deselectAllBtn = document.getElementById('deselect-all-btn');
    const batchApproveBtn = document.getElementById('batch-approve-btn');
    const batchRejectBtn = document.getElementById('batch-reject-btn');
    
    const selectedCount = window.testCaseData.selectedTestCases.size;
    
    // 更新按钮状态
    if (deselectAllBtn) {
        deselectAllBtn.disabled = selectedCount === 0;
    }
    
    if (batchApproveBtn) {
        batchApproveBtn.disabled = selectedCount === 0;
    }
    
    if (batchRejectBtn) {
        batchRejectBtn.disabled = selectedCount === 0;
    }
    
    // 如果全部选中，禁用全选按钮
    if (selectAllBtn) {
        const allCheckboxes = document.querySelectorAll('.testcase-checkbox');
        selectAllBtn.disabled = selectedCount === allCheckboxes.length && allCheckboxes.length > 0;
    }
}

// 批量通过测试用例
function batchApproveTestCases() {
    if (window.testCaseData.selectedTestCases.size === 0) return;
    
    UI.Modal.confirm(
        `确定要将选中的 ${window.testCaseData.selectedTestCases.size} 个测试用例标记为通过吗？`,
        () => {
            // 显示加载动画
            UI.Loader.show('正在批量审核测试用例...');
            
            // 创建审核请求
            const promises = Array.from(window.testCaseData.selectedTestCases).map(testCaseId => {
                return fetch(`/api/testcase/${testCaseId}/approve`, {
                    method: 'PUT'
                }).then(response => {
                    if (!response.ok) {
                        throw new Error(`无法审核测试用例 ${testCaseId}`);
                    }
                    return response.json();
                });
            });
            
            // 处理所有请求
            Promise.all(promises)
                .then(() => {
                    // 隐藏加载动画
                    UI.Loader.hide();
                    
                    // 显示成功通知
                    UI.Toast.success(`已成功审核通过 ${window.testCaseData.selectedTestCases.size} 个测试用例`);
                    
                    // 清空选择
                    window.testCaseData.selectedTestCases.clear();
                    
                    // 重新加载测试用例
                    loadTestCases(window.testCaseData.batchId);
                })
                .catch(error => {
                    console.error('批量审核失败:', error);
                    
                    // 隐藏加载动画
                    UI.Loader.hide();
                    
                    // 显示错误通知
                    UI.Toast.error('批量审核失败: ' + error.message);
                });
        }
    );
}

// 批量拒绝测试用例
function batchRejectTestCases() {
    if (window.testCaseData.selectedTestCases.size === 0) return;
    
    UI.Modal.confirm(
        `确定要将选中的 ${window.testCaseData.selectedTestCases.size} 个测试用例标记为拒绝吗？`,
        () => {
            // 显示加载动画
            UI.Loader.show('正在批量拒绝测试用例...');
            
            // 创建拒绝请求
            const promises = Array.from(window.testCaseData.selectedTestCases).map(testCaseId => {
                return fetch(`/api/testcase/${testCaseId}/reject`, {
                    method: 'PUT'
                }).then(response => {
                    if (!response.ok) {
                        throw new Error(`无法拒绝测试用例 ${testCaseId}`);
                    }
                    return response.json();
                });
            });
            
            // 处理所有请求
            Promise.all(promises)
                .then(() => {
                    // 隐藏加载动画
                    UI.Loader.hide();
                    
                    // 显示成功通知
                    UI.Toast.success(`已成功拒绝 ${window.testCaseData.selectedTestCases.size} 个测试用例`);
                    
                    // 清空选择
                    window.testCaseData.selectedTestCases.clear();
                    
                    // 重新加载测试用例
                    loadTestCases(window.testCaseData.batchId);
                })
                .catch(error => {
                    console.error('批量拒绝失败:', error);
                    
                    // 隐藏加载动画
                    UI.Loader.hide();
                    
                    // 显示错误通知
                    UI.Toast.error('批量拒绝失败: ' + error.message);
                });
        }
    );
}

// 应用测试用例筛选、排序和分页
function applyTestCaseFilters() {
    const data = window.testCaseData;
    let filtered = [...data.testCases];
    
    // 应用搜索
    if (data.searchQuery) {
        filtered = filtered.filter(testCase => 
            testCase.title.toLowerCase().includes(data.searchQuery) || 
            (testCase.description && testCase.description.toLowerCase().includes(data.searchQuery))
        );
    }
    
    // 应用筛选
    if (data.currentFilter !== 'all') {
        filtered = filtered.filter(testCase => testCase.status === data.currentFilter);
    }
    
    // 应用排序
    switch (data.currentSort) {
        case 'title-asc':
            filtered.sort((a, b) => a.title.localeCompare(b.title));
            break;
        case 'title-desc':
            filtered.sort((a, b) => b.title.localeCompare(a.title));
            break;
        case 'status-asc':
            filtered.sort((a, b) => {
                // 待审核 > 已通过 > 已拒绝
                const statusOrder = { pending: 0, approved: 1, rejected: 2 };
                return statusOrder[a.status || 'pending'] - statusOrder[b.status || 'pending'];
            });
            break;
        case 'status-desc':
            filtered.sort((a, b) => {
                // 已拒绝 > 已通过 > 待审核
                const statusOrder = { rejected: 0, approved: 1, pending: 2 };
                return statusOrder[a.status || 'pending'] - statusOrder[b.status || 'pending'];
            });
            break;
    }
    
    // 保存筛选后的结果
    data.filteredTestCases = filtered;
    
    // 渲染测试用例
    renderTestCases();
}

// 渲染测试用例
function renderTestCases() {
    const data = window.testCaseData;
    const testCasesContainer = document.getElementById('test-cases-container');
    const paginationContainer = document.getElementById('pagination-container');
    
    if (!testCasesContainer) return;
    
    // 计算分页
    const totalPages = Math.ceil(data.filteredTestCases.length / data.itemsPerPage);
    const start = (data.currentPage - 1) * data.itemsPerPage;
    const end = start + data.itemsPerPage;
    const paginatedTestCases = data.filteredTestCases.slice(start, end);
    
    // 清空容器
    testCasesContainer.innerHTML = '';
    
    // 如果没有测试用例
    if (data.filteredTestCases.length === 0) {
        testCasesContainer.innerHTML = '<p class="text-center">没有找到匹配的测试用例</p>';
        paginationContainer.innerHTML = '';
        return;
    }
    
    // 创建测试用例列表
    paginatedTestCases.forEach(testCase => {
        const statusClass = testCase.status === 'approved' ? 'approved' : 
                           testCase.status === 'rejected' ? 'rejected' : '';
                           
        const statusText = testCase.status === 'approved' ? '已通过' : 
                          testCase.status === 'rejected' ? '已拒绝' : '待审核';
                          
        const statusIcon = testCase.status === 'approved' ? '<i class="fas fa-check-circle"></i>' : 
                          testCase.status === 'rejected' ? '<i class="fas fa-times-circle"></i>' : 
                          '<i class="fas fa-clock"></i>';
        
        // 根据当前状态显示适当的审核按钮
        let actionButtons = '';
        if (testCase.status === 'approved') {
            // 已通过的测试用例显示拒绝按钮
            actionButtons = `
                <button onclick="rejectTestCase(${testCase.id})" class="button danger">
                    <i class="fas fa-times"></i> 拒绝
                </button>
            `;
        } else if (testCase.status === 'rejected') {
            // 已拒绝的测试用例显示通过按钮
            actionButtons = `
                <button onclick="approveTestCase(${testCase.id})" class="button success">
                    <i class="fas fa-check"></i> 通过
                </button>
            `;
        } else {
            // 待审核的测试用例显示两个按钮
            actionButtons = `
                <button onclick="approveTestCase(${testCase.id})" class="button success">
                    <i class="fas fa-check"></i> 通过
                </button>
                <button onclick="rejectTestCase(${testCase.id})" class="button danger">
                    <i class="fas fa-times"></i> 拒绝
                </button>
            `;
        }
        
        // 创建测试用例卡片
        const card = document.createElement('div');
        card.className = `card test-case ${statusClass} card-hover`;
        card.id = `test-case-${testCase.id}`;
        
        // 添加内容
        card.innerHTML = `
            <div class="test-case-header">
                <div class="test-case-title">
                    <input type="checkbox" class="testcase-checkbox" data-id="${testCase.id}" 
                           ${data.selectedTestCases.has(testCase.id) ? 'checked' : ''}>
                    <h3>${testCase.title}</h3>
                </div>
                <div class="test-case-actions">
                    <span class="status-badge ${statusClass}">${statusIcon} ${statusText}</span>
                    ${actionButtons}
                </div>
            </div>
            <div class="test-case-content">
                <p><strong>描述:</strong> ${testCase.description || '无'}</p>
                <p><strong>前置条件:</strong> ${testCase.preconditions || '无'}</p>
                <div class="collapsible-section">
                    <p class="section-title" onclick="toggleSection(this)">
                        <strong>测试步骤:</strong> <i class="fas fa-chevron-down"></i>
                    </p>
                    <div class="section-content" style="display: none;">
                        <pre>${testCase.steps}</pre>
                    </div>
                </div>
                <div class="collapsible-section">
                    <p class="section-title" onclick="toggleSection(this)">
                        <strong>预期结果:</strong> <i class="fas fa-chevron-down"></i>
                    </p>
                    <div class="section-content" style="display: none;">
                        <pre>${testCase.expected_results}</pre>
                    </div>
                </div>
            </div>
        `;
        
        // 添加到容器
        testCasesContainer.appendChild(card);
    });
    
    // 绑定复选框事件
    const checkboxes = document.querySelectorAll('.testcase-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const testCaseId = parseInt(checkbox.getAttribute('data-id'));
            if (checkbox.checked) {
                window.testCaseData.selectedTestCases.add(testCaseId);
            } else {
                window.testCaseData.selectedTestCases.delete(testCaseId);
            }
            updateBatchButtons();
        });
    });
    
    // 创建分页
    UI.Pagination.create(
        paginationContainer, 
        data.filteredTestCases.length, 
        data.itemsPerPage, 
        data.currentPage, 
        (page) => {
            data.currentPage = page;
            renderTestCases();
        }
    );
}

// 切换折叠区域
window.toggleSection = function(element) {
    const content = element.nextElementSibling;
    const icon = element.querySelector('i');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.className = 'fas fa-chevron-up';
    } else {
        content.style.display = 'none';
        icon.className = 'fas fa-chevron-down';
    }
};

// 加载测试用例
function loadTestCases(batchId) {
    const testCasesContainer = document.getElementById('test-cases-container');
    if (!testCasesContainer) return;
    
    // 显示加载中
    testCasesContainer.innerHTML = `
        <div class="loader">
            <div></div><div></div><div></div><div></div>
        </div>
        <p class="text-center">加载中...</p>
    `;
    
    // 请求测试用例列表
    fetch(`/api/testcase/batch/${batchId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('加载测试用例失败: ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            // 更新批次信息
            document.getElementById('batch-name').textContent = data.batch.name;
            document.getElementById('batch-description').textContent = data.batch.description || '无描述';
            
            // 保存测试用例数据
            window.testCaseData.testCases = data.test_cases;
            
            // 更新批次统计信息
            updateBatchStats(data.test_cases);
            
            // 应用筛选
            applyTestCaseFilters();
        })
        .catch(error => {
            console.error('加载测试用例失败:', error);
            testCasesContainer.innerHTML = `<p class="text-center">加载测试用例失败: ${error.message}</p>`;
            
            // 显示错误通知
            UI.Toast.error('加载测试用例失败: ' + error.message);
        });
}

// 更新批次统计信息
function updateBatchStats(testCases) {
    const totalCount = testCases.length;
    const approvedCount = testCases.filter(tc => tc.status === 'approved').length;
    const rejectedCount = testCases.filter(tc => tc.status === 'rejected').length;
    const reviewedCount = approvedCount + rejectedCount;
    
    document.getElementById('total-count').textContent = totalCount;
    document.getElementById('reviewed-count').textContent = reviewedCount;
    document.getElementById('approved-count').textContent = approvedCount;
    document.getElementById('rejected-count').textContent = rejectedCount;
}

// 通过测试用例
function approveTestCase(testCaseId) {
    // 显示加载动画
    UI.Loader.show('正在审核测试用例...');
    
    fetch(`/api/testcase/${testCaseId}/approve`, {
        method: 'PUT'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('审核测试用例失败: ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            // 隐藏加载动画
            UI.Loader.hide();
            
            // 显示成功通知
            UI.Toast.success('测试用例已审核通过');
            
            // 更新测试用例数据
            const testCase = window.testCaseData.testCases.find(tc => tc.id === testCaseId);
            if (testCase) {
                testCase.status = 'approved';
                updateBatchStats(window.testCaseData.testCases);
                
                // 重新渲染测试用例，以更新按钮状态
                applyTestCaseFilters();
            }
        })
        .catch(error => {
            console.error('审核测试用例失败:', error);
            
            // 隐藏加载动画
            UI.Loader.hide();
            
            // 显示错误通知
            UI.Toast.error('审核测试用例失败: ' + error.message);
        });
}

// 拒绝测试用例
function rejectTestCase(testCaseId) {
    // 显示加载动画
    UI.Loader.show('正在拒绝测试用例...');
    
    fetch(`/api/testcase/${testCaseId}/reject`, {
        method: 'PUT'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('拒绝测试用例失败: ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            // 隐藏加载动画
            UI.Loader.hide();
            
            // 显示成功通知
            UI.Toast.success('测试用例已拒绝');
            
            // 更新测试用例数据
            const testCase = window.testCaseData.testCases.find(tc => tc.id === testCaseId);
            if (testCase) {
                testCase.status = 'rejected';
                updateBatchStats(window.testCaseData.testCases);
                
                // 重新渲染测试用例，以更新按钮状态
                applyTestCaseFilters();
            }
        })
        .catch(error => {
            console.error('拒绝测试用例失败:', error);
            
            // 隐藏加载动画
            UI.Loader.hide();
            
            // 显示错误通知
            UI.Toast.error('拒绝测试用例失败: ' + error.message);
        });
}

// 查看批次
function viewBatch(batchId) {
    window.location.href = `/static/testcase.html?batch_id=${batchId}`;
}

// 导出批次
function exportBatch(batchId, status = 'all') {
    // 显示加载动画
    UI.Loader.show('正在生成Excel文件...');
    
    // 构建URL，添加状态参数
    let url = `/api/testcase/batch/${batchId}/export`;
    if (status && status !== 'all') {
        url += `?status=${status}`;
    }
    
    const downloadLink = document.createElement('a');
    downloadLink.href = url;
    downloadLink.target = '_blank';
    
    // 添加到页面并触发点击
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
    
    // 延迟隐藏加载动画，因为文件下载是在后台进行的
    setTimeout(() => {
        UI.Loader.hide();
        
        // 根据状态显示不同的成功消息
        let message = '正在下载Excel文件';
        if (status === 'approved') {
            message = '正在下载已通过的测试用例';
        } else if (status === 'rejected') {
            message = '正在下载已拒绝的测试用例';
        } else if (status === 'pending') {
            message = '正在下载待审核的测试用例';
        }
        
        UI.Toast.success(message);
    }, 1000);
}

// 上传文档
function uploadDocument() {
    const formData = new FormData(document.getElementById('upload-form'));
    
    // 显示加载中
    const uploadStatus = document.getElementById('upload-status');
    if (uploadStatus) {
        uploadStatus.textContent = '上传中，请稍候...';
    }
    
    // 显示进度信息
    const fileInput = document.getElementById('document-file');
    const fileCount = fileInput.files.length;
    const fileText = fileCount > 1 ? `${fileCount} 个文件` : '1 个文件';
    
    // 显示加载动画
    UI.Loader.show(`正在上传并处理 ${fileText}，这可能需要一些时间...`);
    
    fetch('/api/testcase/upload', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            // 隐藏加载动画
            UI.Loader.hide();
            
            if (data.error) {
                if (uploadStatus) {
                    uploadStatus.textContent = `上传失败: ${data.error}`;
                }
                UI.Toast.error(`上传失败: ${data.error}`);
                return;
            }
            
            if (uploadStatus) {
                uploadStatus.textContent = '上传成功！正在跳转...';
            }
            
            // 显示成功通知
            UI.Toast.success('测试用例生成成功！');
            
            // 跳转到测试用例页面
            window.location.href = `/static/testcase.html?batch_id=${data.batch_id}`;
        })
        .catch(error => {
            // 隐藏加载动画
            UI.Loader.hide();
            
            console.error('上传失败:', error);
            if (uploadStatus) {
                uploadStatus.textContent = `上传失败: ${error.message}`;
            }
            
            // 显示错误通知
            UI.Toast.error(`上传失败: ${error.message}`);
        });
}

// 加载知识库文件
function loadKnowledgeFiles() {
    const filesContainer = document.getElementById('files-container');
    if (!filesContainer) return;
    
    // 显示加载中
    filesContainer.innerHTML = '<p>加载中...</p>';
    
    // 请求文件列表
    fetch('/api/knowledge/files')
        .then(response => response.json())
        .then(data => {
            console.log('知识库文件数据:', data); // 调试输出
            
            if (!data.data || data.data.length === 0) {
                filesContainer.innerHTML = '<p>知识库中暂无文件，请上传文件。</p>';
                return;
            }
            
            // 创建文件列表
            let html = '<ul class="file-list">';
            data.data.forEach(file => {
                // 获取文件类型
                let fileType = 'unknown';
                if (file.data_source_type === 'upload_file' && file.data_source_detail_dict && file.data_source_detail_dict.upload_file) {
                    fileType = file.data_source_detail_dict.upload_file.extension || 'unknown';
                }
                
                const fileIcon = getFileIcon(fileType);
                
                // 获取文件大小
                let fileSize = 0;
                if (file.data_source_detail_dict && file.data_source_detail_dict.upload_file) {
                    fileSize = file.data_source_detail_dict.upload_file.size || 0;
                }
                
                // 获取文件状态
                const status = file.indexing_status || 'unknown';
                const statusText = status === 'completed' ? '已完成' : 
                                   status === 'waiting' ? '等待中' : 
                                   status === 'indexing' ? '处理中' : 
                                   status === 'error' ? '错误' : status;
                
                // 创建状态标签
                const statusClass = `status-${status}`;
                const loadingClass = status === 'indexing' ? 'loading-dots' : '';
                const statusBadge = `<span class="status-badge ${statusClass} ${loadingClass}">${statusText}</span>`;
                
                html += `
                    <li class="file-item">
                        <div class="file-info">
                            <div class="file-icon">${fileIcon}</div>
                            <div>
                                <div class="file-name">
                                    ${file.name}
                                    ${statusBadge}
                                </div>
                                <div class="file-meta">
                                    类型: ${fileType} | 
                                    大小: ${formatFileSize(fileSize)} | 
                                    上传时间: ${formatDateTime(file.created_at)} |
                                    状态: ${statusText}
                                </div>
                            </div>
                        </div>
                        <button onclick="deleteKnowledgeFile('${file.id}')" class="button danger">删除</button>
                    </li>
                `;
            });
            html += '</ul>';
            
            filesContainer.innerHTML = html;
        })
        .catch(error => {
            console.error('加载知识库文件失败:', error);
            filesContainer.innerHTML = `<p>加载知识库文件失败: ${error.message}</p>`;
        });
}

// 获取文件图标
function getFileIcon(fileType) {
    switch (fileType) {
        case 'pdf':
            return '📄';
        case 'docx':
        case 'doc':
            return '📝';
        case 'md':
            return '📋';
        default:
            return '📁';
    }
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 格式化日期时间
function formatDateTime(timestamp) {
    // 确保timestamp是有效的时间格式
    if (!timestamp) return '未知时间';
    
    try {
        // 检查是否是Unix时间戳（整数或数字字符串）
        let date;
        if (typeof timestamp === 'number' || !isNaN(Number(timestamp))) {
            // 如果是10位的Unix时间戳（秒），转换为毫秒
            if (String(timestamp).length === 10) {
                date = new Date(Number(timestamp) * 1000);
            }
            // 如果是13位的Unix时间戳（毫秒），直接使用
            else {
                date = new Date(Number(timestamp));
            }
        }
        // 检查是否是ISO 8601格式或其他标准格式
        else if (typeof timestamp === 'string') {
            // 如果是包含'T'的ISO格式，直接使用
            if (timestamp.includes('T')) {
                date = new Date(timestamp);
            } 
            // 尝试处理"YYYY-MM-DD HH:MM:SS"格式
            else if (timestamp.match(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/)) {
                // 将格式转换为ISO标准格式 "YYYY-MM-DDTHH:MM:SS"
                const parts = timestamp.split(' ');
                date = new Date(`${parts[0]}T${parts[1]}.000Z`);
                // 调整为北京时间 (UTC+8)
                date.setHours(date.getHours() + 8);
            } 
            // 尝试处理其他格式
            else {
                date = new Date(timestamp);
            }
        } else {
            date = new Date(timestamp);
        }
        
        // 检查日期是否有效
        if (isNaN(date.getTime())) {
            console.warn('无效的时间格式:', timestamp);
            return String(timestamp); // 如果无效，返回原始字符串
        }
        
        // 使用中国本地化格式
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
    } catch (e) {
        console.error('时间格式化错误:', e, timestamp);
        return String(timestamp); // 出错时返回原始字符串
    }
}

// 上传知识库文件
function uploadKnowledgeFile() {
    const formData = new FormData(document.getElementById('knowledge-upload-form'));
    
    // 显示加载中
    const uploadStatus = document.getElementById('knowledge-upload-status');
    if (uploadStatus) {
        uploadStatus.textContent = '上传中，请稍候...';
    }
    
    fetch('/api/knowledge/upload', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                if (uploadStatus) {
                    uploadStatus.textContent = `上传失败: ${data.error}`;
                }
                return;
            }
            
            if (uploadStatus) {
                uploadStatus.textContent = '上传成功！';
            }
            
            // 重新加载文件列表
            loadKnowledgeFiles();
            
            // 清空表单
            document.getElementById('knowledge-upload-form').reset();
        })
        .catch(error => {
            console.error('上传失败:', error);
            if (uploadStatus) {
                uploadStatus.textContent = `上传失败: ${error.message}`;
            }
        });
}

// 删除知识库文件
function deleteKnowledgeFile(fileId) {
    if (!confirm('确定要删除此文件吗？此操作不可撤销。')) {
        return;
    }
    
    // 请求删除
    fetch(`/api/knowledge/delete/${fileId}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(data => {
            alert('删除成功！');
            loadKnowledgeFiles();
        })
        .catch(error => {
            console.error('删除失败:', error);
            alert(`删除失败: ${error.message}`);
        });
} 