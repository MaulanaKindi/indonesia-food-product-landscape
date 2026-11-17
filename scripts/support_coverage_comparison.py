"""Compare category-tag coverage between the study country and its peers.

Reports the difference in percentage points with a 95% Wald interval and a
two-proportion z-test p-value, so a claim like "similar to Malaysia" can be
checked rather than asserted. The test treats records as independent trials,
which is an approximation: one product code can appear in several countries
and records are not a random sample of any market.
"""

import argparse
import math
from pathlib import Path

import pandas as pd

STUDY_COUNTRY = "ID"
PEER_COUNTRIES = ("MY", "PH", "SG", "TH")
Z_95 = 1.959963984540054


def two_proportion_test(
    tagged_study: int, records_study: int, tagged_peer: int, records_peer: int
) -> dict[str, float]:
    study_share = tagged_study / records_study
    peer_share = tagged_peer / records_peer
    difference = study_share - peer_share

    pooled = (tagged_study + tagged_peer) / (records_study + records_peer)
    pooled_error = math.sqrt(
        pooled * (1 - pooled) * (1 / records_study + 1 / records_peer)
    )
    z_score = difference / pooled_error
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z_score) / math.sqrt(2))))

    unpooled_error = math.sqrt(
        study_share * (1 - study_share) / records_study
        + peer_share * (1 - peer_share) / records_peer
    )

    return {
        "difference_pp": difference * 100,
        "ci_low_pp": (difference - Z_95 * unpooled_error) * 100,
        "ci_high_pp": (difference + Z_95 * unpooled_error) * 100,
        "z_score": z_score,
        "p_value": p_value,
    }


def comparison_table(scope: pd.DataFrame) -> pd.DataFrame:
    baseline = scope.loc[scope["scenario"].eq("baseline")].set_index("iso_alpha2")
    study_records = int(baseline.loc[STUDY_COUNTRY, "source_rows"])
    study_tagged = int(baseline.loc[STUDY_COUNTRY, "source_rows_with_category_tags"])

    rows = []
    for country in PEER_COUNTRIES:
        records = int(baseline.loc[country, "source_rows"])
        tagged = int(baseline.loc[country, "source_rows_with_category_tags"])
        result = two_proportion_test(study_tagged, study_records, tagged, records)
        rows.append(
            {
                "comparison": f"{STUDY_COUNTRY} vs {country}",
                "study_records": study_records,
                "study_tagged": study_tagged,
                "peer_records": records,
                "peer_tagged": tagged,
                "study_coverage_pct": 100 * study_tagged / study_records,
                "peer_coverage_pct": 100 * tagged / records,
                **result,
            }
        )
    return pd.DataFrame(rows)


def reading(row: pd.Series, alpha: float = 0.05) -> str:
    if row["p_value"] >= alpha:
        return "not distinguishable"
    direction = "higher" if row["difference_pp"] > 0 else "lower"
    return f"clearly {direction}"


def format_p_value(p_value: float) -> str:
    return "<0.0001" if p_value < 0.0001 else f"{p_value:.4f}"


def format_markdown(table: pd.DataFrame, alpha: float = 0.05) -> str:
    lines = [
        "| Comparison | Difference (pp) | 95% CI (pp) | p-value | Reading |",
        "|---|---:|---:|---:|---|",
    ]
    for _, row in table.iterrows():
        lines.append(
            f"| {row['comparison']} | {row['difference_pp']:+.2f} | "
            f"[{row['ci_low_pp']:+.2f}, {row['ci_high_pp']:+.2f}] | "
            f"{format_p_value(row['p_value'])} | {reading(row, alpha)} |"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scope",
        type=Path,
        default=Path("outputs/analysis/stage6_country_scope.csv"),
    )
    parser.add_argument("--alpha", type=float, default=0.05)
    args = parser.parse_args()

    table = comparison_table(pd.read_csv(args.scope))
    print(format_markdown(table, args.alpha))
    bonferroni = args.alpha / len(table)
    print()
    print(
        f"Bonferroni threshold for {len(table)} comparisons: alpha = {bonferroni:.4f}"
    )
    for _, row in table.iterrows():
        verdict = "significant" if row["p_value"] < bonferroni else "not significant"
        print(f"{row['comparison']}: {verdict} at the adjusted threshold")


if __name__ == "__main__":
    main()
