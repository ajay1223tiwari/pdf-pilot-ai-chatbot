
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "chat_history.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pdf_id TEXT NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_pdf_id
            ON chat_messages(pdf_id)
        """)


def save_message(pdf_id, role, message):
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO chat_messages (pdf_id, role, message)
            VALUES (?, ?, ?)
        """, (pdf_id, role, message))

        return cursor.lastrowid


def get_chat_history(pdf_id):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, pdf_id, role, message, created_at
            FROM chat_messages
            WHERE pdf_id = ?
            ORDER BY id ASC
        """, (pdf_id,)).fetchall()

        return [dict(row) for row in rows]


def delete_chat_history(pdf_id):
    with get_connection() as conn:
        conn.execute("""
            DELETE FROM chat_messages
            WHERE pdf_id = ?
        """, (pdf_id,))
