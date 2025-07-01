# Cloud Drive Viewer

這是一個以 Flask 為後端、Vue + Bootstrap 為前端實現的「雲端硬碟」瀏覽與預覽工具，支援多資料夾空間、密碼保護、影像縮圖、RAW 檔解碼、EXIF 資訊顯示、上傳／刪除功能控制，以及縮圖懶載入和後台管理（Admin Console）等特色。

## 功能特色

1. **多資料夾空間 (Spaces)**
   - 可在 `config.py` 中於 `SPACES` 字典設定多個隨機路徑前綴（如 `jakxjs`、`shbsb`），分別對應不同的物理資料夾。
   - 根目錄 `/` 顯示所有註冊空間列表，點擊即可進入相應空間。

2. **密碼保護 (Encryption)**
   - 支援針對單一空間開啟密碼保護 (`encrypted: True`)，未登入者會被導向密碼輸入頁面。
   - 前端以 SHA‑256 雜湊後傳輸密碼，後端比對雜湊值，避免明文傳輸。

3. **獨立控制上傳／刪除**
   - 在 `config.py` 透過 `allow_upload` 和 `allow_delete` 屬性，可分別啟用或關閉上傳與刪除功能。
   - 前端 `index.html` 會依 `window.ALLOW_UPLOAD` 與 `window.ALLOW_DELETE` 來顯示「上傳」及「刪除」按鈕。

4. **響應式前端 (RWD)**
   - 使用 Bootstrap 5 grid 系統與 Vue 3，畫面自動適應手機、平板、桌機。
   - 檔案以卡片形式列出，可雙擊進入資料夾，或點擊縮圖（Thumbnail）預覽大圖。

5. **縮圖預覽 (Thumbnail)**
   - 對一般影像檔 (.jpg/.png/.gif/.bmp/.tif/.tiff) 使用 Pillow 產生縮圖；對 RAW 檔 (.cr2/.nef/.arw/.dng/.cr3) 以 rawpy 半尺解碼並轉為縮圖。
   - 支援**懶載入**：透過 `IntersectionObserver`，只載入可視區域及上下 buffer 的縮圖，並自動按上至下順序觸發。
   - Endpoint：  
     ```
     GET /<space>/api/thumbnail?path=<rel_path>
     ```

6. **原圖預覽 (Raw Preview)**
   - 在 Modal 彈窗中顯示無壓縮大圖：對 RAW 檔全尺解碼後以 Pillow 輸出 JPEG，對一般影像直接回傳。
   - 具備「下載」按鈕，可將原檔下載。  
   - Endpoint：  
     ```
     GET /<space>/api/raw?path=<rel_path>
     ```

7. **檔案下載 (Download)**
   - 可下載所有允許副檔名的檔案（image + RAW）。  
   - Endpoint：  
     ```
     GET /<space>/api/download?path=<rel_path>
     ```

8. **檔案刪除 (Delete)**
   - 透過  
     ```
     POST /<space>/api/delete
     ```
     刪除單一檔案（不支援資料夾刪除）。
   - 只有在該空間的 `allow_delete: True` 時才可呼叫，否則回應 403。

9. **EXIF / Metadata 顯示**
   - RAW 檔使用 exifread 解析完整 EXIF；JPEG/PNG 使用 Pillow + ExifTags 擷取常見欄位（ISO、快門、光圈、相機/鏡頭型號、拍攝時間）。
   - 點擊「內容」可在右側側欄顯示詳細檔案資訊。

10. **Google Drive 風格側欄**
    - 側欄固定在右側，顯示檔案名稱、大小、解析度、製造商、相機型號、鏡頭型號、ISO、快門、光圈、拍攝時間等。

11. **後台管理 (Admin Console)**
    - 位於 `/admin`，需先登入（密碼設定於 `config.py: ADMIN_PASS`）。
    - 提供 GUI 方式新增/編輯/刪除空間，設定：  
      - **key** (URL 前綴)  
      - **path** (物理資料夾)  
      - **encrypted** (是否加密)  
      - **password** (加密密碼)  
      - **allow_upload** (上傳)  
      - **allow_delete** (刪除)  
    - 也可動態編輯全域上傳/下載允許副檔名。  
    - 所有變更會寫入 `spaces.json`，重啟服務後持久保留。

---

## 前置需求

- **Python 3.7 以上**  
- 系統需安裝 [ExifTool](https://exiftool.org/)，並可由命令列呼叫 `exiftool`  
- 建議使用虛擬環境 (venv / conda)  

---

## 安裝與啟動

1. **Clone 本專案**  
   ```bash
   git clone https://github.com/HongMJ1315/simple_drive.git
   cd simple_drive
````

2. **建立並啟用虛擬環境**

   ```bash
   python -m venv venv
   # Linux/macOS
   source venv/bin/activate
   # Windows
   venv\Scripts\activate
   ```

3. **安裝套件**

   ```bash
   pip install -r requirements.txt
   ```

4. **(選填) 設定環境變數**

   ```bash
   export FLASK_SECRET="你的隨機字串"
   export ADMIN_PASS="後台管理密碼"
   ```

5. **啟動伺服器**

   ```bash
   export FLASK_APP=app.py
   export FLASK_ENV=development
   flask run --host=0.0.0.0 --port=5000
   ```

6. **使用瀏覽器**

   * 前端：`http://127.0.0.1:5000/`
   * 管理：`http://127.0.0.1:5000/admin/login`

---

## `config.py` 設定範例

```python
import os, json

# Flask 加密用 secret
FLASK_SECRET = os.environ.get('FLASK_SECRET') or '你的隨機字串'
# Admin 登入密碼
ADMIN_PASS   = os.environ.get('ADMIN_PASS')   or 'admin123'

# 支援的副檔名
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tif', '.tiff'}
RAW_EXTS   = {'.cr2', '.nef', '.arw', '.raf', '.rw2', '.dng', '.cr3'}

# 多資料夾空間動態讀取於 spaces.json
BASE_DIR    = os.path.dirname(__file__)
SPACES_FILE = os.path.join(BASE_DIR, 'spaces.json')
with open(SPACES_FILE, 'r', encoding='utf-8') as f:
    SPACES  = json.load(f)
```

---

### `spaces.json` 範例

```json
{
  "shbsb": {
    "path": "C:/path/to/folder1",
    "encrypted": false,
    "allow_upload": false,
    "allow_delete": false
  },
  "jakxjs": {
    "path": "C:/path/to/folder2",
    "encrypted": true,
    "password": "123",
    "allow_upload": true,
    "allow_delete": true
  }
}
```

---

## 目錄結構

```
├── app.py               # Flask 主程式
├── config.py            # 設定檔（space/ext/secret/admin…）
├── spaces.json          # 可編輯空間列表，Admin API 持久化
├── requirements.txt
├── templates/
│   ├── spaces.html       # 空間列表
│   ├── login.html        # 密碼頁
│   ├── index.html        # 主畫面 Vue 模板
│   ├── admin_login.html  # Admin 登入頁
│   └── admin.html        # Admin GUI 控制台
├── static/
│   ├── css/style.css
│   └── js/app.js         # Vue 3 + IntersectionObserver 懶載入
└── README.md
```

```
