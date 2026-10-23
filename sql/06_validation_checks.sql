-- ============================================================
-- Project: Global Food Brand Landscape Analysis
-- File: 06_validation_checks.sql
--
-- Purpose:
-- Validate table integrity and analytical metric consistency.
--
-- Expected result:
-- 14 validation checks.
-- issue_count = 0 means the tested condition passed.
--
-- Limitations:
-- These checks do not establish dataset representativeness,
-- semantic accuracy, or market-share validity.
-- ============================================================

WITH
-- ------------------------------------------------------------
-- A. Base records and Indonesia brand coverage
-- ------------------------------------------------------------

indonesia_records AS (
    SELECT DISTINCT record_id
    FROM product_countries
    WHERE LOWER(TRIM(country_tag)) = 'en:indonesia'
),

brand_counts AS (
    SELECT
        ir.record_id,
        COUNT(DISTINCT pb.brand_tag) AS brand_label_count
    FROM indonesia_records AS ir
    LEFT JOIN product_brands_clean AS pb
        ON ir.record_id = pb.record_id
    GROUP BY ir.record_id
),

brand_coverage AS (
    SELECT
        COUNT(*) AS total_indonesia_records,
        COUNT(*) FILTER (
            WHERE brand_label_count > 0
        ) AS records_with_brand,
        COUNT(*) FILTER (
            WHERE brand_label_count = 0
        ) AS records_without_brand,
        COUNT(*) FILTER (
            WHERE brand_label_count = 1
        ) AS single_brand_records
    FROM brand_counts
),

-- ------------------------------------------------------------
-- B. Single-brand distribution and concentration
-- ------------------------------------------------------------

single_brand_records AS (
    SELECT
        ir.record_id,
        MIN(pb.brand_tag) AS brand_tag
    FROM indonesia_records AS ir
    INNER JOIN product_brands_clean AS pb
        ON ir.record_id = pb.record_id
    GROUP BY ir.record_id
    HAVING COUNT(DISTINCT pb.brand_tag) = 1
),

single_brand_distribution AS (
    SELECT
        brand_tag,
        COUNT(*) AS record_count
    FROM single_brand_records
    GROUP BY brand_tag
),

ranked_brands AS (
    SELECT
        brand_tag,
        record_count,
        ROW_NUMBER() OVER (
            ORDER BY record_count DESC, brand_tag
        ) AS brand_rank
    FROM single_brand_distribution
),

concentration AS (
    SELECT
        COUNT(*) AS distinct_brand_labels,
        SUM(record_count) AS total_records,
        SUM(
            CASE WHEN brand_rank <= 5
                 THEN record_count ELSE 0 END
        ) AS top_5_records,
        SUM(
            CASE WHEN brand_rank <= 10
                 THEN record_count ELSE 0 END
        ) AS top_10_records,
        SUM(
            CASE WHEN brand_rank <= 20
                 THEN record_count ELSE 0 END
        ) AS top_20_records
    FROM ranked_brands
),

-- ------------------------------------------------------------
-- C. Integrity checks
-- ------------------------------------------------------------

integrity_checks AS (
    SELECT
        'record_id_null' AS check_name,
        COUNT(*) AS issue_count
    FROM product_records
    WHERE record_id IS NULL

    UNION ALL

    SELECT
        'record_id_duplicate',
        COUNT(*) - COUNT(DISTINCT record_id)
    FROM product_records

    UNION ALL

    SELECT
        'country_bridge_null_or_blank_tag',
        COUNT(*)
    FROM product_countries
    WHERE country_tag IS NULL
       OR TRIM(country_tag) = ''

    UNION ALL

    SELECT
        'country_bridge_duplicate_pairs',
        COUNT(*) - COUNT(DISTINCT (record_id, country_tag))
    FROM product_countries

    UNION ALL

    SELECT
        'clean_category_invalid_tags',
        COUNT(*)
    FROM product_categories_clean
    WHERE category_tag IS NULL
       OR TRIM(category_tag) = ''
       OR LOWER(TRIM(category_tag)) IN (
           'en:null',
           'en:unknown',
           'en:undefined'
       )

    UNION ALL

    SELECT
        'clean_category_duplicate_pairs',
        COUNT(*) - COUNT(DISTINCT (record_id, category_tag))
    FROM product_categories_clean

    UNION ALL

    SELECT
        'clean_brand_null_or_blank_tags',
        COUNT(*)
    FROM product_brands_clean
    WHERE brand_tag IS NULL
       OR TRIM(brand_tag) = ''

    UNION ALL

    SELECT
        'clean_brand_duplicate_pairs',
        COUNT(*) - COUNT(DISTINCT (record_id, brand_tag))
    FROM product_brands_clean
),

-- ------------------------------------------------------------
-- D. Metric consistency checks
-- ------------------------------------------------------------

metric_checks AS (
    SELECT
        'indonesia_brand_coverage_reconciliation' AS check_name,
        CASE
            WHEN total_indonesia_records =
                 records_with_brand + records_without_brand
            THEN 0 ELSE 1
        END AS issue_count
    FROM brand_coverage

    UNION ALL

    SELECT
        'single_brand_count_not_above_branded_count',
        CASE
            WHEN single_brand_records <= records_with_brand
            THEN 0 ELSE 1
        END
    FROM brand_coverage

    UNION ALL

    SELECT
        'single_brand_distribution_reconciliation',
        CASE
            WHEN bc.single_brand_records = c.total_records
            THEN 0 ELSE 1
        END
    FROM brand_coverage AS bc
    CROSS JOIN concentration AS c

    UNION ALL

    SELECT
        'top_5_not_above_top_10',
        CASE
            WHEN top_5_records <= top_10_records
            THEN 0 ELSE 1
        END
    FROM concentration

    UNION ALL

    SELECT
        'top_10_not_above_top_20',
        CASE
            WHEN top_10_records <= top_20_records
            THEN 0 ELSE 1
        END
    FROM concentration

    UNION ALL

    SELECT
        'top_20_not_above_total',
        CASE
            WHEN top_20_records <= total_records
            THEN 0 ELSE 1
        END
    FROM concentration
)

-- ------------------------------------------------------------
-- E. Unified validation output
-- ------------------------------------------------------------

SELECT check_name, issue_count
FROM integrity_checks

UNION ALL

SELECT check_name, issue_count
FROM metric_checks

ORDER BY check_name;
