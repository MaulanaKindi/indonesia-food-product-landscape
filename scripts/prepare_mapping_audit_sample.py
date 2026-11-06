"""Prepare a deterministic, unlabelled sample for manual category review."""

import argparse
import csv
from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "global_product_landscape_five_country.duckdb"
)
OUTPUT_FILE = PROJECT_ROOT / "data" / "private" / "category_mapping_audit_sample.csv"
SAMPLE_SIZE = 150
SAMPLE_SEED = "indonesia-category-audit-v1"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DATABASE_FILE)
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE)
    args = parser.parse_args()

    database_file = args.database.resolve()
    output_file = args.output.resolve()
    if not database_file.is_file():
        raise FileNotFoundError(f"Selected-country database is missing: {database_file}")
    if output_file.exists():
        raise FileExistsError(
            f"Refusing to overwrite an existing manual-label file: {output_file}"
        )

    with duckdb.connect(str(database_file), read_only=True) as connection:
        rows = connection.execute(
            """
            SELECT
                record.source_record_id,
                record.code,
                to_json(record.product_name) AS product_name_json,
                record.categories,
                to_json(record.categories_tags) AS categories_tags_json
            FROM record_country AS country
            JOIN source_product_record AS record USING (source_record_id)
            WHERE country.iso_alpha2 = 'ID'
              AND EXISTS (
                  SELECT 1
                  FROM record_category_tag AS category
                  WHERE category.source_record_id = record.source_record_id
              )
            QUALIFY row_number() OVER (
                ORDER BY md5(
                    CAST(record.source_record_id AS VARCHAR) || ?
                )
            ) <= ?
            ORDER BY md5(CAST(record.source_record_id AS VARCHAR) || ?)
            """,
            [SAMPLE_SEED, SAMPLE_SIZE, SAMPLE_SEED],
        ).fetchall()

    if len(rows) != SAMPLE_SIZE:
        raise ValueError(
            f"Expected {SAMPLE_SIZE} Indonesian category-tagged records; found {len(rows)}."
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    fields = (
        "audit_id",
        "source_record_id",
        "code",
        "product_name_json",
        "categories",
        "categories_tags_json",
        "manual_reporting_group_ids",
        "confidence",
        "notes",
    )
    with output_file.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for audit_id, row in enumerate(rows, start=1):
            source_record_id, code, product_name, categories, category_tags = row
            writer.writerow(
                {
                    "audit_id": audit_id,
                    "source_record_id": source_record_id,
                    "code": code,
                    "product_name_json": product_name,
                    "categories": categories,
                    "categories_tags_json": category_tags,
                    "manual_reporting_group_ids": "",
                    "confidence": "",
                    "notes": "",
                }
            )
    print(f"Prepared {len(rows)} records for local manual review: {output_file}")
    print("Candidate mappings are intentionally omitted from the sample.")


if __name__ == "__main__":
    main()
