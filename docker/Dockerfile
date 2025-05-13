FROM python:3.11-alpine

WORKDIR /app

# Установим зависимости ОС
RUN apk add --no-cache postgresql-dev gcc python3-dev musl-dev

# Копируем requirements.txt из project-root
COPY requirements.txt ./requirements.txt

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходники Python-бота
COPY bot/ .

EXPOSE 8080

CMD ["python", "main.py"]
