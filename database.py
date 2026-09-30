import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

if os.environ.get('VERCEL'):
    DB_FILE = os.path.join('/tmp', 'truthscan.db')
else:
    DB_FILE = os.path.join(os.path.dirname(__file__), 'truthscan.db')

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS forensic_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id TEXT UNIQUE NOT NULL,
            analysis_type TEXT NOT NULL,
            input_name TEXT NOT NULL,
            file_type TEXT,
            file_size INTEGER,
            sha256_hash TEXT,
            perceptual_hash TEXT,
            result TEXT,
            confidence REAL,
            metadata_json TEXT,
            fact_check_info TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    # Seed default admin user if not exists
    admin_user = c.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
    if not admin_user:
        hashed_pw = generate_password_hash('admin123')
        c.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                  ('admin', 'admin@truthscan.local', hashed_pw))
        conn.commit()

    conn.close()

def create_user(username, email, password):
    conn = get_db_connection()
    c = conn.cursor()
    hashed_pw = generate_password_hash(password)
    try:
        c.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                  (username.strip(), email.strip().lower(), hashed_pw))
        conn.commit()
        conn.close()
        return True, "User registered successfully."
    except sqlite3.IntegrityError as e:
        conn.close()
        err_str = str(e).lower()
        if 'username' in err_str:
            return False, "Username already exists."
        elif 'email' in err_str:
            return False, "Email already registered."
        return False, "Registration failed due to a constraint conflict."

def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username.strip(),)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email.strip().lower(),)).fetchone()
    conn.close()
    return dict(user) if user else None

def verify_user_password(username, password):
    user = get_user_by_username(username)
    if not user:
        return False, None
    if check_password_hash(user['password_hash'], password):
        return True, user
    return False, None

def save_record(data):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO forensic_records (
            record_id, analysis_type, input_name, file_type, file_size,
            sha256_hash, perceptual_hash, result, confidence, metadata_json, fact_check_info
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('record_id'), data.get('analysis_type'), data.get('input_name'),
        data.get('file_type'), data.get('file_size'), data.get('sha256_hash'),
        data.get('perceptual_hash'), data.get('result'), data.get('confidence'),
        data.get('metadata_json'), data.get('fact_check_info')
    ))
    conn.commit()
    conn.close()

def get_all_records():
    conn = get_db_connection()
    records = conn.execute('SELECT * FROM forensic_records ORDER BY timestamp DESC').fetchall()
    conn.close()
    return [dict(r) for r in records]

def get_record_by_id(record_id):
    conn = get_db_connection()
    record = conn.execute('SELECT * FROM forensic_records WHERE record_id = ?', (record_id,)).fetchone()
    conn.close()
    return dict(record) if record else None

