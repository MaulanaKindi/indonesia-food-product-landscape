"""Build a compact, separately validated database for the current Stage 6 scope."""

import argparse
import hashlib
import tempfile
from pathlib import Path

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILE = PROJECT_ROOT / "data" / "raw" / "food.parquet"
BASELINE_DATABASE = (
    PROJECT_ROOT / "data" / "processed" / "global_product_landscape.duckdb"
)
BASELINE_VALIDATION = (
    PROJECT_ROOT / "outputs" / "quality" / "database_build_validation.csv"
)
CANDIDATE_DATABASE = (
    PROJECT_ROOT / "data" / "processed" / "global_product_landscape_stage6_candidate.duckdb"
)
CANDIDATE_VALIDATION = (
    PROJECT_ROOT / "outputs" / "quality" / "stage6_candidate_build_validation.csv"
)
CROSSWALK_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "profiling"
    / "category_reporting_group_candidate_crosswalk.csv"
)
MANUAL_DECISIONS_FILE = (
    PROJECT_ROOT
    / "data"
    / "mappings"
    / "category_tag_reporting_group_manual_decisions.csv"
)
FRAMEWORK_FILE = (
    PROJECT_ROOT / "data" / "reference" / "category_reporting_group_framework.csv"
)
DISPOSITIONS_FILE = (
    PROJECT_ROOT / "data" / "mappings" / "category_tag_manual_dispositions.csv"
)
ANCHORS_FILE = (
    PROJECT_ROOT / "data" / "mappings" / "category_reporting_group_anchor_candidates.csv"
)
EXPECTED_SNAPSHOT_SHA256 = (
    "DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A"
)
EXPECTED_SOURCE_SIZE = 7_975_461_945
EXPECTED_SOURCE_ROWS = 4_828_207
EXPECTED_CATEGORY_LINKS = 10_480_049
EXPECTED_COUNTRY_SOURCE_TAG_LINKS = 5_079_894
EXPECTED_RECORD_COUNTRY_LINKS = 5_004_567


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


def validate_build_report(path: Path) -> None:
    report = pd.read_csv(path, dtype=str, keep_default_na=False)
    required = {"actual_value", "expected_value", "status"}
    if report.empty or not required.issubset(report.columns):
        raise ValueError(f"Invalid Stage 4 build report: {path}")
    if not (
        report["status"].eq("passed")
        & report["actual_value"].eq(report["expected_value"])
    ).all():
        raise ValueError(f"Stage 4 build report contains failed checks: {path}")


def build_candidate(
    baseline_database: Path,
    output_file: Path,
    crosswalk: pd.DataFrame,
    category_mapping_version: str,
) -> list[tuple[str, str, str]]:
    escaped_baseline = str(baseline_database.resolve()).replace("'", "''")
    connection = duckdb.connect(str(output_file))
    try:
        connection.execute(
            f"ATTACH '{escaped_baseline}' AS baseline (READ_ONLY)"
        )
        connection.register("current_crosswalk", crosswalk)

        connection.execute(
            """
            CREATE TABLE data_snapshot AS
            SELECT * FROM baseline.data_snapshot
            """
        )
        connection.execute(
            """
            CREATE TABLE source_product_record AS
            SELECT
                source_record_id,
                snapshot_id,
                source_row_ordinal,
                code,
                categories_tags,
                nova_group,
                nutriscore_grade,
                ingredients_n
            FROM baseline.source_product_record
            """
        )
        connection.execute(
            """
            CREATE TABLE reporting_group AS
            SELECT * FROM baseline.reporting_group
            """
        )
        connection.execute(
            """
            CREATE TABLE record_country AS
            SELECT * FROM baseline.record_country
            """
        )
        connection.execute(
            """
            CREATE TABLE record_category_tag AS
            SELECT * FROM baseline.record_category_tag
            """
        )
        connection.execute(
            """
            CREATE TABLE record_brand_source_value AS
            SELECT * FROM baseline.record_brand_source_value
            """
        )
        connection.execute(
            """
            CREATE TABLE brand_name_mapping AS
            SELECT * FROM baseline.brand_name_mapping
            """
        )
        connection.execute(
            """
            CREATE TABLE category_tag_group_decision AS
            SELECT
                source_category_tag,
                ? AS mapping_version,
                assignment_status AS decision_status,
                CASE
                    WHEN assignment_status = 'manual_group_assignment'
                    THEN manual_reporting_group_id
                    ELSE NULL
                END AS selected_group_id,
                manual_disposition,
                candidate_rationale AS decision_rationale,
                manual_evidence_tags AS supporting_exact_tags,
                manual_evidence_cooccurrence_rows AS evidence_cooccurrence
            FROM current_crosswalk
            """,
            [category_mapping_version],
        )
        connection.execute(
            """
            CREATE TABLE category_tag_group_candidate AS
            SELECT DISTINCT
                source_category_tag,
                ? AS mapping_version,
                candidate.reporting_group_id,
                crosswalk.assignment_status AS candidate_role,
                crosswalk.comparison_role
            FROM current_crosswalk AS crosswalk,
            UNNEST(string_split(crosswalk.candidate_group_ids, ' | '))
                AS candidate(reporting_group_id)
            WHERE trim(candidate.reporting_group_id) <> ''
            """,
            [category_mapping_version],
        )

        validation_rows = connection.execute(
            """
            WITH projection_mismatches AS (
                SELECT COUNT(*) AS mismatch_count
                FROM baseline.source_product_record AS old
                FULL OUTER JOIN source_product_record AS candidate
                    USING (source_record_id)
                WHERE old.source_record_id IS NULL
                   OR candidate.source_record_id IS NULL
                   OR old.snapshot_id IS DISTINCT FROM candidate.snapshot_id
                   OR old.source_row_ordinal
                        IS DISTINCT FROM candidate.source_row_ordinal
                   OR old.code IS DISTINCT FROM candidate.code
                   OR old.categories_tags
                        IS DISTINCT FROM candidate.categories_tags
                   OR old.nova_group IS DISTINCT FROM candidate.nova_group
                   OR old.nutriscore_grade
                        IS DISTINCT FROM candidate.nutriscore_grade
                   OR old.ingredients_n IS DISTINCT FROM candidate.ingredients_n
            ),
            country_link_mismatches AS (
                SELECT COUNT(*) AS mismatch_count
                FROM (
                    (
                        SELECT source_record_id, iso_alpha2
                        FROM baseline.record_country
                        EXCEPT
                        SELECT source_record_id, iso_alpha2
                        FROM record_country
                    )
                    UNION ALL
                    (
                        SELECT source_record_id, iso_alpha2
                        FROM record_country
                        EXCEPT
                        SELECT source_record_id, iso_alpha2
                        FROM baseline.record_country
                    )
                )
            ),
            category_link_mismatches AS (
                SELECT COUNT(*) AS mismatch_count
                FROM (
                    (
                        SELECT source_record_id, source_category_tag
                        FROM baseline.record_category_tag
                        EXCEPT
                        SELECT source_record_id, source_category_tag
                        FROM record_category_tag
                    )
                    UNION ALL
                    (
                        SELECT source_record_id, source_category_tag
                        FROM record_category_tag
                        EXCEPT
                        SELECT source_record_id, source_category_tag
                        FROM baseline.record_category_tag
                    )
                )
            ),
            brand_value_mismatches AS (
                SELECT COUNT(*) AS mismatch_count
                FROM (
                    (
                        SELECT source_record_id, source_brand_name
                        FROM baseline.record_brand_source_value
                        EXCEPT
                        SELECT source_record_id, source_brand_name
                        FROM record_brand_source_value
                    )
                    UNION ALL
                    (
                        SELECT source_record_id, source_brand_name
                        FROM record_brand_source_value
                        EXCEPT
                        SELECT source_record_id, source_brand_name
                        FROM baseline.record_brand_source_value
                    )
                )
            ),
            invalid_selected_groups AS (
                SELECT COUNT(*) AS invalid_count
                FROM category_tag_group_decision AS decision
                LEFT JOIN reporting_group AS group_ref
                    ON decision.selected_group_id = group_ref.reporting_group_id
                WHERE decision.selected_group_id IS NOT NULL
                  AND group_ref.reporting_group_id IS NULL
            )
            SELECT 'snapshot_id' AS check_name,
                   (SELECT snapshot_id FROM data_snapshot)::VARCHAR AS actual_value,
                   ?::VARCHAR AS expected_value
            UNION ALL
            SELECT 'source_product_record_rows',
                   COUNT(*)::VARCHAR,
                   ?::VARCHAR
            FROM source_product_record
            UNION ALL
            SELECT 'distinct_source_record_ids',
                   COUNT(DISTINCT source_record_id)::VARCHAR,
                   ?::VARCHAR
            FROM source_product_record
            UNION ALL
            SELECT 'stage6_source_projection_mismatches',
                   mismatch_count::VARCHAR,
                   '0'
            FROM projection_mismatches
            UNION ALL
            SELECT 'record_country_rows',
                   COUNT(*)::VARCHAR,
                   ?::VARCHAR
            FROM record_country
            UNION ALL
            SELECT 'record_country_content_mismatches',
                   mismatch_count::VARCHAR,
                   '0'
            FROM country_link_mismatches
            UNION ALL
            SELECT 'record_category_tag_rows',
                   COUNT(*)::VARCHAR,
                   ?::VARCHAR
            FROM record_category_tag
            UNION ALL
            SELECT 'record_category_tag_content_mismatches',
                   mismatch_count::VARCHAR,
                   '0'
            FROM category_link_mismatches
            UNION ALL
            SELECT 'record_brand_source_value_rows',
                   COUNT(*)::VARCHAR,
                   (SELECT COUNT(*)::VARCHAR
                    FROM baseline.record_brand_source_value)
            FROM record_brand_source_value
            UNION ALL
            SELECT 'record_brand_source_value_content_mismatches',
                   mismatch_count::VARCHAR,
                   '0'
            FROM brand_value_mismatches
            UNION ALL
            SELECT 'category_decision_tag_rows',
                   COUNT(*)::VARCHAR,
                   ?::VARCHAR
            FROM category_tag_group_decision
            UNION ALL
            SELECT 'manual_group_decision_count',
                   COUNT(*) FILTER (
                       WHERE decision_status = 'manual_group_assignment'
                   )::VARCHAR,
                   ?::VARCHAR
            FROM category_tag_group_decision
            UNION ALL
            SELECT 'selected_group_reference_errors',
                   invalid_count::VARCHAR,
                   '0'
            FROM invalid_selected_groups
            """,
            [
                EXPECTED_SNAPSHOT_SHA256,
                str(EXPECTED_SOURCE_ROWS),
                str(EXPECTED_SOURCE_ROWS),
                str(EXPECTED_RECORD_COUNTRY_LINKS),
                str(EXPECTED_CATEGORY_LINKS),
                str(len(crosswalk)),
                str(int(crosswalk["assignment_status"].eq("manual_group_assignment").sum())),
            ],
        ).fetchall()
    finally:
        connection.close()

    return validation_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-database", type=Path, default=BASELINE_DATABASE)
    parser.add_argument("--baseline-validation", type=Path, default=BASELINE_VALIDATION)
    parser.add_argument("--output", type=Path, default=CANDIDATE_DATABASE)
    parser.add_argument("--validation-output", type=Path, default=CANDIDATE_VALIDATION)
    args = parser.parse_args()

    baseline_database = args.baseline_database.resolve()
    output_file = args.output.resolve()
    validation_file = args.validation_output.resolve()

    for path in (
        SOURCE_FILE,
        baseline_database,
        args.baseline_validation,
        CROSSWALK_FILE,
        MANUAL_DECISIONS_FILE,
        FRAMEWORK_FILE,
        DISPOSITIONS_FILE,
        ANCHORS_FILE,
    ):
        if not path.is_file():
            raise FileNotFoundError(f"Required candidate-build input missing: {path}")
    if output_file.exists():
        raise FileExistsError(f"Refusing to overwrite existing candidate: {output_file}")
    if validation_file.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing validation report: {validation_file}"
        )

    print("Validating pinned source and prior Stage 4 build...", flush=True)
    if SOURCE_FILE.stat().st_size != EXPECTED_SOURCE_SIZE:
        raise ValueError(
            f"Parquet size mismatch: expected {EXPECTED_SOURCE_SIZE}, "
            f"found {SOURCE_FILE.stat().st_size}."
        )
    if sha256_file(SOURCE_FILE) != EXPECTED_SNAPSHOT_SHA256:
        raise ValueError("Pinned Parquet SHA-256 does not match the expected snapshot.")
    validate_build_report(args.baseline_validation)

    with duckdb.connect(str(baseline_database), read_only=True) as baseline:
        snapshot_id = baseline.execute(
            "SELECT snapshot_id FROM data_snapshot"
        ).fetchone()[0]
        source_rows = baseline.execute(
            "SELECT COUNT(*) FROM source_product_record"
        ).fetchone()[0]
        if snapshot_id != EXPECTED_SNAPSHOT_SHA256 or source_rows != EXPECTED_SOURCE_ROWS:
            raise ValueError(
                "Baseline database does not match the expected pinned source: "
                f"snapshot={snapshot_id}, rows={source_rows}."
            )
        country_link_count = baseline.execute(
            "SELECT COUNT(*) FROM record_country_source_tag"
        ).fetchone()[0]

    crosswalk = pd.read_csv(
        CROSSWALK_FILE,
        dtype=str,
        keep_default_na=False,
    )
    required_crosswalk_columns = {
        "source_category_tag",
        "records_with_tag",
        "assignment_status",
        "manual_reporting_group_id",
        "manual_disposition",
        "candidate_rationale",
        "manual_evidence_tags",
        "manual_evidence_cooccurrence_rows",
        "candidate_group_ids",
        "comparison_role",
        "taxonomy_match_status",
    }
    if not required_crosswalk_columns.issubset(crosswalk.columns):
        raise ValueError(
            "Current category crosswalk is missing required columns: "
            f"{sorted(required_crosswalk_columns - set(crosswalk.columns))}"
        )
    if crosswalk["source_category_tag"].duplicated().any():
        raise ValueError("Current category crosswalk contains duplicate tags.")

    manual = pd.read_csv(
        MANUAL_DECISIONS_FILE,
        dtype=str,
        keep_default_na=False,
    )
    manual_tags = crosswalk.loc[
        crosswalk["assignment_status"].eq("manual_group_assignment")
    ].set_index("source_category_tag")
    manual_input_tags = set(manual["source_category_tag"])
    if manual["source_category_tag"].duplicated().any():
        raise ValueError("Manual category decisions contain duplicate tags.")
    if manual_input_tags != set(manual_tags.index):
        raise ValueError(
            "Manual decisions do not exactly match the crosswalk's manual assignments."
        )
    manual_crosswalk_groups = manual_tags["manual_reporting_group_id"].to_dict()
    manual_input_groups = dict(
        zip(manual["source_category_tag"], manual["reporting_group_id"])
    )
    if manual_crosswalk_groups != manual_input_groups:
        raise ValueError("Manual decisions and crosswalk selected groups disagree.")
    if not manual["review_status"].eq("approved").all():
        raise ValueError("All manual category decisions must be approved.")

    category_mapping_version = sha256_files(
        (
            DISPOSITIONS_FILE,
            MANUAL_DECISIONS_FILE,
            ANCHORS_FILE,
            FRAMEWORK_FILE,
            CROSSWALK_FILE,
        )
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    validation_file.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".stage6_candidate_build_",
        dir=output_file.parent,
    ) as temporary_directory:
        temporary_database = Path(temporary_directory) / output_file.name
        print(
            "Building compact candidate from the validated baseline "
            "and current category crosswalk...",
            flush=True,
        )
        validation_rows = build_candidate(
            baseline_database,
            temporary_database,
            crosswalk,
            category_mapping_version,
        )
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
            raise ValueError("Candidate database validation failed:\n" + detail)
        temporary_database.replace(output_file)

    report = pd.DataFrame(
        validation_rows,
        columns=("check_name", "actual_value", "expected_value"),
    )
    report["status"] = "passed"
    try:
        report["database_file"] = output_file.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        report["database_file"] = str(output_file)
    report.to_csv(validation_file, index=False, encoding="utf-8")

    database_size = output_file.stat().st_size
    print(f"Candidate database created: {output_file}")
    print(f"Candidate database size: {database_size:,} bytes")
    print(f"Baseline country-tag links retained: {country_link_count:,}")
    print(f"Validation checks passed: {len(validation_rows)}")
    print(f"Validation report: {validation_file}")


if __name__ == "__main__":
    main()
