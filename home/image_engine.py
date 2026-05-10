import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io

st.title("カスタムTier表メーカー")

# --- サイドバー設定 ---
st.sidebar.header("全体設定")
title_text = st.sidebar.text_input("アプリのタイトル", "My Tier List")
title_color = st.sidebar.color_picker("タイトルの色", "#FFFFFF")

bg_file = st.sidebar.file_uploader("背景画像をアップロード", type=["png", "jpg", "jpeg"])

st.sidebar.header("軸ラベル設定")
y_label = st.sidebar.text_input("縦軸のラベル (例: S, A, B...)", "S")
y_label_color = st.sidebar.color_picker("ラベルの色", "#FF0000")

# --- メインコンテンツ ---
uploaded_images = st.file_uploader("Tierに配置する画像を選択してください", accept_multiple_files=True)

if st.button("Tier表を生成"):
    if uploaded_images:
        # ベースとなる背景の作成（または読み込み）
        if bg_file:
            base_img = Image.open(bg_file).convert("RGBA").resize((1200, 800))
        else:
            base_img = Image.new("RGBA", (1200, 800), (30, 30, 30, 255))
        
        draw = ImageDraw.Draw(base_img)
        
        # タイトルの描画 (右上に配置)
        # ※フォントファイルが必要な場合は .ttf を指定
        draw.text((1000, 20), title_text, fill=title_color)
        
        # 画像の整列ロジック (簡易版: 横に並べる)
        x_offset = 150
        for img_file in uploaded_images:
            img = Image.open(img_file).convert("RGBA").resize((100, 100))
            base_img.paste(img, (x_offset, 150), img)
            x_offset += 110
            
        # 軸ラベルの描画
        draw.text((50, 150), y_label, fill=y_label_color)

        # プレビュー表示
        st.image(base_img, caption="プレビュー")

        # ダウンロード準備
        buf = io.BytesIO()
        base_img.save(buf, format="PNG")
        byte_im = buf.getvalue()
        st.download_button(label="画像をダウンロード", data=byte_im, file_name="tier_list.png", mime="image/png")
    else:
        st.warning("画像がアップロードされていません")