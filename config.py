import os, json

# Flask 加密用 secret
FLASK_SECRET = os.environ.get('FLASK_SECRET') or 'secret_code'
# Admin 登入密碼
ADMIN_PASS   = os.environ.get('ADMIN_PASS')   or 'admin123'

# 支援的副檔名
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tif', '.tiff'}
RAW_EXTS   = {'.cr2', '.nef', '.arw', '.raf', '.rw2', '.dng', '.cr3'}
DRIVE_ROOT = ""
SETTINGS = {
  "upload_exts": [
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".tif",
    ".tiff"
  ],
  "download_exts": [
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".tif",
    ".tiff",
    ".cr2",
    ".nef",
    ".arw",
    ".raf",
    ".rw2",
    ".dng",
    ".cr3"
  ]
}
# 多資料夾空間動態讀取於 spaces.json
BASE_DIR    = os.path.dirname(__file__)
SPACES_FILE = os.path.join(BASE_DIR, 'spaces.json')
with open(SPACES_FILE, 'r', encoding='utf-8') as f:
    SPACES  = json.load(f)