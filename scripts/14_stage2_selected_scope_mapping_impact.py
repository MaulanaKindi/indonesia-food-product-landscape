from pathlib import Path

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "food.parquet"
COUNTRY_MAPPING_FILE = PROJECT_ROOT / "data" / "mappings" / "country_tag_mapping.csv"
MANUAL_DECISIONS_FILE = (
    PROJECT_ROOT
    / "data"
    / "mappings"
    / "category_tag_reporting_group_manual_decisions.csv"
)
CROSSWALK_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "profiling"
    / "category_reporting_group_candidate_crosswalk.csv"
)
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "profiling"
TAG_IMPACT_FILE = OUTPUT_DIR / "stage2_selected_scope_mapping_tag_impact.csv"
COVERAGE_DELTA_FILE = (
    OUTPUT_DIR / "stage2_selected_scope_mapping_coverage_delta.csv"
)

SELECTED_COUNTRIES = ("ID", "MY", "PH", "SG", "TH")
DECISIONS = {
    "en:drinkable-yogurts": "dairy_eggs",
    "en:savory-snacks": "salty_snacks",
    "en:chili-paste": "condiments_fats_spreads",
    "en:juice": "beverages",
    "en:bars-covered-with-chocolate": "sweet_foods_desserts",
}


def main() -> None:
    for path in (
        DATA_FILE,
        COUNTRY_MAPPING_FILE,
        MANUAL_DECISIONS_FILE,
        CROSSWALK_FILE,
    ):
        if not path.is_file():
            raise FileNotFoundError(f"Required input not found: {path}")

    countries = pd.read_csv(
        COUNTRY_MAPPING_FILE,
        dtype=str,
        encoding="utf-8-sig",
        keep_default_na=False,
    )
    countries = countries.loc[
        countries["mapping_status"].eq("approved")
        & countries["iso_alpha2"].isin(SELECTED_COUNTRIES),
        ["source_country_tag", "iso_alpha2", "country_name"],
    ].copy()
    if set(countries["iso_alpha2"]) != set(SELECTED_COUNTRIES):
        raise ValueError(
            "Approved country mappings do not cover the selected scope: "
            f"{sorted(set(SELECTED_COUNTRIES) - set(countries['iso_alpha2']))}"
        )
    country_names = countries[["iso_alpha2", "country_name"]].drop_duplicates()
    if country_names["iso_alpha2"].duplicated().any():
        raise ValueError("Selected ISO codes have conflicting country names.")

    decisions = pd.read_csv(
        MANUAL_DECISIONS_FILE,
        dtype=str,
        keep_default_na=False,
    )
    decisions = decisions.loc[
        decisions["source_category_tag"].isin(DECISIONS)
    ].copy()
    observed_decisions = dict(
        zip(decisions["source_category_tag"], decisions["reporting_group_id"])
    )
    if (
        len(decisions) != len(DECISIONS)
        or not decisions["review_status"].eq("approved").all()
        or observed_decisions != DECISIONS
    ):
        raise ValueError(
            "Selected manual decisions do not match the approved impact scope."
        )

    crosswalk = pd.read_csv(
        CROSSWALK_FILE,
        dtype=str,
        keep_default_na=False,
    )
    required_columns = {
        "source_category_tag",
        "proposed_group_id",
        "comparison_role",
        "assignment_status",
        "taxonomy_match_status",
    }
    missing_columns = required_columns - set(crosswalk.columns)
    if missing_columns:
        raise ValueError(
            f"Candidate crosswalk is missing columns: {sorted(missing_columns)}"
        )
    if crosswalk["source_category_tag"].duplicated().any():
        raise ValueError("Candidate crosswalk contains duplicate source tags.")
    decisions_in_crosswalk = crosswalk.loc[
        crosswalk["source_category_tag"].isin(DECISIONS)
    ].set_index("source_category_tag")
    if set(decisions_in_crosswalk.index) != set(DECISIONS):
        raise ValueError("Candidate crosswalk is missing an approved decision tag.")
    for tag, group_id in DECISIONS.items():
        row = decisions_in_crosswalk.loc[tag]
        if (
            row["assignment_status"] != "manual_group_assignment"
            or row["proposed_group_id"] != group_id
            or row["taxonomy_match_status"] != "not_found_in_pinned_taxonomy"
        ):
            raise ValueError(
                f"Crosswalk decision mismatch for {tag}: "
                f"{row['assignment_status']} / {row['proposed_group_id']}"
            )

    after_map = crosswalk.loc[
        crosswalk["comparison_role"].eq("primary_candidate")
        & crosswalk["proposed_group_id"].ne(""),
        ["source_category_tag", "proposed_group_id"],
    ].copy()
    before_map = after_map.loc[
        ~after_map["source_category_tag"].isin(DECISIONS)
    ].copy()
    approved_after_map = crosswalk.loc[
        crosswalk["assignment_status"].eq("manual_group_assignment")
        & crosswalk["proposed_group_id"].ne(""),
        ["source_category_tag", "proposed_group_id"],
    ].copy()
    approved_before_map = approved_after_map.loc[
        ~approved_after_map["source_category_tag"].isin(DECISIONS)
    ].copy()

    with duckdb.connect() as connection:
        connection.register("approved_country_map", countries)
        connection.register(
            "selected_decisions",
            decisions[["source_category_tag", "reporting_group_id"]],
        )
        connection.register("before_category_map", before_map)
        connection.register("after_category_map", after_map)
        connection.register("approved_before_category_map", approved_before_map)
        connection.register("approved_after_category_map", approved_after_map)
        connection.execute(
            """
            CREATE TEMP TABLE scope_records AS
            SELECT DISTINCT
                source.source_record_id,
                country.iso_alpha2,
                country.country_name,
                source.category_tags
            FROM (
                SELECT
                    ROW_NUMBER() OVER () AS source_record_id,
                    list_filter(
                        list_distinct(categories_tags),
                        lambda value: value IS NOT NULL AND trim(value) <> ''
                    ) AS category_tags,
                    list_filter(
                        list_distinct(countries_tags),
                        lambda value: value IS NOT NULL AND trim(value) <> ''
                    ) AS country_tags
                FROM read_parquet(?)
            ) AS source
            CROSS JOIN UNNEST(source.country_tags)
                AS country_tags(source_country_tag)
            INNER JOIN approved_country_map AS country
                ON country_tags.source_country_tag = country.source_country_tag
            """,
            [str(DATA_FILE)],
        )
        tag_impact = connection.execute(
            """
            WITH tag_counts AS (
                SELECT
                    records.iso_alpha2,
                    category_tags.source_category_tag,
                    COUNT(DISTINCT records.source_record_id)
                        AS source_rows_with_tag
                FROM scope_records AS records
                CROSS JOIN UNNEST(records.category_tags)
                    AS category_tags(source_category_tag)
                INNER JOIN selected_decisions AS selected
                    ON category_tags.source_category_tag =
                        selected.source_category_tag
                GROUP BY 1, 2
            )
            SELECT
                countries.iso_alpha2,
                countries.country_name,
                decisions.source_category_tag,
                decisions.reporting_group_id,
                COALESCE(tag_counts.source_rows_with_tag, 0)
                    AS source_rows_with_tag
            FROM (
                SELECT DISTINCT iso_alpha2, country_name
                FROM approved_country_map
            ) AS countries
            CROSS JOIN selected_decisions AS decisions
            LEFT JOIN tag_counts
                USING (iso_alpha2, source_category_tag)
            ORDER BY countries.iso_alpha2, decisions.source_category_tag
            """,
        ).fetchdf()

        overall_metrics = []
        group_metrics = []
        group_ids = sorted(
            set(after_map["proposed_group_id"])
            | set(approved_after_map["proposed_group_id"])
        )
        for basis, label, map_name in (
            ("candidate_derived", "before", "before_category_map"),
            ("candidate_derived", "after", "after_category_map"),
            ("approved_only", "before", "approved_before_category_map"),
            ("approved_only", "after", "approved_after_category_map"),
        ):
            assignments = connection.execute(
                f"""
                SELECT DISTINCT
                    records.source_record_id,
                    records.iso_alpha2,
                    category_map.proposed_group_id
                FROM scope_records AS records
                CROSS JOIN UNNEST(records.category_tags)
                    AS category_tags(source_category_tag)
                INNER JOIN {map_name} AS category_map
                    ON category_tags.source_category_tag =
                        category_map.source_category_tag
                """
            ).fetchdf()
            assignment_counts = (
                assignments.groupby(["iso_alpha2", "source_record_id"])
                ["proposed_group_id"]
                .nunique()
                .rename("primary_group_count")
                .reset_index()
            )
            country_metrics = connection.execute(
                """
                SELECT
                    iso_alpha2,
                    country_name,
                    COUNT(*) AS source_rows,
                    COUNT(*) FILTER (
                        WHERE len(category_tags) > 0
                    ) AS category_tagged_rows
                FROM scope_records
                GROUP BY 1, 2
                """
            ).fetchdf()
            country_group_counts = assignments.groupby("iso_alpha2")[
                "source_record_id"
            ].nunique()
            country_overlap = assignment_counts.loc[
                assignment_counts["primary_group_count"].gt(1)
            ].groupby("iso_alpha2")["source_record_id"].nunique()
            country_metrics["records_with_primary_group"] = (
                country_metrics["iso_alpha2"]
                .map(country_group_counts)
                .fillna(0)
                .astype("int64")
            )
            country_metrics["records_with_multiple_primary_groups"] = (
                country_metrics["iso_alpha2"]
                .map(country_overlap)
                .fillna(0)
                .astype("int64")
            )
            country_metrics.insert(1, "mapping_version", label)
            country_metrics.insert(1, "mapping_basis", basis)
            overall_metrics.append(country_metrics)

            if not assignments.empty:
                counts = (
                    assignments.groupby(
                        ["iso_alpha2", "proposed_group_id"]
                    )["source_record_id"]
                    .nunique()
                    .to_dict()
                )
            else:
                counts = {}
            for country_code in SELECTED_COUNTRIES:
                for group_id in group_ids:
                    group_metrics.append(
                        {
                            "iso_alpha2": country_code,
                            "mapping_basis": basis,
                            "mapping_version": label,
                            "metric": "records_in_primary_group",
                            "group_id": group_id,
                            "value": counts.get((country_code, group_id), 0),
                        }
                    )

    overall = pd.concat(overall_metrics, ignore_index=True)
    overall_long = overall.melt(
        id_vars=[
            "iso_alpha2",
            "country_name",
            "mapping_basis",
            "mapping_version",
        ],
        value_vars=[
            "source_rows",
            "category_tagged_rows",
            "records_with_primary_group",
            "records_with_multiple_primary_groups",
        ],
        var_name="metric",
        value_name="value",
    )
    groups_long = pd.DataFrame(group_metrics)
    long_metrics = pd.concat(
        [
            overall_long,
            groups_long.assign(
                country_name=groups_long["iso_alpha2"].map(
                    country_names.set_index("iso_alpha2")["country_name"]
                )
            )[
                [
                    "iso_alpha2",
                    "country_name",
                    "mapping_basis",
                    "mapping_version",
                    "metric",
                    "group_id",
                    "value",
                ]
            ],
        ],
        ignore_index=True,
    )
    if "group_id" not in long_metrics:
        long_metrics["group_id"] = ""
    long_metrics["group_id"] = long_metrics["group_id"].fillna("")
    coverage_delta = (
        long_metrics.pivot(
            index=[
                "iso_alpha2",
                "country_name",
                "mapping_basis",
                "metric",
                "group_id",
            ],
            columns="mapping_version",
            values="value",
        )
        .reset_index()
        .rename_axis(columns=None)
    )
    coverage_delta["before"] = coverage_delta["before"].fillna(0).astype("int64")
    coverage_delta["after"] = coverage_delta["after"].fillna(0).astype("int64")
    coverage_delta["change"] = coverage_delta["after"] - coverage_delta["before"]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tag_impact.to_csv(TAG_IMPACT_FILE, index=False)
    coverage_delta.to_csv(COVERAGE_DELTA_FILE, index=False)
    print("Selected-scope Stage 2 mapping impact audit completed.")
    print(f"Tag-level evidence: {TAG_IMPACT_FILE}")
    print(f"Before/after coverage metrics: {COVERAGE_DELTA_FILE}")
    print(
        "Scope: five owner-approved category decisions across "
        f"{', '.join(SELECTED_COUNTRIES)}."
    )


if __name__ == "__main__":
    main()
