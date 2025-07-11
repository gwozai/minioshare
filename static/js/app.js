const { createApp, ref, onMounted, computed } = Vue;

// 配置axios默认请求头
axios.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';

createApp({
    delimiters: ['[[', ']]'],
    setup() {
        const isAdmin = ref(true); // 默认为管理员模式
        const files = ref([]);
        const pagination = ref({
            page: 1,
            totalPages: 0,
            totalFiles: 0,
            hasPrev: false,
            hasNext: false,
            sortBy: 'date',
            order: 'desc'
        });
        const shareUrl = ref('');
        const selectedFile = ref(null);
        const errorMessage = ref('');
        const successMessage = ref('');
        const selectedFiles = ref([]);
        const selectAll = ref(false);
        const copiedIndex = ref(-1);
        const allCopied = ref(false);
        const searchQuery = ref('');
        let uploadModal = null;
        let shareModal = null;
        let searchTimeout = null;

        // 加载文件列表
        const loadFiles = async () => {
            try {
                let url = `/?page=${pagination.value.page}&sort=${pagination.value.sortBy}&order=${pagination.value.order}`;
                if (searchQuery.value) {
                    url += `&search=${encodeURIComponent(searchQuery.value)}`;
                }
                const response = await axios.get(url);
                files.value = response.data.objects || [];
                Object.assign(pagination.value, response.data.pagination || {});
                isAdmin.value = response.data.is_admin || false;
                
                if (response.data.error) {
                    errorMessage.value = response.data.error;
                }
            } catch (error) {
                console.error('加载文件失败:', error);
                errorMessage.value = error.response?.data?.error || '加载文件失败';
            }
        };

        // 上传文件
        const uploadFile = async () => {
            if (!selectedFile.value) {
                errorMessage.value = '请选择一个文件';
                return;
            }

            const formData = new FormData();
            formData.append('file', selectedFile.value);

            try {
                const response = await axios.post('/upload', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    }
                });
                if (uploadModal) {
                    uploadModal.hide();
                }
                selectedFile.value = null;
                successMessage.value = '文件上传成功';
                
                // 重置到第1页，按最新时间排序，然后重新加载文件列表
                pagination.value.page = 1;
                pagination.value.sortBy = 'date';
                pagination.value.order = 'desc';
                
                // 清除搜索条件，确保能看到新上传的文件
                searchQuery.value = '';
                
                // 重新加载文件列表而不是刷新整个页面
                await loadFiles();
            } catch (error) {
                errorMessage.value = error.response?.data?.error || '上传失败';
            }
        };

        // 生成分享链接
        const shareFile = async (filename) => {
            try {
                let url = `/share/${encodeURIComponent(filename)}`;
                const response = await axios.get(url);
                if (response.data.error) {
                    throw new Error(response.data.error);
                }
                shareUrl.value = response.data.url;
                copiedIndex.value = -1;
                allCopied.value = false;
            } catch (error) {
                errorMessage.value = error.response?.data?.error || error.message || '生成分享链接失败';
                if (shareModal) {
                    shareModal.hide();
                }
            }
        };

        // 批量分享文件
        const shareSelectedFiles = async () => {
            if (selectedFiles.value.length === 0) {
                errorMessage.value = '请选择要分享的文件';
                return;
            }

            try {
                const urls = await Promise.all(selectedFiles.value.map(async (filename) => {
                    let url = `/share/${encodeURIComponent(filename)}`;
                    const response = await axios.get(url);
                    if (response.data.error) {
                        throw new Error(response.data.error);
                    }
                    return response.data.url;
                }));
                shareUrl.value = urls;
                copiedIndex.value = -1;
                allCopied.value = false;
                if (shareModal) {
                    shareModal.show();
                }
            } catch (error) {
                errorMessage.value = error.response?.data?.error || error.message || '生成分享链接失败';
            }
        };

        // 复制分享链接
        const copyShareUrl = async (url, index = 0) => {
            try {
                await navigator.clipboard.writeText(url);
                copiedIndex.value = index;
                successMessage.value = '链接已复制到剪贴板';
                
                // 3秒后重置复制状态
                setTimeout(() => {
                    if (copiedIndex.value === index) {
                        copiedIndex.value = -1;
                    }
                }, 3000);
            } catch (error) {
                errorMessage.value = '复制链接失败';
            }
        };

        // 复制所有链接
        const copyAllUrls = async () => {
            if (!Array.isArray(shareUrl.value)) return;
            
            try {
                const text = shareUrl.value.join('\n');
                await navigator.clipboard.writeText(text);
                allCopied.value = true;
                successMessage.value = '所有链接已复制到剪贴板';
                
                // 3秒后重置复制状态
                setTimeout(() => {
                    allCopied.value = false;
                }, 3000);
            } catch (error) {
                errorMessage.value = '复制链接失败';
            }
        };

        // 全选/取消全选
        const toggleSelectAll = () => {
            if (selectAll.value) {
                selectedFiles.value = files.value
                    .filter(file => !file.is_directory)
                    .map(file => file.name);
            } else {
                selectedFiles.value = [];
            }
        };

        // 切换排序方向
        const toggleOrder = () => {
            pagination.value.order = pagination.value.order === 'desc' ? 'asc' : 'desc';
            loadFiles();
        };

        // 更改排序字段
        const changeSort = (field) => {
            pagination.value.sortBy = field;
            loadFiles();
        };

        // 更改页码
        const changePage = (page) => {
            pagination.value.page = page;
            loadFiles();
        };

        // 文件大小格式化
        const formatFileSize = (size) => {
            const units = ['B', 'KB', 'MB', 'GB', 'TB'];
            let i = 0;
            while (size >= 1024 && i < units.length - 1) {
                size /= 1024;
                i++;
            }
            return `${size.toFixed(2)} ${units[i]}`;
        };

        // 从URL中获取文件名
        const getFilenameFromUrl = (url) => {
            try {
                const urlObj = new URL(url);
                const filename = decodeURIComponent(urlObj.pathname.split('/').pop());
                return filename;
            } catch (error) {
                return '';
            }
        };

        // 搜索文件
        const searchFiles = () => {
            // 使用防抖，避免频繁请求
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }
            searchTimeout = setTimeout(() => {
                pagination.value.page = 1; // 重置到第一页
                loadFiles();
            }, 300);
        };

        // 清除搜索
        const clearSearch = () => {
            searchQuery.value = '';
            pagination.value.page = 1;
            loadFiles();
        };


        // 初始化模态框
        const initModals = () => {
            uploadModal = new bootstrap.Modal(document.getElementById('uploadModal'));
            shareModal = new bootstrap.Modal(document.getElementById('shareModal'));
            
            // 监听模态框关闭事件
            document.getElementById('uploadModal').addEventListener('hidden.bs.modal', () => {
                selectedFile.value = null;
            });
            
            document.getElementById('shareModal').addEventListener('hidden.bs.modal', () => {
                shareUrl.value = '';
                copiedIndex.value = -1;
                allCopied.value = false;
            });
        };

        // 在组件挂载时加载文件
        onMounted(() => {
            loadFiles();
            initModals();
        });

        return {
            isAdmin,
            files,
            pagination,
            shareUrl,
            selectedFile,
            errorMessage,
            successMessage,
            selectedFiles,
            selectAll,
            copiedIndex,
            allCopied,
            searchQuery,
            loadFiles,
            uploadFile,
            shareFile,
            shareSelectedFiles,
            copyShareUrl,
            copyAllUrls,
            getFilenameFromUrl,
            toggleSelectAll,
            toggleOrder,
            changeSort,
            changePage,
            formatFileSize,
            searchFiles,
            clearSearch
        };
    }
}).mount('#app'); 