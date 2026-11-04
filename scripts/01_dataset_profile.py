from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "food.parquet"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "profiling"


def main() -> None:
    if not DATA_FILE.is_file():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with duckdb.connect() as connection:
        row_count = connection.execute(
            "SELECT COUNT(*) AS total_rows FROM read_parquet(?)",
            [str(DATA_FILE)],
        ).fetchdf()
        columns = connection.execute(
            "DESCRIBE SELECT * FROM read_parquet(?)",
            [str(DATA_FILE)],
        ).fetchdf()

    row_count.to_csv(OUTPUT_DIR / "dataset_row_count.csv", index=False)
    columns.to_csv(OUTPUT_DIR / "dataset_columns.csv", index=False)

    print("Dataset profile completed.")
    print(f"Total rows: {row_count.loc[0, 'total_rows']:,}")
    print(f"Total columns: {len(columns):,}")
    print(f"Outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
