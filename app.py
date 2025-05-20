import os
from flask import (
    Flask, jsonify, send_from_directory, send_file,
    request, abort, render_template, session,
    redirect, url_for
)
from PIL import Image
from io import BytesIO
from functools import wraps

app = Flask(__name__, static_folder='static', template_folder='templates')
# 用於 session 加密
app.secret_key = os.environ.get('FLASK_SECRET') or '你自己設的隨機字串'

# 1. 定義多個「空間」，key 為任意隨機路徑前綴
#    path: 實際對應的資料夾
#    encrypted: 是否啟用密碼保護
#    password: 若 encrypted=True，則為該空間密碼
SPACES = {
    'shbsb': {
        'path': r'C:/Users/gonec/Desktop/phonix/表演',
        'encrypted': False
    },
    'jakxjs': {
        'path': r'C:/Users/gonec/Desktop/phonix/彩排',
        'encrypted': True,
        'password': '123'
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
@app.route('/<space>/login', methods=['GET','POST'])
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
    return render_template('index.html', space=space)

# ─── 列出資料夾內容 API ──────────────────────
@app.route('/<space>/api/list')
@login_required
def api_list(space):
    rel_path = request.args.get('path', '')
    cfg = get_space_cfg(space)
    folder = secure_path(cfg['path'], rel_path)
    items = []
    for entry in os.scandir(folder):
        items.append({
            'name': entry.name,
            'path': os.path.join(rel_path, entry.name).replace(os.sep, '/'),
            'is_dir': entry.is_dir(),
            'is_image': entry.is_file() and entry.name.lower().endswith(('.png','.jpg','.jpeg','.gif','.bmp'))
        })
    return jsonify(items)

# ─── 下載檔案 API ────────────────────────────
@app.route('/<space>/api/download')
@login_required
def api_download(space):
    rel = request.args.get('path','')
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
    rel = request.args.get('path','')
    cfg = get_space_cfg(space)
    file_full = secure_path(cfg['path'], rel)
    try:
        img = Image.open(file_full)
        img.thumbnail((200,200))
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
    folder_full = secure_path(cfg['path'], folder)
    return send_from_directory(folder_full, name, as_attachment=False)


if __name__ == '__main__':
    app.run(debug=True)
