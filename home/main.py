from flask import Flask, render_template, request, redirect,send_file, url_for, session, jsonify
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import os
import uuid
from home import app

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
    print("Index function called")  # デバッグ用
    if request.method == 'POST':
        # 過去のアップロードを削除してから新規設定を保存
        cleanup_temp_files()
        
        session['title'] = request.form.get('title', 'My Tier')
        session['title_color'] = normalize_color(request.form.get('title_color', '#ffffff'))
        session['title_weight'] = int(request.form.get('title_weight', 0) or 0)
        session['title_size'] = int(request.form.get('title_size', 40) or 40)
        session['x_label'] = request.form.get('x_label', 'Width')
        session['x_color'] = normalize_color(request.form.get('x_color', '#ffffff'))
        session['x_weight'] = int(request.form.get('x_weight', 0) or 0)
        session['x_size'] = int(request.form.get('x_size', 24) or 24)
        session['y_label'] = request.form.get('y_label', 'Height')
        session['y_color'] = normalize_color(request.form.get('y_color', '#ffffff'))
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
        title=session.get('title', 'My Best Games'),
        title_color=session.get('title_color', "#ffffff"),
        title_weight=session.get('title_weight', 0),
        title_size=session.get('title_size', 40),
        y_label=session.get('y_label', 'Quality'),
        y_color=session.get('y_color', '#ff0000'),
        y_weight=session.get('y_weight', 0),
        y_size=session.get('y_size', 24),
        x_label=session.get('x_label', 'Enjoyment'),
        x_color=session.get('x_color', '#00ff00'),
        x_weight=session.get('x_weight', 0),
        x_size=session.get('x_size', 24),
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
    title_weight = session.get('title_weight', 0)
    title_size = session.get('title_size', 40)
    x_label = session.get('x_label')
    x_color = session.get('x_color')
    x_weight = session.get('x_weight', 0)
    x_size = session.get('x_size', 24)
    y_label = session.get('y_label')
    y_color = session.get('y_color')
    y_weight = session.get('y_weight', 0)
    y_size = session.get('y_size', 24)
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
    title_font = load_font(max(24, title_size))
    y_axis_font = load_font(max(16, y_size))
    x_axis_font = load_font(max(16, x_size))
    
    title_color = normalize_color(title_color, '#ffffff')
    x_color = normalize_color(x_color, '#ffffff')
    y_color = normalize_color(y_color, '#ffffff')
    
    # タイトルと軸ラベルを描画
    draw.text((950, 30), title, fill=title_color, font=title_font, stroke_width=title_weight, stroke_fill=title_color)
    draw.text((50, 100), f"Y: {y_label}", fill=y_color, font=y_axis_font, stroke_width=y_weight, stroke_fill=y_color)
    draw.text((600, 750), f"X: {x_label}", fill=x_color, font=x_axis_font, stroke_width=x_weight, stroke_fill=x_color)
    
    # 軸の矢印を描画
    # 縦軸 (Y軸)
    draw.line([(100, 150), (100, 700)], fill=y_color, width=3)
    draw.polygon([(95, 150), (105, 150), (100, 130)], fill=y_color)
    
    # 横軸 (X軸)
    draw.line([(150, 650), (1100, 650)], fill=x_color, width=3)
    draw.polygon([(1100, 645), (1100, 655), (1120, 650)], fill=x_color)
    
    # 画像を配置
    x_offset, y_offset = 150, 150
    for img_path in image_list:
        if img_path is None:
            # 改行
            x_offset = 150
            y_offset += 120
            continue
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
    #プレビュー画像を返す
    if 'title' not in session:
        return redirect(url_for('index'))
    
    title = session.get('title')
    title_color = session.get('title_color')
    title_weight = session.get('title_weight', 0)
    title_size = session.get('title_size', 40)
    x_label = session.get('x_label')
    x_color = session.get('x_color')
    x_weight = session.get('x_weight', 0)
    x_size = session.get('x_size', 24)
    y_label = session.get('y_label')
    y_color = session.get('y_color')
    y_weight = session.get('y_weight', 0)
    y_size = session.get('y_size', 24)
    text_weight = session.get('text_weight', 0)
    text_size = session.get('text_size', 40)
    bg_file_path = session.get('bg_file_path')
    image_list = session.get('image_list', [])
    
    if bg_file_path and os.path.exists(bg_file_path):
        base_img = Image.open(bg_file_path).convert("RGBA").resize((1200, 800))
    else:
        base_img = Image.new("RGBA", (1200, 800), (40, 44, 52, 255))
    
    draw = ImageDraw.Draw(base_img)
    title_font = load_font(max(24, title_size))
    y_axis_font = load_font(max(16, y_size))
    x_axis_font = load_font(max(16, x_size))
    
    title_color = normalize_color(title_color, '#ffffff')
    x_color = normalize_color(x_color, '#ffffff')
    y_color = normalize_color(y_color, '#ffffff')
    
    # タイトルの配置を右端に合わせる
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = 1200 - title_width - 20  # 右端から20px余白
    draw.text((title_x, 30), title, fill=title_color, font=title_font, stroke_width=title_weight, stroke_fill=title_color)
    
    draw.text((50, 60), f" {y_label}", fill=y_color, font=y_axis_font, stroke_width=y_weight, stroke_fill=y_color)
    draw.text((500, 750), f" {x_label}", fill=x_color, font=x_axis_font, stroke_width=x_weight, stroke_fill=x_color)
    
    # 軸の矢印を描画
    # 縦軸 (Y軸)
    draw.line([(100, 120), (100, 700)], fill=y_color, width=5)
    draw.polygon([(90, 120), (110, 120), (100, 100)], fill=y_color)
    
    # 横軸 (X軸)
    draw.line([(100, 700), (1100, 700)], fill=x_color, width=5)
    draw.polygon([(1100, 690), (1100, 710), (1120, 700)], fill=x_color)
    
    x_offset, y_offset = 150, 150
    for img_path in image_list:
        if img_path is None:
            # 改行
            x_offset = 150
            y_offset += 120
            continue
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

if __name__ == '__main__':
    print("Starting Flask app...")  # デバッグ用
    print(f"App: {app}")  # デバッグ用
    print(f"URL Map: {app.url_map}")  # デバッグ用
    print(f"Template folder: {app.template_folder}")  # デバッグ用
    print(f"Current directory: {os.getcwd()}")  # デバッグ用
    try:
        app.run(debug=True)
    except Exception as e:
        print(f"Error starting Flask app: {e}")  # デバッグ用

