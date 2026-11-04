"""Refresh deterministic category harmonization and its validated analysis outputs."""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
PROFILE_DIR = OUTPUTS_DIR / "profiling"
QUALITY_DIR = OUTPUTS_DIR / "quality"
ANALYSIS_DIR = OUTPUTS_DIR / "analysis"
STAGE7_FILE = PROJECT_ROOT / "docs" / "06_stage7_findings_and_recommendations.md"
BASELINE_DATABASE = PROCESSED_DIR / "global_product_landscape.duckdb"
BASELINE_VALIDATION = QUALITY_DIR / "database_build_validation.csv"
STAGE5_FILE = PROFILE_DIR / "stage5_country_peer_evidence.csv"
STAGE5_NAME = "stage5_country_peer_evidence.csv"
STAGE6_OUTPUTS = (
    "stage6_country_scope.csv",
    "stage6_country_category.csv",
    "stage6_country_brand.csv",
    "stage6_validation.csv",
)
STAGE6_CANDIDATE_VALIDATION = QUALITY_DIR / "stage6_candidate_build_validation.csv"
SUMMARY_FILE = QUALITY_DIR / "harmonization_refresh_summary.csv"
COUNTRIES = ("ID", "MY", "PH", "SG", "TH")
COUNTRY_ROLES = {
    "ID": "Focal",
    "MY": "Contextual peer",
    "PH": "Contextual peer",
    "SG": "Contextual peer",
    "TH": "Coverage contrast",
}
STAGE7_MARKERS = {
    "analysis-status": (
        "<!-- AUTO-GENERATED: analysis-status:START -->",
        "<!-- AUTO-GENERATED: analysis-status:END -->",
    ),
    "country-scope": (
        "<!-- AUTO-GENERATED: country-scope:START -->",
        "<!-- AUTO-GENERATED: country-scope:END -->",
    ),
    "top-groups": (
        "<!-- AUTO-GENERATED: top-groups:START -->",
        "<!-- AUTO-GENERATED: top-groups:END -->",
    ),
    "category-coverage": (
        "<!-- AUTO-GENERATED: category-coverage:START -->",
        "<!-- AUTO-GENERATED: category-coverage:END -->",
    ),
    "category-overlap": (
        "<!-- AUTO-GENERATED: category-overlap:START -->",
        "<!-- AUTO-GENERATED: category-overlap:END -->",
    ),
    "brand-coverage": (
        "<!-- AUTO-GENERATED: brand-coverage:START -->",
        "<!-- AUTO-GENERATED: brand-coverage:END -->",
    ),
    "brand-assignment-note": (
        "<!-- AUTO-GENERATED: brand-assignment-note:START -->",
        "<!-- AUTO-GENERATED: brand-assignment-note:END -->",
    ),
    "nonfood-sensitivity": (
        "<!-- AUTO-GENERATED: nonfood-sensitivity:START -->",
        "<!-- AUTO-GENERATED: nonfood-sensitivity:END -->",
    ),
}


def run_script(script_name: str, *arguments: str) -> None:
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / script_name),
        *arguments,
    ]
    print(f"\nRunning {script_name}...", flush=True)
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def validate_report(path: Path, expected_rows: int, label: str) -> pd.DataFrame:
    report = read_csv(path)
    required = {"actual_value", "expected_value", "status"}
    if len(report) != expected_rows or not required.issubset(report.columns):
        raise ValueError(f"{label} report is incomplete or malformed: {path}")
    if not (
        report["status"].eq("passed")
        & report["actual_value"].eq(report["expected_value"])
    ).all():
        raise ValueError(f"{label} report contains failed checks: {path}")
    return report


def replace_generated_section(
    document: str,
    section_name: str,
    content: str,
) -> str:
    start_marker, end_marker = STAGE7_MARKERS[section_name]
    if document.count(start_marker) != 1 or document.count(end_marker) != 1:
        raise ValueError(
            f"Expected exactly one pair of Stage 7 markers for {section_name}."
        )
    start = document.index(start_marker) + len(start_marker)
    end = document.index(end_marker)
    if start >= end:
        raise ValueError(f"Stage 7 markers are out of order: {section_name}")
    return document[:start] + "\n" + content.rstrip() + "\n" + document[end:]


def render_stage7(
    document: str,
    country_evidence: pd.DataFrame,
    scope: pd.DataFrame,
    categories: pd.DataFrame,
    brands: pd.DataFrame,
    candidate_check_count: int,
    stage6_check_count: int,
) -> str:
    document = replace_generated_section(
        document,
        "analysis-status",
        (
            "Stage 6 was rerun against the separately validated compact candidate "
            "database after the approved category mappings were applied. It "
            f"generated {len(scope):,} country-scenario rows, "
            f"{len(categories):,} country-category rows, and {len(brands):,} "
            "mapped-brand assignment rows. The candidate build passed "
            f"{candidate_check_count} checks and all {stage6_check_count} "
            "Stage 6 checks passed; the four published CSVs are byte-identical "
            "to the validated candidate run. These checks establish the tested "
            "reconciliations and arithmetic for the pinned inputs; they do not "
            "prove all mappings semantically correct or the data representative."
        ),
    )

    evidence_by_country = country_evidence.set_index("iso_alpha2")
    scope_baseline = scope.loc[scope["scenario"].eq("baseline")].set_index(
        "iso_alpha2"
    )
    country_rows = []
    for iso in COUNTRIES:
        row = scope_baseline.loc[iso]
        country_rows.append(
            f"| {iso} | {COUNTRY_ROLES[iso]} | {int(row['source_rows']):,} "
            f"| {int(row['source_rows_with_category_tags']):,} "
            f"| {float(row['category_tags_coverage_pct']):.4f}% |"
        )
    document = replace_generated_section(
        document,
        "country-scope",
        "\n".join(
            [
                "| ISO | Role | Source rows | Rows with `categories_tags` | Category-tag coverage |",
                "|---|---|---:|---:|---:|",
                *country_rows,
            ]
        ),
    )

    candidate_categories = categories.loc[
        categories["scenario"].eq("baseline")
        & categories["assignment_basis"].eq("candidate_derived")
    ].copy()
    candidate_categories["group_source_rows"] = pd.to_numeric(
        candidate_categories["group_source_rows"], errors="raise"
    )
    top_group_rows = []
    for iso in COUNTRIES:
        rows = candidate_categories.loc[
            candidate_categories["iso_alpha2"].eq(iso)
        ].nlargest(3, "group_source_rows")
        if len(rows) != 3:
            raise ValueError(f"Expected three candidate groups for {iso}.")
        first, second, third = rows.itertuples(index=False)
        top_group_rows.append(
            f"| {iso} | {first.reporting_group_label} | "
            f"{int(first.group_source_rows):,} | "
            f"{float(first.group_share_of_country_rows_pct):.4f}% | "
            f"{second.reporting_group_label} | "
            f"{int(second.group_source_rows):,} | "
            f"{third.reporting_group_label} | "
            f"{int(third.group_source_rows):,} |"
        )
    document = replace_generated_section(
        document,
        "top-groups",
        "\n".join(
            [
                "| ISO | Largest group | Rows | Share of country rows | Next largest | Rows | Third largest | Rows |",
                "|---|---|---:|---:|---|---:|---|---:|",
                *top_group_rows,
            ]
        ),
    )

    coverage_rows = []
    for iso in COUNTRIES:
        country_categories = categories.loc[
            categories["iso_alpha2"].eq(iso)
            & categories["scenario"].eq("baseline")
        ]
        by_basis = country_categories.drop_duplicates("assignment_basis").set_index(
            "assignment_basis"
        )
        candidate = by_basis.loc["candidate_derived"]
        approved = by_basis.loc["approved_only"]
        coverage_rows.append(
            f"| {iso} | {int(candidate['source_rows_with_category_tags']):,} "
            f"| {int(candidate['source_rows_assigned_to_any_substantive_group']):,} "
            f"| {int(candidate['category_tagged_rows_without_substantive_group_assignment']):,} "
            f"| {int(approved['source_rows_assigned_to_any_substantive_group']):,} "
            f"| {int(approved['category_tagged_rows_without_substantive_group_assignment']):,} |"
        )
    document = replace_generated_section(
        document,
        "category-coverage",
        "\n".join(
            [
                "| ISO | Category-tagged rows | Candidate-derived assigned | Candidate-derived tagged rows without assignment | Approved-only assigned | Approved-only tagged rows without assignment |",
                "|---|---:|---:|---:|---:|---:|",
                *coverage_rows,
            ]
        ),
    )
    overlap_counts = []
    for iso in COUNTRIES:
        rows = candidate_categories.loc[
            candidate_categories["iso_alpha2"].eq(iso)
        ]
        if rows.empty:
            raise ValueError(f"Candidate category results are missing {iso}.")
        overlap_counts.append(
            f"{iso} {int(rows.iloc[0]['source_rows_in_multiple_groups']):,}"
        )
    document = replace_generated_section(
        document,
        "category-overlap",
        (
            "There are also rows assigned to multiple groups in the "
            "candidate-derived view: "
            + ", ".join(overlap_counts[:-1])
            + f", and {overlap_counts[-1]}. These overlap counts are diagnostics "
            "and must not be added to category totals as if groups formed a "
            "partition."
        ),
    )

    brand_rows = []
    for iso in COUNTRIES:
        row = evidence_by_country.loc[iso]
        brand_rows.append(
            f"| {iso} | {int(row['source_rows_with_approved_brand_mapping']):,} "
            f"| {float(row['approved_brand_mapping_coverage_pct_of_country_rows']):.4f}% |"
        )
    document = replace_generated_section(
        document,
        "brand-coverage",
        "\n".join(
            [
                "| ISO | Rows with approved exact brand mapping | Share of country rows |",
                "|---|---:|---:|",
                *brand_rows,
            ]
        ),
    )
    document = replace_generated_section(
        document,
        "brand-assignment-note",
        (
            f"Stage 6's {len(brands):,} rows are assignments across scenarios, "
            "assignment bases, country-category groups, and mapped canonical "
            f"names; they are not {brands['canonical_brand_name'].nunique():,} "
            "distinct brands or an exhaustive brand census."
        ),
    )

    sensitivity_rows = []
    for iso in COUNTRIES:
        country_scenarios = scope.loc[scope["iso_alpha2"].eq(iso)].set_index(
            "scenario"
        )
        except_strong = int(
            country_scenarios.loc[
                "exclude_A_B_except_strong_food_signals", "excluded_source_rows"
            ]
        )
        all_a_b = int(
            country_scenarios.loc["exclude_all_A_B", "excluded_source_rows"]
        )
        sensitivity_rows.append(f"| {iso} | {except_strong:,} | {all_a_b:,} |")
    return replace_generated_section(
        document,
        "nonfood-sensitivity",
        "\n".join(
            [
                "| ISO | `exclude_A_B_except_strong_food_signals` | `exclude_all_A_B` |",
                "|---|---:|---:|",
                *sensitivity_rows,
            ]
        ),
    )


def validate_stage5_output(path: Path) -> pd.DataFrame:
    evidence = read_csv(path)
    if len(evidence) != 107 or evidence["iso_alpha2"].nunique() != 107:
        raise ValueError(
            f"Stage 5 evidence must contain 107 unique ISO units: {path}"
        )
    missing_countries = set(COUNTRIES) - set(evidence["iso_alpha2"])
    if missing_countries:
        raise ValueError(
            f"Stage 5 evidence is missing selected units: {sorted(missing_countries)}"
        )
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    if not BASELINE_DATABASE.is_file() or not BASELINE_VALIDATION.is_file():
        raise FileNotFoundError(
            "The validated full Stage 4 database and report are required."
        )
    validate_report(BASELINE_VALIDATION, 15, "Stage 4")
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)

    run_script("05_category_brand_profile.py")
    brand_mapping_validation = read_csv(
        PROFILE_DIR / "brand_name_manual_mapping_validation.csv"
    )
    brand_decisions = read_csv(
        PROJECT_ROOT / "data" / "mappings" / "brand_name_manual_decisions.csv"
    )
    if len(brand_mapping_validation) != len(brand_decisions):
        raise ValueError("Brand mapping validation does not cover every approved decision.")

    with tempfile.TemporaryDirectory(
        prefix=".harmonization_candidate_",
        dir=PROCESSED_DIR,
    ) as candidate_temp, tempfile.TemporaryDirectory(
        prefix=".harmonization_refresh_",
        dir=OUTPUTS_DIR,
    ) as refresh_temp:
        candidate_dir = Path(candidate_temp)
        refresh_dir = Path(refresh_temp)
        candidate_database = candidate_dir / "candidate.duckdb"
        candidate_validation = candidate_dir / "candidate_validation.csv"
        stage5_output = refresh_dir / STAGE5_NAME
        stage6_output_dir = refresh_dir / "analysis"

        run_script("07_category_reporting_group_draft.py")
        run_script("08_category_reporting_group_review_queues.py")
        run_script(
            "15_build_stage6_candidate_database.py",
            "--output",
            str(candidate_database),
            "--validation-output",
            str(candidate_validation),
        )
        candidate_report = validate_report(
            candidate_validation, 15, "Stage 6 candidate"
        )

        run_script(
            "12_stage5_country_peer_evidence.py",
            "--database",
            str(candidate_database),
            "--build-validation",
            str(candidate_validation),
            "--output",
            str(stage5_output),
        )
        stage5_evidence = validate_stage5_output(stage5_output)

        run_script(
            "13_run_stage6_analysis.py",
            "--database",
            str(candidate_database),
            "--build-validation",
            str(candidate_validation),
            "--country-evidence",
            str(stage5_output),
            "--output-dir",
            str(stage6_output_dir),
        )
        stage6_validation = validate_report(
            stage6_output_dir / "stage6_validation.csv", 11, "Stage 6"
        )
        scope = read_csv(stage6_output_dir / "stage6_country_scope.csv")
        categories = read_csv(stage6_output_dir / "stage6_country_category.csv")
        brands = read_csv(stage6_output_dir / "stage6_country_brand.csv")
        if len(scope) != 15 or len(categories) != 300:
            raise ValueError("Stage 6 output row counts do not match the approved scope.")

        current_stage7 = STAGE7_FILE.read_text(encoding="utf-8")
        refreshed_stage7 = render_stage7(
            current_stage7,
            stage5_evidence,
            scope,
            categories,
            brands,
            len(candidate_report),
            len(stage6_validation),
        )
        staged_stage7 = refresh_dir / STAGE7_FILE.name
        staged_stage7.write_text(refreshed_stage7, encoding="utf-8")
        staged_candidate_validation = (
            refresh_dir / STAGE6_CANDIDATE_VALIDATION.name
        )
        candidate_report_to_publish = read_csv(candidate_validation)
        if "database_file" in candidate_report_to_publish.columns:
            candidate_report_to_publish["database_file"] = (
                "temporary candidate (removed after successful refresh)"
            )
        candidate_report_to_publish.to_csv(
            staged_candidate_validation,
            index=False,
            encoding="utf-8",
        )

        summary = pd.DataFrame(
            [
                ("category_crosswalk", "completed", "scripts/07_category_reporting_group_draft.py"),
                ("review_queues", "completed", "scripts/08_category_reporting_group_review_queues.py"),
                ("brand_mapping_validation", f"{len(brand_mapping_validation)} exact values validated", "outputs/profiling/brand_name_manual_mapping_validation.csv"),
                ("candidate_validation", "15/15 passed", "outputs/quality/stage6_candidate_build_validation.csv"),
                ("stage5_evidence", "107 units validated", "outputs/profiling/stage5_country_peer_evidence.csv"),
                ("stage6_analysis", "11/11 passed", "outputs/analysis/"),
                ("stage7_findings", "dynamic result tables refreshed", "docs/06_stage7_findings_and_recommendations.md"),
            ],
            columns=("step", "result", "evidence"),
        )
        staged_summary = refresh_dir / SUMMARY_FILE.name
        summary.to_csv(staged_summary, index=False, encoding="utf-8")

        (stage5_output).replace(STAGE5_FILE)
        for output_name in STAGE6_OUTPUTS:
            (stage6_output_dir / output_name).replace(ANALYSIS_DIR / output_name)
        staged_candidate_validation.replace(STAGE6_CANDIDATE_VALIDATION)
        staged_summary.replace(SUMMARY_FILE)
        staged_stage7.replace(STAGE7_FILE)

    print("Automated harmonization refresh completed.")
    print("Candidate-database checks passed: 15")
    print("Stage 6 checks passed: 11")
    print(f"Stage 5 ISO units: {len(stage5_evidence)}")
    print(f"Stage 6 outputs: {ANALYSIS_DIR}")
    print(f"Stage 7 findings: {STAGE7_FILE}")
    print(f"Refresh summary: {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
