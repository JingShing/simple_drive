[繁體中文](README.md) | English

# Cloud Drive Viewer

A “cloud drive” browsing and preview tool built with **Flask** (backend) and **Vue + Bootstrap** (frontend). It supports multiple folder spaces, password protection, image thumbnails, RAW decoding, EXIF display, per-space upload/delete controls, lazy-loading thumbnails, and an Admin Console.

## Features

1. **Multiple Spaces**

   - Configure multiple random URL prefixes (e.g., `jakxjs`, `shbsb`) in the `SPACES` dictionary in `config.py`, each mapping to a different physical folder.
   - The root path `/` lists all registered spaces; click to enter a space.

2. **Password Protection (Encryption)**

   - You can enable password protection per space (`encrypted: True`). Visitors who aren’t logged in will be redirected to a password page.
   - The frontend hashes the password with **SHA-256** before sending; the backend compares the hash to avoid plain-text transmission.

3. **Independent Upload/Delete Controls**

   - In `config.py`, use `allow_upload` and `allow_delete` to independently enable or disable uploading and deleting.
   - The frontend `index.html` shows “Upload” and “Delete” buttons based on `window.ALLOW_UPLOAD` and `window.ALLOW_DELETE`.

4. **Responsive Frontend (RWD)**

   - Built with **Bootstrap 5** grid + **Vue 3**, adapting to mobile, tablet, and desktop.
   - Files are shown as cards; double-click to enter a folder, or click a thumbnail to preview a large image.

5. **Thumbnails**

   - Uses **Pillow** to generate thumbnails for common image formats (.jpg/.png/.gif/.bmp/.tif/.tiff), and **rawpy** (half-size decode) for RAW formats (.cr2/.nef/.arw/.dng/.cr3), then converts to thumbnails.

   - **Lazy loading** via `IntersectionObserver`: only loads thumbnails in the viewport plus a buffer above/below, in top-to-bottom order.

   - Endpoint:

     ```
     GET /<space>/api/thumbnail?path=<rel_path>
     ```

6. **Raw Preview (Full Image)**

   - Shows the full image in a modal: RAW files are fully decoded then output as JPEG via Pillow; regular images are returned directly.

   - Includes a **Download** button to fetch the original file.

   - Endpoint:

     ```
     GET /<space>/api/raw?path=<rel_path>
     ```

7. **Download**

   - Download any allowed file extension (images + RAW).

   - Endpoint:

     ```
     GET /<space>/api/download?path=<rel_path>
     ```

8. **Delete**

   - Delete a single file (folders not supported) via:

     ```
     POST /<space>/api/delete
     ```

   - Only available when `allow_delete: True` for that space; otherwise returns **403**.

9. **EXIF / Metadata Display**

   - RAW files: parse full EXIF using **exifread**.
      JPEG/PNG: use **Pillow + ExifTags** to extract common fields (ISO, shutter, aperture, camera/lens model, capture time).
   - Click “Details” to show file info in the right sidebar.

10. **Google Drive-style Sidebar**

    - Fixed right-hand sidebar showing filename, size, resolution, maker, camera model, lens model, ISO, shutter, aperture, capture time, etc.

11. **Admin Console**

    - Located at `/admin`, login required (password in `config.py: ADMIN_PASS`).
    - GUI to add/edit/delete spaces with:
      - **key** (URL prefix)
      - **path** (physical folder)
      - **encrypted** (enable password)
      - **password** (space password)
      - **allow_upload**
      - **allow_delete**
    - Also lets you edit global allowed upload/download extensions.
    - All changes are written to `spaces.json` and persist after restart.

------

## Prerequisites

- **Python 3.7+**
- **ExifTool** installed and available as `exiftool` on your PATH
- A virtual environment (venv/conda) is recommended

------

## Installation & Run

1. **Clone the repo**

   ```bash
   git clone https://github.com/HongMJ1315/simple_drive.git
   cd simple_drive
   ```

2. **Create & activate a virtual environment**

   ```bash
   python -m venv venv
   # Linux/macOS
   source venv/bin/activate
   # Windows
   venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **(Optional) Set environment variables**

   ```bash
   export FLASK_SECRET="your-random-string"
   export ADMIN_PASS="your-admin-password"
   ```

5. **Start the server**

   ```bash
   export FLASK_APP=app.py
   export FLASK_ENV=development
   flask run --host=0.0.0.0 --port=5000
   ```

6. **Open in browser**

   - Frontend: `http://127.0.0.1:5000/`
   - Admin: `http://127.0.0.1:5000/admin/login`

------

## `config.py` example

```python
import os, json

# Flask secret
FLASK_SECRET = os.environ.get('FLASK_SECRET') or 'secret_code'
# Admin login password
ADMIN_PASS   = os.environ.get('ADMIN_PASS')   or 'admin123'

# Supported extensions
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
# Spaces are loaded dynamically from spaces.json
BASE_DIR    = os.path.dirname(__file__)
SPACES_FILE = os.path.join(BASE_DIR, 'spaces.json')
with open(SPACES_FILE, 'r', encoding='utf-8') as f:
    SPACES  = json.load(f)
```

------

### `spaces.json` example

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

------

### `exts.json` example

```json
{
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
```

------

## Project Structure

```
├── app.py               # Flask application
├── config.py            # Settings (spaces/exts/secret/admin…)
├── spaces.json          # Editable spaces; persisted by Admin API
├── exts.json            # Allowed upload/download extensions
├── requirements.txt
├── templates/
│   ├── spaces.html       # Space list
│   ├── login.html        # Password page
│   ├── index.html        # Main Vue template
│   ├── admin_login.html  # Admin login
│   └── admin.html        # Admin console (GUI)
├── static/
│   ├── css/style.css
│   └── js/app.js         # Vue 3 + IntersectionObserver lazy loading
└── README.md
```