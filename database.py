"""
database.py — قاعدة البيانات SQLite
جداول: users, tracked_urls, price_history, alert_log
"""

import sqlite3
import hashlib
import secrets
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

DB_PATH = Path(os.environ.get("DB_PATH", "price_tracker.db"))


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            telegram_chat_id TEXT,
            telegram_phone   TEXT,
            is_verified   INTEGER NOT NULL DEFAULT 0,
            link_token    TEXT    UNIQUE,
            created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS tracked_urls (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            url        TEXT    NOT NULL,
            category   TEXT    NOT NULL DEFAULT 'competitor',
            label      TEXT,
            created_at TEXT    NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_id, url)
        );

        CREATE TABLE IF NOT EXISTS price_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            url_id     INTEGER NOT NULL REFERENCES tracked_urls(id) ON DELETE CASCADE,
            offer_key  TEXT    NOT NULL,
            price      REAL    NOT NULL,
            checked_at TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS alert_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            url        TEXT    NOT NULL,
            message    TEXT    NOT NULL,
            sent_at    TEXT    NOT NULL DEFAULT (datetime('now'))
        );
        """)


# ─── USERS ────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(name: str, email: str, password: str) -> Optional[int]:
    token = secrets.token_urlsafe(24)
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash, link_token) VALUES (?,?,?,?)",
                (name, email.lower().strip(), hash_password(password), token)
            )
            return cur.lastrowid
    except sqlite3.IntegrityError:
        return None


def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE email=?", (email.lower().strip(),)
        ).fetchone()


def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()


def get_user_by_token(token: str) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE link_token=?", (token,)).fetchone()


def verify_user(user_id: int, chat_id: str, phone: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET telegram_chat_id=?, telegram_phone=?, is_verified=1 WHERE id=?",
            (chat_id, phone, user_id)
        )


def refresh_link_token(user_id: int) -> str:
    token = secrets.token_urlsafe(24)
    with get_conn() as conn:
        conn.execute("UPDATE users SET link_token=? WHERE id=?", (token, user_id))
    return token


def authenticate(email: str, password: str) -> Optional[sqlite3.Row]:
    user = get_user_by_email(email)
    if user and user["password_hash"] == hash_password(password):
        return user
    return None


# ─── TRACKED URLS ─────────────────────────────────────────────

def add_url(user_id: int, url: str, category: str, label: str = "") -> bool:
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO tracked_urls (user_id, url, category, label) VALUES (?,?,?,?)",
                (user_id, url.strip(), category, label.strip())
            )
        return True
    except sqlite3.IntegrityError:
        return False


def delete_url(url_id: int, user_id: int):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM tracked_urls WHERE id=? AND user_id=?", (url_id, user_id)
        )


def get_urls_for_user(user_id: int) -> list:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM tracked_urls WHERE user_id=? ORDER BY category, created_at DESC",
            (user_id,)
        ).fetchall()


def get_all_urls_with_users() -> list:
    """للـ scraper — كل الروابط مع بيانات أصحابها"""
    with get_conn() as conn:
        return conn.execute("""
            SELECT t.id, t.url, t.user_id, u.telegram_chat_id
            FROM tracked_urls t
            JOIN users u ON u.id = t.user_id
            WHERE u.is_verified = 1 AND u.telegram_chat_id IS NOT NULL
        """).fetchall()


# ─── PRICE HISTORY ────────────────────────────────────────────

def get_last_price(url_id: int, offer_key: str) -> Optional[float]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT price FROM price_history WHERE url_id=? AND offer_key=? ORDER BY checked_at DESC LIMIT 1",
            (url_id, offer_key)
        ).fetchone()
        return row["price"] if row else None


def save_price(url_id: int, offer_key: str, price: float):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO price_history (url_id, offer_key, price) VALUES (?,?,?)",
            (url_id, offer_key, price)
        )


# ─── ALERT LOG ────────────────────────────────────────────────

def log_alert(user_id: int, url: str, message: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO alert_log (user_id, url, message) VALUES (?,?,?)",
            (user_id, url, message)
        )


def get_alerts_for_user(user_id: int, limit: int = 50) -> list:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM alert_log WHERE user_id=? ORDER BY sent_at DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()


# تهيئة قاعدة البيانات عند الاستيراد
init_db()
