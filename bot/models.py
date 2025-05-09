# Модели данных для работы с базой данных
import psycopg2
from config import DB_CONFIG

def create_table():
    conn = psycopg2.connect(**DB_CONFIG)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                user_id BIGINT UNIQUE NOT NULL,
                username TEXT
                );''')
    conn.commit()
    conn.close()

def get_all_users():
    conn = psycopg2.connect(**DB_CONFIG)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users;")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def add_or_update_user(user_id, username):
    conn = psycopg2.connect(**DB_CONFIG)
    c = conn.cursor()
    c.execute('''
    INSERT INTO users (user_id, username)
    VALUES (%s, %s)
    ON CONFLICT (user_id) 
    DO UPDATE SET username = EXCLUDED.username;
    ''', (user_id, username))
    conn.commit()
    conn.close()
