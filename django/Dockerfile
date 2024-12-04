FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /code

COPY ./requirements.txt /code

RUN pip install -r requirements.txt

# `./src` ディレクトリをコンテナの `/code` ディレクトリにコピー
COPY ./src /code/src

# src ディレクトリを Python パスに追加
ENV PYTHONPATH=/code/src:$PYTHONPATH

CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
