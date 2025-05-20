const { createApp } = Vue;

createApp({
    data() {
        return {
            SPACE: window.SPACE,
            currentPath: '',
            items: [],
            breadcrumbs: [{ name: 'Home', path: '' }],
            contextItem: null,
            // 新增 Modal 相關 state
            modalVisible: false,
            modalItem: null,
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
        showContext(e, item) {
            this.contextItem = item;
            const menu = document.getElementById('context-menu');
            menu.style.top = `${e.clientY}px`;
            menu.style.left = `${e.clientX}px`;
            menu.style.display = 'block';
        },
        hideContext() {
            document.getElementById('context-menu').style.display = 'none';
        },
        viewDetails() {
            alert(`名稱: ${this.contextItem.name}\n路徑: ${this.contextItem.path}`);
            this.hideContext();
        },
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
    },
    mounted() {
        this.fetchList();
        document.addEventListener('click', this.hideContext);
    }
}).mount('#app');
