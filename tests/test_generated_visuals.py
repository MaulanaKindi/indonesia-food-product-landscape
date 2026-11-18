import importlib.util
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = str(PROJECT_ROOT / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

VISUALS_SPEC = importlib.util.spec_from_file_location(
    "support_generate_visuals", PROJECT_ROOT / "scripts" / "support_generate_visuals.py"
)
visuals = importlib.util.module_from_spec(VISUALS_SPEC)
VISUALS_SPEC.loader.exec_module(visuals)

COUNTRIES = ("ID", "MY", "PH", "SG", "TH")
ROWS = {"ID": 1000, "MY": 2000, "PH": 3000, "SG": 4000, "TH": 5000}
TAGGED = {"ID": 200, "MY": 300, "PH": 400, "SG": 500, "TH": 600}
CANDIDATE_PCT = {"ID": 70.0, "MY": 60.0, "PH": 55.0, "SG": 45.0, "TH": 30.0}
APPROVED_PCT = {"ID": 5.0, "MY": 10.0, "PH": 15.0, "SG": 20.0, "TH": 25.0}
GROUP_SHARES = {
    "ID": (("Beverages", 6.0), ("Fruits & vegetables", 2.0)),
    "MY": (("Beverages", 9.0), ("Fruits & vegetables", 3.0)),
    "PH": (("Beverages", 12.0), ("Fruits & vegetables", 4.0)),
    "SG": (("Beverages", 15.0), ("Fruits & vegetables", 5.0)),
    "TH": (("Beverages", 18.0), ("Fruits & vegetables", 6.0)),
}
BRAND_TEXT = {"ID": 50.0, "MY": 55.0, "PH": 60.0, "SG": 65.0, "TH": 70.0}
BRAND_MAPPED = {"ID": 0.5, "MY": 0.6, "PH": 0.7, "SG": 0.8, "TH": 0.9}


def write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    analysis_dir = tmp_path / "analysis"
    profiling_dir = tmp_path / "profiling"
    analysis_dir.mkdir()
    profiling_dir.mkdir()

    scope_rows = []
    for iso in COUNTRIES:
        scope_rows.append(
            {
                "iso_alpha2": iso,
                "scenario": "baseline",
                "source_rows": ROWS[iso],
                "source_rows_with_category_tags": TAGGED[iso],
                "category_tags_coverage_pct": 100 * TAGGED[iso] / ROWS[iso],
            }
        )
    pd.DataFrame(scope_rows).to_csv(
        analysis_dir / "stage6_country_scope.csv", index=False
    )

    category_rows = []
    for iso in COUNTRIES:
        for index, (label, share) in enumerate(GROUP_SHARES[iso]):
            category_rows.append(
                {
                    "iso_alpha2": iso,
                    "scenario": "baseline",
                    "assignment_basis": "candidate_derived",
                    "reporting_group_label": label,
                    "group_source_rows": round(ROWS[iso] * share / 100),
                    "group_share_of_country_rows_pct": share,
                    "substantive_group_assignment_coverage_of_category_tagged_rows_pct": (
                        CANDIDATE_PCT[iso]
                    ),
                    "reporting_group_id": f"group_{index}",
                }
            )
        category_rows.append(
            {
                "iso_alpha2": iso,
                "scenario": "baseline",
                "assignment_basis": "approved_only",
                "reporting_group_label": "Other / unclassified",
                "group_source_rows": round(ROWS[iso] * APPROVED_PCT[iso] / 100),
                "group_share_of_country_rows_pct": APPROVED_PCT[iso],
                "substantive_group_assignment_coverage_of_category_tagged_rows_pct": (
                    APPROVED_PCT[iso]
                ),
                "reporting_group_id": "group_decoy",
            }
        )
    pd.DataFrame(category_rows).to_csv(
        analysis_dir / "stage6_country_category.csv", index=False
    )

    readiness_rows = []
    for iso in COUNTRIES:
        for metric, value in (
            ("Brand text", BRAND_TEXT[iso]),
            ("Category tags", 100 * TAGGED[iso] / ROWS[iso]),
            ("Ingredient text", 40.0),
            ("Numeric nutrition value", 30.0),
            ("Valid Nutri-Score (A-E)", 20.0),
            ("Packaging information", 10.0),
            ("Label information", 5.0),
            ("Exact-approved brand mapping", BRAND_MAPPED[iso]),
        ):
            readiness_rows.append(
                {"iso_alpha2": iso, "metric": metric, "coverage_pct": value}
            )
    readiness_file = profiling_dir / "data_readiness_scorecard.csv"
    pd.DataFrame(readiness_rows).to_csv(readiness_file, index=False)

    return analysis_dir, readiness_file


def generate_all(tmp_path: Path) -> Path:
    analysis_dir, readiness_file = write_inputs(tmp_path)
    output_dir = tmp_path / "img"
    output_dir.mkdir()

    visuals.save_category_coverage(analysis_dir, output_dir)
    visuals.save_assignment_coverage(analysis_dir, output_dir)
    visuals.save_largest_category_group(analysis_dir, output_dir)
    visuals.save_readiness_heatmap(readiness_file, output_dir)
    visuals.save_brand_mapping_gap(readiness_file, output_dir)

    return output_dir


def test_all_five_charts_are_written(tmp_path) -> None:
    output_dir = generate_all(tmp_path)

    for name in (
        "category_coverage.png",
        "category_assignment_coverage.png",
        "largest_category_group.png",
        "data_readiness_scorecard.png",
        "brand_mapping_gap.png",
    ):
        chart = output_dir / name
        assert chart.is_file(), name
        assert chart.read_bytes().startswith(b"\x89PNG"), name
        assert chart.stat().st_size > 5000, name


def test_palette_keeps_countries_and_series_distinguishable() -> None:
    country_colors = [visuals.COLORS[iso] for iso in COUNTRIES]

    assert len(set(country_colors)) == len(COUNTRIES)
    assert visuals.CANDIDATE_COLOR != visuals.APPROVED_COLOR
    assert visuals.CANDIDATE_COLOR not in country_colors
    assert visuals.APPROVED_COLOR not in country_colors
    assert "0B6E69" not in country_colors
    assert "72B7B2" not in country_colors


def test_largest_group_chart_follows_the_largest_share_row(tmp_path) -> None:
    analysis_dir, readiness_file = write_inputs(tmp_path)
    output_dir = tmp_path / "img"
    output_dir.mkdir()
    visuals.save_largest_category_group(analysis_dir, output_dir)
    baseline_bytes = (output_dir / "largest_category_group.png").read_bytes()

    categories = pd.read_csv(analysis_dir / "stage6_country_category.csv")
    categories.loc[
        categories["iso_alpha2"].eq("TH")
        & categories["assignment_basis"].eq("candidate_derived"),
        "group_share_of_country_rows_pct",
    ] = [90.0, 80.0]
    categories.to_csv(analysis_dir / "stage6_country_category.csv", index=False)
    visuals.save_largest_category_group(analysis_dir, output_dir)
    changed_bytes = (output_dir / "largest_category_group.png").read_bytes()

    assert changed_bytes != baseline_bytes


def test_largest_group_chart_requires_group_source_rows(tmp_path) -> None:
    analysis_dir, _ = write_inputs(tmp_path)
    output_dir = tmp_path / "img"
    output_dir.mkdir()
    categories = pd.read_csv(analysis_dir / "stage6_country_category.csv")
    categories.drop(columns=["group_source_rows"]).to_csv(
        analysis_dir / "stage6_country_category.csv", index=False
    )

    try:
        visuals.save_largest_category_group(analysis_dir, output_dir)
    except KeyError as error:
        assert "group_source_rows" in str(error)
    else:
        raise AssertionError("expected KeyError for a missing group_source_rows column")


def test_brand_chart_requires_brand_text_metric(tmp_path) -> None:
    _, readiness_file = write_inputs(tmp_path)
    output_dir = tmp_path / "img"
    output_dir.mkdir()
    readiness = pd.read_csv(readiness_file)
    readiness.loc[readiness["metric"].eq("Brand text"), "metric"] = "Renamed field"
    readiness.to_csv(readiness_file, index=False)

    try:
        visuals.save_brand_mapping_gap(readiness_file, output_dir)
    except KeyError as error:
        assert "Brand text" in str(error)
    else:
        raise AssertionError("expected KeyError when the Brand text metric is absent")


def test_category_coverage_title_is_computed_and_flags_a_low_result() -> None:
    trailing = pd.DataFrame({"category_tags_coverage_pct": {"ID": 12.18, "TH": 62.63}})
    leading = pd.DataFrame({"category_tags_coverage_pct": {"ID": 62.63, "TH": 12.18}})

    assert visuals.category_coverage_title(trailing).startswith("Only 12%")
    assert "versus 63% in Thailand" in visuals.category_coverage_title(trailing)
    assert not visuals.category_coverage_title(leading).startswith("Only")


def test_category_coverage_title_follows_the_data(tmp_path) -> None:
    analysis_dir, _ = write_inputs(tmp_path)
    scope = pd.read_csv(analysis_dir / "stage6_country_scope.csv")
    before = visuals.category_coverage_title(scope.set_index("iso_alpha2"))
    scope.loc[scope["iso_alpha2"].eq("ID"), "category_tags_coverage_pct"] = 90.0
    after = visuals.category_coverage_title(scope.set_index("iso_alpha2"))

    assert before != after
    assert "90%" in after


def test_assignment_coverage_title_reports_both_views() -> None:
    coverage = pd.DataFrame(
        {"candidate_derived": {"ID": 70.9}, "approved_only": {"ID": 10.2}}
    )

    title = visuals.assignment_coverage_title(coverage)

    assert "71%" in title
    assert "10%" in title


def test_readiness_title_names_the_widest_gap_for_indonesia() -> None:
    matrix = pd.DataFrame(
        {
            "Brand text": {"ID": 38.8, "TH": 80.4},
            "Category tags": {"ID": 12.18, "TH": 62.63},
        }
    )

    title = visuals.readiness_title(matrix)

    assert "Category tags" in title
    assert "12%" in title
    assert "63%" in title
    assert "Thailand" in title


def test_readiness_title_falls_back_to_the_spread_when_indonesia_leads() -> None:
    matrix = pd.DataFrame({"Labels": {"ID": 28.9, "TH": 17.2}})

    title = visuals.readiness_title(matrix)

    assert title == "Widest spread: Labels, 17% in Thailand versus 29% in Indonesia"


def test_largest_group_title_counts_countries() -> None:
    largest = pd.DataFrame(
        {
            "reporting_group_label": {
                "ID": "Beverages",
                "MY": "Snacks",
                "TH": "Snacks",
            },
            "group_share_of_country_rows_pct": {"ID": 6.0, "MY": 9.0, "TH": 18.0},
        }
    )

    assert (
        visuals.largest_group_title(largest)
        == "Snacks is the largest reporting group in 2 of 3 countries"
    )


def test_largest_group_title_names_one_country_when_no_group_repeats() -> None:
    largest = pd.DataFrame(
        {
            "reporting_group_label": {
                "ID": "Beverages",
                "MY": "Snacks",
                "TH": "Bakery",
            },
            "group_share_of_country_rows_pct": {"ID": 6.0, "MY": 9.0, "TH": 18.0},
        }
    )

    title = visuals.largest_group_title(largest)

    assert (
        title == "Bakery is the largest reporting group in Thailand at 18% of records"
    )


def test_brand_gap_title_keeps_two_decimals_below_one_percent() -> None:
    matrix = pd.DataFrame(
        {
            "Brand text": {"ID": 38.8},
            "Exact-approved brand mapping": {"ID": 0.34},
        }
    )

    title = visuals.brand_gap_title(matrix)

    assert "Brand text covers 39% of Indonesian records" in title
    assert "exact-approved mapping covers 0.34%" in title
