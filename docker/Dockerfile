FROM python:3.13-slim
WORKDIR /app

COPY bot/ .
COPY ../requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

# Открываем порт для работы
EXPOSE 8000

CMD ["python", "main.py"]
