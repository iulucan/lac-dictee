"""
Storage module — persists correction sessions to SQLite.
"""

import sqlite3
import json
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from src.correction import CorrectionResult, DictationError

DB_PATH = Path(__file__).parent.parent / "data" / "corrections.db"


@dataclass
class CorrectionRecord:
    id: int
    student_name: str
    correct_text: str
    student_text: str
    score: int
    error_count: int
    total_words: int
    errors_json: str
    created_at: str

    def to_correction_result(self) -> CorrectionResult:
        errors = [
            DictationError(**e) for e in json.loads(self.errors_json)
        ]
        return CorrectionResult(
            score=self.score,
            total_words=self.total_words,
            errors=errors,
        )


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS corrections (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT    NOT NULL DEFAULT '',
                correct_text TEXT    NOT NULL,
                student_text TEXT    NOT NULL,
                score        INTEGER NOT NULL,
                error_count  INTEGER NOT NULL,
                total_words  INTEGER NOT NULL,
                errors_json  TEXT    NOT NULL,
                created_at   TEXT    NOT NULL
            )
        """)


def save_correction(
    correction: CorrectionResult,
    student_name: str,
    correct_text: str,
    student_text: str,
) -> int:
    """Save a correction to the database. Returns the new row id."""
    init_db()
    errors_json = json.dumps([
        {"wrong": e.wrong, "correct": e.correct, "type": e.type, "explanation": e.explanation}
        for e in correction.errors
    ])
    with _connect() as conn:
        cursor = conn.execute(
            """INSERT INTO corrections
               (student_name, correct_text, student_text, score, error_count, total_words, errors_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                student_name or "",
                correct_text,
                student_text,
                correction.score,
                correction.error_count,
                correction.total_words,
                errors_json,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        return cursor.lastrowid


def list_corrections(limit: int = 20) -> list[CorrectionRecord]:
    """Return the most recent corrections, newest first."""
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM corrections ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [CorrectionRecord(**dict(r)) for r in rows]


def get_correction(record_id: int) -> Optional[CorrectionRecord]:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM corrections WHERE id = ?", (record_id,)
        ).fetchone()
    return CorrectionRecord(**dict(row)) if row else None
