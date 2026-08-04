import sqlite3
from pathlib import Path

from services.chunking import count_tokens

Path("data").mkdir(exist_ok=True)
_db = sqlite3.connect("data/history.db", check_same_thread=False)
_db.execute(
    """CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    role TEXT,
    content TEXT,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP
)"""
)
_db.commit()

# Reset conversation memory on every backend startup.
_db.execute("DELETE FROM messages")
_db.commit()

def save_message(session_id: str, role: str, content: str):
    _db.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content),
    )
    _db.commit()

def load_history(session_id: str, token_budget: int = 800) -> list[dict]:
    """Return recent messages that fit within token_budget (a sliding window)
    Oldest messages are dropped first, so the most recent messages are always included."""

    rows = _db.execute(
        "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id DESC",
        (session_id,),
    ).fetchall()
    picked, used = [], 0
    for role, content in rows:
        t = count_tokens(content)
        if used + t > token_budget:
            break
        picked.append({"role": role, "content": content})
        used += t
    return list(reversed(picked))  # reverse to chronological order