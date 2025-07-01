const { createApp } = Vue;
createApp({
    data() {
        return {
            spaces: initialSpaces,
            editingKey: '',
            form: {
                key: '',
                path: '',
                encrypted: false,
                password: '',
                allow_upload: false,
                allow_delete: false
            },
            settings: {
                upload_exts: initialSettings.upload_exts,     // Array
                download_exts: initialSettings.download_exts, // Array
            },
            newUploadExt: '',
            newDownloadExt: ''
        };
    },
    methods: {
        edit(key) {
            this.editingKey = key;
            // 深拷貝避免直接修改 initialSpaces
            this.form = JSON.parse(JSON.stringify({ key, ...this.spaces[key] }));
        },
        reset() {
            this.editingKey = '';
            this.form = { key: '', path: '', encrypted: false, password: '', allow_upload: false, allow_delete: false };
        },
        save() {
            fetch('/admin/api/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.form)
            }).then(_ => location.reload());
        },
        remove(key) {
            if (!confirm(`確定刪除 ${key} ?`)) return;
            fetch('/admin/api/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key })
            }).then(_ => location.reload());
        },
        addUploadExt() {
            const e = this.newUploadExt.trim();
            if (e && !this.settings.upload_exts.includes(e)) {
                this.settings.upload_exts.push(e);
            }
            this.newUploadExt = '';
        },
        removeUploadExt(idx) {
            this.settings.upload_exts.splice(idx, 1);
        },
        addDownloadExt() {
            const e = this.newDownloadExt.trim();
            if (e && !this.settings.download_exts.includes(e)) {
                this.settings.download_exts.push(e);
            }
            this.newDownloadExt = '';
        },
        removeDownloadExt(idx) {
            this.settings.download_exts.splice(idx, 1);
        },
        saveSettings() {
            fetch('/admin/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    upload_exts: this.settings.upload_exts,
                    download_exts: this.settings.download_exts
                })
            })
                .then(r => r.json())
                .then(res => {
                    if (res.success) {
                        alert('設定已更新，頁面即將重新整理');
                        // 按下確定後自動重新整理
                        window.location.reload();
                    } else {
                        alert('更新失敗：伺服器回傳錯誤');
                    }
                })
                .catch(() => {
                    alert('更新失敗：網路錯誤');
                });
        },

    }
}).mount('#app');
