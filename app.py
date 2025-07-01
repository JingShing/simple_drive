from flask import (
    Flask, jsonify, send_from_directory, send_file,
    request, abort, render_template, session,
    redirect, url_for, flash
)
from PIL import Image, ExifTags, UnidentifiedImageError
from PIL.TiffImagePlugin import IFDRational
from io import BytesIO
from functools import wraps
from hashlib import sha256
import json
import os
import rawpy
import exifread
import imageio
import subprocess
import config
import numpy as np


IMAGE_EXTS = set(config.SETTINGS['download_exts'])  # 只要上傳／預覽的 ext
# RAW ext 還是從 config.py RAW_EXTS
RAW_EXTS = set(config.RAW_EXTS)
app = Flask(__name__, static_folder='static', template_folder='templates')
# 用於 session 加密
app.secret_key = config.FLASK_SECRET


SPACES = config.SPACES
SPACES_FILE = config.SPACES_FILE


def get_space_cfg(space):
    cfg = SPACES.get(space)
    if not cfg:
        abort(404)
    return cfg


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        space = kwargs.get('space') or request.view_args.get('space')
        cfg = get_space_cfg(space)
        if cfg.get('encrypted'):
            auth = session.get('authorized_spaces', [])
            if space not in auth:
                return redirect(url_for('login', space=space))
        return func(*args, **kwargs)
    return wrapper


def secure_path(base_dir, rel_path):
    # 防止「../」跨越
    safe = os.path.abspath(base_dir)
    full = os.path.abspath(os.path.join(safe, rel_path))
    if not full.startswith(safe):
        abort(403)
    return full

# ─── 根頁面：顯示所有空間 ─────────────────────


@app.route('/')
def root():
    spaces = [
        {'key': key, 'encrypted': cfg['encrypted']}
        for key, cfg in SPACES.items()
    ]
    return render_template('spaces.html', spaces=spaces)

# ─── 加密空間的登入頁 ────────────────────────


@app.route('/<space>/login', methods=['GET', 'POST'])
def login(space):
    cfg = get_space_cfg(space)
    if not cfg.get('encrypted'):
        return redirect(url_for('browse', space=space))

    error = None
    if request.method == 'POST':

        # 前端送來的是 password_hash（SHA-256(hex)），
        # 後端用 cfg['password'] 做 SHA-256，再比對兩個 hex
        received_hash = request.form.get('password_hash', '')
        expected_hash = sha256(cfg['password'].encode()).hexdigest()
        print(received_hash, expected_hash)
        if received_hash == expected_hash:
            auth = session.get('authorized_spaces', [])
            auth.append(space)
            session['authorized_spaces'] = auth
            return redirect(url_for('browse', space=space))
        else:
            error = '密碼錯誤，請重試'
    return render_template('login.html', space=space, error=error)

# ─── 瀏覽某個空間 ────────────────────────────


@app.route('/<space>/')
@login_required
def browse(space):
    # space 傳給前端，用來組 API 路徑
    cfg = get_space_cfg(space)
    return render_template(
        'index.html',
        space=space,
        allow_upload=cfg.get('allow_upload', False),
        allow_delete=cfg.get('allow_delete', False)
    )

# ─── 列出資料夾內容 API ──────────────────────


@app.route('/<space>/api/list')
@login_required
def api_list(space):
    rel_path = request.args.get('path', '')
    cfg = get_space_cfg(space)
    folder = secure_path(cfg['path'], rel_path)
    items = []
    for entry in os.scandir(folder):
        ext = os.path.splitext(entry.name)[1].lower()

        items.append({
            'name': entry.name,
            'path': os.path.join(rel_path, entry.name).replace(os.sep, '/'),
            'is_dir':  entry.is_dir(),
            # RAW 也算「圖片」，才能顯示 <img>、觸發 openModal
            'is_image': entry.is_file() and (ext in IMAGE_EXTS or ext in RAW_EXTS)
        })
    return jsonify(items)

# ─── 下載檔案 API ────────────────────────────


@app.route('/<space>/api/download')
@login_required
def api_download(space):
    rel = request.args.get('path', '')
    cfg = get_space_cfg(space)
    rel = rel.lstrip('/')
    folder = os.path.dirname(rel)
    name = os.path.basename(rel)
    folder_full = secure_path(cfg['path'], folder)

    # 嚴格檢查副檔名
    allowed = set(config.SETTINGS.get('download_exts', []))
    ext = os.path.splitext(name)[1].lower()
    if ext not in allowed:
        abort(403)

    return send_from_directory(folder_full, name, as_attachment=True)

# ─── 縮圖 API ────────────────────────────────


@app.route('/<space>/api/thumbnail')
@login_required
def api_thumbnail(space):
    rel = request.args.get('path', '').lstrip('/')
    cfg = get_space_cfg(space)
    file_full = secure_path(cfg['path'], rel)
    ext = os.path.splitext(file_full)[1].lower()

    try:
        if ext in RAW_EXTS:
            with rawpy.imread(file_full) as raw:
                rgb = raw.postprocess(use_camera_wb=True, half_size=True)
            img = Image.fromarray(rgb)

        else:
            try:
                # 先用 Pillow 打开
                img = Image.open(file_full)
                img.load()
            except UnidentifiedImageError:
                # Pillow 打不开时，用 imageio 读
                arr = imageio.imread(file_full)

                # 如果是浮点型，就映射到 0–255，再转 uint8
                if issubclass(arr.dtype.type, np.floating):
                    arr = np.clip(arr * 255, 0, 255).astype(np.uint8)
                else:
                    arr = arr.astype(np.uint8)

                img = Image.fromarray(arr)

            # 有些 TIFF 可能是单波道、CMYK、16 位，统一转 RGB
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')

        # 生成缩略图
        img.thumbnail((200, 200))
        buf = BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return send_file(buf, mimetype='image/png')

    except Exception as e:
        app.logger.error(f"Thumbnail 失敗 {file_full}: {e}")
        abort(404)

# ─── 原檔 API（inline 顯示，不會當 attachment） ───────────────────


@app.route('/<space>/api/raw')
@login_required
def api_raw(space):
    # 和 download 類似，但 as_attachment=False
    rel = request.args.get('path', '').lstrip('/')
    cfg = get_space_cfg(space)
    folder = os.path.dirname(rel)
    name = os.path.basename(rel)
    # file_full = secure_path(cfg['path'], rel)
    # folder_full = secure_path(cfg['path'], folder)
    file_full = secure_path(cfg['path'], rel)

    ext = os.path.splitext(file_full)[1].lower()

    # 任何非 image/raw 的副檔名都拒絕
    if ext not in IMAGE_EXTS and ext not in RAW_EXTS:
        abort(403)

    # 如果是 RAW，先 decode 成 JPEG 再回傳
    if ext in RAW_EXTS:
        try:
            # with rawpy.imread(file_full) as raw:
            #     rgb = raw.postprocess(use_camera_wb=True)
            # buf = BytesIO()
            # imageio.imsave(buf, rgb, format='JPEG')
            with rawpy.imread(file_full) as raw:
                # full-size 解碼
                rgb = raw.postprocess(use_camera_wb=True)
            # 用 PIL 存成 JPEG
            img = Image.fromarray(rgb)
            buf = BytesIO()
            img.save(buf, 'JPEG')
            buf.seek(0)
            print("Get RAW")
            return send_file(buf, mimetype='image/jpeg')
        except:
            abort(404)
    else:
        # 不是 RAW，直接送原檔
        folder = os.path.dirname(rel)
        name = os.path.basename(rel)
        folder_full = secure_path(cfg['path'], folder)
        return send_from_directory(folder_full, name, as_attachment=False)


@app.route('/<space>/api/upload', methods=['POST'])
@login_required
def api_upload(space):
    cfg = get_space_cfg(space)
    if not cfg.get('allow_upload'):
        abort(403)

    uploaded = request.files.get('file')
    rel_path = request.form.get('path', '').lstrip('/')
    target_dir = secure_path(cfg['path'], rel_path)

    if not uploaded:
        abort(400, description='沒有傳任何檔案過來')

    filename = uploaded.filename
    # 1. 檔名基本檢查
    if filename == '' or '/' in filename or '\\' in filename:
        abort(400, description='不合法檔名')

    # 2. 副檔名檢查
    # 動態從 settings.json 中讀
    allowed_up = set(config.SETTINGS.get('upload_exts', []))
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_up:
        abort(400, description=f'不支援的副檔名：{ext}')

    # 3. 存檔
    dest = os.path.join(target_dir, filename)
    uploaded.save(dest)
    return jsonify({'success': True, 'filename': filename})


@app.route('/<space>/api/delete', methods=['POST'])
@login_required
def api_delete(space):
    cfg = get_space_cfg(space)
    if not cfg.get('allow_delete'):
        abort(403)
    data = request.get_json() or {}
    rel = data.get('path', '').lstrip('/')
    file_full = secure_path(cfg['path'], rel)
    # 我們只允許刪除檔案，不允許刪除資料夾
    if os.path.isdir(file_full):
        abort(400, '不支援刪除資料夾')
    try:
        os.remove(file_full)
        return jsonify({'success': True})
    except Exception as e:
        abort(500, str(e))


@app.route('/<space>/api/metadata')
@login_required
def api_metadata(space):
    rel = request.args.get('path', '').lstrip('/')
    cfg = get_space_cfg(space)
    file_full = secure_path(cfg['path'], rel)
    ext = os.path.splitext(file_full)[1].lower()

    info = {
        'filename': os.path.basename(file_full),
        'filesize': os.path.getsize(file_full),
    }

    try:
        if ext in RAW_EXTS:
            # 1. 先用 rawpy 取得原始尺寸
            with rawpy.imread(file_full) as raw:
                h, w = raw.raw_image.shape
            info['resolution'] = f"{w}×{h}"

            # 2. 用 ExifTool 讀完整 EXIF（-j 輸出 JSON）
            res = subprocess.run(
                ['exiftool', '-j', file_full],
                capture_output=True,
                text=True,
                check=True
            )
            data = json.loads(res.stdout)[0]  # 取得第一筆

            # 3. 從 data 抽取你想要的欄位
            info.update({
                'Make':      data.get('Make'),
                'Camera':    data.get('Model'),
                'LensModel': data.get('LensModel'),
                'ISO':       data.get('ISO'),
                'ShutterSpeed': data.get('ExposureTime'),
                'Aperture':  data.get('FNumber'),
                'DateTime':  data.get('DateTimeOriginal') or data.get('CreateDate'),
            })
        else:
            # JPEG/PNG 用原本的 PIL + ExifTags
            img = Image.open(file_full)
            info['resolution'] = f"{img.width}×{img.height}"
            exif = img._getexif() or {}
            inv = {v: k for k, v in ExifTags.TAGS.items()}

            def serialize(val):
                if hasattr(val, 'numerator') and hasattr(val, 'denominator'):
                    return f"{val.numerator}/{val.denominator}"
                return val

            def get_tag(name):
                tid = inv.get(name)
                return serialize(exif.get(tid)) if tid else None

            info.update({
                'Make':         get_tag('Make'),
                'Camera':       get_tag('Model'),
                'LensModel':    get_tag('LensModel'),
                'ISO':          get_tag('ISOSpeedRatings'),
                'ShutterSpeed': get_tag('ShutterSpeedValue'),
                'Aperture':     get_tag('FNumber'),
                'DateTime':     get_tag('DateTimeOriginal') or get_tag('DateTime')
            })

        return jsonify(info)
    except subprocess.CalledProcessError as e:
        app.logger.error(f"exiftool error: {e.stderr}")
        abort(500, '無法讀取 Raw EXIF')
    except Exception as e:
        app.logger.error(f"metadata error {file_full}: {e}")
        abort(404)


def admin_required(f):
    @wraps(f)
    def w(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin_login', next=request.path))
        return f(*args, **kwargs)
    return w

# ─── Admin 登录 ───────────────────────────


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        pw = request.form.get('password', '')
        if pw == config.ADMIN_PASS:
            session['is_admin'] = True
            return redirect(request.args.get('next') or url_for('admin_index'))
        else:
            error = '密碼錯誤'
    return render_template('admin_login.html', error=error)

# ─── Admin 登出 ───────────────────────────


@app.route('/admin/logout')
@admin_required
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('admin_login'))

# ─── Admin Dashboard: 列表 & 新增/編輯表單 ─────────


@app.route('/admin')
@admin_required
def admin_index():
    return render_template(
        'admin.html',
        spaces=SPACES,
        settings=config.SETTINGS    # <<< 一定要传这个！
    )

# ─── Admin API: 新增或更新 Space ─────────────────


@app.route('/admin/api/save', methods=['POST'])
@admin_required
def admin_save():
    data = request.get_json()
    key = data.get('key', '').strip()
    # 基本驗證
    if not key:
        return jsonify({'error': 'Key 不能為空'}), 400
    SPACES[key] = {
        'path':         data.get('path', ''),
        'encrypted':    data.get('encrypted', False),
        'password':     data.get('password', ''),
        'allow_upload': data.get('allow_upload', False),
        'allow_delete': data.get('allow_delete', False)
    }
    # 寫回 spaces.json
    with open(SPACES_FILE, 'w', encoding='utf-8') as f:
        json.dump(SPACES, f, ensure_ascii=False, indent=2)
    flash(f"已儲存空間 {key}")
    return jsonify({'success': True})

# ─── Admin API: 刪除 Space ────────────────────


@app.route('/admin/api/delete', methods=['POST'])
@admin_required
def admin_delete_space():
    data = request.get_json()
    key = data.get('key')
    if key in SPACES:
        SPACES.pop(key)
        with open(SPACES_FILE, 'w', encoding='utf-8') as f:
            json.dump(SPACES, f, ensure_ascii=False, indent=2)
        return jsonify({'success': True})
    return jsonify({'error': '找不到該空間'}), 404

# ─── Admin API: 更新全域副檔名白名單 ──────────────


@app.route('/admin/api/settings', methods=['POST'])
@admin_required
def admin_save_settings():
    data = request.get_json() or {}
    # 把新的配置写文件
    with open(config.SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # **同步刷新内存里的 SETTINGS**：
    config.SETTINGS = data
    # **同时刷新 IMAGE_EXTS** 供 thumbnail 路由使用
    global IMAGE_EXTS
    IMAGE_EXTS = set(config.SETTINGS.get('upload_exts', []))
    return jsonify({'success': True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
