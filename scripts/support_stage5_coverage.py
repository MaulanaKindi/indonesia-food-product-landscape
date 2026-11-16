"""Stage 5 readiness and coverage diagnostics."""

from pathlib import Path

import duckdb
import pandas as pd


def build_source_tag_coverage(
    connection: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    return connection.execute(
        """
        WITH country_totals AS (
            SELECT iso_alpha2, COUNT(*) AS country_records
            FROM record_country
            GROUP BY iso_alpha2
        ),
        tag_rows AS (
            SELECT
                country.iso_alpha2,
                country.source_record_id,
                source_tag.tag
            FROM record_country AS country
            JOIN source_product_record AS record USING (source_record_id),
            UNNEST(list_distinct(record.data_sources_tags)) AS source_tag(tag)
            WHERE NULLIF(trim(source_tag.tag), '') IS NOT NULL
        ),
        tag_counts AS (
            SELECT
                tag_rows.iso_alpha2,
                tag_rows.tag AS data_source_tag,
                COUNT(DISTINCT tag_rows.source_record_id) AS tagged_records,
                COUNT(DISTINCT tag_rows.source_record_id) FILTER (
                    WHERE EXISTS (
                        SELECT 1
                        FROM record_category_tag AS category
                        WHERE category.source_record_id = tag_rows.source_record_id
                    )
                ) AS category_tagged_records
            FROM tag_rows
            GROUP BY tag_rows.iso_alpha2, tag_rows.tag
        ),
        ranked AS (
            SELECT *,
                   row_number() OVER (
                       PARTITION BY iso_alpha2
                       ORDER BY tagged_records DESC, data_source_tag
                   ) AS source_rank
            FROM tag_counts
        )
        SELECT
            ranked.iso_alpha2,
            ranked.data_source_tag,
            ranked.source_rank,
            ranked.tagged_records,
            totals.country_records,
            round(100.0 * ranked.tagged_records / totals.country_records, 4)
                AS share_of_country_records_pct,
            ranked.category_tagged_records,
            round(
                100.0 * ranked.category_tagged_records
                    / NULLIF(ranked.tagged_records, 0),
                4
            ) AS category_tag_coverage_pct
        FROM ranked
        JOIN country_totals AS totals USING (iso_alpha2)
        WHERE ranked.source_rank <= 10
        ORDER BY ranked.iso_alpha2, ranked.source_rank
        """
    ).fetchdf()


def build_country_code_overlap(
    connection: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    return connection.execute(
        """
        WITH country_codes AS (
            SELECT DISTINCT
                country.iso_alpha2,
                record.code
            FROM record_country AS country
            JOIN source_product_record AS record USING (source_record_id)
            WHERE NULLIF(trim(record.code), '') IS NOT NULL
        ),
        country_sizes AS (
            SELECT iso_alpha2, COUNT(*) AS distinct_codes
            FROM country_codes
            GROUP BY iso_alpha2
        ),
        intersections AS (
            SELECT
                left_side.iso_alpha2 AS country_a,
                right_side.iso_alpha2 AS country_b,
                COUNT(*) AS shared_codes
            FROM country_codes AS left_side
            JOIN country_codes AS right_side
                ON left_side.code = right_side.code
               AND left_side.iso_alpha2 < right_side.iso_alpha2
            GROUP BY left_side.iso_alpha2, right_side.iso_alpha2
        ),
        country_pairs AS (
            SELECT
                left_side.iso_alpha2 AS country_a,
                right_side.iso_alpha2 AS country_b
            FROM country_sizes AS left_side
            CROSS JOIN country_sizes AS right_side
            WHERE left_side.iso_alpha2 < right_side.iso_alpha2
        ),
        shared_source_records AS (
            SELECT
                left_side.iso_alpha2 AS country_a,
                right_side.iso_alpha2 AS country_b,
                COUNT(DISTINCT left_side.source_record_id) AS shared_source_record_ids
            FROM record_country AS left_side
            JOIN record_country AS right_side
                ON left_side.source_record_id = right_side.source_record_id
               AND left_side.iso_alpha2 < right_side.iso_alpha2
            GROUP BY left_side.iso_alpha2, right_side.iso_alpha2
        )
        SELECT
            pairs.country_a,
            pairs.country_b,
            COALESCE(intersection.shared_codes, 0) AS shared_codes,
            COALESCE(source.shared_source_record_ids, 0)
                AS shared_source_record_ids,
            size_a.distinct_codes AS country_a_distinct_codes,
            size_b.distinct_codes AS country_b_distinct_codes,
            COALESCE(intersection.shared_codes, 0)
                / (size_a.distinct_codes + size_b.distinct_codes
                   - COALESCE(intersection.shared_codes, 0))::DOUBLE
                AS jaccard_index
        FROM country_pairs AS pairs
        JOIN country_sizes AS size_a ON pairs.country_a = size_a.iso_alpha2
        JOIN country_sizes AS size_b ON pairs.country_b = size_b.iso_alpha2
        LEFT JOIN intersections AS intersection
            USING (country_a, country_b)
        LEFT JOIN shared_source_records AS source
            USING (country_a, country_b)
        ORDER BY pairs.country_a, pairs.country_b
        """
    ).fetchdf()


def build_food_groups_crosscheck(
    connection: duckdb.DuckDBPyConnection,
    crosswalk_file: Path,
) -> pd.DataFrame:
    crosswalk = pd.read_csv(crosswalk_file, dtype=str, keep_default_na=False)
    required_columns = {
        "food_group_tag",
        "reporting_group_id",
        "crosswalk_status",
        "mapping_basis",
    }
    if not required_columns.issubset(crosswalk.columns):
        raise ValueError(
            f"Food-group diagnostic crosswalk is malformed: {crosswalk_file}"
        )
    if crosswalk["food_group_tag"].duplicated().any():
        raise ValueError(
            f"Food-group diagnostic crosswalk has duplicate tags: {crosswalk_file}"
        )
    if not crosswalk["crosswalk_status"].eq("diagnostic_only").all():
        raise ValueError("Food-group crosswalk must remain diagnostic-only.")
    valid_groups = {
        row[0]
        for row in connection.execute(
            "SELECT reporting_group_id FROM reporting_group"
        ).fetchall()
    }
    invalid_groups = set(crosswalk["reporting_group_id"]) - valid_groups
    if invalid_groups:
        raise ValueError(
            "Food-group diagnostic crosswalk contains unknown reporting groups: "
            f"{sorted(invalid_groups)}"
        )
    connection.register("food_group_diagnostic_crosswalk", crosswalk)
    return connection.execute(
        """
        WITH country_records AS MATERIALIZED (
            SELECT
                country.iso_alpha2,
                country.source_record_id,
                EXISTS (
                    SELECT 1
                    FROM UNNEST(list_distinct(record.food_groups_tags))
                        AS food_group_tag(tag)
                    WHERE NULLIF(trim(food_group_tag.tag), '') IS NOT NULL
                ) AS has_food_group_tags,
                record.food_groups_tags
            FROM record_country AS country
            JOIN source_product_record AS record USING (source_record_id)
        ),
        food_group_assignments AS (
            SELECT DISTINCT
                record.iso_alpha2,
                record.source_record_id,
                crosswalk.reporting_group_id
            FROM country_records AS record,
            UNNEST(list_distinct(record.food_groups_tags))
                AS food_group_tag(tag)
            JOIN food_group_diagnostic_crosswalk AS crosswalk
                ON food_group_tag.tag = crosswalk.food_group_tag
            WHERE crosswalk.crosswalk_status = 'diagnostic_only'
        ),
        candidate_assignments AS (
            SELECT DISTINCT
                country.iso_alpha2,
                category.source_record_id,
                candidate.reporting_group_id
            FROM record_country AS country
            JOIN record_category_tag AS category USING (source_record_id)
            JOIN category_tag_group_candidate AS candidate
                USING (source_category_tag)
        ),
        record_group_sets AS (
            SELECT
                record.iso_alpha2,
                record.source_record_id,
                record.has_food_group_tags,
                COALESCE(
                    list_sort(
                        list(DISTINCT food.reporting_group_id)
                            FILTER (WHERE food.reporting_group_id IS NOT NULL)
                    ),
                    []::VARCHAR[]
                ) AS food_group_reporting_groups,
                COALESCE(
                    list_sort(
                        list(DISTINCT candidate.reporting_group_id)
                            FILTER (
                                WHERE candidate.reporting_group_id IS NOT NULL
                            )
                    ),
                    []::VARCHAR[]
                ) AS candidate_reporting_groups
            FROM country_records AS record
            LEFT JOIN food_group_assignments AS food
                USING (iso_alpha2, source_record_id)
            LEFT JOIN candidate_assignments AS candidate
                USING (iso_alpha2, source_record_id)
            GROUP BY
                record.iso_alpha2,
                record.source_record_id,
                record.has_food_group_tags
        ),
        comparison AS (
            SELECT *,
                   len(food_group_reporting_groups) > 0 AS has_mapped_food_group,
                   len(candidate_reporting_groups) > 0 AS has_candidate_group,
                   len(food_group_reporting_groups) > 0
                       AND len(candidate_reporting_groups) > 0 AS comparable
            FROM record_group_sets
        )
        SELECT
            iso_alpha2,
            COUNT(*) AS country_records,
            COUNT(*) FILTER (WHERE has_food_group_tags)
                AS records_with_food_group_tags,
            COUNT(*) FILTER (WHERE has_mapped_food_group)
                AS records_with_crosswalked_food_groups,
            COUNT(*) FILTER (WHERE has_candidate_group)
                AS records_with_candidate_groups,
            COUNT(*) FILTER (WHERE comparable) AS records_compared,
            COUNT(*) FILTER (
                WHERE comparable
                  AND food_group_reporting_groups = candidate_reporting_groups
            ) AS exact_group_set_matches,
            COUNT(*) FILTER (
                WHERE comparable
                  AND list_has_any(
                      food_group_reporting_groups,
                      candidate_reporting_groups
                  )
            ) AS records_with_any_group_overlap,
            round(
                100.0 * COUNT(*) FILTER (
                    WHERE comparable
                      AND food_group_reporting_groups = candidate_reporting_groups
                ) / NULLIF(COUNT(*) FILTER (WHERE comparable), 0),
                4
            ) AS exact_group_set_match_pct,
            round(
                100.0 * COUNT(*) FILTER (
                    WHERE comparable
                      AND list_has_any(
                          food_group_reporting_groups,
                          candidate_reporting_groups
                      )
                ) / NULLIF(COUNT(*) FILTER (WHERE comparable), 0),
                4
            ) AS any_group_overlap_pct
        FROM comparison
        GROUP BY iso_alpha2
        ORDER BY iso_alpha2
        """
    ).fetchdf()
