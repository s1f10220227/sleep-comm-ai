FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1 && DJANGO_SETTINGS_MODULE config.production

WORKDIR /code

COPY ./django/requirements.txt /code

RUN pip install -r requirements.txt

COPY ./src /code/src

# src ディレクトリを Python パスに追加
ENV PYTHONPATH=/code/src:$PYTHONPATH

CMD python manage.py migrate && uvicorn config.wsgi:application -b 0.0.0.0:8000