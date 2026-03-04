import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "reverselens.db"

def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            pw_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            img_hash TEXT,
            answer TEXT,
            sources TEXT,
            agent_steps TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()

def add_user(username, pw_hash):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO users (username, pw_hash) VALUES (?, ?)", (username, pw_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user(username):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None

def save_history(user_id, img_hash, answer, sources, agent_steps=None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO history (user_id, img_hash, answer, sources, agent_steps) VALUES (?, ?, ?, ?, ?)",
        (user_id, img_hash, answer, json.dumps(sources, ensure_ascii=False), json.dumps(agent_steps or [], ensure_ascii=False))
    )
    conn.commit()
    conn.close()

def get_history(user_id, limit=20):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        d["sources"] = json.loads(d["sources"]) if d["sources"] else []
        d["agent_steps"] = json.loads(d["agent_steps"]) if d["agent_steps"] else []
        out.append(d)
    return out

init_db()
