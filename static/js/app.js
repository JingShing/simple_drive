const { createApp } = Vue;

createApp({
    data() {
        return {
            SPACE: window.SPACE,
            allowUpload: window.ALLOW_UPLOAD,  // 從後端傳過來的布林
            allowDelete: window.ALLOW_DELETE,   // 來自後端

            currentPath: '',
            items: [],
            breadcrumbs: [{ name: 'Home', path: '' }],
            contextItem: null,

            // Modal 相关
            modalVisible: false,
            modalItem: null,

            // Sidebar 相关，一定要在 data 里初始化！
            sidebarVisible: false,
            metadata: {},    // 用来存 API 抓回来的 EXIF data
        }
    },
    methods: {
        fetchList(path = '') {
            fetch(`/${this.SPACE}/api/list?path=${encodeURIComponent(path)}`)
                .then(r => r.json())
                .then(data => {
                    this.items = data;
                    this.currentPath = path;
                    this.updateBreadcrumbs();
                });
        },
        updateBreadcrumbs() {
            const parts = this.currentPath.split('/').filter(Boolean);
            let acc = '';
            this.breadcrumbs = [{ name: 'Home', path: '' }];
            parts.forEach(p => {
                acc += `/${p}`;
                this.breadcrumbs.push({ name: p, path: acc });
            });
        },
        navigate(path) {
            this.fetchList(path);
        },
        open(item) {
            if (item.is_dir) {
                this.fetchList(item.path);
            } else {
                window.open(`/${this.SPACE}/api/download?path=${encodeURIComponent(item.path)}`, '_blank');
            }
        },
        // showContext(e, item) {
        //     this.contextItem = item;
        //     const menu = document.getElementById('context-menu');
        //     menu.style.top = `${e.clientY}px`;
        //     menu.style.left = `${e.clientX}px`;
        //     menu.style.display = 'block';
        // },
        openMenu(evt, item) {
            this.contextItem = item;
            const menu = document.getElementById('context-menu');
            // 跳出在按鈕附近
            menu.style.top = `${evt.clientY}px`;
            menu.style.left = `${evt.clientX}px`;
            menu.style.display = 'block';
        },
        hideContext() {
            const menu = document.getElementById('context-menu');
            menu.style.display = 'none';
        },
        // viewDetails() {
        //     alert(`名稱: ${this.contextItem.name}\n路徑: ${this.contextItem.path}`);
        //     this.hideContext();
        // },
        download() {
            window.location.href = `/${this.SPACE}/api/download?path=${encodeURIComponent(this.contextItem.path)}`;
            this.hideContext();
        },
        // ===== Modal methods =====
        openModal(item) {
            if (!item.is_image) return;
            this.modalItem = item;
            this.modalVisible = true;
        },
        closeModal() {
            this.modalVisible = false;
            this.modalItem = null;
        },

        viewDetails() {
            this.hideContext();
            this.openSidebar(this.contextItem);
        },
        openSidebar(item) {
            fetch(`/${this.SPACE}/api/metadata?path=${encodeURIComponent(item.path)}`)
                .then(r => {
                    if (!r.ok) throw new Error(`HTTP ${r.status}`);
                    return r.json();
                })
                .then(data => {
                    this.metadata = data;
                    this.sidebarVisible = true;
                })
                .catch(err => {
                    console.error('metadata fetch failed:', err);
                    alert('取得檔案資訊失敗');
                });
        },
        closeSidebar() {
            this.sidebarVisible = false;
            this.metadata = {};
        },

        // 處理檔案上傳
        uploadFile(event) {
            const file = event.target.files[0];
            if (!file) return;
            this.uploading = true;
            const form = new FormData();
            form.append('file', file);
            // 傳目前資料夾路徑 (this.currentPath)，讓後端存到對應子資料夾
            form.append('path', this.currentPath);
            fetch(`/${this.SPACE}/api/upload`, {
                method: 'POST',
                body: form,
            })
                .then(r => {
                    this.uploading = false;
                    if (!r.ok) throw new Error(`Upload failed: ${r.status}`);
                    return r.json();
                })
                .then(res => {
                    // 上傳成功，重新整理該目錄列表
                    this.fetchList(this.currentPath);
                })
                .catch(err => {
                    this.uploading = false;
                    console.error(err);
                    alert('上傳失敗');
                });
        },
        // 刪除檔案
        deleteItem() {
            if (!confirm(`確定要刪除 ${this.contextItem.name} 嗎？`)) {
                this.hideContext();
                return;
            }
            fetch(`/${this.SPACE}/api/delete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: this.contextItem.path })
            })
                .then(r => {
                    this.hideContext();
                    if (!r.ok) throw new Error(`DELETE ${r.status}`);
                    return r.json();
                })
                .then(res => {
                    if (res.success) {
                        this.fetchList(this.currentPath);
                    } else {
                        alert('刪除失敗');
                    }
                })
                .catch(err => {
                    console.error(err);
                    alert('刪除發生錯誤');
                });
        },
    },
    mounted() {
        this.fetchList();
        document.addEventListener('click', this.hideContext);
        window.addEventListener('scroll', this.hideContext);
    }
}).mount('#app');
