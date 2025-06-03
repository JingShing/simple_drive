import os
from flask import (
    Flask, jsonify, send_from_directory, send_file,
    request, abort, render_template, session,
    redirect, url_for
)
from PIL import Image, ExifTags
from PIL.TiffImagePlugin import IFDRational

from io import BytesIO
from functools import wraps
import rawpy
import exifread
import imageio

IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}

RAW_EXTS = {'.cr2', '.nef', '.arw', '.raf', '.rw2', '.dng', '.cr3'}

app = Flask(__name__, static_folder='static', template_folder='templates')
# 用於 session 加密
app.secret_key = os.environ.get('FLASK_SECRET') or '你自己設的隨機字串'

# 1. 定義多個「空間」，key 為任意隨機路徑前綴
#    path: 實際對應的資料夾
#    encrypted: 是否啟用密碼保護
#    password: 若 encrypted=True，則為該空間密碼
SPACES = {
    'shbsb': {
        'path': r'C:/Users/gonec/Pictures/Phone/Picture/2025-03',
        'encrypted': False,
        'allow_upload': False
    },
    'jakxjs': {
        'path': r'C:/Users/gonec/Pictures/Phone/Picture/2025-04',
        'encrypted': True,
        'password': '123',
        'allow_upload': True
    },
    # ……你可以再加更多
}


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
        if request.form.get('password') == cfg['password']:
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
        allow_upload=cfg.get('allow_upload', False)
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
        # img = Image.open(file_full)
        if ext in RAW_EXTS:
            # 用 rawpy 解碼到半尺（half-size）
            with rawpy.imread(file_full) as raw:
                rgb = raw.postprocess(use_camera_wb=True, half_size=True)
            print("Get RAW")
            img = Image.fromarray(rgb)
        else:
            img = Image.open(file_full)
        img.thumbnail((200, 200))
        buf = BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return send_file(buf, mimetype='image/png')
    except:
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
    # 如果不允許上傳，就回 403
    if not cfg.get('allow_upload'):
        abort(403)

    # 前端會以 form-data 傳一個檔案欄位 "file"
    uploaded = request.files.get('file')
    # 你也可以傳一個相對路徑參數 path，決定上傳到哪個子資料夾
    rel_path = request.form.get('path', '').lstrip('/')
    target_dir = secure_path(cfg['path'], rel_path)

    if not uploaded:
        abort(400, description='沒有傳任何檔案過來')
    # 簡單檢查副檔名（避免任意程式上傳）
    filename = uploaded.filename
    if filename == '' or '/' in filename or '\\' in filename:
        abort(400, description='不合法檔名')

    # 存到 target_dir 底下
    dest = os.path.join(target_dir, filename)
    # 如果遠端有同名檔，可以自行決定要複寫或改名，這裡示範覆寫
    uploaded.save(dest)
    return jsonify({'success': True, 'filename': filename})


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
            # 用 rawpy 取得原始尺寸
            with rawpy.imread(file_full) as raw:
                h, w = raw.raw_image.shape
            info['resolution'] = f"{w}×{h}"

            # 用 exifread 解析 EXIF
            with open(file_full, 'rb') as f:
                tags = exifread.process_file(f, details=False)

            def first_tag(names):
                for n in names:
                    if n in tags:
                        return str(tags[n])
                return None

            info.update({
                'Make':         first_tag(['Image Make']),
                'Camera':       first_tag(['Image Model']),
                'LensModel':    first_tag(['EXIF LensModel', 'MakerNotes LensModel']),
                'ISO':          first_tag(['EXIF ISOSpeedRatings']),
                'ShutterSpeed': first_tag(['EXIF ExposureTime']),
                'Aperture':     first_tag(['EXIF FNumber']),
                'DateTime':     first_tag(['EXIF DateTimeOriginal', 'Image DateTime'])
            })
        else:
            # 一般影像走 PIL 路徑
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

    except Exception as e:
        app.logger.error(f"metadata error {file_full}: {e}")
        abort(404)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
