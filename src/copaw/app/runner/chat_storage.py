import json
import sqlite3
import time
import uuid
from pathlib import Path


class ChatStorage:
    def __init__(self, db_path: Path):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _ensure_schema(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at INTEGER,
                    updated_at INTEGER,
                    status TEXT,
                    meta TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT,
                    tool_calls TEXT,
                    reasoning_content TEXT,
                    token_count INTEGER,
                    tool_call_id TEXT,
                    position INTEGER,
                    created_at INTEGER,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_pos
                ON messages(conversation_id, position)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS im_sessions (
                    provider TEXT NOT NULL,
                    im_user_id TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    created_at INTEGER,
                    updated_at INTEGER,
                    PRIMARY KEY (provider, im_user_id)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_im_sessions_conversation
                ON im_sessions(conversation_id)
                """
            )
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                    content,
                    reasoning_content,
                    content='messages',
                    content_rowid='rowid'
                )
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
                    INSERT INTO messages_fts(rowid, content, reasoning_content)
                    VALUES (new.rowid, new.content, new.reasoning_content);
                END
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
                    INSERT INTO messages_fts(messages_fts, rowid, content, reasoning_content)
                    VALUES('delete', old.rowid, old.content, old.reasoning_content);
                END
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
                    INSERT INTO messages_fts(messages_fts, rowid, content, reasoning_content)
                    VALUES('delete', old.rowid, old.content, old.reasoning_content);
                    INSERT INTO messages_fts(rowid, content, reasoning_content)
                    VALUES (new.rowid, new.content, new.reasoning_content);
                END
                """
            )

    def upsert_conversation(
        self,
        conversation_id,
        title=None,
        status="active",
        meta=None,
    ):
        now = int(time.time())
        meta_json = json.dumps(meta, ensure_ascii=False) if meta is not None else None
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT id, created_at FROM conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE conversations
                    SET title = ?, updated_at = ?, status = ?, meta = ?
                    WHERE id = ?
                    """,
                    (title, now, status, meta_json, conversation_id),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO conversations (id, title, created_at, updated_at, status, meta)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (conversation_id, title, now, now, status, meta_json),
                )

    def _message_count(self, conversation_id):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(1) AS cnt FROM messages WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
        return int(row["cnt"] or 0) if row else 0

    def append_messages(
        self,
        conversation_id,
        messages,
        title=None,
        status="active",
        meta=None,
    ):
        if not messages:
            return
        self.upsert_conversation(
            conversation_id,
            title=title,
            status=status,
            meta=meta,
        )
        now = int(time.time())
        position = self._message_count(conversation_id)
        with self._connect() as conn:
            for msg in messages:
                msg_id = msg.get("id") or uuid.uuid4().hex
                tool_calls = msg.get("tool_calls")
                tool_calls_json = (
                    json.dumps(tool_calls, ensure_ascii=False)
                    if tool_calls is not None
                    else None
                )
                reasoning_content = msg.get("reasoning_content") or msg.get(
                    "reasoning",
                )
                conn.execute(
                    """
                    INSERT INTO messages (
                        id, conversation_id, role, content, tool_calls, reasoning_content,
                        token_count, tool_call_id, position, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        msg_id,
                        conversation_id,
                        msg.get("role") or "assistant",
                        msg.get("content"),
                        tool_calls_json,
                        reasoning_content,
                        msg.get("token_count"),
                        msg.get("tool_call_id"),
                        position,
                        msg.get("created_at") or now,
                    ),
                )
                position += 1

    def list_conversations(self):
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT c.id, c.title, c.updated_at, im.provider AS im_provider
                FROM conversations c
                LEFT JOIN (
                    SELECT conversation_id, MIN(provider) AS provider
                    FROM im_sessions
                    GROUP BY conversation_id
                ) im ON im.conversation_id = c.id
                ORDER BY c.updated_at DESC
                """
            ).fetchall()
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "updated_at": row["updated_at"],
                "im_provider": row["im_provider"],
            }
            for row in rows
        ]

    def get_messages(self, conversation_id):
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT role, content, tool_calls, reasoning_content, token_count, tool_call_id
                FROM messages
                WHERE conversation_id = ?
                ORDER BY position ASC
                """,
                (conversation_id,),
            ).fetchall()
        messages = []
        for row in rows:
            msg = {"role": row["role"], "content": row["content"]}
            if row["tool_calls"]:
                msg["tool_calls"] = json.loads(row["tool_calls"])
            if row["reasoning_content"] is not None:
                msg["reasoning_content"] = row["reasoning_content"]
                msg["reasoning"] = row["reasoning_content"]
            if row["token_count"] is not None:
                msg["token_count"] = row["token_count"]
            if row["tool_call_id"] is not None:
                msg["tool_call_id"] = row["tool_call_id"]
            messages.append(msg)
        return messages

    def get_recent_messages(self, conversation_id, limit: int = 20):
        if limit <= 0:
            return []
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT role, content, tool_calls, reasoning_content, token_count, tool_call_id
                FROM messages
                WHERE conversation_id = ?
                ORDER BY position DESC
                LIMIT ?
                """,
                (conversation_id, limit),
            ).fetchall()
        rows = list(reversed(rows))
        messages = []
        for row in rows:
            msg = {"role": row["role"], "content": row["content"]}
            if row["tool_calls"]:
                msg["tool_calls"] = json.loads(row["tool_calls"])
            if row["reasoning_content"] is not None:
                msg["reasoning_content"] = row["reasoning_content"]
                msg["reasoning"] = row["reasoning_content"]
            if row["token_count"] is not None:
                msg["token_count"] = row["token_count"]
            if row["tool_call_id"] is not None:
                msg["tool_call_id"] = row["tool_call_id"]
            messages.append(msg)
        return messages

    def search_messages(self, conversation_id, query, limit=5):
        if not query:
            return []
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT m.role, m.content, m.reasoning_content, m.tool_calls, m.tool_call_id
                FROM messages_fts f
                JOIN messages m ON m.rowid = f.rowid
                WHERE m.conversation_id = ? AND messages_fts MATCH ?
                ORDER BY m.created_at DESC
                LIMIT ?
                """,
                (conversation_id, query, limit),
            ).fetchall()
        results = []
        for row in rows:
            results.append(
                {
                    "role": row["role"],
                    "content": row["content"],
                    "reasoning_content": row["reasoning_content"],
                    "tool_calls": (
                        json.loads(row["tool_calls"])
                        if row["tool_calls"]
                        else None
                    ),
                    "tool_call_id": row["tool_call_id"],
                }
            )
        return results
