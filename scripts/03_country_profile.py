from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "food.parquet"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "profiling"

COUNTRY_PROFILE_CTES = """
WITH records AS (
    SELECT
        list_filter(
            list_distinct(countries_tags),
            lambda country_tag:
                country_tag IS NOT NULL
                AND trim(country_tag) <> ''
        ) AS country_tags
    FROM read_parquet(?)
),
country_counts AS (
    SELECT country_tag, COUNT(*) AS record_count
    FROM records
    CROSS JOIN UNNEST(country_tags) AS country(country_tag)
    GROUP BY country_tag
),
coverage AS (
    SELECT
        COUNT(*) AS total_records,
        COUNT(*) FILTER (
            WHERE country_tags IS NOT NULL
                AND len(country_tags) > 0
        ) AS records_with_country
    FROM records
)
"""


def main() -> None:
    if not DATA_FILE.is_file():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with duckdb.connect() as connection:
        columns = connection.execute(
            "DESCRIBE SELECT * FROM read_parquet(?)",
            [str(DATA_FILE)],
        ).fetchdf()
        if "countries_tags" not in columns["column_name"].values:
            raise ValueError(
                f"Required column 'countries_tags' is missing from {DATA_FILE}"
            )

        country_profile = connection.execute(
            COUNTRY_PROFILE_CTES
            + """
            SELECT
                ROW_NUMBER() OVER (
                    ORDER BY country_counts.record_count DESC,
                             country_counts.country_tag
                ) AS rank,
                country_counts.country_tag AS source_country_tag,
                country_counts.record_count AS records_with_tag,
                ROUND(
                    100.0 * country_counts.record_count
                    / coverage.total_records,
                    4
                ) AS pct_of_all_records,
                ROUND(
                    100.0 * country_counts.record_count
                    / coverage.records_with_country,
                    4
                ) AS pct_of_records_with_any_tag
            FROM country_counts
            CROSS JOIN coverage
            ORDER BY rank
            """,
            [str(DATA_FILE)],
        ).fetchdf()
        coverage_summary = connection.execute(
            COUNTRY_PROFILE_CTES
            + """
            SELECT
                coverage.total_records,
                coverage.records_with_country AS records_with_any_country_tag,
                coverage.total_records - coverage.records_with_country
                    AS records_without_country_tags,
                (SELECT COUNT(*) FROM country_counts)
                    AS distinct_source_country_tags,
                COALESCE(
                    (SELECT SUM(record_count) FROM country_counts),
                    0
                ) AS source_tag_record_assignments,
                ROUND(
                    100.0 * coverage.records_with_country
                    / coverage.total_records,
                    4
                ) AS pct_records_with_any_country_tag
            FROM coverage
            """,
            [str(DATA_FILE)],
        ).fetchdf()

    country_profile.to_csv(OUTPUT_DIR / "country_profile.csv", index=False)
    coverage_summary.to_csv(
        OUTPUT_DIR / "country_coverage_summary.csv",
        index=False,
    )

    print("Country profile completed.")
    print(
        "Distinct source country tags: "
        f"{coverage_summary.loc[0, 'distinct_source_country_tags']:,}"
    )
    print(
        "Records without country tags: "
        f"{coverage_summary.loc[0, 'records_without_country_tags']:,}"
    )
    print(f"Output saved to: {OUTPUT_DIR / 'country_profile.csv'}")
    print(
        "Coverage summary saved to: "
        f"{OUTPUT_DIR / 'country_coverage_summary.csv'}"
    )


if __name__ == "__main__":
    main()
