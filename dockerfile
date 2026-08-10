FROM python:3.13-slim

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

EXPOSE 8001

CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn app.wsgi:application --bind 0.0.0.0:8001"]
