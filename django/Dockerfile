FROM python:3.11-slim

# 環境変数の設定
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.production

# 作業ディレクトリ設定
WORKDIR /code

# requirements.txt をコピーしてパッケージをインストール
COPY ./django/requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY ./src /code/src

# マイグレーションとサーバーの起動をコマンドで実行
CMD python src/manage.py migrate && \
    uvicorn config.asgi:application --host 0.0.0.0 --port 8000
