import csv
import re
from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "food.parquet"
MAPPING_FILE = PROJECT_ROOT / "data" / "mappings" / "country_tag_mapping.csv"
ISO_REFERENCE_FILE = (
    PROJECT_ROOT / "data" / "reference" / "iso_3166_alpha2.csv"
)
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "profiling"
ISO_ALPHA2_PATTERN = re.compile(r"^[A-Z]{2}$")
MIN_COUNTRY_RECORDS = 1_000


def validate_mapping_file() -> None:
    if not ISO_REFERENCE_FILE.is_file():
        raise FileNotFoundError(
            f"ISO 3166-1 reference file not found: {ISO_REFERENCE_FILE}"
        )

    with ISO_REFERENCE_FILE.open(encoding="utf-8-sig", newline="") as reference_file:
        reference_rows = list(csv.DictReader(reference_file))
    iso_codes = [row["iso_alpha2"] for row in reference_rows]
    if not iso_codes or len(iso_codes) != len(set(iso_codes)):
        raise ValueError(
            f"ISO reference must contain unique alpha-2 codes: "
            f"{ISO_REFERENCE_FILE}"
        )
    valid_iso_codes = set(iso_codes)

    with MAPPING_FILE.open(encoding="utf-8-sig", newline="") as mapping_file:
        mapping_rows = list(csv.DictReader(mapping_file))

    if not mapping_rows:
        raise ValueError(f"Country mapping file is empty: {MAPPING_FILE}")

    tags = [row["source_country_tag"] for row in mapping_rows]
    if len(tags) != len(set(tags)):
        raise ValueError("Country mapping file contains duplicate source tags.")

    allowed_statuses = {"approved", "excluded", "review_required"}
    for row in mapping_rows:
        if row["mapping_status"] not in allowed_statuses:
            raise ValueError(
                f"Invalid mapping status for {row['source_country_tag']}: "
                f"{row['mapping_status']}"
            )

    names_by_code: dict[str, set[str]] = {}
    for row in mapping_rows:
        code = row["iso_alpha2"]
        if row["mapping_status"] == "approved":
            if not ISO_ALPHA2_PATTERN.fullmatch(code):
                raise ValueError(
                    f"Approved mapping has invalid ISO alpha-2 code for "
                    f"{row['source_country_tag']}: {code}"
                )
            if code not in valid_iso_codes:
                raise ValueError(
                    f"Approved mapping code is absent from the ISO 3166-1 "
                    f"reference for {row['source_country_tag']}: {code}"
                )
            names_by_code.setdefault(code, set()).add(row["country_name"])
            if not row["country_name"]:
                raise ValueError(
                    f"Approved mapping has no country name for "
                    f"{row['source_country_tag']}"
                )
        elif code:
            raise ValueError(
                f"Non-approved mapping must not have an ISO code: "
                f"{row['source_country_tag']}"
            )

    inconsistent_names = {
        code: sorted(names)
        for code, names in names_by_code.items()
        if len(names) > 1
    }
    if inconsistent_names:
        raise ValueError(
            "Approved tags for an ISO code must use one canonical country name: "
            f"{inconsistent_names}"
        )


def main() -> None:
    if not DATA_FILE.is_file():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")
    if not MAPPING_FILE.is_file():
        raise FileNotFoundError(f"Country mapping file not found: {MAPPING_FILE}")

    validate_mapping_file()
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

        connection.execute(
            """
            CREATE TEMP TABLE country_records AS
            SELECT
                ROW_NUMBER() OVER () AS record_id,
                countries_tags
            FROM read_parquet(?)
            """,
            [str(DATA_FILE)],
        )
        connection.execute(
            """
            CREATE TEMP TABLE source_country_tags AS
            SELECT record_id, country_tag AS source_country_tag
            FROM country_records
            CROSS JOIN UNNEST(
                list_filter(
                    list_distinct(countries_tags),
                    lambda country_tag:
                        country_tag IS NOT NULL
                        AND trim(country_tag) <> ''
                )
            ) AS country(country_tag)
            """
        )
        connection.execute(
            """
            CREATE TEMP TABLE country_mapping AS
            SELECT *
            FROM read_csv(?, all_varchar = true, header = true)
            """,
            [str(MAPPING_FILE)],
        )

        mapping_mismatches = connection.execute(
            """
            WITH observed AS (
                SELECT DISTINCT source_country_tag
                FROM source_country_tags
            )
            SELECT
                COALESCE(observed.source_country_tag, mapping.source_country_tag)
                    AS source_country_tag
            FROM observed
            FULL OUTER JOIN country_mapping AS mapping
                USING (source_country_tag)
            WHERE observed.source_country_tag IS NULL
                OR mapping.source_country_tag IS NULL
            LIMIT 10
            """
        ).fetchdf()
        if not mapping_mismatches.empty:
            raise ValueError(
                "Country mapping does not match the current dataset's raw tag "
                "set. Rebuild or review "
                "data/mappings/country_tag_mapping.csv. "
                f"Examples: {mapping_mismatches.to_dict(orient='records')}"
            )

        connection.execute(
            """
            CREATE TEMP TABLE country_assignments AS
            SELECT
                source.record_id,
                mapping.iso_alpha2,
                MIN(mapping.country_name) AS country_name
            FROM source_country_tags AS source
            JOIN country_mapping AS mapping
                USING (source_country_tag)
            WHERE mapping.mapping_status = 'approved'
            GROUP BY source.record_id, mapping.iso_alpha2
            """
        )

        country_profile = connection.execute(
            """
            WITH profile AS (
                SELECT iso_alpha2, country_name, COUNT(*) AS record_count
                FROM country_assignments
                GROUP BY iso_alpha2, country_name
            ),
            coverage AS (
                SELECT COUNT(DISTINCT record_id) AS mapped_records
                FROM country_assignments
            ),
            all_records AS (
                SELECT COUNT(*) AS total_records
                FROM country_records
            )
            SELECT
                ROW_NUMBER() OVER (
                    ORDER BY profile.record_count DESC, profile.country_name
                ) AS rank,
                profile.iso_alpha2,
                profile.country_name,
                profile.record_count,
                ROUND(
                    100.0 * profile.record_count / all_records.total_records,
                    4
                ) AS pct_of_all_records,
                ROUND(
                    100.0 * profile.record_count / coverage.mapped_records,
                    4
                ) AS pct_of_records_with_approved_country
            FROM profile
            CROSS JOIN coverage
            CROSS JOIN all_records
            ORDER BY rank
            """
        ).fetchdf()

        coverage_summary = connection.execute(
            """
            WITH mapping_counts AS (
                SELECT
                    COUNT(*) AS total_source_tags,
                    COUNT(*) FILTER (
                        WHERE mapping_status = 'approved'
                    ) AS approved_source_tags,
                    COUNT(*) FILTER (
                        WHERE mapping_status = 'excluded'
                    ) AS excluded_source_tags,
                    COUNT(*) FILTER (
                        WHERE mapping_status = 'review_required'
                    ) AS review_required_source_tags
                FROM country_mapping
            ),
            assignment_counts AS (
                SELECT
                    COUNT(*) AS total_tag_record_assignments,
                    COUNT(*) FILTER (
                        WHERE mapping.mapping_status = 'approved'
                    ) AS approved_tag_record_assignments,
                    COUNT(*) FILTER (
                        WHERE mapping.mapping_status = 'excluded'
                    ) AS excluded_tag_record_assignments,
                    COUNT(*) FILTER (
                        WHERE mapping.mapping_status = 'review_required'
                    ) AS review_required_tag_record_assignments,
                    COUNT(DISTINCT source.record_id) FILTER (
                        WHERE mapping.mapping_status = 'approved'
                    ) AS records_with_approved_country,
                    COUNT(DISTINCT source.record_id) FILTER (
                        WHERE mapping.mapping_status = 'excluded'
                    ) AS records_with_excluded_tags,
                    COUNT(DISTINCT source.record_id) FILTER (
                        WHERE mapping.mapping_status = 'review_required'
                    ) AS records_with_review_required_tags
                FROM source_country_tags AS source
                JOIN country_mapping AS mapping
                    USING (source_country_tag)
            ),
            totals AS (
                SELECT COUNT(*) AS total_records
                FROM country_records
            ),
            assignment_totals AS (
                SELECT COUNT(*) AS approved_country_record_assignments
                FROM country_assignments
            )
            SELECT
                totals.total_records,
                assignment_counts.records_with_approved_country,
                totals.total_records
                    - assignment_counts.records_with_approved_country
                    AS records_without_approved_country,
                ROUND(
                    100.0 * assignment_counts.records_with_approved_country
                    / totals.total_records,
                    4
                ) AS pct_records_with_approved_country,
                assignment_counts.records_with_excluded_tags,
                assignment_counts.records_with_review_required_tags,
                mapping_counts.total_source_tags,
                mapping_counts.approved_source_tags,
                mapping_counts.excluded_source_tags,
                mapping_counts.review_required_source_tags,
                assignment_counts.total_tag_record_assignments,
                assignment_counts.approved_tag_record_assignments,
                assignment_counts.excluded_tag_record_assignments,
                assignment_counts.review_required_tag_record_assignments,
                assignment_totals.approved_country_record_assignments
            FROM totals
            CROSS JOIN mapping_counts
            CROSS JOIN assignment_counts
            CROSS JOIN assignment_totals
            """
        ).fetchdf()

    country_shortlist = country_profile[
        country_profile["record_count"] >= MIN_COUNTRY_RECORDS
    ].copy()
    coverage_summary["minimum_records_for_shortlist"] = MIN_COUNTRY_RECORDS
    coverage_summary["units_meeting_minimum_record_count"] = len(
        country_shortlist
    )

    country_profile.to_csv(
        OUTPUT_DIR / "normalized_country_profile.csv",
        index=False,
    )
    country_shortlist.to_csv(
        OUTPUT_DIR / "country_comparison_shortlist.csv",
        index=False,
    )
    coverage_summary.to_csv(
        OUTPUT_DIR / "normalized_country_coverage_summary.csv",
        index=False,
    )

    summary = coverage_summary.iloc[0]
    print("Normalized country profile completed.")
    print(f"Countries/territories: {len(country_profile):,}")
    print(
        "Records with an approved country mapping: "
        f"{summary['records_with_approved_country']:,}"
    )
    print(
        "Raw tag assignments requiring review: "
        f"{summary['review_required_tag_record_assignments']:,}"
    )
    print(
        f"Comparison shortlist (>= {MIN_COUNTRY_RECORDS:,} records): "
        f"{len(country_shortlist):,} ISO units"
    )
    print(f"Outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
