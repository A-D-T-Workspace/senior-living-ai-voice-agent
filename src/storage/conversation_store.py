import asyncio
import sqlite3
from pathlib import Path

from src.config import get_settings
from src.conversation.models import ConversationState

class ConversationStore:
    """Persistent SQLite storage for conversation sessions."""

    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or get_settings().database_url

        if not self.database_url.startswith("sqlite:///"):
            raise ValueError(
                "ConversationStore currently supports SQLite only."
            )

        database_path = self.database_url.removeprefix("sqlite:///")

        if database_path == ":memory:":
            raise ValueError(
                "In-memory SQLite is not supported for shared sessions."
            )

        self.database_path = Path(database_path).expanduser()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self):
        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    def _initialize(self):
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    session_id TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    async def initialize(self):
        """Create the database schema if it does not exist."""
        await asyncio.to_thread(self._initialize)

    def _save(self, state: ConversationState):
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO conversations (
                    session_id,
                    state_json,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    state_json = excluded.state_json,
                    updated_at = excluded.updated_at
                """,
                (
                    state.session_id,
                    state.model_dump_json(),
                    state.created_at.isoformat(),
                    state.updated_at.isoformat(),
                ),
            )

    async def save(self, state: ConversationState):
        """Persist a conversation state."""
        await asyncio.to_thread(self._save, state)

    def _get(self, session_id: str):
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT state_json
                FROM conversations
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()

        if row is None:
            return None

        return ConversationState.model_validate_json(row["state_json"])

    async def get(self, session_id: str):
        """Retrieve a conversation state by session ID."""
        return await asyncio.to_thread(self._get, session_id)

    def _delete(self, session_id: str):
        with self._connect() as connection:
            connection.execute(
                """
                DELETE FROM conversations
                WHERE session_id = ?
                """,
                (session_id,),
            )

    async def delete(self, session_id: str):
        """Delete a conversation session."""
        await asyncio.to_thread(self._delete, session_id)
