import sqlite3
import os
from datetime import datetime

DB_FILE = "truthscan.db"

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
    conn.commit()
    conn.close()

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
