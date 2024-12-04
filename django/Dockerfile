FROM python:3.11-slim

# 環境変数設定
ENV PYTHONUNBUFFERED 1 && DJANGO_SETTINGS_MODULE config.production

WORKDIR /code

# requirements.txt を最初にコピーしてインストール
COPY ./django/requirements.txt /code
RUN pip install -r requirements.txt

# src ディレクトリを /code/src にコピー
COPY ./src /code/src

# src 内の manage.py を /code にコピー
COPY ./src/manage.py /code/manage.py

# src ディレクトリを Python パスに追加
ENV PYTHONPATH=/code/src:$PYTHONPATH

# マイグレーションとサーバーの起動
CMD python manage.py migrate && uvicorn config.wsgi:application -b 0.0.0.0:8000
