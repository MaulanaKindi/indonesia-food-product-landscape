"""Re-render generated README and Stage 7 sections from tracked CSV outputs.

Read-only with respect to CSV inputs; writes only the generated blocks in
README.md and docs/07_stage7_findings_and_recommendations.md. Does not touch
the database, charts, or any other file. Use this instead of the full Stage 16
refresh when only the generated presentation changes.
"""

from pathlib import Path

from support_render_readme import render_readme
from support_render_stage7 import render_stage7
from support_report_common import read_csv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = PROJECT_ROOT / "outputs" / "profiling"
QUALITY_DIR = PROJECT_ROOT / "outputs" / "quality"
ANALYSIS_DIR = PROJECT_ROOT / "outputs" / "analysis"
README_FILE = PROJECT_ROOT / "README.md"
STAGE7_FILE = PROJECT_ROOT / "docs" / "07_stage7_findings_and_recommendations.md"
STAGE5_FILE = PROFILE_DIR / "stage5_country_peer_evidence.csv"
READINESS_FILE = PROFILE_DIR / "data_readiness_scorecard.csv"
CONTRIBUTOR_FILE = PROFILE_DIR / "contributor_year_diagnostics.csv"
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
STAGE6_SCOPE_FILE = ANALYSIS_DIR / "stage6_country_scope.csv"
STAGE6_CATEGORY_FILE = ANALYSIS_DIR / "stage6_country_category.csv"
STAGE6_BRAND_FILE = ANALYSIS_DIR / "stage6_country_brand.csv"
STAGE6_VALIDATION_FILE = ANALYSIS_DIR / "stage6_validation.csv"
CANDIDATE_VALIDATION_FILE = QUALITY_DIR / "stage6_candidate_build_validation.csv"


def main() -> None:
    stage5 = read_csv(STAGE5_FILE)
    scope = read_csv(STAGE6_SCOPE_FILE)
    categories = read_csv(STAGE6_CATEGORY_FILE)
    brands = read_csv(STAGE6_BRAND_FILE)
    readiness = read_csv(READINESS_FILE)
    contributors = read_csv(CONTRIBUTOR_FILE)
    source_tags = read_csv(SOURCE_TAG_FILE)
    overlap = read_csv(OVERLAP_FILE)
    food_groups = read_csv(FOOD_GROUP_FILE)
    semantic_audit_records = read_csv(SEMANTIC_AUDIT_RECORDS_FILE)
    semantic_audit_summary = read_csv(SEMANTIC_AUDIT_SUMMARY_FILE)
    semantic_audit_groups = read_csv(SEMANTIC_AUDIT_GROUP_FILE)
    stage6_validation = read_csv(STAGE6_VALIDATION_FILE)
    candidate_validation = read_csv(CANDIDATE_VALIDATION_FILE)

    current_stage7 = STAGE7_FILE.read_text(encoding="utf-8")
    refreshed_stage7 = render_stage7(
        current_stage7,
        stage5,
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
        len(candidate_validation),
        len(stage6_validation),
    )
    current_readme = README_FILE.read_text(encoding="utf-8")
    refreshed_readme = render_readme(
        current_readme,
        stage5,
        scope,
        categories,
        readiness,
        semantic_audit_summary,
    )

    STAGE7_FILE.write_text(refreshed_stage7, encoding="utf-8")
    README_FILE.write_text(refreshed_readme, encoding="utf-8")
    print(f"Re-rendered generated sections in {STAGE7_FILE.relative_to(PROJECT_ROOT)}")
    print(f"Re-rendered generated sections in {README_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
