import sqlite3
import time
from typing import Optional, Tuple


DB_PATH = 'data/state.sqlite'


def _ensure_db() -> sqlite3.Connection:
    import os
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS matches (
            id TEXT PRIMARY KEY,
            url TEXT,
            status TEXT,
            last_hash TEXT,
            last_checked_at INTEGER,
            last_updated_at INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS maps (
            match_id TEXT,
            map_num INTEGER,
            last_hash TEXT,
            last_updated_at INTEGER,
            PRIMARY KEY(match_id, map_num)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS file_hashes (
            file_path TEXT PRIMARY KEY,
            content_hash TEXT,
            last_written_at INTEGER,
            last_modified_time REAL
        )
        """
    )
    conn.commit()
    return conn


def get_match_state(match_id: str) -> Optional[Tuple[str, str, str, str, int, int]]:
    conn = _ensure_db()
    cur = conn.execute(
        "SELECT id, url, status, last_hash, last_checked_at, last_updated_at FROM matches WHERE id=?",
        (match_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def upsert_match_state(match_id: str, url: str, last_hash: str, status: str) -> None:
    now = int(time.time())
    conn = _ensure_db()
    conn.execute(
        """
        INSERT INTO matches(id, url, status, last_hash, last_checked_at, last_updated_at)
        VALUES(?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
          url=excluded.url,
          status=excluded.status,
          last_hash=excluded.last_hash,
          last_checked_at=excluded.last_checked_at,
          last_updated_at=excluded.last_updated_at
        """,
        (match_id, url, status, last_hash, now, now),
    )
    conn.commit()
    conn.close()


def get_map_state(match_id: str, map_num: int) -> Optional[Tuple[str, int, str, int]]:
    conn = _ensure_db()
    cur = conn.execute(
        "SELECT match_id, map_num, last_hash, last_updated_at FROM maps WHERE match_id=? AND map_num=?",
        (match_id, map_num),
    )
    row = cur.fetchone()
    conn.close()
    return row


def upsert_map_state(match_id: str, map_num: int, last_hash: str) -> None:
    now = int(time.time())
    conn = _ensure_db()
    conn.execute(
        """
        INSERT INTO maps(match_id, map_num, last_hash, last_updated_at)
        VALUES(?,?,?,?)
        ON CONFLICT(match_id, map_num) DO UPDATE SET
          last_hash=excluded.last_hash,
          last_updated_at=excluded.last_updated_at
        """,
        (match_id, map_num, last_hash, now),
    )
    conn.commit()
    conn.close()


def get_file_hash(file_path: str) -> Optional[Tuple[str, int, float]]:
    """Get stored content hash and timestamps for a file."""
    conn = _ensure_db()
    cur = conn.execute(
        "SELECT content_hash, last_written_at, last_modified_time FROM file_hashes WHERE file_path=?",
        (file_path,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def upsert_file_hash(file_path: str, content_hash: str, modified_time: float) -> None:
    """Store content hash and timestamps for a file."""
    now = int(time.time())
    conn = _ensure_db()
    conn.execute(
        """
        INSERT INTO file_hashes(file_path, content_hash, last_written_at, last_modified_time)
        VALUES(?,?,?,?)
        ON CONFLICT(file_path) DO UPDATE SET
          content_hash=excluded.content_hash,
          last_written_at=excluded.last_written_at,
          last_modified_time=excluded.last_modified_time
        """,
        (file_path, content_hash, now, modified_time),
    )
    conn.commit()
    conn.close()
