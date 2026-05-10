from home import app
from flask import render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont
import io
import base64


def generate_tier_image(files, title, title_color, x_label, x_color, y_label, y_color, bg_file=None):
    # 背景の作成
    if bg_file and bg_file.filename != '':
        base_img = Image.open(bg_file).convert("RGBA").resize((1200, 800))
    else:
        base_img = Image.new("RGBA", (1200, 800), (40, 44, 52, 255))
    
    draw = ImageDraw.Draw(base_img)
    
    # 1. タイトルを描画 (右上)
    draw.text((950, 30), title, fill=title_color)
    
    # 2. 軸ラベルを描画
    draw.text((50, 100), f"Y: {y_label}", fill=y_color) # 縦軸
    draw.text((600, 750), f"X: {x_label}", fill=x_color) # 横軸
    
    # 3. アップロードされた画像を配置
    x_offset, y_offset = 150, 150
    for file in files:
        if file.filename == '': continue
        img = Image.open(file).convert("RGBA").resize((100, 100))
        base_img.paste(img, (x_offset, y_offset), img)
        x_offset += 120
        if x_offset > 1000: # 右端まで行ったら改行
            x_offset = 150
            y_offset += 120
            
    return base_img

@app.route('/', methods=['GET', 'POST'])
def index():
    img_data = None
    if request.method == 'POST':
        # フォームデータの取得
        title = request.form.get('title', 'My Tier')
        title_color = request.form.get('title_color', '#ffffff')
        x_label = request.form.get('x_label', 'Width')
        x_color = request.form.get('x_color', '#ffffff')
        y_label = request.form.get('y_label', 'Height')
        y_color = request.form.get('y_color', '#ffffff')
        
        bg_file = request.files.get('bg_file')
        files = request.files.getlist('images')
        
        # 画像生成
        result_img = generate_tier_image(files, title, title_color, x_label, x_color, y_label, y_color, bg_file)
        
        # ブラウザ表示用にbase64エンコード
        buf = io.BytesIO()
        result_img.save(buf, format="PNG")
        img_data = base64.b64encode(buf.getvalue()).decode('utf-8')
        
    return render_template('index.html', img_data=img_data)

if __name__ == '__main__':
    app.run(debug=True)

