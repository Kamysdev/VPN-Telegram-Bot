import os
from dotenv import load_dotenv

load_dotenv("./.env") 

# Конфигурация для бота
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Токен бота
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Telegram ID

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "vpn_db"),
    "user": os.getenv("DB_USER", "vpn_user"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}
