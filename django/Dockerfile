FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /code

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY ./django/requirements.txt /code

RUN pip install --no-cache-dir -r requirements.txt

COPY ./src /code/src

# src ディレクトリを Python パスに追加
ENV PYTHONPATH=/code/src:$PYTHONPATH

# マイグレーションとサーバー起動
CMD ["sh", "-c", "python src/manage.py makemigrations && python src/manage.py migrate && uvicorn config.asgi:application --host 0.0.0.0 --port $PORT"]