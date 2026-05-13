from flask import Flask, render_template, request, redirect,send_file, url_for, session, jsonify
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont
import io
import os
import uuid
from home import app

UPLOAD_DIR = os.path.join(os.getcwd(), os.environ.get('UPLOAD_DIR', 'tmp_uploads'))
os.makedirs(UPLOAD_DIR, exist_ok=True)

FONT_FAMILY_MAP = {
    'Arial': ['arial.ttf', 'Arial.ttf', 'LiberationSans-Regular.ttf', 'DejaVuSans.ttf'],
    'Times New Roman': ['times.ttf', 'Times New Roman.ttf', 'LiberationSerif-Regular.ttf', 'DejaVuSerif.ttf'],
    'Courier New': ['cour.ttf', 'Courier New.ttf', 'LiberationMono-Regular.ttf', 'DejaVuSansMono.ttf'],
    'DejaVu Sans': ['DejaVuSans.ttf', 'LiberationSans-Regular.ttf', 'arial.ttf', 'Arial.ttf'],
    'Default': ['arial.ttf', 'Arial.ttf', 'LiberationSans-Regular.ttf', 'DejaVuSans.ttf'],
}

FONT_DIRS = [
    os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'),
    '/usr/share/fonts/truetype',
    '/usr/share/fonts',
]


def find_font_path(candidate):
    if not candidate:
        return None
    if os.path.isabs(candidate) and os.path.exists(candidate):
        return candidate
    if os.path.exists(candidate):
        return candidate
    lower_candidate = candidate.lower()
    for fonts_dir in FONT_DIRS:
        path = os.path.join(fonts_dir, candidate)
        if os.path.exists(path):
            return path

    for fonts_dir in FONT_DIRS:
        if not os.path.isdir(fonts_dir):
            continue
        for root, _, files in os.walk(fonts_dir):
            for filename in files:
                if filename.lower() == lower_candidate:
                    return os.path.join(root, filename)
    return None


def load_font(family, size):
    if not family:
        family = 'Default'
    candidates = FONT_FAMILY_MAP.get(family, [])
    for candidate in candidates:
        path = find_font_path(candidate)
        if path:
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue

    # 最後の手段として PIL に同梱されている DejaVu フォントを使う
    try:
        return ImageFont.truetype('DejaVuSans.ttf', size)
    except OSError:
        return ImageFont.load_default()


def normalize_color(color, default='#ffffff'):
    if not color or not isinstance(color, str):
        return default
    color = color.strip()
    if color.startswith('#') and len(color) in (4, 7):
        return color
    return default


def cleanup_temp_files():
    bg_path = session.pop('bg_file_path', None)
    image_paths = session.pop('image_list', None)
    if bg_path and os.path.exists(bg_path):
        try:
            os.remove(bg_path)
        except OSError:
            pass
    if image_paths:
        for p in image_paths:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass


def save_uploaded_file(file_storage, prefix):
    filename = secure_filename(file_storage.filename)
    if not filename:
        return None
    
    # ファイルタイプの検証（画像のみ許可）
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return None
    
    # MIMEタイプの検証
    if not file_storage.mimetype.startswith('image/'):
        return None
    
    # ファイルサイズの制限（例: 5MB）
    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)
    if file_size > 5 * 1024 * 1024:  # 5MB
        return None
    
    unique_name = f"{prefix}_{uuid.uuid4().hex}_{filename}"
    path = os.path.join(UPLOAD_DIR, unique_name)
    file_storage.save(path)
    return path


def build_preview_image():
    title = session.get('title')
    title_color = session.get('title_color')
    title_weight = session.get('title_weight', 0)
    title_size = session.get('title_size', 40)
    x_label = session.get('x_label')
    x_label_color = session.get('x_label_color', session.get('x_color'))
    x_arrow_color = session.get('x_arrow_color', session.get('x_color', x_label_color))
    x_weight = session.get('x_weight', 0)
    x_size = session.get('x_size', 24)
    y_label = session.get('y_label')
    y_label_color = session.get('y_label_color', session.get('y_color'))
    y_arrow_color = session.get('y_arrow_color', session.get('y_color', y_label_color))
    y_weight = session.get('y_weight', 0)
    y_size = session.get('y_size', 24)
    bg_file_path = session.get('bg_file_path')
    image_list = session.get('image_list', [])

    if bg_file_path and os.path.exists(bg_file_path):
        base_img = Image.open(bg_file_path).convert("RGBA").resize((1200, 800))
    else:
        base_img = Image.new("RGBA", (1200, 800), (40, 44, 52, 255))

    draw = ImageDraw.Draw(base_img)
    title_font_family = session.get('title_font_family', 'Arial')
    y_axis_font_family = session.get('y_font_family', 'Arial')
    x_axis_font_family = session.get('x_font_family', 'Arial')
    title_font = load_font(title_font_family, max(24, title_size))
    y_axis_font = load_font(y_axis_font_family, max(16, y_size))
    x_axis_font = load_font(x_axis_font_family, max(16, x_size))

    title_color = normalize_color(title_color, '#ffffff')
    x_label_color = normalize_color(x_label_color, '#ffffff')
    x_arrow_color = normalize_color(x_arrow_color, x_label_color)
    y_label_color = normalize_color(y_label_color, '#ffffff')
    y_arrow_color = normalize_color(y_arrow_color, y_label_color)

    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = 1200 - title_width - 20
    draw.text((title_x, 30), title, fill=title_color, font=title_font, stroke_width=title_weight, stroke_fill=title_color)
    draw.text((30, 60), f" {y_label}", fill=y_label_color, font=y_axis_font, stroke_width=y_weight, stroke_fill=y_label_color)
    draw.text((1100, 680), f" {x_label}", fill=x_label_color, font=x_axis_font, stroke_width=x_weight, stroke_fill=x_label_color)

    draw.line([(100, 150), (100, 700)], fill=y_arrow_color, width=5)
    draw.polygon([(90, 150), (110, 150), (100, 130)], fill=y_arrow_color)
    draw.line([(100, 700), (1100, 700)], fill=x_arrow_color, width=5)
    draw.polygon([(1080, 690), (1080, 710), (1100, 700)], fill=x_arrow_color)

    max_cols = 8
    row_gap = 20
    max_bottom = 700 - 20
    available_height = max_bottom - 150
    rows = 0
    current_col = 0
    for img_path in image_list:
        if img_path is None:
            if current_col != 0 or rows == 0:
                rows += 1
            current_col = 0
            continue
        current_col += 1
        if current_col > max_cols:
            rows += 1
            current_col = 1
    if current_col > 0:
        rows += 1

    image_size = 100
    if rows > 0:
        image_size = min(100, max(20, (available_height - (rows - 1) * row_gap) // rows))
        if image_size < 40:
            row_gap = 10
            image_size = max(20, min(100, (available_height - (rows - 1) * row_gap) // rows))

    x_offset, y_offset = 150, 150
    cell_width = image_size + row_gap
    for img_path in image_list:
        if img_path is None:
            x_offset = 150
            y_offset += image_size + row_gap
            continue
        if not img_path or not os.path.exists(img_path):
            continue
        img = Image.open(img_path).convert("RGBA").resize((image_size, image_size))
        base_img.paste(img, (x_offset, y_offset), img)
        x_offset += cell_width
        if x_offset > 1000:
            x_offset = 150
            y_offset += image_size + row_gap

    buf = io.BytesIO()
    base_img.save(buf, format="PNG")
    buf.seek(0)
    return buf


@app.route('/', methods=['GET', 'POST'])
def index():
    app.logger.info("Index function called")  # デバッグ用
    if request.method == 'POST':
        # 過去のアップロードを削除してから新規設定を保存
        cleanup_temp_files()
        
        session['title'] = request.form.get('title', 'My Tier')
        session['title_color'] = normalize_color(request.form.get('title_color', '#ffffff'))
        session['title_weight'] = int(request.form.get('title_weight', 0) or 0)
        session['title_size'] = int(request.form.get('title_size', 40) or 40)
        session['title_font_family'] = request.form.get('title_font_family', 'Arial')
        session['x_label'] = request.form.get('x_label', 'Width')
        session['x_label_color'] = normalize_color(request.form.get('x_label_color', '#ffffff'))
        session['x_arrow_color'] = normalize_color(request.form.get('x_arrow_color', request.form.get('x_label_color', '#ffffff')))
        session['x_color'] = session['x_label_color']
        session['x_weight'] = int(request.form.get('x_weight', 0) or 0)
        session['x_size'] = int(request.form.get('x_size', 24) or 24)
        session['y_label'] = request.form.get('y_label', 'Height')
        session['y_label_color'] = normalize_color(request.form.get('y_label_color', '#ffffff'))
        session['y_arrow_color'] = normalize_color(request.form.get('y_arrow_color', request.form.get('y_label_color', '#ffffff')))
        session['y_color'] = session['y_label_color']
        session['y_font_family'] = request.form.get('y_font_family', 'Arial')
        session['x_font_family'] = request.form.get('x_font_family', 'Arial')
        session['y_weight'] = int(request.form.get('y_weight', 0) or 0)
        session['y_size'] = int(request.form.get('y_size', 24) or 24)
        session['text_weight'] = int(request.form.get('text_weight', 0) or 0)
        session['text_size'] = int(request.form.get('text_size', 40) or 40)
        
        # 背景画像を保存
        bg_file = request.files.get('bg_file')
        if bg_file and bg_file.filename != '':
            session['bg_file_path'] = save_uploaded_file(bg_file, 'bg')
        else:
            session['bg_file_path'] = None
        
        # 初期化: 画像リスト
        session['image_list'] = []
        
        return redirect(url_for('place_images'))
    
    return render_template(
        'step1_settings.html',
        title = session.get('title', 'My Best Games'),
        title_color = session.get('title_color', "#ffffff"),
        title_weight = session.get('title_weight', 0),
        title_size = session.get('title_size', 40),
        y_label = session.get('y_label', 'Quality'),
        y_label_color = session.get('y_label_color', session.get('y_color', '#ff0000')),
        y_arrow_color = session.get('y_arrow_color', session.get('y_color', '#ff0000')),
        y_weight = session.get('y_weight', 0),
        y_size = session.get('y_size', 24),
        x_label = session.get('x_label', 'Enjoyment'),
        x_label_color = session.get('x_label_color', session.get('x_color', '#00ff00')),
        x_arrow_color = session.get('x_arrow_color', session.get('x_color', '#00ff00')),
        x_weight = session.get('x_weight', 0),
        x_size = session.get('x_size', 24),
        text_weight = session.get('text_weight', 1),
        text_size = session.get('text_size', 40),
        title_font_family = session.get('title_font_family', 'Arial'),
        y_font_family = session.get('y_font_family', 'Arial'),
        x_font_family = session.get('x_font_family', 'Arial'),
    )

@app.route('/place_images', methods=['GET', 'POST'])
def place_images():
    # ステップ1の設定がない場合は戻す
    if 'title' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # 画像が追加されたか確認
        new_image = request.files.get('image')
        if new_image and new_image.filename != '':
            image_path = save_uploaded_file(new_image, 'item')
            if image_path:
                session['image_list'].append(image_path)
                session.modified = True
        
        # 最終画像生成
        if 'generate' in request.form:
            return redirect(url_for('generate_final'))
    
    image_list = session.get('image_list', [])
    image_count = sum(1 for item in image_list if item is not None)
    return render_template('step2_place_images.html', image_count=image_count)

@app.route('/generate_final')
def generate_final():
    if 'title' not in session or 'image_list' not in session:
        return redirect(url_for('index'))
    return render_template('step3_result.html')

@app.route('/preview_image')
def preview_image():
    if 'title' not in session:
        return redirect(url_for('index'))
    buf = build_preview_image()
    return send_file(buf, mimetype='image/png')


@app.route('/download_image')
def download_image():
    if 'title' not in session:
        return redirect(url_for('index'))
    buf = build_preview_image()
    return send_file(buf, mimetype='image/png', as_attachment=True, download_name='tier_list.png')

@app.route('/api/image_list')
def api_image_list():
    """セッションの画像リスト情報をJSON返す"""
    image_list = session.get('image_list', [])
    images = []
    for i, img_path in enumerate(image_list):
        if img_path is None:
            images.append(f'改行 {i + 1}')
        else:
            images.append(f'画像 {i + 1}')
    return {'images': images}

@app.route('/api/remove_image/<int:idx>', methods=['POST'])
def api_remove_image(idx):
    #セッションから指定インデックスの画像または改行を削除
    image_list = session.get('image_list', [])
    if 0 <= idx < len(image_list):
        image_list.pop(idx)
        session['image_list'] = image_list
        session.modified = True
        return {'success': True}
    return {'success': False}

@app.route('/api/add_newline', methods=['POST'])
def api_add_newline():
    #改行を追加
    image_list = session.get('image_list', [])
    image_list.append(None)  # Noneを追加して改行を表す
    session['image_list'] = image_list
    session.modified = True
    return {'success': True}

