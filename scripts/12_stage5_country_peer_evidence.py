"""Build a compact coverage evidence table for Stage 5 country-peer review."""

import argparse
import csv
from pathlib import Path

from support_duckdb_runtime import connect_duckdb
from support_pinned_inputs import SNAPSHOT_SHA256
from support_stage5_coverage import (
    build_country_code_overlap,
    build_food_groups_crosscheck,
    build_source_tag_coverage,
)
from support_stage5_readiness import (
    build_contributor_diagnostics,
    build_readiness_scorecard,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_FILE = (
    PROJECT_ROOT / "data" / "processed" / "global_product_landscape_five_country.duckdb"
)
SHORTLIST_FILE = (
    PROJECT_ROOT / "outputs" / "profiling" / "country_comparison_shortlist.csv"
)
CATEGORY_OVERLAP_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "profiling"
    / "category_reporting_group_candidate_country_overlap.csv"
)
NONFOOD_COUNTRY_FILE = (
    PROJECT_ROOT / "outputs" / "profiling" / "nonfood_scope_country_impact.csv"
)
VALIDATION_FILE = (
    PROJECT_ROOT / "outputs" / "quality" / "database_build_validation_five_country.csv"
)
OUTPUT_FILE = (
    PROJECT_ROOT / "outputs" / "profiling" / "stage5_country_peer_evidence.csv"
)
READINESS_OUTPUT = (
    PROJECT_ROOT / "outputs" / "profiling" / "data_readiness_scorecard.csv"
)
CONTRIBUTOR_OUTPUT = (
    PROJECT_ROOT / "outputs" / "profiling" / "contributor_year_diagnostics.csv"
)
YEARLY_OUTPUT = PROJECT_ROOT / "outputs" / "profiling" / "record_creation_year.csv"
SOURCE_TAG_OUTPUT = PROJECT_ROOT / "outputs" / "profiling" / "source_tag_coverage.csv"
OVERLAP_OUTPUT = PROJECT_ROOT / "outputs" / "profiling" / "country_code_overlap.csv"
FOOD_GROUP_CROSSWALK_FILE = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "food_group_reporting_group_diagnostic_crosswalk.csv"
)
FOOD_GROUP_OUTPUT = (
    PROJECT_ROOT / "outputs" / "profiling" / "food_groups_crosscheck.csv"
)
EXPECTED_SNAPSHOT_SHA256 = SNAPSHOT_SHA256


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def validate_inputs(database_file: Path, validation_file: Path) -> None:
    required = (
        database_file,
        SHORTLIST_FILE,
        CATEGORY_OVERLAP_FILE,
        NONFOOD_COUNTRY_FILE,
        validation_file,
        FOOD_GROUP_CROSSWALK_FILE,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Required Stage 5 evidence input missing:\n" + "\n".join(missing)
        )

    checks = read_csv(validation_file)
    if not checks or any(
        row["status"] != "passed" or row["actual_value"] != row["expected_value"]
        for row in checks
    ):
        raise ValueError(
            f"Database build validation is not fully passed: {validation_file}"
        )

    shortlist = read_csv(SHORTLIST_FILE)
    if len(shortlist) != 107:
        raise ValueError(
            "Expected the existing 107-unit, 1,000-row screening shortlist; "
            f"found {len(shortlist)} units."
        )
    if len({row["iso_alpha2"] for row in shortlist}) != len(shortlist):
        raise ValueError("Country shortlist contains duplicate ISO units.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DATABASE_FILE)
    parser.add_argument("--build-validation", type=Path, default=VALIDATION_FILE)
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE)
    parser.add_argument("--readiness-output", type=Path, default=READINESS_OUTPUT)
    parser.add_argument("--contributor-output", type=Path, default=CONTRIBUTOR_OUTPUT)
    parser.add_argument("--yearly-output", type=Path, default=YEARLY_OUTPUT)
    parser.add_argument("--source-tag-output", type=Path, default=SOURCE_TAG_OUTPUT)
    parser.add_argument("--overlap-output", type=Path, default=OVERLAP_OUTPUT)
    parser.add_argument("--food-groups-output", type=Path, default=FOOD_GROUP_OUTPUT)
    args = parser.parse_args()

    validate_inputs(args.database, args.build_validation)
    shortlist = read_csv(SHORTLIST_FILE)
    category_rows = read_csv(CATEGORY_OVERLAP_FILE)
    nonfood_rows = read_csv(NONFOOD_COUNTRY_FILE)
    category_by_iso = {row["iso_alpha2"]: row for row in category_rows}
    nonfood_by_iso = {row["iso_alpha2"]: row for row in nonfood_rows}

    connection = connect_duckdb(str(args.database), read_only=True)
    try:
        snapshot_row = connection.execute(
            "SELECT snapshot_id FROM data_snapshot"
        ).fetchone()
        assert snapshot_row is not None
        snapshot_id = snapshot_row[0]
        if snapshot_id != EXPECTED_SNAPSHOT_SHA256:
            raise ValueError(f"Unexpected database snapshot ID: {snapshot_id}")

        country_row_counts = connection.execute(
            """
            SELECT
                country.iso_alpha2,
                COUNT(*) AS source_rows,
                COUNT(DISTINCT record.code) AS distinct_codes,
                COUNT(*) FILTER (WHERE record.code IS NULL) AS rows_without_code
            FROM record_country AS country
            JOIN source_product_record AS record
                USING (source_record_id)
            GROUP BY iso_alpha2
            """
        ).fetchall()
        database_country_counts = {
            iso_alpha2: {
                "source_rows": int(source_rows),
                "distinct_codes": int(distinct_codes),
                "rows_without_code": int(rows_without_code),
            }
            for iso_alpha2, source_rows, distinct_codes, rows_without_code in country_row_counts
        }
        selected_country_codes = set(database_country_counts)
        if selected_country_codes != {"ID", "MY", "PH", "SG", "TH"}:
            raise ValueError(
                "Stage 5 evidence requires the five selected countries; found "
                f"{sorted(selected_country_codes)}."
            )

        approved_category_coverage = connection.execute(
            """
            SELECT
                country.iso_alpha2,
                COUNT(DISTINCT assignment.source_record_id)
                    AS approved_group_source_rows
            FROM record_country AS country
            JOIN record_category_tag AS assignment
                ON country.source_record_id = assignment.source_record_id
            JOIN category_tag_group_decision AS decision
                ON assignment.source_category_tag = decision.source_category_tag
            WHERE decision.selected_group_id IS NOT NULL
            GROUP BY country.iso_alpha2
            """
        ).fetchall()
        approved_category_by_iso = {
            iso_alpha2: int(record_count)
            for iso_alpha2, record_count in approved_category_coverage
        }

        brand_coverage = connection.execute(
            """
            SELECT
                country.iso_alpha2,
                COUNT(DISTINCT brand.source_record_id)
                    AS source_rows_with_brand_text,
                COUNT(DISTINCT brand.source_record_id) FILTER (
                    WHERE mapping.review_status = 'approved'
                ) AS source_rows_with_approved_brand_mapping,
                COUNT(DISTINCT mapping.canonical_brand_name) FILTER (
                    WHERE mapping.review_status = 'approved'
                ) AS approved_canonical_brand_names
            FROM record_country AS country
            LEFT JOIN record_brand_source_value AS brand
                ON country.source_record_id = brand.source_record_id
            LEFT JOIN brand_name_mapping AS mapping
                ON brand.source_brand_name = mapping.source_brand_name
            GROUP BY country.iso_alpha2
            """
        ).fetchall()
        readiness = build_readiness_scorecard(connection)
        contributor_diagnostics, yearly_diagnostics = build_contributor_diagnostics(
            connection
        )
        source_tag_coverage = build_source_tag_coverage(connection)
        country_code_overlap = build_country_code_overlap(connection)
        food_groups_crosscheck = build_food_groups_crosscheck(
            connection,
            FOOD_GROUP_CROSSWALK_FILE,
        )
    finally:
        connection.close()

    brand_by_iso = {
        iso_alpha2: {
            "source_rows_with_brand_text": int(rows_with_text),
            "source_rows_with_approved_brand_mapping": int(rows_with_mapping),
            "approved_canonical_brand_names": int(canonical_names),
        }
        for iso_alpha2, rows_with_text, rows_with_mapping, canonical_names in brand_coverage
    }

    fields = (
        "snapshot_sha256",
        "rank",
        "iso_alpha2",
        "country_name",
        "country_source_rows",
        "country_distinct_codes",
        "country_rows_minus_distinct_codes",
        "country_rows_without_code",
        "source_rows_with_category_tags",
        "category_tags_coverage_pct",
        "source_rows_with_primary_candidate_group",
        "primary_candidate_coverage_pct_of_category_tagged_rows",
        "source_rows_with_multiple_primary_groups",
        "source_rows_with_approved_group_decision",
        "source_rows_with_brand_text",
        "source_rows_with_approved_brand_mapping",
        "approved_brand_mapping_coverage_pct_of_country_rows",
        "approved_canonical_brand_names_present",
        "class_A_or_B_flagged_rows",
        "class_A_or_B_flagged_share_pct",
    )

    output_rows: list[dict[str, str]] = []
    selected_shortlist = [
        candidate
        for candidate in shortlist
        if candidate["iso_alpha2"] in selected_country_codes
    ]
    for candidate in selected_shortlist:
        iso_alpha2 = candidate["iso_alpha2"]
        if iso_alpha2 not in category_by_iso or iso_alpha2 not in nonfood_by_iso:
            raise ValueError(
                f"Missing category or non-food evidence for shortlisted unit {iso_alpha2}."
            )
        category = category_by_iso[iso_alpha2]
        nonfood = nonfood_by_iso[iso_alpha2]
        brand = brand_by_iso.get(
            iso_alpha2,
            {
                "source_rows_with_brand_text": 0,
                "source_rows_with_approved_brand_mapping": 0,
                "approved_canonical_brand_names": 0,
            },
        )
        country_rows = int(candidate["record_count"])
        country_database_counts = database_country_counts.get(iso_alpha2)
        if (
            country_database_counts is None
            or country_database_counts["source_rows"] != country_rows
        ):
            raise ValueError(
                f"Country row count does not reconcile for {iso_alpha2}: "
                f"shortlist={country_rows}, database="
                f"{country_database_counts}."
            )
        if int(category["country_source_records"]) != country_rows:
            raise ValueError(
                f"Category evidence denominator does not reconcile for {iso_alpha2}."
            )
        if (
            int(nonfood["total_records"]) != country_rows
            or nonfood["reconciles_to_normalized_profile"] != "Y"
        ):
            raise ValueError(
                f"Non-food country denominator does not reconcile for {iso_alpha2}."
            )
        category_tagged_rows = int(category["country_records_with_category_tags"])
        primary_rows = int(category["records_with_any_primary_group"])
        flagged_ab_rows = int(nonfood["class_a_records"]) + int(
            nonfood["class_b_records"]
        )

        if category_tagged_rows > country_rows:
            raise ValueError(
                f"Category-tagged rows exceed country rows for {iso_alpha2}."
            )
        if country_database_counts["rows_without_code"] != 0:
            raise ValueError(f"Source code is missing for records in {iso_alpha2}.")
        if primary_rows > country_rows:
            raise ValueError(
                f"Primary-group rows exceed country rows for {iso_alpha2}."
            )
        if (
            brand["source_rows_with_approved_brand_mapping"]
            > brand["source_rows_with_brand_text"]
        ):
            raise ValueError(
                f"Mapped brand rows exceed brand-text rows for {iso_alpha2}."
            )
        if flagged_ab_rows > country_rows:
            raise ValueError(f"A/B flagged rows exceed country rows for {iso_alpha2}.")

        output_rows.append(
            {
                "snapshot_sha256": snapshot_id,
                "rank": candidate["rank"],
                "iso_alpha2": iso_alpha2,
                "country_name": candidate["country_name"],
                "country_source_rows": str(country_rows),
                "country_distinct_codes": str(
                    country_database_counts["distinct_codes"]
                ),
                "country_rows_minus_distinct_codes": str(
                    country_rows - country_database_counts["distinct_codes"]
                ),
                "country_rows_without_code": str(
                    country_database_counts["rows_without_code"]
                ),
                "source_rows_with_category_tags": str(category_tagged_rows),
                "category_tags_coverage_pct": f"{100 * category_tagged_rows / country_rows:.4f}",
                "source_rows_with_primary_candidate_group": str(primary_rows),
                "primary_candidate_coverage_pct_of_category_tagged_rows": (
                    f"{100 * primary_rows / category_tagged_rows:.4f}"
                    if category_tagged_rows
                    else ""
                ),
                "source_rows_with_multiple_primary_groups": category[
                    "records_with_multiple_primary_groups"
                ],
                "source_rows_with_approved_group_decision": str(
                    approved_category_by_iso.get(iso_alpha2, 0)
                ),
                "source_rows_with_brand_text": str(
                    brand["source_rows_with_brand_text"]
                ),
                "source_rows_with_approved_brand_mapping": str(
                    brand["source_rows_with_approved_brand_mapping"]
                ),
                "approved_brand_mapping_coverage_pct_of_country_rows": (
                    f"{100 * brand['source_rows_with_approved_brand_mapping'] / country_rows:.4f}"
                ),
                "approved_canonical_brand_names_present": str(
                    brand["approved_canonical_brand_names"]
                ),
                "class_A_or_B_flagged_rows": str(flagged_ab_rows),
                "class_A_or_B_flagged_share_pct": f"{100 * flagged_ab_rows / country_rows:.4f}",
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)

    diagnostic_outputs = (
        (readiness, args.readiness_output),
        (contributor_diagnostics, args.contributor_output),
        (yearly_diagnostics, args.yearly_output),
        (source_tag_coverage, args.source_tag_output),
        (country_code_overlap, args.overlap_output),
        (food_groups_crosscheck, args.food_groups_output),
    )
    for frame, path in diagnostic_outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False, encoding="utf-8")

    print(f"Selected-country evidence rows: {len(output_rows)}")
    print(f"Snapshot SHA-256: {snapshot_id}")
    print(f"Evidence output: {args.output}")
    print(f"Data-readiness scorecard: {args.readiness_output}")
    print(f"Contributor and year diagnostics: {args.contributor_output}")
    print(f"Country-code overlap: {args.overlap_output}")
    print(f"Food-groups diagnostic: {args.food_groups_output}")


if __name__ == "__main__":
    main()
