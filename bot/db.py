import os
from dotenv import load_dotenv
from contextlib import contextmanager
import psycopg2
from psycopg2 import sql
from datetime import date, timedelta

load_dotenv("./.env") 

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

@contextmanager
def get_cursor():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn.cursor()
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_db():
    with get_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                vpn_key TEXT,
                payment_due DATE,
                is_active BOOLEAN DEFAULT TRUE
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                message TEXT
            );
        """)


def log_message(user_id: int, message: str):
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO logs (user_id, message) VALUES (%s, %s);",
            (user_id, message)
        )


def add_or_update_user(telegram_id: int, username: str):
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO users (telegram_id, username, is_active)
            VALUES (%s, %s, FALSE)
            ON CONFLICT (telegram_id)
            DO UPDATE SET username = EXCLUDED.username;
        """, (telegram_id, username))


def get_all_users():
    with get_cursor() as cur:
        cur.execute("SELECT telegram_id FROM users WHERE is_active = TRUE;")
        return [row[0] for row in cur.fetchall()]


def add_access_for_user(telegram_id: str, vpn_key: str) -> int | None:
    with get_cursor() as cur:
        cur.execute("SELECT telegram_id FROM users WHERE telegram_id = %s;", (telegram_id,))
        result = cur.fetchone()

        if not result:
            return None

        telegram_id = result[0]

        cur.execute("""
            UPDATE users 
            SET payment_due = %s, is_active = TRUE, vpn_key = %s
            WHERE telegram_id = %s;
        """, (date.today() + timedelta(days=30), vpn_key, telegram_id))

        return telegram_id


        return telegram_id

def get_user_status(telegram_id: int) -> bool:
    with get_cursor() as cur:
        cur.execute("SELECT is_active FROM users WHERE telegram_id = %s;", (telegram_id,))
        row = cur.fetchone()
        return row[0] if row else False

def get_user_by_username(username: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute("""
            SELECT telegram_id, username, payment_due, is_active
            FROM users
            WHERE username = %s;
        """, (username,))
        row = cur.fetchone()

        if row:
            return {
                "telegram_id": row[0],
                "username": row[1],
                "payment_due": row[2],
                "is_active": row[3],
            }
        return None

def get_user_info(telegram_id: int) -> dict | None:
    with get_cursor() as cur:
        cur.execute("""
            SELECT payment_due, vpn_key FROM users WHERE telegram_id = %s;
        """, (telegram_id,))
        row = cur.fetchone()
        if row:
            return {"payment_due": row[0], "vpn_key": row[1]}
        return None
