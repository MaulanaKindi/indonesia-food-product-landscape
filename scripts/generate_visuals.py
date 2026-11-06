"""Generate the three static charts used by the project README."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


COUNTRIES = ("ID", "MY", "PH", "SG", "TH")
COUNTRY_NAMES = {
    "ID": "Indonesia",
    "MY": "Malaysia",
    "PH": "Philippines",
    "SG": "Singapore",
    "TH": "Thailand",
}
COLORS = {
    "ID": "#0B6E69",
    "MY": "#4C78A8",
    "PH": "#F58518",
    "SG": "#72B7B2",
    "TH": "#E45756",
}


def save_category_coverage(analysis_dir: Path, output_dir: Path) -> None:
    scope = pd.read_csv(analysis_dir / "stage6_country_scope.csv")
    baseline = scope.loc[scope["scenario"].eq("baseline")].set_index("iso_alpha2")
    values = baseline.loc[list(COUNTRIES), "category_tags_coverage_pct"]

    fig, axis = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    bars = axis.bar(
        [COUNTRY_NAMES[code] for code in COUNTRIES],
        values,
        color=[COLORS[code] for code in COUNTRIES],
    )
    axis.set_ylabel("Records with category tags (%)")
    axis.set_title("Category-tag coverage varies across the selected countries")
    axis.set_ylim(0, 70)
    axis.grid(axis="y", alpha=0.25)
    axis.set_axisbelow(True)
    axis.bar_label(bars, fmt="%.1f%%", padding=3)
    fig.savefig(output_dir / "category_coverage.png", dpi=180)
    plt.close(fig)


def save_assignment_coverage(analysis_dir: Path, output_dir: Path) -> None:
    categories = pd.read_csv(analysis_dir / "stage6_country_category.csv")
    baseline = categories.loc[categories["scenario"].eq("baseline")]
    coverage = baseline.drop_duplicates(
        ["iso_alpha2", "assignment_basis"]
    ).pivot(
        index="iso_alpha2",
        columns="assignment_basis",
        values="substantive_group_assignment_coverage_of_category_tagged_rows_pct",
    )
    coverage = coverage.loc[list(COUNTRIES)]
    x_positions = list(range(len(COUNTRIES)))
    width = 0.36

    fig, axis = plt.subplots(figsize=(9, 4.8), constrained_layout=True)
    candidate = axis.bar(
        [position - width / 2 for position in x_positions],
        coverage["candidate_derived"],
        width,
        label="Candidate-derived",
        color="#4C78A8",
    )
    approved = axis.bar(
        [position + width / 2 for position in x_positions],
        coverage["approved_only"],
        width,
        label="Approved-only",
        color="#F58518",
    )
    axis.set_xticks(x_positions, [COUNTRY_NAMES[code] for code in COUNTRIES])
    axis.set_ylabel("Category-tagged records assigned to ≥1 group (%)")
    axis.set_title("Broader candidate coverage narrows under approved-only mapping")
    axis.set_ylim(0, 100)
    axis.grid(axis="y", alpha=0.25)
    axis.set_axisbelow(True)
    axis.legend(frameon=False, loc="upper left")
    axis.bar_label(candidate, fmt="%.0f%%", padding=2, fontsize=8)
    axis.bar_label(approved, fmt="%.0f%%", padding=2, fontsize=8)
    fig.savefig(output_dir / "category_assignment_coverage.png", dpi=180)
    plt.close(fig)


def save_readiness_heatmap(readiness_file: Path, output_dir: Path) -> None:
    readiness = pd.read_csv(readiness_file)
    metrics = (
        "Brand text",
        "Category tags",
        "Ingredient text",
        "Numeric nutrition value",
        "Valid Nutri-Score (A-E)",
        "Packaging information",
        "Label information",
        "Exact-approved brand mapping",
    )
    matrix = readiness.pivot(
        index="iso_alpha2",
        columns="metric",
        values="coverage_pct",
    ).loc[list(COUNTRIES), list(metrics)]

    fig, axis = plt.subplots(figsize=(12, 4.6), constrained_layout=True)
    image = axis.imshow(matrix.to_numpy(), cmap="YlGnBu", vmin=0, vmax=100, aspect="auto")
    axis.set_xticks(
        range(len(metrics)),
        [metric.replace(" ", "\n", 1) for metric in metrics],
        rotation=0,
        fontsize=8,
    )
    axis.set_yticks(range(len(COUNTRIES)), [COUNTRY_NAMES[code] for code in COUNTRIES])
    axis.set_title("Field availability in recorded products")
    for row in range(len(COUNTRIES)):
        for column in range(len(metrics)):
            value = matrix.iloc[row, column]
            axis.text(
                column,
                row,
                f"{value:.1f}%",
                ha="center",
                va="center",
                fontsize=8,
                color="white" if value >= 55 else "black",
            )
    colorbar = fig.colorbar(image, ax=axis, shrink=0.85)
    colorbar.set_label("Records with field/value (%)")
    fig.savefig(output_dir / "data_readiness_scorecard.png", dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-dir", type=Path, required=True)
    parser.add_argument("--readiness", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    save_category_coverage(args.analysis_dir, args.output_dir)
    save_assignment_coverage(args.analysis_dir, args.output_dir)
    save_readiness_heatmap(args.readiness, args.output_dir)
    print(f"Charts generated under {args.output_dir}")


if __name__ == "__main__":
    main()
