from home import app
from flask import render_template, request, send_file, session, redirect, url_for
from PIL import Image, ImageDraw, ImageFont
from werkzeug.utils import secure_filename
import io
import os
import uuid
import base64
import json

UPLOAD_DIR = os.path.join(os.getcwd(), 'tmp_uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


def load_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
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
    unique_name = f"{prefix}_{uuid.uuid4().hex}_{filename}"
    path = os.path.join(UPLOAD_DIR, unique_name)
    file_storage.save(path)
    return path


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 過去のアップロードを削除してから新規設定を保存
        cleanup_temp_files()
        
        session['title'] = request.form.get('title', 'My Tier')
        session['title_color'] = normalize_color(request.form.get('title_color', '#ffffff'))
        session['x_label'] = request.form.get('x_label', 'Width')
        session['x_color'] = normalize_color(request.form.get('x_color', '#ffffff'))
        session['y_label'] = request.form.get('y_label', 'Height')
        session['y_color'] = normalize_color(request.form.get('y_color', '#ffffff'))
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
        title=session.get('title', 'My Best Games'),
        title_color=session.get('title_color', '#ffffff'),
        y_label=session.get('y_label', 'Quality'),
        y_color=session.get('y_color', '#ff0000'),
        x_label=session.get('x_label', 'Enjoyment'),
        x_color=session.get('x_color', '#00ff00'),
        text_weight=session.get('text_weight', 1),
        text_size=session.get('text_size', 40),
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
    
    image_count = len(session.get('image_list', []))
    return render_template('step2_place_images.html', image_count=image_count)

@app.route('/generate_final')
def generate_final():
    if 'title' not in session or 'image_list' not in session:
        return redirect(url_for('index'))
    
    # 設定を取得
    title = session.get('title')
    title_color = session.get('title_color')
    x_label = session.get('x_label')
    x_color = session.get('x_color')
    y_label = session.get('y_label')
    y_color = session.get('y_color')
    text_weight = session.get('text_weight', 0)
    text_size = session.get('text_size', 40)
    bg_file_path = session.get('bg_file_path')
    image_list = session.get('image_list', [])
    
    # 背景画像をセット
    if bg_file_path and os.path.exists(bg_file_path):
        base_img = Image.open(bg_file_path).convert("RGBA").resize((1200, 800))
    else:
        base_img = Image.new("RGBA", (1200, 800), (40, 44, 52, 255))
    
    draw = ImageDraw.Draw(base_img)
    text_size = session.get('text_size', 40)
    title_size = max(24, text_size)
    axis_size = max(16, int(text_size * 0.6))
    title_font = load_font(title_size)
    axis_font = load_font(axis_size)
    
    title_color = normalize_color(title_color, '#ffffff')
    x_color = normalize_color(x_color, '#ffffff')
    y_color = normalize_color(y_color, '#ffffff')
    
    # タイトルと軸ラベルを描画
    draw.text((950, 30), title, fill=title_color, font=title_font, stroke_width=text_weight, stroke_fill=title_color)
    draw.text((50, 100), f"Y: {y_label}", fill=y_color, font=axis_font, stroke_width=text_weight, stroke_fill=y_color)
    draw.text((600, 750), f"X: {x_label}", fill=x_color, font=axis_font, stroke_width=text_weight, stroke_fill=x_color)
    
    # 画像を配置
    x_offset, y_offset = 150, 150
    for img_path in image_list:
        if not img_path or not os.path.exists(img_path):
            continue
        img = Image.open(img_path).convert("RGBA").resize((100, 100))
        base_img.paste(img, (x_offset, y_offset), img)
        x_offset += 120
        if x_offset > 1000:
            x_offset = 150
            y_offset += 120
    
    # ブラウザ表示用にbase64エンコード
    buf = io.BytesIO()
    base_img.save(buf, format="PNG")
    img_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return render_template('step3_result.html', img_data=img_data)

@app.route('/preview_image')
def preview_image():
    """プレビュー画像を返す"""
    if 'title' not in session:
        return redirect(url_for('index'))
    
    title = session.get('title')
    title_color = session.get('title_color')
    x_label = session.get('x_label')
    x_color = session.get('x_color')
    y_label = session.get('y_label')
    y_color = session.get('y_color')
    text_weight = session.get('text_weight', 0)
    text_size = session.get('text_size', 40)
    bg_file_path = session.get('bg_file_path')
    image_list = session.get('image_list', [])
    
    if bg_file_path and os.path.exists(bg_file_path):
        base_img = Image.open(bg_file_path).convert("RGBA").resize((1200, 800))
    else:
        base_img = Image.new("RGBA", (1200, 800), (40, 44, 52, 255))
    
    draw = ImageDraw.Draw(base_img)
    text_size = session.get('text_size', 40)
    title_size = max(24, text_size)
    axis_size = max(16, int(text_size * 0.6))
    title_font = load_font(title_size)
    axis_font = load_font(axis_size)
    
    title_color = normalize_color(title_color, '#ffffff')
    x_color = normalize_color(x_color, '#ffffff')
    y_color = normalize_color(y_color, '#ffffff')
    
    draw.text((950, 30), title, fill=title_color, font=title_font, stroke_width=text_weight, stroke_fill=title_color)
    draw.text((50, 100), f"Y: {y_label}", fill=y_color, font=axis_font, stroke_width=text_weight, stroke_fill=y_color)
    draw.text((600, 750), f"X: {x_label}", fill=x_color, font=axis_font, stroke_width=text_weight, stroke_fill=x_color)
    
    x_offset, y_offset = 150, 150
    for img_path in image_list:
        if not img_path or not os.path.exists(img_path):
            continue
        img = Image.open(img_path).convert("RGBA").resize((100, 100))
        base_img.paste(img, (x_offset, y_offset), img)
        x_offset += 120
        if x_offset > 1000:
            x_offset = 150
            y_offset += 120
    
    buf = io.BytesIO()
    base_img.save(buf, format="PNG")
    buf.seek(0)
    
    return send_file(buf, mimetype='image/png')

@app.route('/api/image_list')
def api_image_list():
    """セッションの画像リスト情報をJSON返す"""
    image_list = session.get('image_list', [])
    return {'images': [f'image_{i}' for i in range(len(image_list))]}

@app.route('/api/remove_image/<int:idx>', methods=['POST'])
def api_remove_image(idx):
    """セッションから指定インデックスの画像を削除"""
    image_list = session.get('image_list', [])
    if 0 <= idx < len(image_list):
        image_list.pop(idx)
        session['image_list'] = image_list
        session.modified = True
        return {'success': True}
    return {'success': False}

if __name__ == '__main__':
    app.run(debug=True)

