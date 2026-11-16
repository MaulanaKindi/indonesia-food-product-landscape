"""Stage 5 readiness and coverage diagnostics."""

import duckdb
import pandas as pd


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
