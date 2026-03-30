"""Voice library storage - SQLite backend."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

from audiobook.models.voice import Voice


class VoiceLibrary:
    """SQLite-backed voice library storage."""

    def __init__(self, path: str) -> None:
        """Initialize voice library with database at given path.

        Args:
            path: Directory path for the voice library database.
        """
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.db_path = self.path / "voice_library.db"
        self._conn: Optional[sqlite3.Connection] = None
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self) -> None:
        """Close database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _init_database(self) -> None:
        """Create voices table and indexes."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voices (
                voice_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                gender TEXT NOT NULL,
                age_range TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT '[]',
                description TEXT NOT NULL DEFAULT '',
                embedding TEXT,
                audio_path TEXT NOT NULL DEFAULT ''
            )
        """)

        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_voices_gender
            ON voices(gender)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_voices_age_range
            ON voices(age_range)
        """)

        conn.commit()

    def add(self, voice: Voice) -> None:
        """Add or replace a voice in the library.

        Args:
            voice: Voice object to add.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO voices
            (voice_id, name, gender, age_range, tags, description, embedding, audio_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            voice.voice_id,
            voice.name,
            voice.gender,
            voice.age_range,
            json.dumps(voice.tags),
            voice.description,
            json.dumps(voice.embedding) if voice.embedding else None,
            voice.audio_path,
        ))

        conn.commit()

    def get(self, voice_id: str) -> Optional[Voice]:
        """Get a voice by ID.

        Args:
            voice_id: The voice ID to look up.

        Returns:
            Voice object if found, None otherwise.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM voices WHERE voice_id = ?",
            (voice_id,)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_voice(row)

    def list(
        self,
        gender: Optional[str] = None,
        age_range: Optional[str] = None
    ) -> list[Voice]:
        """List voices with optional filtering.

        Args:
            gender: Filter by gender (optional).
            age_range: Filter by age range (optional).

        Returns:
            List of matching Voice objects.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM voices WHERE 1=1"
        params: list[str] = []

        if gender is not None:
            query += " AND gender = ?"
            params.append(gender)

        if age_range is not None:
            query += " AND age_range = ?"
            params.append(age_range)

        query += " ORDER BY name"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [self._row_to_voice(row) for row in rows]

    def search_by_tags(self, tags: list[str]) -> list[Voice]:
        """Search voices by tags using OR logic.

        Args:
            tags: List of tags to search for.

        Returns:
            List of Voice objects matching any of the tags.
        """
        if not tags:
            return []

        conn = self._get_connection()
        cursor = conn.cursor()

        # Use JSON functions to search tags (SQLite 3.38+)
        # Fallback: fetch all and filter in Python
        cursor.execute("SELECT * FROM voices")
        rows = cursor.fetchall()

        results = []
        for row in rows:
            voice = self._row_to_voice(row)
            # Check if any tag matches (OR logic)
            if any(tag in voice.tags for tag in tags):
                results.append(voice)

        return results

    def delete(self, voice_id: str) -> None:
        """Delete a voice by ID.

        Args:
            voice_id: The voice ID to delete.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM voices WHERE voice_id = ?", (voice_id,))
        conn.commit()

    def update(self, voice: Voice) -> None:
        """Update an existing voice.

        Args:
            voice: Voice object with updated data.
        """
        # Use add with INSERT OR REPLACE semantics
        self.add(voice)

    def count(self) -> int:
        """Count total voices in the library.

        Returns:
            Number of voices in the library.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM voices")
        result = cursor.fetchone()
        return result[0] if result else 0

    def _row_to_voice(self, row: sqlite3.Row) -> Voice:
        """Convert database row to Voice object.

        Args:
            row: SQLite row object.

        Returns:
            Voice object populated from row data.
        """
        return Voice(
            voice_id=row["voice_id"],
            name=row["name"],
            gender=row["gender"],
            age_range=row["age_range"],
            tags=json.loads(row["tags"]),
            description=row["description"],
            embedding=json.loads(row["embedding"]) if row["embedding"] else None,
            audio_path=row["audio_path"],
        )