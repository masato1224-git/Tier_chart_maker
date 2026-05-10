from home import app
from flask import render_template, request, send_file, session, redirect, url_for
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import json


def load_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # ステップ1: 設定を保存
        session['title'] = request.form.get('title', 'My Tier')
        session['title_color'] = request.form.get('title_color', '#ffffff')
        session['x_label'] = request.form.get('x_label', 'Width')
        session['x_color'] = request.form.get('x_color', '#ffffff')
        session['y_label'] = request.form.get('y_label', 'Height')
        session['y_color'] = request.form.get('y_color', '#ffffff')
        session['text_weight'] = int(request.form.get('text_weight', 0) or 0)
        
        # 背景画像を保存
        bg_file = request.files.get('bg_file')
        if bg_file and bg_file.filename != '':
            bg_data = base64.b64encode(bg_file.read()).decode('utf-8')
            session['bg_file_data'] = bg_data
        else:
            session['bg_file_data'] = None
        
        # 初期化: 画像リスト
        session['image_list'] = []
        
        return redirect(url_for('place_images'))
    
    return render_template('step1_settings.html')

@app.route('/place_images', methods=['GET', 'POST'])
def place_images():
    # ステップ1の設定がない場合は戻す
    if 'title' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # 画像が追加されたか確認
        new_image = request.files.get('image')
        if new_image and new_image.filename != '':
            img_data = base64.b64encode(new_image.read()).decode('utf-8')
            session['image_list'].append(img_data)
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
    bg_file_data = session.get('bg_file_data')
    image_list = session.get('image_list', [])
    
    # 背景画像をセット
    if bg_file_data:
        bg_file_bytes = io.BytesIO(base64.b64decode(bg_file_data))
        base_img = Image.open(bg_file_bytes).convert("RGBA").resize((1200, 800))
    else:
        base_img = Image.new("RGBA", (1200, 800), (40, 44, 52, 255))
    
    draw = ImageDraw.Draw(base_img)
    title_font = load_font(40)
    axis_font = load_font(24)
    
    # タイトルと軸ラベルを描画
    draw.text((950, 30), title, fill=title_color, font=title_font, stroke_width=text_weight, stroke_fill=title_color)
    draw.text((50, 100), f"Y: {y_label}", fill=y_color, font=axis_font, stroke_width=text_weight, stroke_fill=y_color)
    draw.text((600, 750), f"X: {x_label}", fill=x_color, font=axis_font, stroke_width=text_weight, stroke_fill=x_color)
    
    # 画像を配置
    x_offset, y_offset = 150, 150
    for img_data in image_list:
        img_bytes = io.BytesIO(base64.b64decode(img_data))
        img = Image.open(img_bytes).convert("RGBA").resize((100, 100))
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
    bg_file_data = session.get('bg_file_data')
    image_list = session.get('image_list', [])
    
    if bg_file_data:
        bg_file_bytes = io.BytesIO(base64.b64decode(bg_file_data))
        base_img = Image.open(bg_file_bytes).convert("RGBA").resize((1200, 800))
    else:
        base_img = Image.new("RGBA", (1200, 800), (40, 44, 52, 255))
    
    draw = ImageDraw.Draw(base_img)
    title_font = load_font(40)
    axis_font = load_font(24)
    
    draw.text((950, 30), title, fill=title_color, font=title_font, stroke_width=text_weight, stroke_fill=title_color)
    draw.text((50, 100), f"Y: {y_label}", fill=y_color, font=axis_font, stroke_width=text_weight, stroke_fill=y_color)
    draw.text((600, 750), f"X: {x_label}", fill=x_color, font=axis_font, stroke_width=text_weight, stroke_fill=x_color)
    
    x_offset, y_offset = 150, 150
    for img_data in image_list:
        img_bytes = io.BytesIO(base64.b64decode(img_data))
        img = Image.open(img_bytes).convert("RGBA").resize((100, 100))
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

