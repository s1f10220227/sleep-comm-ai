FROM python:3.11-slim

# 環境変数の設定
ENV PYTHONUNBUFFERED=1

# 作業ディレクトリ設定
WORKDIR /code

# requirements.txt をコピーしてパッケージをインストール
COPY ./django/requirements.txt /code/

RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY ./src /code/src

# src ディレクトリを Python パスに追加
ENV PYTHONPATH=/code/src:$PYTHONPATH

# マイグレーションとサーバーの起動をコマンドで実行
CMD python src/manage.py migrate && \
    uvicorn config.wsgi:application --host 0.0.0.0 --port 8000
