"""Build and validate the project DuckDB database from pinned local inputs."""

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARQUET_FILE = PROJECT_ROOT / "data" / "raw" / "food.parquet"
TAXONOMY_FILE = (
    PROJECT_ROOT / "data" / "reference" / "off_categories_taxonomy_2026-10-25.json"
)
DATABASE_FILE = PROJECT_ROOT / "data" / "processed" / "global_product_landscape.duckdb"
VALIDATION_FILE = PROJECT_ROOT / "outputs" / "quality" / "database_build_validation.csv"
EXPECTED_PARQUET_SHA256 = (
    "DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A"
)
EXPECTED_TAXONOMY_SHA256 = (
    "EB03AEFABAE4C6269B5FBC3E89160F8DA84CA3300A53787E27EAB5FE2D1020D5"
)
EXPECTED_PARQUET_SIZE = 7_975_461_945
EXPECTED_ROWS = 4_828_207
EXPECTED_SOURCE_COLUMNS = 111
TAXONOMY_VERSION = "2026-10-25"

BUILD_SQL = PROJECT_ROOT / "sql" / "01_build_relational_database.sql"
VALIDATE_SQL = PROJECT_ROOT / "sql" / "02_validate_relational_database.sql"
INPUTS = (
    PARQUET_FILE,
    TAXONOMY_FILE,
    PROJECT_ROOT / "data" / "reference" / "iso_3166_alpha2.csv",
    PROJECT_ROOT / "data" / "reference" / "category_reporting_group_framework.csv",
    PROJECT_ROOT / "data" / "mappings" / "country_tag_mapping.csv",
    PROJECT_ROOT / "data" / "mappings" / "category_tag_manual_dispositions.csv",
    PROJECT_ROOT / "data" / "mappings" / "category_tag_reporting_group_manual_decisions.csv",
    PROJECT_ROOT / "data" / "mappings" / "category_reporting_group_anchor_candidates.csv",
    PROJECT_ROOT / "data" / "mappings" / "brand_name_manual_decisions.csv",
    PROJECT_ROOT / "outputs" / "profiling" / "category_reporting_group_candidate_crosswalk.csv",
    PROJECT_ROOT / "outputs" / "profiling" / "normalized_country_profile.csv",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def sha256_files(paths: tuple[Path, ...]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(PROJECT_ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest().upper()


def load_taxonomy_nodes() -> pd.DataFrame:
    taxonomy: dict[str, dict[str, Any]] = json.loads(
        TAXONOMY_FILE.read_text(encoding="utf-8")
    )
    nodes: list[dict[str, Any]] = []
    for category_tag, details in taxonomy.items():
        name = details.get("name", {})
        parents = details.get("parents", [])
        if not isinstance(parents, list):
            raise ValueError(f"Taxonomy parents are not a list for {category_tag}")
        nodes.append(
            {
                "category_tag": category_tag,
                "name_en": name.get("en") if isinstance(name, dict) else None,
                "direct_parent_tags": parents,
            }
        )
    return pd.DataFrame(
        nodes,
        columns=("category_tag", "name_en", "direct_parent_tags"),
    )


def read_sql(path: Path, replacements: dict[str, str]) -> str:
    sql = path.read_text(encoding="utf-8")
    for placeholder, value in replacements.items():
        sql = sql.replace(placeholder, value)
    unresolved = [
        word for word in sql.split() if word.startswith("{{") and word.endswith("}}")
    ]
    if unresolved:
        raise ValueError(f"Unresolved SQL placeholders in {path}: {unresolved}")
    return sql


def validate_inputs() -> None:
    print("Checking required local inputs and pinned file identities...", flush=True)
    missing = [str(path) for path in INPUTS if not path.is_file()]
    if missing:
        raise FileNotFoundError("Required inputs are missing:\n" + "\n".join(missing))
    if not BUILD_SQL.is_file() or not VALIDATE_SQL.is_file():
        raise FileNotFoundError("Required SQL build or validation file is missing.")
    if PARQUET_FILE.stat().st_size != EXPECTED_PARQUET_SIZE:
        raise ValueError(
            f"Parquet size mismatch: expected {EXPECTED_PARQUET_SIZE}, "
            f"found {PARQUET_FILE.stat().st_size}."
        )
    parquet_hash = sha256_file(PARQUET_FILE)
    if parquet_hash != EXPECTED_PARQUET_SHA256:
        raise ValueError(
            f"Parquet SHA-256 mismatch: expected {EXPECTED_PARQUET_SHA256}, "
            f"found {parquet_hash}."
        )
    taxonomy_hash = sha256_file(TAXONOMY_FILE)
    if taxonomy_hash != EXPECTED_TAXONOMY_SHA256:
        raise ValueError(
            f"Taxonomy SHA-256 mismatch: expected {EXPECTED_TAXONOMY_SHA256}, "
            f"found {taxonomy_hash}."
        )
    if sha256_file(TAXONOMY_FILE) != EXPECTED_TAXONOMY_SHA256:
        raise ValueError("Pinned taxonomy changed while validating build inputs.")


def build_database(output_file: Path) -> list[tuple[str, str, str]]:
    country_mapping_version = sha256_files(
        (PROJECT_ROOT / "data" / "mappings" / "country_tag_mapping.csv",)
    )
    category_mapping_version = sha256_files(
        (
            PROJECT_ROOT
            / "data"
            / "mappings"
            / "category_tag_manual_dispositions.csv",
            PROJECT_ROOT
            / "data"
            / "mappings"
            / "category_tag_reporting_group_manual_decisions.csv",
            PROJECT_ROOT
            / "data"
            / "mappings"
            / "category_reporting_group_anchor_candidates.csv",
            PROJECT_ROOT
            / "data"
            / "reference"
            / "category_reporting_group_framework.csv",
            PROJECT_ROOT
            / "outputs"
            / "profiling"
            / "category_reporting_group_candidate_crosswalk.csv",
        )
    )
    brand_mapping_version = sha256_files(
        (PROJECT_ROOT / "data" / "mappings" / "brand_name_manual_decisions.csv",)
    )
    replacements = {
        "{{SNAPSHOT_ID}}": EXPECTED_PARQUET_SHA256,
        "{{COUNTRY_MAPPING_VERSION}}": country_mapping_version,
        "{{CATEGORY_MAPPING_VERSION}}": category_mapping_version,
        "{{BRAND_MAPPING_VERSION}}": brand_mapping_version,
        "{{TAXONOMY_VERSION}}": TAXONOMY_VERSION,
    }

    connection = duckdb.connect(str(output_file))
    try:
        connection.register("taxonomy_nodes_input", load_taxonomy_nodes())
        connection.execute(read_sql(BUILD_SQL, replacements))
        validation_rows = connection.execute(
            read_sql(VALIDATE_SQL, {})
        ).fetchall()
    finally:
        connection.close()

    failures = [
        (name, actual, expected)
        for name, actual, expected in validation_rows
        if actual != expected
    ]
    if failures:
        detail = "\n".join(
            f"{name}: expected {expected}, found {actual}"
            for name, actual, expected in failures
        )
        raise ValueError("Database validation failed:\n" + detail)
    return validation_rows


def write_validation_output(
    validation_rows: list[tuple[str, str, str]],
    database_file: Path,
) -> None:
    validation_file = VALIDATION_FILE
    validation_file.parent.mkdir(parents=True, exist_ok=True)
    report = pd.DataFrame(
        validation_rows,
        columns=("check_name", "actual_value", "expected_value"),
    )
    report["status"] = "passed"
    try:
        database_path = database_file.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        database_path = str(database_file)
    report["database_file"] = database_path
    report.to_csv(validation_file, index=False, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DATABASE_FILE,
        help="New DuckDB output path (existing files are never overwritten).",
    )
    args = parser.parse_args()

    validate_inputs()
    output_file = args.output.resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    if output_file.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing database: {output_file}"
        )

    os.chdir(PROJECT_ROOT)
    with tempfile.TemporaryDirectory(
        prefix=".global_product_landscape_build_",
        dir=output_file.parent,
    ) as temporary_directory:
        temporary_database = Path(temporary_directory) / output_file.name
        print("Loading source records and relational tables into DuckDB...", flush=True)
        validation_rows = build_database(temporary_database)
        print("All database validation checks passed; finalizing database...", flush=True)
        temporary_database.replace(output_file)

    write_validation_output(validation_rows, output_file)
    print(f"Database created: {output_file}")
    print(f"Database size: {output_file.stat().st_size} bytes")
    print(f"Validation checks passed: {len(validation_rows)}")
    print(f"Validation report: {VALIDATION_FILE}")


if __name__ == "__main__":
    main()
