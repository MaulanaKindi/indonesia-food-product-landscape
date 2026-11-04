from pathlib import Path

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "food.parquet"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "profiling"
MANUAL_BRAND_MAPPING_FILE = (
    PROJECT_ROOT / "data" / "mappings" / "brand_name_manual_decisions.csv"
)
TAG_FIELDS = {
    "brands_tags": "brand_tag",
    "categories_tags": "category_tag",
    "food_groups_tags": "food_group_tag",
}
NAME_FIELDS = {
    "brands": "brand_name",
    "categories": "category_name",
}


def create_source_tables(connection: duckdb.DuckDBPyConnection) -> None:
    columns = connection.execute(
        "DESCRIBE SELECT * FROM read_parquet(?)",
        [str(DATA_FILE)],
    ).fetchdf()
    available_columns = set(columns["column_name"])
    required_columns = set(TAG_FIELDS) | set(NAME_FIELDS)
    missing_columns = required_columns - available_columns
    if missing_columns:
        raise ValueError(
            "Required category/brand columns are missing from the dataset: "
            f"{sorted(missing_columns)}"
        )

    for source_column, entity in TAG_FIELDS.items():
        print(f"Profiling {source_column}...", flush=True)
        connection.execute(
            f"""
            CREATE TEMP TABLE {entity}_profile AS
            SELECT source_value, COUNT(*) AS record_count
            FROM read_parquet(?) AS source
            CROSS JOIN UNNEST(
                list_filter(
                    list_distinct(source.{source_column}),
                    lambda value: value IS NOT NULL AND trim(value) <> ''
                )
            ) AS values(source_value)
            GROUP BY source_value
            """,
            [str(DATA_FILE)],
        )

    for source_column, entity in NAME_FIELDS.items():
        print(f"Profiling {source_column}...", flush=True)
        connection.execute(
            f"""
            CREATE TEMP TABLE {entity}_profile AS
            SELECT {source_column} AS source_value, COUNT(*) AS record_count
            FROM read_parquet(?)
            WHERE {source_column} IS NOT NULL
                AND trim({source_column}) <> ''
            GROUP BY {source_column}
            """,
            [str(DATA_FILE)],
        )

    print("Calculating source-field coverage...", flush=True)
    connection.execute(
        """
        CREATE TEMP TABLE source_coverage AS
        SELECT
            COUNT(*) AS total_records,
            COUNT(*) FILTER (
                WHERE len(list_filter(
                    list_distinct(brands_tags),
                    lambda value: value IS NOT NULL AND trim(value) <> ''
                )) > 0
            ) AS records_with_brand_tag,
            COUNT(*) FILTER (
                WHERE len(list_filter(
                    list_distinct(brands_tags),
                    lambda value: value IS NOT NULL AND trim(value) <> ''
                )) > 1
            ) AS records_with_multiple_brand_tags,
            COUNT(*) FILTER (
                WHERE brands IS NOT NULL AND trim(brands) <> ''
            ) AS records_with_brand_name,
            COUNT(*) FILTER (
                WHERE len(list_filter(
                    list_distinct(categories_tags),
                    lambda value: value IS NOT NULL AND trim(value) <> ''
                )) > 0
            ) AS records_with_category_tag,
            COUNT(*) FILTER (
                WHERE len(list_filter(
                    list_distinct(categories_tags),
                    lambda value: value IS NOT NULL AND trim(value) <> ''
                )) > 1
            ) AS records_with_multiple_category_tags,
            COUNT(*) FILTER (
                WHERE len(list_filter(
                    list_distinct(food_groups_tags),
                    lambda value: value IS NOT NULL AND trim(value) <> ''
                )) > 0
            ) AS records_with_food_group_tag,
            COUNT(*) FILTER (
                WHERE len(list_filter(
                    list_distinct(food_groups_tags),
                    lambda value: value IS NOT NULL AND trim(value) <> ''
                )) > 1
            ) AS records_with_multiple_food_group_tags,
            COUNT(*) FILTER (
                WHERE categories IS NOT NULL AND trim(categories) <> ''
            ) AS records_with_category_name
        FROM read_parquet(?)
        """,
        [str(DATA_FILE)],
    )


def build_coverage_summary(
    connection: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    source_coverage = connection.execute(
        "SELECT * FROM source_coverage"
    ).fetchdf().iloc[0]
    total_records = int(source_coverage["total_records"])
    rows = []

    for entity, source_column, coverage_key, multi_key in (
        (
            "brand_tag",
            "brands_tags",
            "records_with_brand_tag",
            "records_with_multiple_brand_tags",
        ),
        ("brand_name", "brands", "records_with_brand_name", None),
        (
            "category_tag",
            "categories_tags",
            "records_with_category_tag",
            "records_with_multiple_category_tags",
        ),
        (
            "food_group_tag",
            "food_groups_tags",
            "records_with_food_group_tag",
            "records_with_multiple_food_group_tags",
        ),
        ("category_name", "categories", "records_with_category_name", None),
    ):
        source_representation = "tag_array" if entity.endswith("_tag") else "text"
        values = connection.execute(
            f"""
            SELECT
                COUNT(*) AS distinct_values,
                SUM(record_count) AS record_value_assignments
            FROM {entity}_profile
            """
        ).fetchone()
        records_with_value = int(source_coverage[coverage_key])
        distinct_values, total_assignments = values
        rows.append(
            {
                "source_column": source_column,
                "representation": source_representation,
                "total_records": total_records,
                "records_with_value": records_with_value,
                "records_without_value": total_records - records_with_value,
                "pct_records_with_value": round(
                    100.0 * records_with_value / total_records, 4
                )
                if total_records
                else 0,
                "distinct_source_values": distinct_values,
                "record_value_assignments": total_assignments,
                "records_with_multiple_values": (
                    int(source_coverage[multi_key]) if multi_key else 0
                ),
            }
        )

    return pd.DataFrame(rows)


def build_value_profile(
    connection: duckdb.DuckDBPyConnection,
    entity: str,
) -> pd.DataFrame:
    return connection.execute(
        f"""
        SELECT
            ROW_NUMBER() OVER (
                ORDER BY record_count DESC, source_value
            ) AS rank,
                source_value,
                record_count AS records_with_value,
                ROUND(
                    100.0 * record_count / (SELECT total_records FROM source_coverage),
                    4
                ) AS pct_of_all_records
        FROM {entity}_profile
        ORDER BY rank
        """
    ).fetchdf()


def build_tag_variant_candidates(
    connection: duckdb.DuckDBPyConnection,
    entity: str,
) -> pd.DataFrame:
    return connection.execute(
        f"""
        WITH grouped AS (
            SELECT
                lower(regexp_extract(source_value, '^[^:]+:(.*)$', 1))
                    AS normalized_suffix,
                COUNT(*) AS distinct_source_tags,
                COUNT(DISTINCT regexp_extract(source_value, '^([^:]+):', 1))
                    AS distinct_language_prefixes,
                SUM(record_count) AS combined_tag_record_count,
                string_agg(
                    source_value,
                    ' | ' ORDER BY source_value
                ) AS source_tags
            FROM {entity}_profile
            WHERE regexp_matches(source_value, '^[a-z]{{2,3}}:')
            GROUP BY normalized_suffix
            HAVING COUNT(*) > 1
        )
        SELECT
            normalized_suffix,
            distinct_source_tags,
            distinct_language_prefixes,
            combined_tag_record_count,
            source_tags,
            'Identical tag suffix across language prefixes; review, not an automatic alias'
                AS candidate_signal
        FROM grouped
        ORDER BY combined_tag_record_count DESC, normalized_suffix
        """
    ).fetchdf()


def build_name_normalization_candidates(
    connection: duckdb.DuckDBPyConnection,
    entity: str,
) -> pd.DataFrame:
    return connection.execute(
        f"""
        WITH grouped AS (
            SELECT
                lower(regexp_replace(trim(source_value), '\\s+', ' ', 'g'))
                    AS normalized_name,
                COUNT(*) AS distinct_source_names,
                SUM(record_count) AS combined_name_record_count,
                string_agg(
                    source_value,
                    ' | ' ORDER BY source_value
                ) AS source_names
            FROM {entity}_profile
            GROUP BY normalized_name
            HAVING COUNT(*) > 1
        )
        SELECT
            normalized_name,
            distinct_source_names,
            combined_name_record_count,
            source_names,
            'Case/whitespace-only normalization collision; review, not an automatic merge'
                AS candidate_signal
        FROM grouped
        ORDER BY combined_name_record_count DESC, normalized_name
        """
    ).fetchdf()


def build_manual_brand_mapping_validation(
    brand_name_profile: pd.DataFrame,
) -> pd.DataFrame:
    if not MANUAL_BRAND_MAPPING_FILE.is_file():
        raise FileNotFoundError(
            f"Required manual brand mapping not found: {MANUAL_BRAND_MAPPING_FILE}"
        )
    mapping = pd.read_csv(
        MANUAL_BRAND_MAPPING_FILE,
        dtype=str,
        keep_default_na=False,
    )
    required_columns = {
        "source_brand_name",
        "canonical_brand_name",
        "review_status",
        "decision_basis",
        "reviewed_on",
    }
    missing_columns = required_columns - set(mapping.columns)
    if missing_columns:
        raise ValueError(
            "Manual brand mapping is missing columns: "
            f"{sorted(missing_columns)}"
        )
    if mapping["source_brand_name"].duplicated().any():
        raise ValueError("Manual brand mapping contains duplicate source values.")
    if not mapping["review_status"].eq("approved").all():
        raise ValueError("Manual brand mappings must be owner-approved.")
    if not mapping["decision_basis"].str.strip().ne("").all():
        raise ValueError("Manual brand mappings must include a decision basis.")
    if mapping[["source_brand_name", "canonical_brand_name"]].eq("").any().any():
        raise ValueError(
            "Manual brand mappings must include source and canonical values."
        )

    source_counts = brand_name_profile.set_index("source_value")[
        "records_with_value"
    ].to_dict()
    missing_source_values = sorted(
        set(mapping["source_brand_name"]) - set(source_counts)
    )
    if missing_source_values:
        raise ValueError(
            "Manual brand mappings reference source values absent from the exact "
            f"brand profile: {missing_source_values}"
        )

    def normalized_name(value: str) -> str:
        return " ".join(value.split()).casefold()

    inconsistent = mapping.loc[
        mapping.apply(
            lambda row: normalized_name(row["source_brand_name"])
            != normalized_name(row["canonical_brand_name"]),
            axis=1,
        ),
        "source_brand_name",
    ].tolist()
    if inconsistent:
        raise ValueError(
            "Manual brand mappings must be limited to case/whitespace changes: "
            f"{inconsistent}"
        )

    validation = mapping[
        [
            "source_brand_name",
            "canonical_brand_name",
            "review_status",
            "decision_basis",
            "reviewed_on",
        ]
    ].copy()
    validation["records_with_source_name"] = validation[
        "source_brand_name"
    ].map(source_counts)
    return validation.sort_values(
        ["canonical_brand_name", "source_brand_name"],
        kind="stable",
    ).reset_index(drop=True)


def main() -> None:
    if not DATA_FILE.is_file():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")
    if not MANUAL_BRAND_MAPPING_FILE.is_file():
        raise FileNotFoundError(
            f"Required manual brand mapping not found: {MANUAL_BRAND_MAPPING_FILE}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with duckdb.connect() as connection:
        create_source_tables(connection)
        print("Building coverage summary...", flush=True)
        coverage_summary = build_coverage_summary(connection)
        profiles = {}
        for entity, filename in (
            ("brand_tag", "brand_tag_profile.csv"),
            ("brand_name", "brand_name_profile.csv"),
            ("category_tag", "category_tag_profile.csv"),
            ("food_group_tag", "food_group_tag_profile.csv"),
            ("category_name", "category_name_profile.csv"),
        ):
            print(f"Building {filename}...", flush=True)
            profiles[filename] = build_value_profile(connection, entity)
        for entity, filename in (
            ("brand_tag", "brand_tag_variant_candidates.csv"),
            ("category_tag", "category_tag_variant_candidates.csv"),
        ):
            print(f"Building {filename}...", flush=True)
            profiles[filename] = build_tag_variant_candidates(connection, entity)
        for entity, filename in (
            ("brand_name", "brand_name_normalization_candidates.csv"),
            ("category_name", "category_name_normalization_candidates.csv"),
        ):
            print(f"Building {filename}...", flush=True)
            profiles[filename] = build_name_normalization_candidates(
                connection, entity
            )

    profiles["brand_name_manual_mapping_validation.csv"] = (
        build_manual_brand_mapping_validation(profiles["brand_name_profile.csv"])
    )
    coverage_summary.to_csv(
        OUTPUT_DIR / "category_brand_coverage_summary.csv",
        index=False,
    )
    for filename, profile in profiles.items():
        profile.to_csv(OUTPUT_DIR / filename, index=False)

    print("Category and brand profiling completed.")
    for row in coverage_summary.itertuples(index=False):
        print(
            f"{row.source_column}: {row.records_with_value:,} records with value, "
            f"{row.distinct_source_values:,} distinct source values"
        )
    print(f"Outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
