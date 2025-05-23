const { createApp } = Vue;

createApp({
    data() {
        return {
            SPACE: window.SPACE,
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
    },
    mounted() {
        this.fetchList();
        document.addEventListener('click', this.hideContext);
        window.addEventListener('scroll', this.hideContext);
    }
}).mount('#app');
