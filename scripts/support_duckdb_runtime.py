"""Shared DuckDB memory and spill-file settings for reproducible local runs."""

from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DUCKDB_TEMP_DIRECTORY = PROJECT_ROOT / "data" / "processed" / ".duckdb_temp"
DUCKDB_MEMORY_LIMIT = "3GB"
DUCKDB_MAX_TEMP_DIRECTORY_SIZE = "50GB"


def connect_duckdb(
    database: str | Path = ":memory:",
    *,
    read_only: bool = False,
) -> duckdb.DuckDBPyConnection:
    """Open DuckDB with bounded memory and spill files on the project data drive."""
    config = {
        "temp_directory": str(DUCKDB_TEMP_DIRECTORY.resolve()),
        "memory_limit": DUCKDB_MEMORY_LIMIT,
        "max_temp_directory_size": DUCKDB_MAX_TEMP_DIRECTORY_SIZE,
    }
    return duckdb.connect(
        str(database),
        read_only=read_only,
        config=config,
    )
