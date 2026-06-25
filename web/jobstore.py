"""SQLite-backed job store for the web UI.

Replaces the original in-memory `JOBS` dict, which lost all job state on
every server restart.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,
    output_dir TEXT NOT NULL,
    error TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT
)
"""


class JobStore:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(SCHEMA)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def create_job(self, job_id, output_dir):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO jobs (job_id, status, progress, output_dir, created_at) VALUES (?, ?, ?, ?, ?)",
                (job_id, "pending", 0, str(output_dir), datetime.now().isoformat()),
            )

    def update_job(self, job_id, **fields):
        if not fields:
            return
        columns = ", ".join(f"{key} = ?" for key in fields)
        values = list(fields.values()) + [job_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE jobs SET {columns} WHERE job_id = ?", values)

    def get_job(self, job_id):
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            return dict(row) if row else None

    def list_jobs(self):
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
            return [dict(row) for row in rows]
