# Cloud Drive Viewer

這是一個以 Flask 為後端、Vue + Bootstrap 為前端實現的「雲端硬碟」瀏覽與預覽工具，並支援多資料夾空間、密碼保護、影像縮圖、RAW 檔解碼、EXIF 資訊顯示等功能。

## 功能特色

1. **多資料夾空間 (Spaces)**

   * 在 `SPACES` 字典中設定多個隨機路徑前綴 (e.g. `jakxjs`, `shbsb`)，各自對應不同物理資料夾。
   * 根目錄 `/` 顯示所有註冊空間列表，點擊即可進入相應空間。

2. **資料夾加密保護**

   * 可針對指定空間開啟密碼保護 (encrypted=True)，未登入者將被導向密碼頁面。
   * 登入後以 Session 記錄授權狀態。

3. **響應式前端 (RWD)**

   * 使用 Bootstrap grid 系統與 Vue3，畫面自動適應手機、平板、桌機。
   * 檔案以卡片形式列出，可雙擊進入資料夾或點擊縮圖預覽大圖。

4. **縮圖預覽 (Thumbnail)**

   * 對一般影像檔 (.jpg/.png/.gif) 直接以 Pillow 縮圖。
   * 對 RAW 檔 (.cr2/.nef/.arw/.dng/.cr3 等) 以 rawpy 半尺解碼，再轉成縮圖。
   * Endpoint: `GET /<space>/api/thumbnail?path=<rel_path>`。

5. **原檔預覽 (Raw Preview)**

   * 一鍵在 Modal 彈窗顯示無壓縮大圖。
   * RAW 檔使用 rawpy 全尺解碼並以 Pillow 輸出 JPEG；一般影像直接回傳原檔。
   * Endpoint: `GET /<space>/api/raw?path=<rel_path>`。

6. **檔案下載 (Download)**

   * 下載任何格式檔案 (含 RAW)。
   * Endpoint: `GET /<space>/api/download?path=<rel_path>`。

7. **EXIF / Metadata 偵測**

   * 對 RAW 檔呼叫系統 ExifTool 取得完整 Tag (含 CR3)，並以 JSON 回傳。
   * 對 JPEG/PNG 使用 Pillow + ExifTags 擷取常見欄位 (ISO、快門、光圈、相機/鏡頭型號、拍攝時間)。
   * Endpoint: `GET /<space>/api/metadata?path=<rel_path>`。

8. **Google Drive 風格側欄**

   * 點擊「內容」按鈕，在右側固定面板顯示檔案細節。
   * 可隨時關閉側欄。

## 前置需求

* **Python 3.7 以上**
* **系統安裝 [ExifTool](https://exiftool.org/)**，需可從命令列呼叫 `exiftool`。
* 建議建立虛擬環境 (venv / conda)。

## 安裝與啟動

1. 下載或 clone 本專案：

   ```bash
   git clone https://github.com/你的帳號/your-repo.git
   cd your-repo
   ```

2. 建立並啟用虛擬環境：

   ```bash
   python -m venv venv
   source venv/bin/activate    # Linux / macOS
   venv\Scripts\activate     # Windows
   ```

3. 安裝 Python 套件：

   ```bash
   pip install -r requirements.txt
   ```

4. 設定環境變數（選填）：

   ```bash
   export FLASK_SECRET="你的隨機字串"
   ```

5. 執行 Flask 伺服器：

   ```bash
   export FLASK_APP=app.py
   export FLASK_ENV=development
   flask run --host=0.0.0.0 --port=5000
   ```

   Windows PowerShell：

   ```powershell
   $env:FLASK_APP = "app.py"
   $env:FLASK_ENV = "development"
   flask run --host=0.0.0.0 --port=5000
   ```

6. 打開瀏覽器，前往 `http://127.0.0.1:5000/`，選擇空間並開始瀏覽。

## 設定多資料夾與密碼

在 `app.py` 中修改 `SPACES` 字典：

```python
SPACES = {
  'shbsb': { 'path': r'C:/path/to/folder1', 'encrypted': False },
  'jakxjs': { 'path': r'C:/path/to/folder2', 'encrypted': True, 'password': '1234' },
}
```

* **key**：URL 路徑前綴 (訪問時使用 `http://.../<key>/`)。
* **path**：對應的磁碟資料夾。
* **encrypted**：是否啟用密碼保護。
* **password**：若加密則為該空間的密碼。

## 設定多資料夾與密碼

在 `app.py` 中修改 `SPACES` 字典：

```python
SPACES = {
  'shbsb': { 'path': r'C:/path/to/folder1', 'encrypted': False },
  'jakxjs': { 'path': r'C:/path/to/folder2', 'encrypted': True, 'password': '1234' },
}
```

* **key**：URL 路徑前綴 (訪問時使用 `http://.../<key>/`)。
* **path**：對應的磁碟資料夾。
* **encrypted**：是否啟用密碼保護。
* **password**：若加密則為該空間的密碼。

## 使用 config.py 進行設定拆分

為了讓專案更易於維護，我們已將所有空間設定與相關常數抽出到獨立的 `config.py`：

```python
# config.py

import os

# Flask 用的 secret
FLASK_SECRET = os.environ.get('FLASK_SECRET') or '你自己設的隨機字串'

# 支援的影像與 RAW 副檔名
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}
RAW_EXTS   = {'.cr2', '.nef', '.arw', '.raf', '.rw2', '.dng', '.cr3'}

# 多個空間的設定：path, encrypted, password, allow_upload
SPACES = {
    'shbsb': {
        'path': r'Your Folder Path',
        'encrypted': False,
        'allow_upload': False
    },
    'jakxjs': {
        'path': r'Your Folder Path',
        'encrypted': True,
        'password': '123',
        'allow_upload': True
    },
}
```

在 `app.py` 中載入並使用 `config.py` 中的常數：

```python
import config

IMAGE_EXTS = config.IMAGE_EXTS
RAW_EXTS   = config.RAW_EXTS
SPACES     = config.SPACES
app.secret_key = config.FLASK_SECRET
```

這樣做能將設定集中管理，方便日後調整與維護。

## 前端技術

* Vue 3
* Bootstrap 5
* Bootstrap Icons

## 目錄結構

```
├── app.py
├── config.py        # 集中化設定檔
├── requirements.txt
├── templates/
│   ├── spaces.html   # 根目錄列表
│   ├── login.html    # 密碼輸入頁
│   └── index.html    # 主畫面 + Vue 模板
├── static/
│   ├── css/style.css
│   └── js/app.js
└── README.md
```
