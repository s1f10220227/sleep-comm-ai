FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /code

COPY ./django/requirements.txt /code

RUN pip install -r requirements.txt

COPY . /code

CMD ["uvicorn", "config.wsgi:application", "--host", "0.0.0.0", "--port", "8000"]
