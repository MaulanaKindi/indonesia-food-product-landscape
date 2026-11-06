"""Build a compact coverage evidence table for Stage 5 country-peer review."""

import argparse
import csv
from pathlib import Path

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "global_product_landscape_five_country.duckdb"
)
SHORTLIST_FILE = (
    PROJECT_ROOT / "outputs" / "profiling" / "country_comparison_shortlist.csv"
)
CATEGORY_OVERLAP_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "profiling"
    / "category_reporting_group_candidate_country_overlap.csv"
)
NONFOOD_COUNTRY_FILE = (
    PROJECT_ROOT / "outputs" / "profiling" / "nonfood_scope_country_impact.csv"
)
VALIDATION_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "quality"
    / "database_build_validation_five_country.csv"
)
OUTPUT_FILE = (
    PROJECT_ROOT / "outputs" / "profiling" / "stage5_country_peer_evidence.csv"
)
READINESS_OUTPUT = (
    PROJECT_ROOT / "outputs" / "profiling" / "data_readiness_scorecard.csv"
)
CONTRIBUTOR_OUTPUT = (
    PROJECT_ROOT / "outputs" / "profiling" / "contributor_year_diagnostics.csv"
)
YEARLY_OUTPUT = (
    PROJECT_ROOT / "outputs" / "profiling" / "record_creation_year.csv"
)
SOURCE_TAG_OUTPUT = (
    PROJECT_ROOT / "outputs" / "profiling" / "source_tag_coverage.csv"
)
OVERLAP_OUTPUT = (
    PROJECT_ROOT / "outputs" / "profiling" / "country_code_overlap.csv"
)
FOOD_GROUP_CROSSWALK_FILE = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "food_group_reporting_group_diagnostic_crosswalk.csv"
)
FOOD_GROUP_OUTPUT = (
    PROJECT_ROOT / "outputs" / "profiling" / "food_groups_crosscheck.csv"
)
EXPECTED_SNAPSHOT_SHA256 = (
    "DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def validate_inputs(database_file: Path, validation_file: Path) -> None:
    required = (
        database_file,
        SHORTLIST_FILE,
        CATEGORY_OVERLAP_FILE,
        NONFOOD_COUNTRY_FILE,
        validation_file,
        FOOD_GROUP_CROSSWALK_FILE,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Required Stage 5 evidence input missing:\n" + "\n".join(missing))

    checks = read_csv(validation_file)
    if not checks or any(
        row["status"] != "passed"
        or row["actual_value"] != row["expected_value"]
        for row in checks
    ):
        raise ValueError(
            f"Database build validation is not fully passed: {validation_file}"
        )

    shortlist = read_csv(SHORTLIST_FILE)
    if len(shortlist) != 107:
        raise ValueError(
            "Expected the existing 107-unit, 1,000-row screening shortlist; "
            f"found {len(shortlist)} units."
        )
    if len({row["iso_alpha2"] for row in shortlist}) != len(shortlist):
        raise ValueError("Country shortlist contains duplicate ISO units.")


def build_readiness_scorecard(connection: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return connection.execute(
        """
        WITH record_features AS MATERIALIZED (
            SELECT
                country.iso_alpha2,
                record.source_record_id,
                NULLIF(trim(record.brands), '') IS NOT NULL AS has_brand_text,
                EXISTS (
                    SELECT 1
                    FROM record_category_tag AS category
                    WHERE category.source_record_id = record.source_record_id
                ) AS has_category_tags,
                EXISTS (
                    SELECT 1
                    FROM UNNEST(record.ingredients_text)
                        AS ingredient_text(item)
                    WHERE NULLIF(trim(item.text), '') IS NOT NULL
                ) AS has_ingredient_text,
                EXISTS (
                    SELECT 1
                    FROM UNNEST(record.nutriments) AS nutrient(item)
                    WHERE COALESCE(
                        item.value,
                        item."100g",
                        item.serving,
                        item.prepared_value,
                        item.prepared_100g,
                        item.prepared_serving
                    ) IS NOT NULL
                ) AS has_numeric_nutrition,
                upper(trim(COALESCE(record.nutriscore_grade, '')))
                    IN ('A', 'B', 'C', 'D', 'E') AS has_valid_nutriscore,
                (
                    NULLIF(trim(record.packaging), '') IS NOT NULL
                    OR COALESCE(len(record.packaging_tags), 0) > 0
                    OR COALESCE(len(record.packagings), 0) > 0
                ) AS has_packaging,
                (
                    NULLIF(trim(record.labels), '') IS NOT NULL
                    OR COALESCE(len(record.labels_tags), 0) > 0
                ) AS has_label,
                EXISTS (
                    SELECT 1
                    FROM record_brand_source_value AS brand
                    JOIN brand_name_mapping AS mapping
                        ON brand.source_brand_name = mapping.source_brand_name
                    WHERE brand.source_record_id = record.source_record_id
                      AND mapping.review_status = 'approved'
                ) AS has_exact_approved_brand_mapping
            FROM record_country AS country
            JOIN source_product_record AS record
                USING (source_record_id)
        ),
        readiness AS (
            SELECT
                iso_alpha2,
                COUNT(*) AS country_records,
                COUNT(*) FILTER (WHERE has_brand_text) AS brand_text_records,
                COUNT(*) FILTER (WHERE has_category_tags) AS category_tag_records,
                COUNT(*) FILTER (WHERE has_ingredient_text) AS ingredient_text_records,
                COUNT(*) FILTER (WHERE has_numeric_nutrition) AS nutrition_records,
                COUNT(*) FILTER (WHERE has_valid_nutriscore) AS nutriscore_records,
                COUNT(*) FILTER (WHERE has_packaging) AS packaging_records,
                COUNT(*) FILTER (WHERE has_label) AS label_records,
                COUNT(*) FILTER (WHERE has_exact_approved_brand_mapping)
                    AS exact_approved_brand_records
            FROM record_features
            GROUP BY iso_alpha2
        )
        SELECT iso_alpha2, metric, records_with_field, country_records,
               round(100.0 * records_with_field / country_records, 4)
                   AS coverage_pct
        FROM readiness
        CROSS JOIN LATERAL (
            VALUES
                ('Brand text', brand_text_records),
                ('Category tags', category_tag_records),
                ('Ingredient text', ingredient_text_records),
                ('Numeric nutrition value', nutrition_records),
                ('Valid Nutri-Score (A-E)', nutriscore_records),
                ('Packaging information', packaging_records),
                ('Label information', label_records),
                ('Exact-approved brand mapping', exact_approved_brand_records)
        ) AS metric_rows(metric, records_with_field)
        ORDER BY iso_alpha2, metric
        """
    ).fetchdf()


def build_contributor_diagnostics(
    connection: duckdb.DuckDBPyConnection,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary = connection.execute(
        """
        WITH country_records AS MATERIALIZED (
            SELECT country.iso_alpha2, record.source_record_id,
                   record.creator, record.created_t
            FROM record_country AS country
            JOIN source_product_record AS record USING (source_record_id)
        ),
        country_totals AS (
            SELECT iso_alpha2, COUNT(*) AS country_records
            FROM country_records
            GROUP BY iso_alpha2
        ),
        creator_counts AS (
            SELECT iso_alpha2, creator, COUNT(*) AS creator_records
            FROM country_records
            WHERE NULLIF(trim(creator), '') IS NOT NULL
            GROUP BY iso_alpha2, creator
        ),
        creator_ranked AS (
            SELECT *,
                   row_number() OVER (
                       PARTITION BY iso_alpha2
                       ORDER BY creator_records DESC, creator
                   ) AS creator_rank
            FROM creator_counts
        ),
        creator_segments AS (
            SELECT country.iso_alpha2,
                   CASE
                       WHEN NULLIF(trim(country.creator), '') IS NULL
                           THEN 'missing_creator'
                       WHEN ranked.creator_rank <= 5 THEN 'top_five'
                       ELSE 'other_named'
                   END AS creator_segment,
                   COUNT(*) AS segment_records,
                   COUNT(*) FILTER (
                       WHERE EXISTS (
                           SELECT 1
                           FROM record_category_tag AS category
                           WHERE category.source_record_id = country.source_record_id
                       )
                   ) AS category_tagged_records
            FROM country_records AS country
            LEFT JOIN creator_ranked AS ranked
                ON ranked.iso_alpha2 = country.iso_alpha2
               AND ranked.creator = country.creator
            GROUP BY country.iso_alpha2, creator_segment
        ),
        creator_summary AS (
            SELECT iso_alpha2,
                   COUNT(*) AS unique_creators,
                   SUM(creator_records) FILTER (WHERE creator_rank <= 5)
                       AS top_5_creator_records
            FROM creator_ranked
            GROUP BY iso_alpha2
        ),
        dated_records AS (
            SELECT iso_alpha2, source_record_id,
                   year(to_timestamp(created_t)) AS creation_year,
                   CAST(to_timestamp(created_t) AS DATE) AS creation_date
            FROM country_records
            WHERE created_t BETWEEN 1 AND 4102444800
        ),
        yearly_counts AS (
            SELECT iso_alpha2, creation_year, COUNT(*) AS year_records
            FROM dated_records
            GROUP BY iso_alpha2, creation_year
        ),
        yearly_ranked AS (
            SELECT *,
                   row_number() OVER (
                       PARTITION BY iso_alpha2
                       ORDER BY year_records DESC, creation_year DESC
                   ) AS year_rank
            FROM yearly_counts
        ),
        year_summary AS (
            SELECT iso_alpha2,
                   SUM(year_records) AS valid_year_records,
                   MAX(creation_year) FILTER (WHERE year_rank = 1)
                       AS peak_creation_year,
                   MAX(year_records) FILTER (WHERE year_rank = 1)
                       AS peak_year_records
            FROM yearly_ranked
            GROUP BY iso_alpha2
        ),
        daily_counts AS (
            SELECT iso_alpha2, creation_date, COUNT(*) AS day_records
            FROM dated_records
            GROUP BY iso_alpha2, creation_date
        ),
        daily_summary AS (
            SELECT iso_alpha2, MAX(day_records) AS peak_day_records
            FROM daily_counts
            GROUP BY iso_alpha2
        ),
        creator_day_counts AS (
            SELECT iso_alpha2, creator, creation_date,
                   COUNT(*) AS creator_day_records,
                   COUNT(*) FILTER (
                       WHERE EXISTS (
                           SELECT 1
                           FROM record_category_tag AS category
                           WHERE category.source_record_id = country_records.source_record_id
                       )
                   ) AS category_tagged_records
            FROM country_records
            JOIN dated_records USING (iso_alpha2, source_record_id)
            WHERE NULLIF(trim(creator), '') IS NOT NULL
            GROUP BY iso_alpha2, creator, creation_date
        ),
        creator_day_ranked AS (
            SELECT *, row_number() OVER (
                PARTITION BY iso_alpha2
                ORDER BY creator_day_records DESC, creator, creation_date
            ) AS burst_rank
            FROM creator_day_counts
        ),
        creator_day_summary AS (
            SELECT iso_alpha2,
                   MAX(creator_day_records) FILTER (WHERE burst_rank = 1)
                       AS peak_creator_day_records,
                   MAX(category_tagged_records) FILTER (WHERE burst_rank = 1)
                       AS peak_creator_day_category_records
            FROM creator_day_ranked
            GROUP BY iso_alpha2
        ),
        creator_segment_summary AS (
            SELECT iso_alpha2,
                   MAX(100.0 * category_tagged_records
                       / NULLIF(segment_records, 0))
                       FILTER (WHERE creator_segment = 'top_five')
                       AS top_5_category_tag_coverage_pct,
                   MAX(100.0 * category_tagged_records
                       / NULLIF(segment_records, 0))
                       FILTER (WHERE creator_segment = 'other_named')
                       AS other_named_creator_category_tag_coverage_pct,
                   MAX(100.0 * category_tagged_records
                       / NULLIF(segment_records, 0))
                       FILTER (WHERE creator_segment = 'missing_creator')
                       AS missing_creator_category_tag_coverage_pct
            FROM creator_segments
            GROUP BY iso_alpha2
        )
        SELECT
            totals.iso_alpha2,
            totals.country_records,
            COALESCE(creators.unique_creators, 0) AS unique_creators,
            COALESCE(creators.top_5_creator_records, 0) AS top_5_creator_records,
            round(
                100.0 * COALESCE(creators.top_5_creator_records, 0)
                    / totals.country_records,
                4
            ) AS top_5_creator_share_pct,
            COALESCE(years.valid_year_records, 0) AS valid_year_records,
            years.peak_creation_year,
            COALESCE(years.peak_year_records, 0) AS peak_year_records,
            round(
                100.0 * COALESCE(years.peak_year_records, 0)
                    / NULLIF(years.valid_year_records, 0),
                4
            ) AS peak_year_share_of_dated_records_pct,
            COALESCE(days.peak_day_records, 0) AS peak_day_records,
            round(
                100.0 * COALESCE(days.peak_day_records, 0)
                    / NULLIF(years.valid_year_records, 0),
                4
            ) AS peak_day_share_of_dated_records_pct,
            COALESCE(bursts.peak_creator_day_records, 0)
                AS peak_creator_day_records,
            round(
                100.0 * COALESCE(bursts.peak_creator_day_records, 0)
                    / totals.country_records,
                4
            ) AS peak_creator_day_share_of_country_records_pct,
            round(
                100.0 * COALESCE(bursts.peak_creator_day_category_records, 0)
                    / NULLIF(bursts.peak_creator_day_records, 0),
                4
            ) AS peak_creator_day_category_tag_coverage_pct,
            round(segments.top_5_category_tag_coverage_pct, 4)
                AS top_5_category_tag_coverage_pct,
            round(segments.other_named_creator_category_tag_coverage_pct, 4)
                AS other_named_creator_category_tag_coverage_pct,
            round(segments.missing_creator_category_tag_coverage_pct, 4)
                AS missing_creator_category_tag_coverage_pct
        FROM country_totals AS totals
        LEFT JOIN creator_summary AS creators USING (iso_alpha2)
        LEFT JOIN year_summary AS years USING (iso_alpha2)
        LEFT JOIN daily_summary AS days USING (iso_alpha2)
        LEFT JOIN creator_day_summary AS bursts USING (iso_alpha2)
        LEFT JOIN creator_segment_summary AS segments USING (iso_alpha2)
        ORDER BY totals.iso_alpha2
        """
    ).fetchdf()
    yearly = connection.execute(
        """
        WITH country_records AS MATERIALIZED (
            SELECT country.iso_alpha2, record.source_record_id,
                   record.created_t
            FROM record_country AS country
            JOIN source_product_record AS record USING (source_record_id)
            WHERE record.created_t BETWEEN 1 AND 4102444800
        ),
        yearly AS (
            SELECT
                country.iso_alpha2,
                year(to_timestamp(country.created_t)) AS creation_year,
                COUNT(*) AS year_records,
                COUNT(*) FILTER (
                    WHERE EXISTS (
                        SELECT 1
                        FROM record_category_tag AS category
                        WHERE category.source_record_id = country.source_record_id
                    )
                ) AS category_tagged_records
            FROM country_records AS country
            GROUP BY country.iso_alpha2, creation_year
        )
        SELECT
            iso_alpha2,
            creation_year,
            year_records,
            category_tagged_records,
            round(100.0 * category_tagged_records / year_records, 4)
                AS category_tag_coverage_pct
        FROM yearly
        ORDER BY iso_alpha2, creation_year
        """
    ).fetchdf()
    return summary, yearly


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
        raise ValueError(f"Food-group diagnostic crosswalk is malformed: {crosswalk_file}")
    if crosswalk["food_group_tag"].duplicated().any():
        raise ValueError(f"Food-group diagnostic crosswalk has duplicate tags: {crosswalk_file}")
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DATABASE_FILE)
    parser.add_argument("--build-validation", type=Path, default=VALIDATION_FILE)
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE)
    parser.add_argument("--readiness-output", type=Path, default=READINESS_OUTPUT)
    parser.add_argument("--contributor-output", type=Path, default=CONTRIBUTOR_OUTPUT)
    parser.add_argument("--yearly-output", type=Path, default=YEARLY_OUTPUT)
    parser.add_argument("--source-tag-output", type=Path, default=SOURCE_TAG_OUTPUT)
    parser.add_argument("--overlap-output", type=Path, default=OVERLAP_OUTPUT)
    parser.add_argument("--food-groups-output", type=Path, default=FOOD_GROUP_OUTPUT)
    args = parser.parse_args()

    validate_inputs(args.database, args.build_validation)
    shortlist = read_csv(SHORTLIST_FILE)
    category_rows = read_csv(CATEGORY_OVERLAP_FILE)
    nonfood_rows = read_csv(NONFOOD_COUNTRY_FILE)
    category_by_iso = {row["iso_alpha2"]: row for row in category_rows}
    nonfood_by_iso = {row["iso_alpha2"]: row for row in nonfood_rows}

    connection = duckdb.connect(str(args.database), read_only=True)
    try:
        snapshot_id = connection.execute(
            "SELECT snapshot_id FROM data_snapshot"
        ).fetchone()[0]
        if snapshot_id != EXPECTED_SNAPSHOT_SHA256:
            raise ValueError(
                f"Unexpected database snapshot ID: {snapshot_id}"
            )

        country_row_counts = connection.execute(
            """
            SELECT
                country.iso_alpha2,
                COUNT(*) AS source_rows,
                COUNT(DISTINCT record.code) AS distinct_codes,
                COUNT(*) FILTER (WHERE record.code IS NULL) AS rows_without_code
            FROM record_country AS country
            JOIN source_product_record AS record
                USING (source_record_id)
            GROUP BY iso_alpha2
            """
        ).fetchall()
        database_country_counts = {
            iso_alpha2: {
                "source_rows": int(source_rows),
                "distinct_codes": int(distinct_codes),
                "rows_without_code": int(rows_without_code),
            }
            for iso_alpha2, source_rows, distinct_codes, rows_without_code
            in country_row_counts
        }
        selected_country_codes = set(database_country_counts)
        if selected_country_codes != {"ID", "MY", "PH", "SG", "TH"}:
            raise ValueError(
                "Stage 5 evidence requires the five selected countries; found "
                f"{sorted(selected_country_codes)}."
            )

        approved_category_coverage = connection.execute(
            """
            SELECT
                country.iso_alpha2,
                COUNT(DISTINCT assignment.source_record_id)
                    AS approved_group_source_rows
            FROM record_country AS country
            JOIN record_category_tag AS assignment
                ON country.source_record_id = assignment.source_record_id
            JOIN category_tag_group_decision AS decision
                ON assignment.source_category_tag = decision.source_category_tag
            WHERE decision.selected_group_id IS NOT NULL
            GROUP BY country.iso_alpha2
            """
        ).fetchall()
        approved_category_by_iso = {
            iso_alpha2: int(record_count)
            for iso_alpha2, record_count in approved_category_coverage
        }

        brand_coverage = connection.execute(
            """
            SELECT
                country.iso_alpha2,
                COUNT(DISTINCT brand.source_record_id)
                    AS source_rows_with_brand_text,
                COUNT(DISTINCT brand.source_record_id) FILTER (
                    WHERE mapping.review_status = 'approved'
                ) AS source_rows_with_approved_brand_mapping,
                COUNT(DISTINCT mapping.canonical_brand_name) FILTER (
                    WHERE mapping.review_status = 'approved'
                ) AS approved_canonical_brand_names
            FROM record_country AS country
            LEFT JOIN record_brand_source_value AS brand
                ON country.source_record_id = brand.source_record_id
            LEFT JOIN brand_name_mapping AS mapping
                ON brand.source_brand_name = mapping.source_brand_name
            GROUP BY country.iso_alpha2
            """
        ).fetchall()
        readiness = build_readiness_scorecard(connection)
        contributor_diagnostics, yearly_diagnostics = build_contributor_diagnostics(
            connection
        )
        source_tag_coverage = build_source_tag_coverage(connection)
        country_code_overlap = build_country_code_overlap(connection)
        food_groups_crosscheck = build_food_groups_crosscheck(
            connection,
            FOOD_GROUP_CROSSWALK_FILE,
        )
    finally:
        connection.close()

    brand_by_iso = {
        iso_alpha2: {
            "source_rows_with_brand_text": int(rows_with_text),
            "source_rows_with_approved_brand_mapping": int(rows_with_mapping),
            "approved_canonical_brand_names": int(canonical_names),
        }
        for iso_alpha2, rows_with_text, rows_with_mapping, canonical_names
        in brand_coverage
    }

    fields = (
        "snapshot_sha256",
        "rank",
        "iso_alpha2",
        "country_name",
        "country_source_rows",
        "country_distinct_codes",
        "country_rows_minus_distinct_codes",
        "country_rows_without_code",
        "source_rows_with_category_tags",
        "category_tags_coverage_pct",
        "source_rows_with_primary_candidate_group",
        "primary_candidate_coverage_pct_of_category_tagged_rows",
        "source_rows_with_multiple_primary_groups",
        "source_rows_with_approved_group_decision",
        "source_rows_with_brand_text",
        "source_rows_with_approved_brand_mapping",
        "approved_brand_mapping_coverage_pct_of_country_rows",
        "approved_canonical_brand_names_present",
        "class_A_or_B_flagged_rows",
        "class_A_or_B_flagged_share_pct",
    )

    output_rows: list[dict[str, str]] = []
    selected_shortlist = [
        candidate
        for candidate in shortlist
        if candidate["iso_alpha2"] in selected_country_codes
    ]
    for candidate in selected_shortlist:
        iso_alpha2 = candidate["iso_alpha2"]
        if iso_alpha2 not in category_by_iso or iso_alpha2 not in nonfood_by_iso:
            raise ValueError(
                f"Missing category or non-food evidence for shortlisted unit {iso_alpha2}."
            )
        category = category_by_iso[iso_alpha2]
        nonfood = nonfood_by_iso[iso_alpha2]
        brand = brand_by_iso.get(
            iso_alpha2,
            {
                "source_rows_with_brand_text": 0,
                "source_rows_with_approved_brand_mapping": 0,
                "approved_canonical_brand_names": 0,
            },
        )
        country_rows = int(candidate["record_count"])
        country_database_counts = database_country_counts.get(iso_alpha2)
        if (
            country_database_counts is None
            or country_database_counts["source_rows"] != country_rows
        ):
            raise ValueError(
                f"Country row count does not reconcile for {iso_alpha2}: "
                f"shortlist={country_rows}, database="
                f"{country_database_counts}."
            )
        if int(category["country_source_records"]) != country_rows:
            raise ValueError(
                f"Category evidence denominator does not reconcile for {iso_alpha2}."
            )
        if (
            int(nonfood["total_records"]) != country_rows
            or nonfood["reconciles_to_normalized_profile"] != "Y"
        ):
            raise ValueError(
                f"Non-food country denominator does not reconcile for {iso_alpha2}."
            )
        category_tagged_rows = int(category["country_records_with_category_tags"])
        primary_rows = int(category["records_with_any_primary_group"])
        flagged_ab_rows = (
            int(nonfood["class_a_records"]) + int(nonfood["class_b_records"])
        )

        if category_tagged_rows > country_rows:
            raise ValueError(f"Category-tagged rows exceed country rows for {iso_alpha2}.")
        if country_database_counts["rows_without_code"] != 0:
            raise ValueError(f"Source code is missing for records in {iso_alpha2}.")
        if primary_rows > country_rows:
            raise ValueError(f"Primary-group rows exceed country rows for {iso_alpha2}.")
        if brand["source_rows_with_approved_brand_mapping"] > brand["source_rows_with_brand_text"]:
            raise ValueError(f"Mapped brand rows exceed brand-text rows for {iso_alpha2}.")
        if flagged_ab_rows > country_rows:
            raise ValueError(f"A/B flagged rows exceed country rows for {iso_alpha2}.")

        output_rows.append(
            {
                "snapshot_sha256": snapshot_id,
                "rank": candidate["rank"],
                "iso_alpha2": iso_alpha2,
                "country_name": candidate["country_name"],
                "country_source_rows": str(country_rows),
                "country_distinct_codes": str(
                    country_database_counts["distinct_codes"]
                ),
                "country_rows_minus_distinct_codes": str(
                    country_rows - country_database_counts["distinct_codes"]
                ),
                "country_rows_without_code": str(
                    country_database_counts["rows_without_code"]
                ),
                "source_rows_with_category_tags": str(category_tagged_rows),
                "category_tags_coverage_pct": f"{100 * category_tagged_rows / country_rows:.4f}",
                "source_rows_with_primary_candidate_group": str(primary_rows),
                "primary_candidate_coverage_pct_of_category_tagged_rows": (
                    f"{100 * primary_rows / category_tagged_rows:.4f}"
                    if category_tagged_rows
                    else ""
                ),
                "source_rows_with_multiple_primary_groups": category[
                    "records_with_multiple_primary_groups"
                ],
                "source_rows_with_approved_group_decision": str(
                    approved_category_by_iso.get(iso_alpha2, 0)
                ),
                "source_rows_with_brand_text": str(
                    brand["source_rows_with_brand_text"]
                ),
                "source_rows_with_approved_brand_mapping": str(
                    brand["source_rows_with_approved_brand_mapping"]
                ),
                "approved_brand_mapping_coverage_pct_of_country_rows": (
                    f"{100 * brand['source_rows_with_approved_brand_mapping'] / country_rows:.4f}"
                ),
                "approved_canonical_brand_names_present": str(
                    brand["approved_canonical_brand_names"]
                ),
                "class_A_or_B_flagged_rows": str(flagged_ab_rows),
                "class_A_or_B_flagged_share_pct": f"{100 * flagged_ab_rows / country_rows:.4f}",
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)

    diagnostic_outputs = (
        (readiness, args.readiness_output),
        (contributor_diagnostics, args.contributor_output),
        (yearly_diagnostics, args.yearly_output),
        (source_tag_coverage, args.source_tag_output),
        (country_code_overlap, args.overlap_output),
        (food_groups_crosscheck, args.food_groups_output),
    )
    for frame, path in diagnostic_outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False, encoding="utf-8")

    print(f"Selected-country evidence rows: {len(output_rows)}")
    print(f"Snapshot SHA-256: {snapshot_id}")
    print(f"Evidence output: {args.output}")
    print(f"Data-readiness scorecard: {args.readiness_output}")
    print(f"Contributor and year diagnostics: {args.contributor_output}")
    print(f"Country-code overlap: {args.overlap_output}")
    print(f"Food-groups diagnostic: {args.food_groups_output}")


if __name__ == "__main__":
    main()
