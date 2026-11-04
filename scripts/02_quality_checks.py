import json
from collections import defaultdict
from pathlib import Path

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "food.parquet"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "quality"
DUPLICATE_IDENTITY_FIELDS = (
    "product_name",
    "brands",
    "brands_tags",
    "categories_tags",
    "countries_tags",
    "quantity",
    "packaging_text",
    "packaging_tags",
)


def serialize_record_summaries(records: list[dict]) -> str:
    fields = (
        "rev",
        "last_modified_t",
        "last_updated_t",
        "last_editor",
        *DUPLICATE_IDENTITY_FIELDS,
    )
    summaries = [
        {field: record.get(field) for field in fields}
        for record in sorted(
            records,
            key=lambda record: int(record.get("last_modified_t") or 0),
        )
    ]
    return json.dumps(
        summaries,
        ensure_ascii=False,
        sort_keys=True,
    )


def main() -> None:
    if not DATA_FILE.is_file():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with duckdb.connect() as connection:
        columns = connection.execute(
            "DESCRIBE SELECT * FROM read_parquet(?)",
            [str(DATA_FILE)],
        ).fetchdf()
        if "code" not in columns["column_name"].values:
            raise ValueError(
                f"Required column 'code' is missing from {DATA_FILE}"
            )

        summary = connection.execute(
            """
            WITH code_counts AS (
                SELECT code, COUNT(*) AS occurrence_count
                FROM read_parquet(?)
                WHERE code IS NOT NULL
                GROUP BY code
            ),
            dataset_counts AS (
                SELECT
                    COUNT(*) AS total_rows,
                    COUNT(*) FILTER (WHERE code IS NULL) AS null_code_rows,
                    COUNT(*) FILTER (WHERE code IS NOT NULL) AS non_null_code_rows,
                    COUNT(DISTINCT code) AS distinct_non_null_codes
                FROM read_parquet(?)
            )
            SELECT
                total_rows,
                null_code_rows,
                non_null_code_rows,
                distinct_non_null_codes,
                (
                    SELECT COUNT(*)
                    FROM code_counts
                    WHERE occurrence_count > 1
                ) AS duplicate_code_groups,
                CAST(
                    COALESCE(
                        (
                            SELECT SUM(occurrence_count - 1)
                            FROM code_counts
                            WHERE occurrence_count > 1
                        ),
                        0
                    ) AS BIGINT
                ) AS duplicate_rows
            FROM dataset_counts
            """,
            [str(DATA_FILE), str(DATA_FILE)],
        ).fetchdf()
        duplicate_codes = connection.execute(
            """
            SELECT code, COUNT(*) AS occurrence_count
            FROM read_parquet(?)
            WHERE code IS NOT NULL
            GROUP BY code
            HAVING COUNT(*) > 1
            ORDER BY code
            """,
            [str(DATA_FILE)],
        ).fetchdf()
        duplicate_records = connection.execute(
            """
            WITH duplicate_codes AS (
                SELECT code
                FROM read_parquet(?)
                WHERE code IS NOT NULL
                GROUP BY code
                HAVING COUNT(*) > 1
            )
            SELECT duplicate_record.code, to_json(duplicate_record) AS row_json
            FROM read_parquet(?) AS duplicate_record
            INNER JOIN duplicate_codes USING (code)
            ORDER BY duplicate_record.code
            """,
            [str(DATA_FILE), str(DATA_FILE)],
        ).fetchall()

    summary.to_csv(OUTPUT_DIR / "quality_summary.csv", index=False)
    duplicate_codes.to_csv(OUTPUT_DIR / "duplicate_codes.csv", index=False)

    records_by_code: dict[str, list[dict]] = defaultdict(list)
    for code, row_json in duplicate_records:
        records_by_code[code].append(json.loads(row_json))

    investigation_rows = []
    for code, records in records_by_code.items():
        differing_fields = [
            field
            for field in records[0]
            if any(record.get(field) != records[0].get(field) for record in records[1:])
        ]
        identity_conflict_fields = [
            field for field in DUPLICATE_IDENTITY_FIELDS if field in differing_fields
        ]
        modified_values = [
            record.get("last_modified_t")
            for record in records
            if record.get("last_modified_t") is not None
        ]
        unique_latest_modified = (
            bool(modified_values)
            and modified_values.count(max(modified_values)) == 1
        )
        investigation_rows.append(
            {
                "code": code,
                "occurrence_count": len(records),
                "exact_duplicate_records": not differing_fields,
                "differing_field_count": len(differing_fields),
                "differing_fields": ";".join(differing_fields),
                "identity_conflict_fields": ";".join(identity_conflict_fields),
                "record_summaries": serialize_record_summaries(records),
                "unique_latest_last_modified": unique_latest_modified,
            }
        )
    duplicate_investigation = pd.DataFrame(investigation_rows)
    duplicate_investigation.to_csv(
        OUTPUT_DIR / "duplicate_code_investigation.csv",
        index=False,
    )

    values = summary.iloc[0]
    identity_conflict_groups = sum(
        bool(row["identity_conflict_fields"]) for row in investigation_rows
    )
    print("Quality checks completed.")
    print(f"Total rows: {values['total_rows']:,}")
    print(f"Null code rows: {values['null_code_rows']:,}")
    print(f"Distinct non-null codes: {values['distinct_non_null_codes']:,}")
    print(f"Duplicate code groups: {values['duplicate_code_groups']:,}")
    print(f"Duplicate rows: {values['duplicate_rows']:,}")
    print(
        "Duplicate groups with identity-field conflicts: "
        f"{identity_conflict_groups:,}"
    )
    print(f"Outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
