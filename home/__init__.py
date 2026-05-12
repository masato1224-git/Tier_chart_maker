from flask import Flask, render_template, request, send_file
import os
app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'tier_chart_maker_secret_2024')  # 環境変数から読み込み、デフォルトは開発用
from . import main
# エラーハンドリング
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

