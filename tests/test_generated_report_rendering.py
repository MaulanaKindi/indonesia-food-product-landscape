import importlib.util
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = str(PROJECT_ROOT / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

RENDER_SPEC = importlib.util.spec_from_file_location(
    "support_render_readme", PROJECT_ROOT / "scripts" / "support_render_readme.py"
)
render_module = importlib.util.module_from_spec(RENDER_SPEC)
RENDER_SPEC.loader.exec_module(render_module)

CHECK_SPEC = importlib.util.spec_from_file_location(
    "headline_numbers_check", PROJECT_ROOT / "scripts" / "18_check_headline_numbers.py"
)
check_module = importlib.util.module_from_spec(CHECK_SPEC)
CHECK_SPEC.loader.exec_module(check_module)

COUNTRIES = ("ID", "MY", "PH", "SG", "TH")
ROWS = {"ID": 1000, "MY": 2000, "PH": 3000, "SG": 4000, "TH": 5000}
TAGGED = {"ID": 200, "MY": 300, "PH": 400, "SG": 500, "TH": 600}
CANDIDATE = {"ID": 100, "MY": 150, "PH": 200, "SG": 250, "TH": 300}
APPROVED = {"ID": 20, "MY": 30, "PH": 40, "SG": 50, "TH": 60}

READINESS_METRICS = (
    "Brand text",
    "Category tags",
    "Ingredient text",
    "Numeric nutrition value",
    "Valid Nutri-Score (A-E)",
    "Packaging information",
    "Label information",
    "Exact-approved brand mapping",
)

DOCUMENT_TEMPLATE = (
    "<!-- AUTO-GENERATED: headline-metrics:START -->\n"
    "<!-- AUTO-GENERATED: headline-metrics:END -->\n"
    "<!-- AUTO-GENERATED: country-comparison:START -->\n"
    "<!-- AUTO-GENERATED: country-comparison:END -->\n"
    "<!-- AUTO-GENERATED: readiness-scorecard:START -->\n"
    "<!-- AUTO-GENERATED: readiness-scorecard:END -->\n"
)


def synthetic_frames() -> tuple[
    pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame
]:
    scope = pd.DataFrame(
        [
            {
                "iso_alpha2": iso,
                "scenario": "baseline",
                "source_rows": str(ROWS[iso]),
                "distinct_codes": str(ROWS[iso]),
                "source_rows_with_category_tags": str(TAGGED[iso]),
                "category_tags_coverage_pct": f"{100 * TAGGED[iso] / ROWS[iso]:.4f}",
            }
            for iso in COUNTRIES
        ]
    )
    categories = pd.DataFrame(
        [
            {
                "iso_alpha2": iso,
                "scenario": "baseline",
                "assignment_basis": basis,
                "source_rows_assigned_to_any_substantive_group": str(counts[iso]),
                "substantive_group_assignment_coverage_of_category_tagged_rows_pct": (
                    f"{100 * counts[iso] / TAGGED[iso]:.4f}"
                ),
            }
            for basis, counts in (
                ("candidate_derived", CANDIDATE),
                ("approved_only", APPROVED),
            )
            for iso in COUNTRIES
        ]
    )
    evidence = pd.DataFrame(
        [
            {
                "iso_alpha2": iso,
                "approved_brand_mapping_coverage_pct_of_country_rows": "0.5000",
            }
            for iso in COUNTRIES
        ]
    )
    readiness = pd.DataFrame(
        [
            {"iso_alpha2": iso, "metric": metric, "coverage_pct": "40.0000"}
            for iso in COUNTRIES
            for metric in READINESS_METRICS
        ]
    )
    audit = pd.DataFrame(
        [
            {
                "analysis_scope": "primary_sample",
                "correct_assignments": "97",
                "candidate_assignment_pairs": "130",
            }
        ]
    )
    return scope, categories, evidence, readiness, audit


def render() -> str:
    scope, categories, evidence, readiness, audit = synthetic_frames()
    return render_module.render_readme(
        DOCUMENT_TEMPLATE, evidence, scope, categories, readiness, audit
    )


def test_derived_shares_use_all_country_records_as_denominator() -> None:
    rendered = render()

    assert "| Indonesia (ID) | Study country | 1,000 | 200 |" in rendered
    assert "| 10.00% | 2.00% |" in rendered
    assert "50.00%" not in rendered


def test_country_table_uses_plain_language_roles_and_full_names() -> None:
    rendered = render()

    assert "Indonesia (ID)" in rendered
    assert "Malaysia (MY)" in rendered
    assert "Study country" in rendered
    assert "Comparison country" in rendered
    assert "High-coverage contrast" in rendered
    assert "Candidate-derived, share of all records" in rendered
    assert "Approved-only, share of all records" in rendered


def test_country_table_omits_the_brand_column_duplicated_in_readiness() -> None:
    rendered = render()

    assert "Exact-approved brand mapped" not in rendered
    assert "Exact-approved brand map" in rendered


def test_headline_bullets_use_plain_language_role_names() -> None:
    rendered = render()

    assert "in the comparison countries" in rendered
    assert "in Thailand, the high-coverage contrast" in rendered


def test_static_string_guard_accepts_complete_static_text(
    tmp_path, monkeypatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "9,118 rows, 12.2% tagged, 788/9,118 records, 8.64%, 1.24%, 0.34%, "
        "97 of 130 pairs, 61/150 agreement\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(check_module, "README_FILE", readme)
    checker = check_module.Checker()

    check_module.check_readme_static_strings(checker)

    assert checker.failures == []


def test_static_string_guard_ignores_generated_blocks(tmp_path, monkeypatch) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "9,118 rows, 12.2% tagged, 788/9,118 records, 1.24%, 0.34%, "
        "97 of 130 pairs, 61/150 agreement\n"
        "<!-- AUTO-GENERATED: country-comparison:START -->\n"
        "| Indonesia (ID) | 8.64% |\n"
        "<!-- AUTO-GENERATED: country-comparison:END -->\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(check_module, "README_FILE", readme)
    checker = check_module.Checker()

    check_module.check_readme_static_strings(checker)

    assert checker.failures == [
        "README static text contains '8.64%': False != expected True"
    ]


def test_static_string_guard_reports_missing_string(tmp_path, monkeypatch) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("9,118 rows\n", encoding="utf-8")
    monkeypatch.setattr(check_module, "README_FILE", readme)
    checker = check_module.Checker()

    check_module.check_readme_static_strings(checker)

    assert len(checker.failures) == len(check_module.EXPECTED_README_STATIC_STRINGS) - 1
