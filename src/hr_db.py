import sqlite3
import os
from datetime import datetime, timezone, timedelta

DB_PATH = os.path.join('data', 'applications.db')


def init_db():
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            thread_id TEXT,
            company TEXT,
            role TEXT,
            sender TEXT,
            subject TEXT,
            body TEXT,
            status TEXT,
            hr_email TEXT,
            noted_at TEXT,
            followup_scheduled_at TEXT,
            followup_sent INTEGER DEFAULT 0
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS hr_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hr_email TEXT UNIQUE,
            name TEXT,
            company TEXT,
            notes TEXT,
            added_at TEXT
        )
    ''')

    conn.commit()
    conn.close()


def add_or_update_application(message):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    cur.execute('''
        INSERT OR IGNORE INTO applications
        (message_id, thread_id, company, role, sender, subject, body, status, noted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        message['id'],
        message['threadId'],
        message.get('company'),
        message.get('role'),
        message['from'],
        message['subject'],
        message['body'],
        message['status'],
        now
    ))

    cur.execute('''
        UPDATE applications
        SET status = ?, subject = ?, body = ?
        WHERE message_id = ?
    ''', (message['status'], message['subject'], message['body'], message['id']))

    conn.commit()
    conn.close()


def upsert_hr_contact(hr_email, name=None, company=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    cur.execute('''
        INSERT INTO hr_contacts (hr_email, name, company, added_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(hr_email) DO UPDATE SET
            name=excluded.name,
            company=excluded.company
    ''', (hr_email, name, company, now))

    conn.commit()
    conn.close()


def schedule_followup(message_id, days=7):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    follow_time = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()

    cur.execute('''
        UPDATE applications
        SET followup_scheduled_at=?, followup_sent=0
        WHERE message_id=?
    ''', (follow_time, message_id))

    conn.commit()
    conn.close()


def get_pending_followups():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    now = datetime.now(timezone.utc).isoformat()

    cur.execute('''
        SELECT message_id, subject, hr_email
        FROM applications
        WHERE followup_scheduled_at <= ?
        AND followup_sent = 0
    ''', (now,))

    rows = cur.fetchall()
    conn.close()
    return rows


def mark_followup_sent(message_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute('''
        UPDATE applications
        SET followup_sent = 1
        WHERE message_id = ?
    ''', (message_id,))

    conn.commit()
    conn.close()
