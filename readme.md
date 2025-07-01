# Cloud Drive Viewer

這是一個以 Flask 為後端、Vue + Bootstrap 為前端實現的「雲端硬碟」瀏覽與預覽工具，支援多資料夾空間、密碼保護、影像縮圖、RAW 檔解碼、EXIF 資訊顯示、上傳／刪除功能控制，以及縮圖懶載入等特色。

## 功能特色

1. **多資料夾空間 (Spaces)**

   * 可在 `config.py` 中於 `SPACES` 字典設定多個隨機路徑前綴（如 `jakxjs`、`shbsb`），分別對應不同的物理資料夾。
   * 根目錄 `/` 顯示所有註冊空間列表，點擊即可進入相應空間。

2. **密碼保護 (Encryption)**

   * 支援針對單一空間開啟密碼保護 (`encrypted: True`)，未登入者會被導向密碼輸入頁面。
   * 前端以 SHA‑256 雜湊後傳輸密碼，後端比對雜湊值，避免明文傳輸。

3. **獨立控制上傳／刪除**

   * 在 `config.py` 透過 `allow_upload` 和 `allow_delete` 屬性，可分別啟用或關閉上傳與刪除功能。
   * 前端 `index.html` 會依 `window.ALLOW_UPLOAD` 與 `window.ALLOW_DELETE` 來顯示「上傳」及「刪除」按鈕。

4. **響應式前端 (RWD)**

   * 使用 Bootstrap 5 grid 系統與 Vue 3，畫面自動適應手機、平板、桌機。
   * 檔案以卡片形式列出，可雙擊進入資料夾，或點擊縮圖（Thumbnail）預覽大圖。

5. **縮圖預覽 (Thumbnail)**

   * 對一般影像檔 (.jpg/.png/.gif/.bmp) 使用 Pillow 產生縮圖；對 RAW 檔 (.cr2/.nef/.arw/.dng/.cr3) 以 rawpy 半尺解碼並轉為縮圖。
   * 支援**懶載入**：透過 IntersectionObserver，只載入可視區域及上下 buffer 的縮圖，並自動按上至下順序觸發。
   * Endpoint：`GET /<space>/api/thumbnail?path=<rel_path>`。

6. **原圖預覽 (Raw Preview)**

   * 在 Modal 彈窗中顯示無壓縮大圖：對 RAW 檔全尺解碼後以 Pillow 輸出 JPEG，對一般影像直接回傳。
   * 具備「下載」按鈕，可將原檔下載。
   * Endpoint：`GET /<space>/api/raw?path=<rel_path>`。

7. **檔案下載 (Download)**

   * 可下載所有允許副檔名的檔案（image + RAW）。
   * Endpoint：`GET /<space>/api/download?path=<rel_path>`。

8. **檔案刪除 (Delete)**

   * 透過 `POST /<space>/api/delete` 路由刪除單一檔案（不支援資料夾刪除）。
   * 只有在該空間的 `allow_delete=True` 時才可呼叫，否則回應 403。

9. **EXIF / Metadata 顯示**

   * RAW 檔以 exifread 解析完整 EXIF，JPEG/PNG 使用 Pillow + ExifTags 擷取常見欄位（ISO、快門、光圈、相機/鏡頭型號、拍攝時間）。
   * 點擊「內容」可在右側側欄顯示詳細檔案資訊。

10. **Google Drive 風格側欄**

    * 側欄固定在右側，顯示檔案名稱、大小、解析度、製造商、相機型號、鏡頭型號、ISO、快門、光圈、拍攝時間等。

## 前置需求

* **Python 3.7 以上**
* 系統需安裝 [ExifTool](https://exiftool.org/)，並可由命令列呼叫 `exiftool`
* 建議使用虛擬環境 (venv / conda)

## 安裝與啟動

1. Clone 本專案：

   ```bash
   git clone https://github.com/HongMJ1315/simple_drive.git
   cd your-repo
   ```

2. 建立並啟用虛擬環境：

   ```bash
   python -m venv venv
   # Linux/macOS
   source venv/bin/activate
   # Windows
   venv\Scripts\activate
   ```

3. 安裝套件：

   ```bash
   pip install -r requirements.txt
   ```

4. （選填）設定環境變數：

   ```bash
   export FLASK_SECRET="你的隨機字串"
   ```

5. 啟動伺服器：

   ```bash
   export FLASK_APP=app.py
   export FLASK_ENV=development
   flask run --host=0.0.0.0 --port=5000
   ```

6. 在瀏覽器開啟 `http://127.0.0.1:5000/`，選擇空間並開始使用

## `config.py` 設定範例

```python
import os

# Flask 加密用 secret
FLASK_SECRET = os.environ.get('FLASK_SECRET') or '你的隨機字串'

# 支援的副檔名
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}
RAW_EXTS   = {'.cr2', '.nef', '.arw', '.raf', '.rw2', '.dng', '.cr3'}

# 資料空間設定
# allow_upload: 是否顯示上傳按鈕
# allow_delete: 是否顯示刪除按鈕
SPACES = {
    'shbsb': {
        'path': r'C:/path/to/folder1',
        'encrypted': False,
        'allow_upload': False,
        'allow_delete': False
    },
    'jakxjs': {
        'path': r'C:/path/to/folder2',
        'encrypted': True,
        'password': '123',
        'allow_upload': True,
        'allow_delete': True
    },
}
```

在 `app.py` 載入設定：

```python
import config
IMAGE_EXTS    = config.IMAGE_EXTS
RAW_EXTS      = config.RAW_EXTS
SPACES        = config.SPACES
app.secret_key = config.FLASK_SECRET
```

## 目錄結構

```
├── app.py         # Flask 主程式
├── config.py      # 設定檔（space, ext, secret...）
├── requirements.txt
├── templates/
│   ├── spaces.html  # 空間列表
│   ├── login.html   # 密碼頁
│   └── index.html   # 主畫面 Vue 模板
├── static/
│   ├── css/style.css
│   └── js/app.js   # Vue 3 + IntersectionObserver 懶載入
└── README.md
```
