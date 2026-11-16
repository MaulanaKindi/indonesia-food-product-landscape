"""Assert published headline numbers match the tracked analysis CSVs.

Read-only guard against README/docs drift: no DuckDB, no pipeline re-run, no
network access. Reads only tracked outputs under ``outputs/`` and fails loudly
when a headline number quoted in the README or docs no longer matches the data.
Also asserts that key static README strings are present outside generated blocks.
"""

import re
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
README_FILE = PROJECT_ROOT / "README.md"
STAGE5_FILE = (
    PROJECT_ROOT / "outputs" / "profiling" / "stage5_country_peer_evidence.csv"
)
STAGE6_SCOPE_FILE = PROJECT_ROOT / "outputs" / "analysis" / "stage6_country_scope.csv"
READINESS_FILE = PROJECT_ROOT / "outputs" / "profiling" / "data_readiness_scorecard.csv"
SEMANTIC_AUDIT_SUMMARY_FILE = (
    PROJECT_ROOT / "outputs" / "quality" / "category_mapping_semantic_audit_summary.csv"
)
ONLINE_AUDIT_FILE = (
    PROJECT_ROOT / "outputs" / "quality" / "category_mapping_online_evidence_audit.csv"
)

EXPECTED_DERIVED = {
    "ID": {"candidate_share": 8.64, "approved_share": 1.24},
    "MY": {"candidate_share": 8.35, "approved_share": 1.13},
    "PH": {"candidate_share": 13.87, "approved_share": 1.72},
    "SG": {"candidate_share": 15.07, "approved_share": 2.19},
    "TH": {"candidate_share": 39.81, "approved_share": 5.93},
}

GENERATED_BLOCK_PATTERN = re.compile(
    r"<!-- AUTO-GENERATED: [a-z0-9-]+:START -->"
    r".*?"
    r"<!-- AUTO-GENERATED: [a-z0-9-]+:END -->",
    re.DOTALL,
)

EXPECTED_README_STATIC_STRINGS = (
    "9,118",
    "12.2%",
    "788/9,118",
    "8.64%",
    "1.24%",
    "0.34%",
    "97 of 130",
    "61/150",
)

EXPECTED_HEADLINES = {
    "ID": {
        "rows": 9118,
        "category_tagged": 1111,
        "coverage_pct": 12.1847,
        "candidate_groups": 788,
        "approved_groups": 113,
        "brand_mapped": 31,
        "brand_coverage_pct": 0.34,
    },
    "MY": {
        "rows": 7426,
        "category_tagged": 840,
        "coverage_pct": 11.3116,
        "candidate_groups": 620,
        "approved_groups": 84,
        "brand_mapped": 64,
        "brand_coverage_pct": 0.8618,
    },
    "PH": {
        "rows": 9176,
        "category_tagged": 1535,
        "coverage_pct": 16.7284,
        "candidate_groups": 1273,
        "approved_groups": 158,
        "brand_mapped": 88,
        "brand_coverage_pct": 0.959,
    },
    "SG": {
        "rows": 11986,
        "category_tagged": 2074,
        "coverage_pct": 17.3035,
        "candidate_groups": 1806,
        "approved_groups": 263,
        "brand_mapped": 341,
        "brand_coverage_pct": 2.845,
    },
    "TH": {
        "rows": 11343,
        "category_tagged": 7104,
        "coverage_pct": 62.6289,
        "candidate_groups": 4516,
        "approved_groups": 673,
        "brand_mapped": 46,
        "brand_coverage_pct": 0.4055,
    },
}


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


class Checker:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.count = 0

    def equal(self, label: str, actual: object, expected: object) -> None:
        self.count += 1
        if actual != expected:
            self.failures.append(f"{label}: {actual!r} != expected {expected!r}")

    def int(self, label: str, actual: str, expected: int) -> None:
        self.equal(label, int(actual), expected)

    def pct(self, label: str, actual: str, expected: float) -> None:
        self.equal(label, round(float(actual), 4), round(expected, 4))


def country_row(frame: pd.DataFrame, iso_alpha2: str) -> pd.Series:
    matches = frame[frame["iso_alpha2"] == iso_alpha2]
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one row for {iso_alpha2}, found {len(matches)}"
        )
    return matches.iloc[0]


def metric_row(frame: pd.DataFrame, iso_alpha2: str, metric: str) -> pd.Series:
    matches = frame[(frame["iso_alpha2"] == iso_alpha2) & (frame["metric"] == metric)]
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one row for {iso_alpha2}/{metric}, found {len(matches)}"
        )
    return matches.iloc[0]


def check_country(
    iso_alpha2: str,
    expected: dict[str, float],
    stage5: pd.DataFrame,
    baseline: pd.DataFrame,
    readiness: pd.DataFrame,
    checker: Checker,
) -> None:
    rows = int(expected["rows"])
    tagged = int(expected["category_tagged"])
    candidate = int(expected["candidate_groups"])
    approved = int(expected["approved_groups"])
    brand = int(expected["brand_mapped"])

    scope_row = country_row(baseline, iso_alpha2)
    checker.int(f"{iso_alpha2} scope rows", scope_row["source_rows"], rows)
    checker.int(f"{iso_alpha2} scope distinct codes", scope_row["distinct_codes"], rows)
    checker.int(
        f"{iso_alpha2} scope category-tagged rows",
        scope_row["source_rows_with_category_tags"],
        tagged,
    )
    checker.pct(
        f"{iso_alpha2} scope category coverage pct",
        scope_row["category_tags_coverage_pct"],
        float(expected["coverage_pct"]),
    )

    stage5_row = country_row(stage5, iso_alpha2)
    checker.int(f"{iso_alpha2} stage5 rows", stage5_row["country_source_rows"], rows)
    checker.int(
        f"{iso_alpha2} stage5 category-tagged rows",
        stage5_row["source_rows_with_category_tags"],
        tagged,
    )
    checker.pct(
        f"{iso_alpha2} stage5 category coverage pct",
        stage5_row["category_tags_coverage_pct"],
        float(expected["coverage_pct"]),
    )
    checker.int(
        f"{iso_alpha2} stage5 candidate-derived groups",
        stage5_row["source_rows_with_primary_candidate_group"],
        candidate,
    )
    checker.int(
        f"{iso_alpha2} stage5 approved-only groups",
        stage5_row["source_rows_with_approved_group_decision"],
        approved,
    )
    checker.int(
        f"{iso_alpha2} stage5 exact-approved brand mappings",
        stage5_row["source_rows_with_approved_brand_mapping"],
        brand,
    )
    checker.pct(
        f"{iso_alpha2} stage5 brand coverage pct",
        stage5_row["approved_brand_mapping_coverage_pct_of_country_rows"],
        float(expected["brand_coverage_pct"]),
    )

    category_metric = metric_row(readiness, iso_alpha2, "Category tags")
    checker.int(
        f"{iso_alpha2} readiness category records",
        category_metric["records_with_field"],
        tagged,
    )
    checker.int(
        f"{iso_alpha2} readiness country records",
        category_metric["country_records"],
        rows,
    )
    checker.pct(
        f"{iso_alpha2} readiness category coverage pct",
        category_metric["coverage_pct"],
        float(expected["coverage_pct"]),
    )

    brand_metric = metric_row(readiness, iso_alpha2, "Exact-approved brand mapping")
    checker.int(
        f"{iso_alpha2} readiness brand records",
        brand_metric["records_with_field"],
        brand,
    )
    checker.pct(
        f"{iso_alpha2} readiness brand coverage pct",
        brand_metric["coverage_pct"],
        float(expected["brand_coverage_pct"]),
    )

    derived = EXPECTED_DERIVED[iso_alpha2]
    checker.equal(
        f"{iso_alpha2} candidate-derived share of all records",
        round(100 * candidate / rows, 2),
        derived["candidate_share"],
    )
    checker.equal(
        f"{iso_alpha2} approved-only share of all records",
        round(100 * approved / rows, 2),
        derived["approved_share"],
    )


def check_audit_headlines(
    summary: pd.DataFrame,
    online: pd.DataFrame,
    checker: Checker,
) -> None:
    primary = summary.loc[summary["analysis_scope"].eq("primary_sample")].iloc[0]
    checker.equal("audit correct assignments", int(primary["correct_assignments"]), 97)
    checker.equal(
        "audit candidate pairs", int(primary["candidate_assignment_pairs"]), 130
    )
    checker.equal(
        "audit incorrect assignments", int(primary["incorrect_assignments"]), 16
    )
    checker.equal(
        "audit ambiguous assignments", int(primary["ambiguous_assignments"]), 8
    )
    checker.equal(
        "audit insufficient-evidence assignments",
        int(primary["insufficient_evidence_assignments"]),
        9,
    )
    checker.equal("audit exact-set matches", int(primary["exact_set_matches"]), 61)
    checker.equal("audit records reviewed", int(primary["records_reviewed"]), 150)
    checker.equal(
        "online supported cases",
        int(online["online_review_status"].eq("researched_supports").sum()),
        30,
    )
    checker.equal(
        "online cases with source URL",
        int(online["source_url"].ne("").sum()),
        36,
    )
    checker.equal(
        "online exact-code matches",
        int(online["identifier_match"].eq("yes").sum()),
        29,
    )


def check_readme_static_strings(checker: Checker) -> None:
    document = README_FILE.read_text(encoding="utf-8")
    static_text = GENERATED_BLOCK_PATTERN.sub("", document)
    for needle in EXPECTED_README_STATIC_STRINGS:
        checker.equal(
            f"README static text contains {needle!r}",
            needle in static_text,
            True,
        )


def main() -> None:
    stage5 = read_csv(STAGE5_FILE)
    scope = read_csv(STAGE6_SCOPE_FILE)
    readiness = read_csv(READINESS_FILE)
    baseline = scope[scope["scenario"] == "baseline"]
    if baseline.empty:
        raise ValueError("No baseline rows found in stage6_country_scope.csv")

    checker = Checker()

    snapshot_hashes = set(stage5["snapshot_sha256"]) | set(baseline["snapshot_sha256"])
    checker.equal(
        "snapshot_sha256 consistent across stage5 and stage6 scope",
        len(snapshot_hashes),
        1,
    )

    for iso_alpha2, expected in EXPECTED_HEADLINES.items():
        check_country(iso_alpha2, expected, stage5, baseline, readiness, checker)

    audit_summary = read_csv(SEMANTIC_AUDIT_SUMMARY_FILE)
    online_audit = read_csv(ONLINE_AUDIT_FILE)
    check_audit_headlines(audit_summary, online_audit, checker)
    check_readme_static_strings(checker)

    if checker.failures:
        print(
            f"Headline-number check FAILED ({len(checker.failures)} of "
            f"{checker.count} assertions failed):",
            file=sys.stderr,
        )
        for failure in checker.failures:
            print(f"  - {failure}", file=sys.stderr)
        raise SystemExit(1)

    print(
        f"Headline-number check OK: {checker.count} assertions passed for "
        f"{len(EXPECTED_HEADLINES)} countries."
    )


if __name__ == "__main__":
    main()
