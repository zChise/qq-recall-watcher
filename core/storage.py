import json
import sqlite3
from pathlib import Path
from typing import List, Optional

DB_PATH = Path("data/recalled.db")


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recalled (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                msg_id      INTEGER UNIQUE,
                chat_type   TEXT,
                group_id    INTEGER,
                group_name  TEXT DEFAULT '',
                user_id     INTEGER,
                sender_name TEXT,
                content     TEXT,
                recalled_at REAL,
                is_read     INTEGER DEFAULT 0
            )
        """)
        # 兼容旧数据库：新增列不报错
        try:
            conn.execute("ALTER TABLE recalled ADD COLUMN group_name TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass
        conn.execute("CREATE INDEX IF NOT EXISTS idx_time ON recalled(recalled_at DESC)")


def _conn():
    return sqlite3.connect(DB_PATH)


def save_recalled(msg, final_content: list, recalled_at: float):
    with _conn() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO recalled
            (msg_id, chat_type, group_id, group_name, user_id, sender_name, content, recalled_at)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            msg.msg_id, msg.chat_type, msg.group_id, msg.group_name,
            msg.user_id, msg.sender_name,
            json.dumps(final_content, ensure_ascii=False),
            recalled_at,
        ))


def get_unread_count() -> int:
    with _conn() as conn:
        row = conn.execute("SELECT COUNT(*) FROM recalled WHERE is_read=0").fetchone()
    return row[0]


def get_messages(page: int = 1, page_size: int = 30,
                 group_id: Optional[int] = None,
                 user_id:  Optional[int] = None) -> List[dict]:
    where, params = [], []
    if group_id is not None:
        where.append("group_id = ?")
        params.append(group_id)
    elif user_id is not None:
        where.append("user_id = ? AND chat_type = 'private'")
        params.append(user_id)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    params += [page_size, (page - 1) * page_size]

    cols = "id,msg_id,chat_type,group_id,group_name,user_id,sender_name,content,recalled_at,is_read"
    with _conn() as conn:
        rows = conn.execute(f"""
            SELECT {cols} FROM recalled {where_sql}
            ORDER BY recalled_at DESC LIMIT ? OFFSET ?
        """, params).fetchall()

    result = []
    for row in rows:
        d = dict(zip(cols.split(","), row))
        d["content"] = json.loads(d["content"])
        result.append(d)
    return result


def mark_read(msg_id: int):
    with _conn() as conn:
        conn.execute("UPDATE recalled SET is_read=1 WHERE msg_id=?", (msg_id,))


def mark_all_read(group_id: Optional[int] = None, user_id: Optional[int] = None):
    where, params = [], []
    if group_id is not None:
        where.append("group_id = ?"); params.append(group_id)
    elif user_id is not None:
        where.append("user_id = ? AND chat_type = 'private'"); params.append(user_id)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    with _conn() as conn:
        conn.execute(f"UPDATE recalled SET is_read=1 {where_sql}", params)


def get_chat_list() -> List[dict]:
    with _conn() as conn:
        rows = conn.execute("""
            SELECT chat_type, group_id,
                   MAX(group_name) group_name,
                   user_id, sender_name,
                   COUNT(*) total, SUM(1 - is_read) unread,
                   MAX(recalled_at) last_time
            FROM recalled
            GROUP BY chat_type, COALESCE(group_id, user_id)
            ORDER BY last_time DESC
        """).fetchall()
    return [
        dict(zip(["chat_type","group_id","group_name","user_id","sender_name",
                  "total","unread","last_time"], row))
        for row in rows
    ]
