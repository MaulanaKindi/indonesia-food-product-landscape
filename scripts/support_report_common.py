"""Shared paths, scope, and Markdown replacement helpers for reports."""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUALITY_DIR = PROJECT_ROOT / "outputs" / "quality"
ONLINE_AUDIT_FILE = QUALITY_DIR / "category_mapping_online_evidence_audit.csv"

COUNTRIES = ("ID", "MY", "PH", "SG", "TH")


COUNTRY_ROLES = {
    "ID": "Focal",
    "MY": "Contextual peer",
    "PH": "Contextual peer",
    "SG": "Contextual peer",
    "TH": "Coverage contrast",
}


STAGE7_MARKERS = {
    "executive-summary": (
        "<!-- AUTO-GENERATED: executive-summary:START -->",
        "<!-- AUTO-GENERATED: executive-summary:END -->",
    ),
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
    "data-readiness": (
        "<!-- AUTO-GENERATED: data-readiness:START -->",
        "<!-- AUTO-GENERATED: data-readiness:END -->",
    ),
    "contributor-diagnostics": (
        "<!-- AUTO-GENERATED: contributor-diagnostics:START -->",
        "<!-- AUTO-GENERATED: contributor-diagnostics:END -->",
    ),
    "country-code-overlap": (
        "<!-- AUTO-GENERATED: country-code-overlap:START -->",
        "<!-- AUTO-GENERATED: country-code-overlap:END -->",
    ),
    "food-groups-crosscheck": (
        "<!-- AUTO-GENERATED: food-groups-crosscheck:START -->",
        "<!-- AUTO-GENERATED: food-groups-crosscheck:END -->",
    ),
    "semantic-mapping-audit": (
        "<!-- AUTO-GENERATED: semantic-mapping-audit:START -->",
        "<!-- AUTO-GENERATED: semantic-mapping-audit:END -->",
    ),
}


README_MARKERS = {
    "headline-metrics": (
        "<!-- AUTO-GENERATED: headline-metrics:START -->",
        "<!-- AUTO-GENERATED: headline-metrics:END -->",
    ),
    "country-comparison": (
        "<!-- AUTO-GENERATED: country-comparison:START -->",
        "<!-- AUTO-GENERATED: country-comparison:END -->",
    ),
    "readiness-scorecard": (
        "<!-- AUTO-GENERATED: readiness-scorecard:START -->",
        "<!-- AUTO-GENERATED: readiness-scorecard:END -->",
    ),
}


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


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


def replace_readme_section(
    document: str,
    section_name: str,
    content: str,
) -> str:
    start_marker, end_marker = README_MARKERS[section_name]
    if document.count(start_marker) != 1 or document.count(end_marker) != 1:
        raise ValueError(
            f"Expected exactly one pair of README markers for {section_name}."
        )
    start = document.index(start_marker) + len(start_marker)
    end = document.index(end_marker)
    if start >= end:
        raise ValueError(f"README markers are out of order: {section_name}")
    return document[:start] + "\n" + content.rstrip() + "\n" + document[end:]
