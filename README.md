# Tier_chart_maker
Tier表生成アプリ

## セットアップ
1. Python 3.8以上をインストール
2. `pip install -r requirements.txt`

## 実行
- 開発: `python -m home`
- 本番: WSGIサーバー（Gunicornなど）を使用

## 環境変数
- `SECRET_KEY`: Flaskのシークレットキー
- `FLASK_DEBUG`: デバッグモード（true/false）
- `PORT`: ポート番号（デフォルト5000）
- `UPLOAD_DIR`: アップロードディレクトリ（デフォルトtmp_uploads）

## デプロイ
Herokuなどのプラットフォームでデプロイ可能。環境変数を設定してください。
