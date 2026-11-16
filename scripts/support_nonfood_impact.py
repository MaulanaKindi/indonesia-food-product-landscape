"""support nonfood impact helpers."""

import duckdb
import pandas as pd
from support_nonfood_config import (
    COUNTRY_PROFILE_FILE,
    ISO_REFERENCE_FILE,
    csv_rows,
)


def country_impact(
    connection: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    iso_rows = csv_rows(ISO_REFERENCE_FILE)
    iso_names = {
        row["iso_alpha2"]: row.get("country_name", row.get("name", ""))
        for row in iso_rows
    }
    baseline = pd.read_csv(
        COUNTRY_PROFILE_FILE,
        dtype={"iso_alpha2": str, "country_name": str},
        keep_default_na=False,
    )
    if len(baseline) != 237 or baseline["iso_alpha2"].nunique() != 237:
        raise ValueError(
            "Normalized country baseline must contain 237 unique ISO units; "
            f"found {len(baseline)} rows and {baseline['iso_alpha2'].nunique()} units."
        )
    shortlisted = baseline.loc[baseline["record_count"].astype(int) >= 1_000]
    if len(shortlisted) != 107:
        raise ValueError(
            "The 1,000-record baseline must contain 107 shortlisted ISO units; "
            f"found {len(shortlisted)}."
        )
    if "ID" not in set(baseline["iso_alpha2"]):
        raise ValueError("Indonesia (ID) is missing from normalized country profile.")
    iso_codes = sorted(baseline["iso_alpha2"].tolist())
    observed = connection.execute(
        """
        SELECT
            assignment.iso_alpha2,
            COUNT(*) AS total_records,
            COUNT(*) FILTER (
                WHERE records.strongest_class = 'A_contributor_flag'
            ) AS class_a_records,
            COUNT(*) FILTER (
                WHERE records.strongest_class = 'B_reviewed_exclusion'
            ) AS class_b_records,
            COUNT(*) FILTER (
                WHERE records.strongest_class = 'C_pattern_candidate'
            ) AS class_c_records,
            COUNT(*) FILTER (WHERE records.has_category_tags)
                AS records_with_categories_tags
        FROM country_record_assignments AS assignment
        JOIN record_flags AS records USING (record_id)
        GROUP BY assignment.iso_alpha2
        """
    ).fetchdf()
    observed_by_iso = {
        row["iso_alpha2"]: row for row in observed.to_dict(orient="records")
    }
    baseline_by_iso = {
        row["iso_alpha2"]: int(row["record_count"])
        for row in baseline.to_dict(orient="records")
    }
    if set(iso_codes) != set(baseline_by_iso):
        raise ValueError("Normalized country profile ISO keys are inconsistent.")
    if set(observed_by_iso) != set(baseline_by_iso):
        raise ValueError(
            "Country audit and normalized profile contain different ISO-unit sets."
        )

    output = []
    for iso in iso_codes:
        metric = observed_by_iso.get(iso)
        count = int(metric["total_records"]) if metric else 0
        expected = baseline_by_iso[iso]
        if count != expected:
            raise ValueError(
                "Country record reconciliation failed for "
                f"{iso} ({baseline.loc[baseline.iso_alpha2.eq(iso), 'country_name'].iloc[0]}): "
                f"audit={count:,}, normalized_country_profile={expected:,}."
            )
        class_a = int(metric["class_a_records"]) if metric else 0
        class_b = int(metric["class_b_records"]) if metric else 0
        class_c = int(metric["class_c_records"]) if metric else 0
        category_records = int(metric["records_with_categories_tags"]) if metric else 0
        flagged = class_a + class_b + class_c
        output.append(
            {
                "iso_alpha2": iso,
                "country_name": baseline.loc[
                    baseline.iso_alpha2.eq(iso), "country_name"
                ].iloc[0]
                or iso_names.get(iso, ""),
                "total_records": count,
                "class_a_records": class_a,
                "class_b_records": class_b,
                "class_c_records": class_c,
                "flagged_abc_records": flagged,
                "flagged_abc_share_of_total_records": (
                    flagged / count if count else 0.0
                ),
                "records_with_categories_tags": category_records,
                "categories_tags_share_of_total_records": (
                    category_records / count if count else 0.0
                ),
                "normalized_profile_record_count": expected,
                "reconciles_to_normalized_profile": "Y",
            }
        )
    return pd.DataFrame(output)


def signal_validation(connection: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    groups = [
        "A_contributor_flag",
        "B_reviewed_exclusion",
        "C_pattern_candidate",
        "D_food_confirming",
        "unflagged",
    ]
    output = []
    for scope, iso_clause in (
        ("all_records", ""),
        ("ID", "AND country.iso_alpha2 = 'ID'"),
    ):
        for group in groups:
            if scope == "ID":
                if not country_exists(connection, "ID"):
                    raise ValueError(
                        "Indonesia (ID) is missing from country assignments."
                    )
                query = f"""
                    SELECT
                        COUNT(*) AS rows,
                        COUNT(DISTINCT records.code) AS distinct_codes,
                        COUNT(*) FILTER (WHERE records.nova_group IS NOT NULL)
                            AS nova_group_rows,
                        COUNT(*) FILTER (
                            WHERE lower(records.nutriscore_grade)
                                IN ('a', 'b', 'c', 'd', 'e')
                        ) AS nutriscore_a_e_rows,
                        COUNT(*) FILTER (WHERE records.ingredients_n > 0)
                            AS ingredients_positive_rows,
                        COUNT(*) FILTER (WHERE records.has_food_group_tags)
                            AS food_groups_tag_rows
                    FROM country_record_assignments AS country
                    JOIN record_flags AS records USING (record_id)
                    WHERE records.strongest_class = ?
                    {iso_clause}
                """
                params = [group]
            else:
                query = """
                    SELECT
                        COUNT(*) AS rows,
                        COUNT(DISTINCT code) AS distinct_codes,
                        COUNT(*) FILTER (WHERE nova_group IS NOT NULL)
                            AS nova_group_rows,
                        COUNT(*) FILTER (
                            WHERE lower(nutriscore_grade) IN ('a', 'b', 'c', 'd', 'e')
                        ) AS nutriscore_a_e_rows,
                        COUNT(*) FILTER (WHERE ingredients_n > 0)
                            AS ingredients_positive_rows,
                        COUNT(*) FILTER (WHERE has_food_group_tags)
                            AS food_groups_tag_rows
                    FROM record_flags
                    WHERE strongest_class = ?
                """
                params = [group]
            metrics = connection.execute(query, params).fetchone()
            assert metrics is not None
            denominator = int(metrics[0])
            output.append(
                {
                    "scope": scope,
                    "strongest_class": group,
                    "rows": denominator,
                    "distinct_codes": int(metrics[1]),
                    "pct_with_nova_group": (
                        int(metrics[2]) / denominator if denominator else 0.0
                    ),
                    "pct_with_nutriscore_grade_a_to_e": (
                        int(metrics[3]) / denominator if denominator else 0.0
                    ),
                    "pct_with_ingredients_n_gt_0": (
                        int(metrics[4]) / denominator if denominator else 0.0
                    ),
                    "pct_with_nonempty_food_groups_tags": (
                        int(metrics[5]) / denominator if denominator else 0.0
                    ),
                }
            )
    return pd.DataFrame(output)


def sensitivity_impact(connection: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    connection.execute(
        """
        CREATE TEMP TABLE sensitivity_records AS
        SELECT
            record_id,
            code,
            has_category_tags,
            (has_a OR has_b) AS has_ab_flag,
            (
                (has_a OR has_b)
                AND nova_group IS NOT NULL
                AND lower(nutriscore_grade) IN ('a', 'b', 'c', 'd', 'e')
                AND ingredients_n >= 2
            ) AS has_strong_food_signals
        FROM record_flags
        """
    )
    connection.execute(
        """
        CREATE TEMP TABLE sensitivity_scenarios AS
        SELECT record_id, code, has_category_tags, has_ab_flag,
            has_strong_food_signals, 'baseline' AS scenario
        FROM sensitivity_records
        UNION ALL
        SELECT record_id, code, has_category_tags, has_ab_flag,
            has_strong_food_signals, 'exclude_all_A_B' AS scenario
        FROM sensitivity_records
        WHERE NOT has_ab_flag
        UNION ALL
        SELECT record_id, code, has_category_tags, has_ab_flag,
            has_strong_food_signals,
            'exclude_A_B_except_strong_food_signals' AS scenario
        FROM sensitivity_records
        WHERE NOT has_ab_flag OR has_strong_food_signals
        """
    )

    overall = connection.execute(
        """
        WITH scenario_totals AS (
            SELECT
                scenario,
                COUNT(*) AS included_rows,
                COUNT(DISTINCT code) AS included_distinct_codes,
                COUNT(*) FILTER (WHERE has_category_tags)
                    AS included_rows_with_categories_tags,
                COUNT(*) FILTER (WHERE has_ab_flag)
                    AS included_rows_with_A_B_flags,
                COUNT(*) FILTER (
                    WHERE has_ab_flag AND has_strong_food_signals
                ) AS retained_A_B_rows_with_strong_food_signals
            FROM sensitivity_scenarios
            GROUP BY scenario
        ),
        baseline AS (
            SELECT
                COUNT(*) AS baseline_rows,
                COUNT(DISTINCT code) AS baseline_distinct_codes
            FROM record_flags
        )
        SELECT
            totals.*,
            baseline.baseline_rows,
            baseline.baseline_distinct_codes,
            baseline.baseline_rows - totals.included_rows AS excluded_rows,
            baseline.baseline_distinct_codes
                - totals.included_distinct_codes
                AS net_distinct_code_reduction,
            totals.included_rows_with_categories_tags::DOUBLE
                / nullif(totals.included_rows, 0)
                AS categories_tags_coverage_of_included_rows
        FROM scenario_totals AS totals
        CROSS JOIN baseline
        """
    ).fetchdf()
    overall["geography_level"] = "overall"
    overall["iso_alpha2"] = ""
    overall["country_name"] = ""

    country = connection.execute(
        """
        WITH scenario_totals AS (
            SELECT
                assignment.iso_alpha2,
                mapping.country_name,
                scenario.scenario,
                COUNT(*) AS included_rows,
                COUNT(DISTINCT scenario.code) AS included_distinct_codes,
                COUNT(*) FILTER (WHERE scenario.has_category_tags)
                    AS included_rows_with_categories_tags,
                COUNT(*) FILTER (WHERE scenario.has_ab_flag)
                    AS included_rows_with_A_B_flags,
                COUNT(*) FILTER (
                    WHERE scenario.has_ab_flag
                        AND scenario.has_strong_food_signals
                ) AS retained_A_B_rows_with_strong_food_signals
            FROM sensitivity_scenarios AS scenario
            JOIN country_record_assignments AS assignment
                USING (record_id)
            JOIN (
                SELECT DISTINCT iso_alpha2, country_name
                FROM approved_country_tags
            ) AS mapping
                ON mapping.iso_alpha2 = assignment.iso_alpha2
            GROUP BY
                assignment.iso_alpha2,
                mapping.country_name,
                scenario.scenario
        ),
        baseline AS (
            SELECT
                iso_alpha2,
                included_rows AS baseline_rows,
                included_distinct_codes AS baseline_distinct_codes
            FROM scenario_totals
            WHERE scenario = 'baseline'
        )
        SELECT
            totals.scenario,
            totals.iso_alpha2,
            totals.country_name,
            totals.included_rows,
            totals.included_distinct_codes,
            totals.included_rows_with_categories_tags,
            totals.included_rows_with_A_B_flags,
            totals.retained_A_B_rows_with_strong_food_signals,
            baseline.baseline_rows,
            baseline.baseline_distinct_codes,
            baseline.baseline_rows - totals.included_rows AS excluded_rows,
            baseline.baseline_distinct_codes
                - totals.included_distinct_codes
                AS net_distinct_code_reduction,
            totals.included_rows_with_categories_tags::DOUBLE
                / nullif(totals.included_rows, 0)
                AS categories_tags_coverage_of_included_rows
        FROM scenario_totals AS totals
        JOIN baseline USING (iso_alpha2)
        """
    ).fetchdf()
    country["geography_level"] = "country_iso"

    baseline_country = country[country["scenario"].eq("baseline")].set_index(
        "iso_alpha2"
    )
    normalized = pd.read_csv(
        COUNTRY_PROFILE_FILE,
        dtype={"iso_alpha2": str},
        keep_default_na=False,
    ).set_index("iso_alpha2")
    if set(baseline_country.index) != set(normalized.index):
        raise ValueError(
            "Sensitivity country baseline ISO units do not match the normalized profile."
        )
    mismatches = [
        iso
        for iso in normalized.index
        if int(baseline_country.loc[iso, "included_rows"])
        != int(normalized.loc[iso, "record_count"])
    ]
    if mismatches:
        raise ValueError(
            "Sensitivity baseline does not reconcile to normalized country profile: "
            f"{mismatches[:10]}"
        )

    combined = pd.concat([overall, country], ignore_index=True, sort=False)
    combined["reconciles_to_normalized_profile"] = ""
    combined.loc[
        combined["geography_level"].eq("country_iso")
        & combined["scenario"].eq("baseline"),
        "reconciles_to_normalized_profile",
    ] = "Y"
    combined.loc[
        combined["geography_level"].eq("overall") & combined["scenario"].eq("baseline"),
        "reconciles_to_normalized_profile",
    ] = "Y"
    return combined


def country_exists(connection: duckdb.DuckDBPyConnection, iso: str) -> bool:
    row = connection.execute(
        "SELECT COUNT(*) FROM country_record_assignments WHERE iso_alpha2 = ?",
        [iso],
    ).fetchone()
    assert row is not None
    return row[0] > 0
