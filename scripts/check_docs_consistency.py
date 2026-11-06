"""Fail when generated README or Stage 7 values drift from validated CSVs."""

import importlib.util
import sys
from pathlib import Path

import pandas as pd


REFRESH_SCRIPT = Path(__file__).with_name("16_refresh_harmonized_analysis.py")
SPEC = importlib.util.spec_from_file_location("refresh_harmonized_analysis", REFRESH_SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Unable to load renderer: {REFRESH_SCRIPT}")
refresh = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = refresh
SPEC.loader.exec_module(refresh)


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def main() -> None:
    stage5 = read_csv(refresh.STAGE5_FILE)
    scope = read_csv(refresh.ANALYSIS_DIR / "stage6_country_scope.csv")
    categories = read_csv(refresh.ANALYSIS_DIR / "stage6_country_category.csv")
    brands = read_csv(refresh.ANALYSIS_DIR / "stage6_country_brand.csv")
    readiness = read_csv(refresh.READINESS_FILE)
    contributors = read_csv(refresh.CONTRIBUTOR_FILE)
    source_tags = read_csv(refresh.SOURCE_TAG_FILE)
    overlap = read_csv(refresh.OVERLAP_FILE)
    food_groups = read_csv(refresh.FOOD_GROUP_FILE)
    (
        semantic_audit_records,
        semantic_audit_summary,
        semantic_audit_groups,
    ) = refresh.load_semantic_audit_outputs()
    candidate_report = refresh.validate_report(
        refresh.STAGE6_CANDIDATE_VALIDATION,
        15,
        "Stage 6 candidate",
    )
    stage6_report = refresh.validate_report(
        refresh.ANALYSIS_DIR / "stage6_validation.csv",
        11,
        "Stage 6",
    )

    expected_stage7 = refresh.render_stage7(
        refresh.STAGE7_FILE.read_text(encoding="utf-8"),
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
        len(candidate_report),
        len(stage6_report),
    )
    expected_readme = refresh.render_readme(
        refresh.README_FILE.read_text(encoding="utf-8"),
        stage5,
        scope,
        categories,
        readiness,
        semantic_audit_summary,
    )

    if len(expected_readme.splitlines()) > 150:
        raise ValueError(
            "README exceeds the 150-line presentation limit: "
            f"{len(expected_readme.splitlines())} lines."
        )
    if expected_stage7 != refresh.STAGE7_FILE.read_text(encoding="utf-8"):
        raise ValueError(
            "Generated values in docs/06_stage7_findings_and_recommendations.md "
            "do not match the validated CSV outputs. Run scripts/16_refresh_harmonized_analysis.py."
        )
    if expected_readme != refresh.README_FILE.read_text(encoding="utf-8"):
        raise ValueError(
            "Generated values in README.md do not match the validated CSV outputs. "
            "Run scripts/16_refresh_harmonized_analysis.py."
        )
    print("README and Stage 7 generated sections match validated CSV outputs.")


if __name__ == "__main__":
    main()
