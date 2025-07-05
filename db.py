import sqlite3
import os
import json
from datetime import datetime
import threading
import time

db_lock = threading.Lock()
DB_PATH= "keystroke2.db"
MAX_FEATURES_PER_USER = 2000

def safe_execute(cursor, sql, values, retries=5, delay=1):
    for i in range(retries):
        try:
            cursor.execute(sql, values)
            return
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                print(f"[RETRY {i+1}] DB is locked, retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise
    raise Exception("[FAILED] Max retries reached for DB INSERT.")

def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    c = conn.cursor()

    # Buat tabel users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            password TEXT
        )
    ''')

    # Buat tabel features (minimal kolom dasar)
    c.execute('''
        CREATE TABLE IF NOT EXISTS features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            password TEXT
        )
    ''')

    conn.commit()
    conn.close()

def column_exists(column_name):
    conn = sqlite3.connect(DB_PATH, timeout=5)
    c = conn.cursor()
    c.execute("PRAGMA table_info(features)")
    columns = [row[1] for row in c.fetchall()]
    conn.close()
    return column_name in columns

def add_column_if_not_exists(column_name, c):
    c.execute("PRAGMA table_info(features)")
    columns = [row[1] for row in c.fetchall()]
    if column_name in columns:
        return
    try:
        # Gunakan kutip ganda untuk nama kolom seperti "H.1"
        if column_name == "created_at":
            c.execute(f'ALTER TABLE features ADD COLUMN "{column_name}" TEXT')
        else:
            c.execute(f'ALTER TABLE features ADD COLUMN "{column_name}" REAL')
    except Exception as e:
        print(f"[ERROR] Gagal tambah kolom '{column_name}': {e}")

def insert_user(user_id, password):
    conn = sqlite3.connect(DB_PATH, timeout=5)
    c = conn.cursor()
    c.execute("INSERT INTO users (user_id, password) VALUES (?, ?)", (user_id, password))
    conn.commit()
    conn.close()

def insert_features(user_id, password, features_list):
    with db_lock:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        c = conn.cursor()

        add_column_if_not_exists("created_at", c)

        all_keys = set()
        for feature_dict in features_list:
            all_keys.update(feature_dict.keys())
        for key in all_keys:
            add_column_if_not_exists(key, c)

        for feature_dict in features_list:
            feature_dict["created_at"] = datetime.now().isoformat()

            columns = ['user_id', 'password'] + list(feature_dict.keys())
            
            values = [user_id, password] + list(feature_dict.values())
            
            placeholders = ', '.join(['?'] * len(values))
            quoted_columns = ', '.join([f'"{col}"' for col in columns])  # INI PENTING
            
            sql = f"INSERT INTO features ({quoted_columns}) VALUES ({placeholders})"

            try:
                safe_execute(c, sql, values)
            except Exception as e:
                print(f"[ERROR] Gagal INSERT: {e}")
                print("SQL:", sql)
                print("VALUES:", values)
                raise e
            
        c.execute("SELECT COUNT(*) FROM features WHERE user_id = ?", (user_id,))
        count = c.fetchone()[0]

        if count > MAX_FEATURES_PER_USER:
            to_delete = count - MAX_FEATURES_PER_USER
            try:
                c.execute(f'''
                    DELETE FROM features
                    WHERE id IN (
                        SELECT id FROM features
                        WHERE user_id = ?
                        ORDER BY created_at ASC
                        LIMIT ?
                    )
                ''', (user_id, to_delete))
                print(f"[INFO] Hapus {to_delete} data lama user '{user_id}' karena melebihi batas {MAX_FEATURES_PER_USER}")
            except Exception as e:
                print(f"[WARNING] Gagal hapus data lama: {e}")

        conn.commit()
        conn.close()

def get_all_data():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    c = conn.cursor()
    c.execute("SELECT * FROM features")
    rows = c.fetchall()
    conn.close()
    return rows

def user_exists(user_id):
    conn = sqlite3.connect(DB_PATH, timeout=5)
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None
