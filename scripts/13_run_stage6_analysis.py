"""Run the owner-approved, snapshot-pinned Stage 6 descriptive analysis."""

import argparse
import csv
import os
import tempfile
from pathlib import Path

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_FILE = PROJECT_ROOT / "data" / "processed" / "global_product_landscape.duckdb"
BUILD_VALIDATION_FILE = (
    PROJECT_ROOT / "outputs" / "quality" / "database_build_validation.csv"
)
COUNTRY_EVIDENCE_FILE = (
    PROJECT_ROOT / "outputs" / "profiling" / "stage5_country_peer_evidence.csv"
)
NONFOOD_SENSITIVITY_FILE = (
    PROJECT_ROOT / "outputs" / "profiling" / "nonfood_scope_sensitivity_impact.csv"
)
ANALYSIS_SQL = PROJECT_ROOT / "sql" / "03_stage6_analysis.sql"
VALIDATION_SQL = PROJECT_ROOT / "sql" / "04_stage6_validation.sql"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "analysis"
SNAPSHOT_SHA256 = (
    "DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A"
)
ANALYSIS_OUTPUTS = (
    "stage6_country_scope.csv",
    "stage6_country_category.csv",
    "stage6_country_brand.csv",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def validate_inputs(
    database_file: Path,
    build_validation_file: Path,
    country_evidence_file: Path,
) -> None:
    required = (
        database_file,
        build_validation_file,
        country_evidence_file,
        NONFOOD_SENSITIVITY_FILE,
        ANALYSIS_SQL,
        VALIDATION_SQL,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Required Stage 6 inputs are missing:\n" + "\n".join(missing)
        )

    build_checks = read_csv(build_validation_file)
    if not build_checks or any(
        row["status"] != "passed"
        or row["actual_value"] != row["expected_value"]
        for row in build_checks
    ):
        raise ValueError(
            f"Database build validation is not fully passed: {build_validation_file}"
        )

    country_evidence = read_csv(country_evidence_file)
    role_codes = {"ID", "MY", "PH", "SG", "TH"}
    if not role_codes.issubset({row["iso_alpha2"] for row in country_evidence}):
        raise ValueError("Stage 5 evidence is missing an owner-approved country.")

    connection = duckdb.connect(str(database_file), read_only=True)
    try:
        snapshot_id = connection.execute(
            "SELECT snapshot_id FROM data_snapshot"
        ).fetchone()[0]
    finally:
        connection.close()
    if snapshot_id != SNAPSHOT_SHA256:
        raise ValueError(
            f"Database snapshot mismatch: expected {SNAPSHOT_SHA256}, "
            f"found {snapshot_id}."
        )


def sql_with_output_dir(
    sql_path: Path,
    output_dir: Path,
    country_evidence_file: Path,
) -> str:
    sql = sql_path.read_text(encoding="utf-8")
    escaped_output_dir = str(output_dir.resolve()).replace("\\", "/").replace("'", "''")
    escaped_evidence_file = (
        str(country_evidence_file.resolve()).replace("\\", "/").replace("'", "''")
    )
    sql = sql.replace("{{SNAPSHOT_ID}}", SNAPSHOT_SHA256)
    sql = sql.replace("{{ANALYSIS_OUTPUT_DIR}}", escaped_output_dir)
    sql = sql.replace(
        "'{{COUNTRY_EVIDENCE_FILE}}'",
        f"'{escaped_evidence_file}'",
    )
    if "{{" in sql or "}}" in sql:
        raise ValueError(f"Unresolved SQL placeholder in {sql_path}.")
    return sql


def write_validation_report(
    validation_rows: list[tuple[str, str, str]],
    report_path: Path,
) -> Path:
    report = pd.DataFrame(
        validation_rows,
        columns=("check_name", "actual_value", "expected_value"),
    )
    report["status"] = "passed"
    report["snapshot_sha256"] = SNAPSHOT_SHA256
    report.to_csv(report_path, index=False, encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DATABASE_FILE)
    parser.add_argument("--build-validation", type=Path, default=BUILD_VALIDATION_FILE)
    parser.add_argument("--country-evidence", type=Path, default=COUNTRY_EVIDENCE_FILE)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    validate_inputs(
        args.database,
        args.build_validation,
        args.country_evidence,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(PROJECT_ROOT)

    with tempfile.TemporaryDirectory(
        prefix=".stage6_analysis_",
        dir=args.output_dir.parent,
    ) as temporary_directory:
        temporary_output = Path(temporary_directory)
        connection = duckdb.connect(str(args.database), read_only=True)
        try:
            connection.execute(
                sql_with_output_dir(
                    ANALYSIS_SQL,
                    temporary_output,
                    args.country_evidence,
                )
            )
            validation_rows = connection.execute(
                sql_with_output_dir(
                    VALIDATION_SQL,
                    temporary_output,
                    args.country_evidence,
                )
            ).fetchall()
        finally:
            connection.close()

        failures = [
            (check_name, actual, expected)
            for check_name, actual, expected in validation_rows
            if actual != expected
        ]
        if failures:
            details = "\n".join(
                f"{check_name}: expected {expected}, found {actual}"
                for check_name, actual, expected in failures
            )
            raise ValueError("Stage 6 validation failed:\n" + details)

        staged_outputs = (*ANALYSIS_OUTPUTS, "stage6_validation.csv")
        for output_name in staged_outputs:
            if output_name == "stage6_validation.csv":
                write_validation_report(
                    validation_rows,
                    temporary_output / output_name,
                )
                continue
            staged_output = temporary_output / output_name
            if not staged_output.is_file():
                raise FileNotFoundError(
                    f"Expected staged analysis output is missing: {staged_output}"
                )
        for output_name in staged_outputs:
            (temporary_output / output_name).replace(args.output_dir / output_name)
        report_path = args.output_dir / "stage6_validation.csv"

    print(f"Snapshot SHA-256: {SNAPSHOT_SHA256}")
    print(f"Analysis output directory: {args.output_dir}")
    print(f"Validation checks passed: {len(validation_rows)}")
    print(f"Validation report: {report_path}")
    for output_name in ANALYSIS_OUTPUTS:
        print(f"Created: {args.output_dir / output_name}")


if __name__ == "__main__":
    main()
