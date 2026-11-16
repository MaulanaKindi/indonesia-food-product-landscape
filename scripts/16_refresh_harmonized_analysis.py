"""Refresh deterministic category harmonization and its validated analysis outputs."""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

from support_report_common import (
    COUNTRIES,
    read_csv,
)
from support_render_readme import render_readme
from support_render_stage7 import render_stage7


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
PROFILE_DIR = OUTPUTS_DIR / "profiling"
QUALITY_DIR = OUTPUTS_DIR / "quality"
ANALYSIS_DIR = OUTPUTS_DIR / "analysis"
STAGE7_FILE = PROJECT_ROOT / "docs" / "07_stage7_findings_and_recommendations.md"
README_FILE = PROJECT_ROOT / "README.md"
BASELINE_DATABASE = PROCESSED_DIR / "global_product_landscape_five_country.duckdb"
BASELINE_VALIDATION = QUALITY_DIR / "database_build_validation_five_country.csv"
STAGE5_FILE = PROFILE_DIR / "stage5_country_peer_evidence.csv"
STAGE5_NAME = "stage5_country_peer_evidence.csv"
READINESS_FILE = PROFILE_DIR / "data_readiness_scorecard.csv"
CONTRIBUTOR_FILE = PROFILE_DIR / "contributor_year_diagnostics.csv"
YEARLY_FILE = PROFILE_DIR / "record_creation_year.csv"
SOURCE_TAG_FILE = PROFILE_DIR / "source_tag_coverage.csv"
OVERLAP_FILE = PROFILE_DIR / "country_code_overlap.csv"
FOOD_GROUP_FILE = PROFILE_DIR / "food_groups_crosscheck.csv"
SEMANTIC_AUDIT_RECORDS_FILE = (
    QUALITY_DIR / "category_mapping_semantic_audit_records.csv"
)
SEMANTIC_AUDIT_SUMMARY_FILE = (
    QUALITY_DIR / "category_mapping_semantic_audit_summary.csv"
)
SEMANTIC_AUDIT_GROUP_FILE = QUALITY_DIR / "category_mapping_semantic_audit_by_group.csv"
ONLINE_AUDIT_FILE = QUALITY_DIR / "category_mapping_online_evidence_audit.csv"
VISUAL_DIR = PROJECT_ROOT / "docs" / "img"
VISUAL_NAMES = (
    "category_coverage.png",
    "category_assignment_coverage.png",
    "data_readiness_scorecard.png",
)
STAGE6_OUTPUTS = (
    "stage6_country_scope.csv",
    "stage6_country_category.csv",
    "stage6_country_brand.csv",
    "stage6_validation.csv",
)
STAGE6_CANDIDATE_VALIDATION = QUALITY_DIR / "stage6_candidate_build_validation.csv"
SUMMARY_FILE = QUALITY_DIR / "harmonization_refresh_summary.csv"


def run_script(script_name: str, *arguments: str) -> None:
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / script_name),
        *arguments,
    ]
    print(f"\nRunning {script_name}...", flush=True)
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def load_semantic_audit_outputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    records = read_csv(SEMANTIC_AUDIT_RECORDS_FILE)
    summary = read_csv(SEMANTIC_AUDIT_SUMMARY_FILE)
    groups = read_csv(SEMANTIC_AUDIT_GROUP_FILE)
    required_summary_columns = {
        "analysis_scope",
        "sampling_frame_records",
        "records_reviewed",
        "candidate_assignment_pairs",
        "correct_assignments",
        "incorrect_assignments",
        "ambiguous_assignments",
        "insufficient_evidence_assignments",
        "exact_set_matches",
        "record_exact_set_agreement_all_records",
        "determinate_record_denominator",
        "record_exact_set_agreement_determinate_only",
        "record_exact_set_ci_low",
        "record_exact_set_ci_high",
        "ambiguous_record_count",
        "ambiguity_rate",
        "insufficient_evidence_record_count",
        "insufficient_evidence_rate",
        "taxonomy_only_candidate_assignment_pairs",
        "taxonomy_only_correct_assignments",
        "taxonomy_only_incorrect_assignments",
        "taxonomy_only_ambiguous_assignments",
        "taxonomy_only_insufficient_evidence_assignments",
        "taxonomy_only_determinate_denominator",
        "taxonomy_only_precision_ci_low",
        "taxonomy_only_precision_ci_high",
        "manual_overlap_correct_assignments",
        "manual_overlap_incorrect_assignments",
        "manual_overlap_ambiguous_assignments",
        "manual_overlap_insufficient_evidence_assignments",
        "manual_overlap_determinate_denominator",
        "manual_overlap_precision_ci_low",
        "manual_overlap_precision_ci_high",
        "manual_exact_overlap_assignment_pairs",
        "determinate_assignment_precision",
        "determinate_precision_ci_low",
        "determinate_precision_ci_high",
        "confirmed_assignment_share_all_pairs",
        "confirmed_share_ci_low",
        "confirmed_share_ci_high",
        "food_groups_comparable_records",
        "food_groups_exact_set_matches",
        "food_groups_exact_match_rate",
        "food_groups_any_overlap_records",
        "food_groups_any_overlap_rate",
        "determinate_records_with_supported_groups_missing_from_candidate",
        "determinate_reviewer_supported_group_pairs_missing_from_candidate",
    }
    if not required_summary_columns.issubset(summary.columns):
        raise ValueError(
            "Semantic audit summary is missing required columns: "
            f"{sorted(required_summary_columns - set(summary.columns))}"
        )
    expected_scopes = {"primary_sample", "meat_poultry_census"}
    if (
        len(summary) != 2
        or summary["analysis_scope"].duplicated().any()
        or set(summary["analysis_scope"]) != expected_scopes
    ):
        raise ValueError(
            "Semantic audit summary must contain the primary sample and "
            "separate Meat & poultry census."
        )
    primary = summary.loc[summary["analysis_scope"].eq("primary_sample")].iloc[0]
    census = summary.loc[summary["analysis_scope"].eq("meat_poultry_census")].iloc[0]
    if (
        int(primary["sampling_frame_records"]) != 1_111
        or int(primary["records_reviewed"]) != 150
        or int(census["sampling_frame_records"]) != 8
        or int(census["records_reviewed"]) != 8
        or len(records) != 158
        or records["sampling_design"].value_counts().to_dict()
        != {"primary_sample": 150, "meat_poultry_census": 8}
    ):
        raise ValueError("Semantic audit outputs do not match the reviewed sample.")
    if set(records["sampling_design"]) != expected_scopes:
        raise ValueError("Semantic audit record output has unexpected scope values.")
    if not {
        "reporting_group_id",
        "analysis_scope",
        "candidate_assignment_records",
        "correct_assignments",
        "incorrect_assignments",
        "ambiguous_assignments",
        "insufficient_evidence_assignments",
        "determinate_assignment_denominator",
        "determinate_assignment_precision",
        "determinate_precision_ci_low",
        "determinate_precision_ci_high",
    }.issubset(groups.columns):
        raise ValueError("Semantic audit per-group output is incomplete.")
    if (
        set(groups["analysis_scope"]) != expected_scopes
        or len(groups) != 20
        or groups.duplicated(["analysis_scope", "reporting_group_id"]).any()
    ):
        raise ValueError(
            "Semantic audit per-group output has unexpected scope or rows."
        )
    for row in summary.itertuples(index=False):
        classified_pairs = sum(
            int(getattr(row, column))
            for column in (
                "correct_assignments",
                "incorrect_assignments",
                "ambiguous_assignments",
                "insufficient_evidence_assignments",
            )
        )
        group_pairs = int(
            groups.loc[
                groups["analysis_scope"].eq(row.analysis_scope),
                "candidate_assignment_records",
            ]
            .astype(int)
            .sum()
        )
        if classified_pairs != int(
            row.candidate_assignment_pairs
        ) or group_pairs != int(row.candidate_assignment_pairs):
            raise ValueError(
                f"Semantic audit assignment totals do not reconcile for "
                f"{row.analysis_scope}."
            )
    return records, summary, groups


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


def validate_stage5_output(path: Path) -> pd.DataFrame:
    evidence = read_csv(path)
    if len(evidence) != len(COUNTRIES) or evidence["iso_alpha2"].nunique() != len(
        COUNTRIES
    ):
        raise ValueError(
            f"Stage 5 evidence must contain {len(COUNTRIES)} selected ISO units: {path}"
        )
    missing_countries = set(COUNTRIES) - set(evidence["iso_alpha2"])
    if missing_countries:
        raise ValueError(
            f"Stage 5 evidence is missing selected units: {sorted(missing_countries)}"
        )
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-mapping-refresh",
        action="store_true",
        help=(
            "Reuse the category crosswalk and review queues generated by a "
            "calling pipeline from the current mapping inputs."
        ),
    )
    parser.add_argument(
        "--skip-brand-profile-refresh",
        action="store_true",
        help=(
            "Reuse brand mapping validation generated by a calling pipeline "
            "from the current source and mapping inputs."
        ),
    )
    args = parser.parse_args()

    if not BASELINE_DATABASE.is_file() or not BASELINE_VALIDATION.is_file():
        raise FileNotFoundError(
            "The validated five-country Stage 4 database and report are required."
        )
    validate_report(BASELINE_VALIDATION, 15, "Stage 4")
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)

    if not args.skip_brand_profile_refresh:
        run_script("05_category_brand_profile.py")
    brand_mapping_validation = read_csv(
        PROFILE_DIR / "brand_name_manual_mapping_validation.csv"
    )
    brand_decisions = read_csv(
        PROJECT_ROOT / "data" / "mappings" / "brand_name_manual_decisions.csv"
    )
    if len(brand_mapping_validation) != len(brand_decisions):
        raise ValueError(
            "Brand mapping validation does not cover every approved decision."
        )

    with (
        tempfile.TemporaryDirectory(
            prefix=".harmonization_candidate_",
            dir=PROCESSED_DIR,
        ) as candidate_temp,
        tempfile.TemporaryDirectory(
            prefix=".harmonization_refresh_",
            dir=OUTPUTS_DIR,
        ) as refresh_temp,
    ):
        candidate_dir = Path(candidate_temp)
        refresh_dir = Path(refresh_temp)
        candidate_database = candidate_dir / "candidate.duckdb"
        candidate_validation = candidate_dir / "candidate_validation.csv"
        stage5_output = refresh_dir / STAGE5_NAME
        readiness_output = refresh_dir / READINESS_FILE.name
        contributor_output = refresh_dir / CONTRIBUTOR_FILE.name
        yearly_output = refresh_dir / YEARLY_FILE.name
        source_tag_output = refresh_dir / SOURCE_TAG_FILE.name
        overlap_output = refresh_dir / OVERLAP_FILE.name
        food_groups_output = refresh_dir / FOOD_GROUP_FILE.name
        visual_output_dir = refresh_dir / "img"
        stage6_output_dir = refresh_dir / "analysis"

        if not args.skip_mapping_refresh:
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
            "--readiness-output",
            str(readiness_output),
            "--contributor-output",
            str(contributor_output),
            "--yearly-output",
            str(yearly_output),
            "--source-tag-output",
            str(source_tag_output),
            "--overlap-output",
            str(overlap_output),
            "--food-groups-output",
            str(food_groups_output),
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
        readiness = read_csv(readiness_output)
        contributors = read_csv(contributor_output)
        source_tags = read_csv(source_tag_output)
        overlap = read_csv(overlap_output)
        food_groups = read_csv(food_groups_output)
        (
            semantic_audit_records,
            semantic_audit_summary,
            semantic_audit_groups,
        ) = load_semantic_audit_outputs()
        if len(scope) != 15 or len(categories) != 300:
            raise ValueError(
                "Stage 6 output row counts do not match the approved scope."
            )

        run_script(
            "support_generate_visuals.py",
            "--analysis-dir",
            str(stage6_output_dir),
            "--readiness",
            str(readiness_output),
            "--output-dir",
            str(visual_output_dir),
        )

        current_stage7 = STAGE7_FILE.read_text(encoding="utf-8")
        refreshed_stage7 = render_stage7(
            current_stage7,
            stage5_evidence,
            scope,
            categories,
            brands,
            readiness,
            contributors,
            source_tags,
            overlap,
            food_groups,
            semantic_audit_records,
            semantic_audit_summary,
            semantic_audit_groups,
            len(candidate_report),
            len(stage6_validation),
        )
        staged_stage7 = refresh_dir / STAGE7_FILE.name
        staged_stage7.write_text(refreshed_stage7, encoding="utf-8")
        current_readme = README_FILE.read_text(encoding="utf-8")
        refreshed_readme = render_readme(
            current_readme,
            stage5_evidence,
            scope,
            categories,
            readiness,
            semantic_audit_summary,
        )
        staged_readme = refresh_dir / README_FILE.name
        staged_readme.write_text(refreshed_readme, encoding="utf-8")
        staged_candidate_validation = refresh_dir / STAGE6_CANDIDATE_VALIDATION.name
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
                (
                    "category_crosswalk",
                    "completed",
                    "scripts/07_category_reporting_group_draft.py",
                ),
                (
                    "review_queues",
                    "completed",
                    "scripts/08_category_reporting_group_review_queues.py",
                ),
                (
                    "brand_mapping_validation",
                    f"{len(brand_mapping_validation)} exact values validated",
                    "outputs/profiling/brand_name_manual_mapping_validation.csv",
                ),
                (
                    "readiness_and_contributor_diagnostics",
                    "five-country scorecard, creator/year and source-tag diagnostics, identifier overlap, and food-groups cross-check generated",
                    "outputs/profiling/",
                ),
                (
                    "candidate_validation",
                    "15/15 passed",
                    "outputs/quality/stage6_candidate_build_validation.csv",
                ),
                (
                    "stage5_evidence",
                    f"{len(stage5_evidence)} selected units validated",
                    "outputs/profiling/stage5_country_peer_evidence.csv",
                ),
                ("stage6_analysis", "11/11 passed", "outputs/analysis/"),
                (
                    "semantic_mapping_audit",
                    "AI-assisted audit outputs validated and included in generated findings",
                    "outputs/quality/category_mapping_semantic_audit_*.csv",
                ),
                (
                    "stage7_findings",
                    "dynamic result tables refreshed",
                    "docs/07_stage7_findings_and_recommendations.md",
                ),
            ],
            columns=("step", "result", "evidence"),
        )
        staged_summary = refresh_dir / SUMMARY_FILE.name
        summary.to_csv(staged_summary, index=False, encoding="utf-8")

        (stage5_output).replace(STAGE5_FILE)
        readiness_output.replace(READINESS_FILE)
        contributor_output.replace(CONTRIBUTOR_FILE)
        yearly_output.replace(YEARLY_FILE)
        source_tag_output.replace(SOURCE_TAG_FILE)
        overlap_output.replace(OVERLAP_FILE)
        food_groups_output.replace(FOOD_GROUP_FILE)
        VISUAL_DIR.mkdir(parents=True, exist_ok=True)
        for visual_name in VISUAL_NAMES:
            (visual_output_dir / visual_name).replace(VISUAL_DIR / visual_name)
        for output_name in STAGE6_OUTPUTS:
            (stage6_output_dir / output_name).replace(ANALYSIS_DIR / output_name)
        staged_candidate_validation.replace(STAGE6_CANDIDATE_VALIDATION)
        staged_summary.replace(SUMMARY_FILE)
        staged_readme.replace(README_FILE)
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
