"""Validate exact group evidence and summarize country-level coverage."""

from pathlib import Path

import pandas as pd
from support_duckdb_runtime import connect_duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "food.parquet"


def build_country_coverage(
    crosswalk: pd.DataFrame,
    country_mapping: pd.DataFrame,
    framework: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    approved_countries = country_mapping.loc[
        country_mapping["mapping_status"].eq("approved")
    ].copy()
    incomplete_approved = approved_countries[
        approved_countries[["iso_alpha2", "country_name"]].eq("").any(axis=1)
    ]
    if not incomplete_approved.empty:
        raise ValueError(
            "Approved country mappings must have an ISO code and name: "
            f"{incomplete_approved['source_country_tag'].tolist()}"
        )

    category_map = crosswalk.loc[
        crosswalk["proposed_group_id"].ne(""),
        [
            "source_category_tag",
            "proposed_group_id",
            "assignment_status",
            "comparison_role",
        ],
    ].copy()
    if category_map["source_category_tag"].duplicated().any():
        raise ValueError("Candidate category crosswalk contains duplicate source tags.")

    group_labels = framework[["group_id", "reporting_group", "display_order"]].copy()
    with connect_duckdb() as connection:
        connection.register("candidate_category_map", category_map)
        connection.register("approved_country_map", approved_countries)
        connection.register("reporting_group_framework", group_labels)
        connection.execute(
            """
            CREATE TEMP TABLE source_records AS
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
            """,
            [str(DATA_FILE)],
        )
        coverage = connection.execute(
            """
            WITH country_records AS (
                SELECT DISTINCT
                    source.source_record_id,
                    country.iso_alpha2,
                    country.country_name,
                    len(source.category_tags) > 0 AS has_category_tags
                FROM source_records AS source
                CROSS JOIN UNNEST(source.country_tags)
                    AS country_tags(source_country_tag)
                INNER JOIN approved_country_map AS country
                    ON country_tags.source_country_tag = country.source_country_tag
            ),
            record_group_assignments AS (
                SELECT DISTINCT
                    country_records.source_record_id,
                    country_records.iso_alpha2,
                    country_records.country_name,
                    category_map.proposed_group_id,
                    category_map.assignment_status,
                    category_map.comparison_role
                FROM country_records
                INNER JOIN source_records AS source
                    USING (source_record_id)
                CROSS JOIN UNNEST(source.category_tags)
                    AS category_tags(source_category_tag)
                INNER JOIN candidate_category_map AS category_map
                    ON category_tags.source_category_tag =
                        category_map.source_category_tag
            ),
            country_totals AS (
                SELECT
                    iso_alpha2,
                    country_name,
                    COUNT(*) AS country_source_records,
                    COUNT(*) FILTER (
                        WHERE has_category_tags
                    ) AS country_records_with_category_tags
                FROM country_records
                GROUP BY iso_alpha2, country_name
            ),
            country_candidate_totals AS (
                SELECT
                    iso_alpha2,
                    COUNT(DISTINCT source_record_id)
                        AS records_with_any_primary_group
                FROM record_group_assignments
                WHERE comparison_role = 'primary_candidate'
                GROUP BY iso_alpha2
            ),
            country_diagnostic_totals AS (
                SELECT
                    iso_alpha2,
                    COUNT(DISTINCT source_record_id)
                        AS records_with_diagnostic_residual
                FROM record_group_assignments
                WHERE assignment_status = 'other_residual_candidate'
                GROUP BY iso_alpha2
            ),
            record_group_counts AS (
                SELECT
                    source_record_id,
                    iso_alpha2,
                    COUNT(DISTINCT proposed_group_id)
                        AS primary_group_count
                FROM record_group_assignments
                WHERE comparison_role = 'primary_candidate'
                GROUP BY source_record_id, iso_alpha2
            ),
            country_overlap AS (
                SELECT
                    iso_alpha2,
                    COUNT(*) FILTER (
                        WHERE primary_group_count > 1
                    ) AS records_with_multiple_primary_groups
                FROM record_group_counts
                GROUP BY iso_alpha2
            ),
            group_counts AS (
                SELECT
                    iso_alpha2,
                    proposed_group_id AS group_id,
                    COUNT(*) AS source_records_in_group
                FROM record_group_assignments
                GROUP BY iso_alpha2, proposed_group_id
            )
            SELECT
                totals.iso_alpha2,
                totals.country_name,
                groups.group_id,
                groups.reporting_group,
                CASE
                    WHEN groups.group_id = 'other_unclassified'
                        THEN 'diagnostic_only'
                    ELSE 'primary_candidate'
                END AS comparison_role,
                totals.country_source_records,
                totals.country_records_with_category_tags,
                COALESCE(candidate_totals.records_with_any_primary_group, 0)
                    AS records_with_any_primary_group,
                COALESCE(diagnostic_totals.records_with_diagnostic_residual, 0)
                    AS records_with_diagnostic_residual,
                COALESCE(group_counts.source_records_in_group, 0)
                    AS source_records_in_group,
                ROUND(
                    100.0 * COALESCE(group_counts.source_records_in_group, 0)
                    / NULLIF(totals.country_source_records, 0),
                    4
                ) AS pct_country_records_in_group,
                ROUND(
                    100.0 * COALESCE(group_counts.source_records_in_group, 0)
                    / NULLIF(totals.country_records_with_category_tags, 0),
                    4
                ) AS pct_category_tagged_records_in_group
            FROM country_totals AS totals
            CROSS JOIN reporting_group_framework AS groups
            LEFT JOIN country_candidate_totals AS candidate_totals
                USING (iso_alpha2)
            LEFT JOIN country_diagnostic_totals AS diagnostic_totals
                USING (iso_alpha2)
            LEFT JOIN group_counts
                ON group_counts.iso_alpha2 = totals.iso_alpha2
                AND group_counts.group_id = groups.group_id
            ORDER BY TRY_CAST(groups.display_order AS INTEGER), totals.iso_alpha2
            """
        ).fetchdf()
        overlap = connection.execute(
            """
            WITH country_records AS (
                SELECT DISTINCT
                    source.source_record_id,
                    country.iso_alpha2,
                    country.country_name,
                    len(source.category_tags) > 0 AS has_category_tags
                FROM source_records AS source
                CROSS JOIN UNNEST(source.country_tags)
                    AS country_tags(source_country_tag)
                INNER JOIN approved_country_map AS country
                    ON country_tags.source_country_tag = country.source_country_tag
            ),
            record_group_assignments AS (
                SELECT DISTINCT
                    country_records.source_record_id,
                    country_records.iso_alpha2,
                    category_map.proposed_group_id,
                    category_map.assignment_status,
                    category_map.comparison_role
                FROM country_records
                INNER JOIN source_records AS source
                    USING (source_record_id)
                CROSS JOIN UNNEST(source.category_tags)
                    AS category_tags(source_category_tag)
                INNER JOIN candidate_category_map AS category_map
                    ON category_tags.source_category_tag =
                        category_map.source_category_tag
            ),
            record_group_counts AS (
                SELECT
                    source_record_id,
                    iso_alpha2,
                    COUNT(DISTINCT proposed_group_id)
                        AS primary_group_count
                FROM record_group_assignments
                WHERE comparison_role = 'primary_candidate'
                GROUP BY source_record_id, iso_alpha2
            ),
            overlap_counts AS (
                SELECT
                    iso_alpha2,
                    COUNT(*) FILTER (
                        WHERE primary_group_count > 1
                    ) AS records_with_multiple_primary_groups
                FROM record_group_counts
                GROUP BY iso_alpha2
            ),
            candidate_counts AS (
                SELECT
                    iso_alpha2,
                    COUNT(DISTINCT source_record_id)
                        AS records_with_any_primary_group
                FROM record_group_assignments
                WHERE comparison_role = 'primary_candidate'
                GROUP BY iso_alpha2
            ),
            diagnostic_counts AS (
                SELECT
                    iso_alpha2,
                    COUNT(DISTINCT source_record_id)
                        AS records_with_diagnostic_residual
                FROM record_group_assignments
                WHERE assignment_status = 'other_residual_candidate'
                GROUP BY iso_alpha2
            )
            SELECT
                country.iso_alpha2,
                country.country_name,
                COUNT(*) AS country_source_records,
                COUNT(*) FILTER (
                    WHERE country.has_category_tags
                ) AS country_records_with_category_tags,
                COALESCE(candidate.records_with_any_primary_group, 0)
                    AS records_with_any_primary_group,
                COALESCE(diagnostic.records_with_diagnostic_residual, 0)
                    AS records_with_diagnostic_residual,
                COALESCE(overlap.records_with_multiple_primary_groups, 0)
                    AS records_with_multiple_primary_groups,
                ROUND(
                    100.0
                    * COALESCE(overlap.records_with_multiple_primary_groups, 0)
                    / NULLIF(
                        COALESCE(candidate.records_with_any_primary_group, 0),
                        0
                    ),
                    4
                ) AS pct_primary_group_records_with_overlap,
                ROUND(
                    100.0
                    * COALESCE(candidate.records_with_any_primary_group, 0)
                    / NULLIF(
                        COUNT(*) FILTER (
                            WHERE country.has_category_tags
                        ),
                        0
                    ),
                    4
                ) AS pct_category_tagged_records_with_primary_group
            FROM country_records AS country
            LEFT JOIN candidate_counts AS candidate
                USING (iso_alpha2)
            LEFT JOIN diagnostic_counts AS diagnostic
                USING (iso_alpha2)
            LEFT JOIN overlap_counts AS overlap
                USING (iso_alpha2)
            GROUP BY
                country.iso_alpha2,
                country.country_name,
                candidate.records_with_any_primary_group,
                diagnostic.records_with_diagnostic_residual,
                overlap.records_with_multiple_primary_groups
            ORDER BY country.iso_alpha2
            """
        ).fetchdf()

    coverage["coverage_unit_note"] = (
        "Source records counted once per country/group; source rows are not "
        "deduplicated by product code. Groups include single-group taxonomy "
        "candidates and approved manual decisions; unresolved multi-group and "
        "unmatched tags are excluded. Other / unclassified is diagnostic only."
    )
    overlap["overlap_unit_note"] = (
        "Primary-group overlap is the share of source records with at least one "
        "primary candidate assigned to more than one primary group. Other / "
        "unclassified residuals are diagnostic only and excluded."
    )
    return coverage, overlap


def validate_manual_group_evidence(
    decisions: pd.DataFrame,
    taxonomy: dict,
    category_profile: pd.DataFrame,
) -> dict[tuple[str, str], int]:
    profile_tags = set(category_profile["source_value"])
    evidence_pairs = []

    for row in decisions.itertuples(index=False):
        supporting_tags = [
            tag.strip() for tag in row.supporting_exact_tags.split("|") if tag.strip()
        ]
        if row.source_category_tag not in taxonomy and not supporting_tags:
            raise ValueError(
                "Manual decisions for tags absent from the pinned taxonomy must "
                f"include exact supporting tags: {row.source_category_tag}"
            )
        for supporting_tag in supporting_tags:
            if supporting_tag not in taxonomy:
                raise ValueError(
                    "Manual decision evidence is not an exact pinned taxonomy "
                    f"node: {supporting_tag}"
                )
            if supporting_tag not in profile_tags:
                raise ValueError(
                    "Manual decision evidence tag is absent from the category "
                    f"profile: {supporting_tag}"
                )
            if supporting_tag == row.source_category_tag:
                raise ValueError(
                    "A source category tag cannot be its own supporting tag: "
                    f"{supporting_tag}"
                )
            evidence_pairs.append(
                {
                    "source_category_tag": row.source_category_tag,
                    "supporting_exact_tag": supporting_tag,
                }
            )

    if not evidence_pairs:
        return {}

    evidence_frame = pd.DataFrame(evidence_pairs)
    with connect_duckdb() as connection:
        connection.register("manual_group_evidence_pairs", evidence_frame)
        cooccurrence = connection.execute(
            """
            SELECT
                evidence.source_category_tag,
                evidence.supporting_exact_tag,
                COUNT(*) AS cooccurring_source_rows
            FROM read_parquet(?) AS source
            CROSS JOIN UNNEST(source.categories_tags) AS observed(source_tag)
            INNER JOIN manual_group_evidence_pairs AS evidence
                ON observed.source_tag = evidence.source_category_tag
            WHERE list_contains(
                source.categories_tags,
                evidence.supporting_exact_tag
            )
            GROUP BY
                evidence.source_category_tag,
                evidence.supporting_exact_tag
            """,
            [str(DATA_FILE)],
        ).fetchdf()

    evidence_counts = {
        (row.source_category_tag, row.supporting_exact_tag): int(
            row.cooccurring_source_rows
        )
        for row in cooccurrence.itertuples(index=False)
    }
    missing_pairs = sorted(
        {
            (
                pair["source_category_tag"],
                pair["supporting_exact_tag"],
            )
            for pair in evidence_pairs
        }
        - set(evidence_counts)
    )
    if missing_pairs:
        raise ValueError(
            "Manual decision evidence tags do not co-occur with their source "
            f"tags in the Parquet: {missing_pairs}"
        )
    return evidence_counts
