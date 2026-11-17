import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = str(PROJECT_ROOT / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

COMPARISON_SPEC = importlib.util.spec_from_file_location(
    "support_coverage_comparison",
    PROJECT_ROOT / "scripts" / "support_coverage_comparison.py",
)
comparison = importlib.util.module_from_spec(COMPARISON_SPEC)
COMPARISON_SPEC.loader.exec_module(comparison)

SCOPE_FILE = PROJECT_ROOT / "outputs" / "analysis" / "stage6_country_scope.csv"


def scope_frame() -> pd.DataFrame:
    return pd.read_csv(SCOPE_FILE)


def row_for(table: pd.DataFrame, peer: str) -> pd.Series:
    return table.loc[table["comparison"].eq(f"ID vs {peer}")].iloc[0]


BASE_PANEL = {
    "ID": (9118, 1111),
    "MY": (7426, 840),
    "PH": (9176, 1535),
    "SG": (11986, 2074),
    "TH": (11343, 7104),
}


def synthetic_scope(overrides: dict[str, tuple[int, int]]) -> pd.DataFrame:
    rows = {**BASE_PANEL, **overrides}
    return pd.DataFrame(
        [
            {
                "iso_alpha2": iso,
                "scenario": "baseline",
                "source_rows": records,
                "source_rows_with_category_tags": tagged,
            }
            for iso, (records, tagged) in rows.items()
        ]
    )


def test_comparison_table_covers_the_four_peers() -> None:
    table = comparison.comparison_table(scope_frame())

    assert list(table["comparison"]) == ["ID vs MY", "ID vs PH", "ID vs SG", "ID vs TH"]
    assert len(table) == 4


def test_my_difference_is_not_distinguishable_from_zero() -> None:
    row = row_for(comparison.comparison_table(scope_frame()), "MY")

    assert row["difference_pp"] == pytest.approx(0.87, abs=0.01)
    assert row["ci_low_pp"] < 0 < row["ci_high_pp"]
    assert row["p_value"] == pytest.approx(0.0833, abs=0.001)
    assert comparison.reading(row) == "not distinguishable"


def test_lower_coverage_gaps_exclude_zero() -> None:
    table = comparison.comparison_table(scope_frame())

    for peer in ("PH", "SG", "TH"):
        row = row_for(table, peer)
        assert row["difference_pp"] < 0
        assert row["ci_high_pp"] < 0
        assert row["p_value"] < 0.0001
        assert comparison.reading(row) == "clearly lower"


def test_bonferroni_threshold_keeps_every_conclusion() -> None:
    table = comparison.comparison_table(scope_frame())
    threshold = 0.05 / len(table)

    my_row = row_for(table, "MY")
    assert my_row["p_value"] > threshold
    for peer in ("PH", "SG", "TH"):
        assert row_for(table, peer)["p_value"] < threshold


def test_identical_coverage_is_never_called_a_difference() -> None:
    scope = synthetic_scope({"MY": (9118, 1111)})

    row = row_for(comparison.comparison_table(scope), "MY")

    assert row["difference_pp"] == pytest.approx(0.0, abs=1e-9)
    assert row["p_value"] == pytest.approx(1.0, abs=1e-6)
    assert comparison.reading(row) == "not distinguishable"


def test_higher_peer_coverage_reads_as_higher() -> None:
    scope = synthetic_scope({"MY": (7426, 2000)})

    row = row_for(comparison.comparison_table(scope), "MY")

    assert row["difference_pp"] < 0
    assert comparison.reading(row) == "clearly lower"


def test_tiny_p_values_are_reported_as_a_bound() -> None:
    assert comparison.format_p_value(1e-9) == "<0.0001"
    assert comparison.format_p_value(0.0833) == "0.0833"
