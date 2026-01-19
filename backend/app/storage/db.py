import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parents[2] / "data.sqlite3"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS parses (
            id TEXT PRIMARY KEY,
            created_at TEXT,
            parser TEXT,
            columns_json TEXT,
            rows_json TEXT,
            cell_conf_json TEXT,
            warnings_json TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS datasets (
            id TEXT PRIMARY KEY,
            name TEXT,
            created_at TEXT,
            source_parse_id TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS dataset_data (
            dataset_id TEXT PRIMARY KEY,
            columns_json TEXT,
            rows_json TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def insert_parse(
    parse_id: str,
    created_at: str,
    parser: str,
    columns: List[str],
    rows: List[Dict[str, Any]],
    cell_conf: List[List[int]],
    warnings: List[str],
) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO parses (id, created_at, parser, columns_json, rows_json, cell_conf_json, warnings_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            parse_id,
            created_at,
            parser,
            json.dumps(columns),
            json.dumps(rows),
            json.dumps(cell_conf),
            json.dumps(warnings),
        ),
    )
    conn.commit()
    conn.close()


def insert_dataset(
    dataset_id: str,
    name: str,
    created_at: str,
    source_parse_id: Optional[str],
    columns: List[str],
    rows: List[Dict[str, Any]],
) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO datasets (id, name, created_at, source_parse_id)
        VALUES (?, ?, ?, ?)
        """,
        (dataset_id, name, created_at, source_parse_id),
    )
    cur.execute(
        """
        INSERT INTO dataset_data (dataset_id, columns_json, rows_json)
        VALUES (?, ?, ?)
        """,
        (dataset_id, json.dumps(columns), json.dumps(rows)),
    )
    conn.commit()
    conn.close()


def list_datasets() -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT d.id, d.name, d.created_at, data.rows_json
        FROM datasets d
        JOIN dataset_data data ON data.dataset_id = d.id
        ORDER BY d.created_at DESC
        """
    )
    rows = []
    for row in cur.fetchall():
        rows.append(
            {
                "id": row["id"],
                "name": row["name"],
                "created_at": row["created_at"],
                "row_count": len(json.loads(row["rows_json"]) or []),
            }
        )
    conn.close()
    return rows


def get_dataset(dataset_id: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT d.id, d.name, d.created_at, d.source_parse_id, data.columns_json, data.rows_json
        FROM datasets d
        JOIN dataset_data data ON data.dataset_id = d.id
        WHERE d.id = ?
        """,
        (dataset_id,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "name": row["name"],
        "created_at": row["created_at"],
        "source_parse_id": row["source_parse_id"],
        "columns": json.loads(row["columns_json"]),
        "rows": json.loads(row["rows_json"]),
    }
