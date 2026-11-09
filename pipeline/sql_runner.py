"""Run the SQL files in order. The gap ratio comes from config."""

from __future__ import annotations

from pathlib import Path

import duckdb

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"


def run_sql(con: duckdb.DuckDBPyConnection, name: str, **params: object) -> None:
    text = (SQL_DIR / name).read_text()
    for key, value in params.items():
        text = text.replace("{{" + key + "}}", str(value))
    for statement in _statements(text):
        con.execute(statement)


def _statements(text: str) -> list[str]:
    cleaned: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        cleaned.append(line)
    return [part.strip() for part in "\n".join(cleaned).split(";") if part.strip()]
