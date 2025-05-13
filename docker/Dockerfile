FROM python:3.12-alpine
WORKDIR /app

COPY bot/ .
COPY ../requirements.txt /app/requirements.txt

RUN apk add postgresql-dev gcc python3-dev musl-dev
RUN pip install --no-cache-dir -r /app/requirements.txt

# Открываем порт для работы
EXPOSE 8000

CMD ["python", "main.py"]
