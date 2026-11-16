from pathlib import Path

import scripts.support_duckdb_runtime as runtime


def test_duckdb_uses_configured_workspace_spill_directory(
    tmp_path, monkeypatch
) -> None:
    spill_directory = tmp_path / "duckdb-spill"
    monkeypatch.setattr(runtime, "DUCKDB_TEMP_DIRECTORY", spill_directory)

    with runtime.connect_duckdb() as connection:
        settings = dict(
            connection.execute(
                "SELECT name, value FROM duckdb_settings() "
                "WHERE name IN ('temp_directory', 'memory_limit', 'max_temp_directory_size')"
            ).fetchall()
        )

    assert Path(settings["temp_directory"]) == spill_directory.resolve()
    assert "GiB" in settings["memory_limit"]
    assert "GiB" in settings["max_temp_directory_size"]
