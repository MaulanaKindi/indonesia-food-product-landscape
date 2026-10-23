-- ============================================================
-- Project: Global Food Brand Landscape Analysis
-- File: 05_brand_analysis.sql
--
-- Purpose:
-- 1. Assess brand-label coverage among Indonesian records.
-- 2. Rank brand labels by recorded product-record count.
-- 3. Measure record concentration among the top-ranked labels.
--
-- Source tables:
--   product_countries
--   product_brands_clean
--
-- Important limitations:
-- - Results describe Open Food Facts records, not sales or market share.
-- - A record is not necessarily a unique physical product.
-- - Brand labels are normalized tags, not verified company identities.
-- - Records with multiple cleaned brand labels are excluded from
--   the single-brand distribution and concentration analysis.
-- ============================================================


-- ============================================================
-- QUERY 1: Brand-label coverage in Indonesia
--
-- Denominator: distinct product_records represented by the
-- country tag 'en:indonesia'.
--
-- A record is classified as:
-- - with brand: at least one cleaned brand label
-- - without brand: no cleaned brand label
-- - one brand: exactly one cleaned brand label
-- - multiple brands: more than one cleaned brand label
--
-- The four coverage counts should reconcile:
-- with brand + without brand = total records
-- one brand + multiple brands = with brand
-- ============================================================

WITH indonesia_records AS (
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
)

SELECT
    COUNT(*) AS indonesia_record_count,

    COUNT(*) FILTER (
        WHERE brand_label_count > 0
    ) AS records_with_brand,

    COUNT(*) FILTER (
        WHERE brand_label_count = 0
    ) AS records_without_brand,

    COUNT(*) FILTER (
        WHERE brand_label_count = 1
    ) AS records_with_one_brand,

    COUNT(*) FILTER (
        WHERE brand_label_count > 1
    ) AS records_with_multiple_brands,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE brand_label_count > 0
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS brand_coverage_pct

FROM brand_counts;


-- ============================================================
-- QUERY 2: Top 20 brand labels among Indonesian records
--          with exactly one cleaned brand label
--
-- Denominator: all eligible Indonesian records with exactly
-- one cleaned brand label, not just the top 20.
--
-- SUM(...) OVER () calculates the total across all brand labels.
-- This ensures record_pct and cumulative_record_pct use the
-- same global denominator.
--
-- Ranking ties are resolved alphabetically by brand_tag.
-- ============================================================

WITH indonesia_records AS (
    SELECT DISTINCT record_id
    FROM product_countries
    WHERE LOWER(TRIM(country_tag)) = 'en:indonesia'
),

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

brand_distribution AS (
    SELECT
        brand_tag,
        COUNT(*) AS recorded_product_records
    FROM single_brand_records
    GROUP BY brand_tag
),

ranked_brands AS (
    SELECT
        brand_tag,
        recorded_product_records,

        ROW_NUMBER() OVER (
            ORDER BY
                recorded_product_records DESC,
                brand_tag
        ) AS brand_rank,

        SUM(recorded_product_records) OVER ()
            AS total_records

    FROM brand_distribution
)

SELECT
    brand_rank,
    brand_tag,
    recorded_product_records,

    ROUND(
        100.0 * recorded_product_records
        / NULLIF(total_records, 0),
        2
    ) AS record_pct,

    ROUND(
        100.0 * SUM(recorded_product_records) OVER (
            ORDER BY brand_rank
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) / NULLIF(total_records, 0),
        2
    ) AS cumulative_record_pct

FROM ranked_brands
WHERE brand_rank <= 20
ORDER BY brand_rank;


-- ============================================================
-- QUERY 3: Record concentration among ranked brand labels
--
-- Denominator: all Indonesian records with exactly one cleaned
-- brand label.
--
-- Measures:
-- - distinct_brand_labels: number of distinct labels in scope
-- - records_in_analysis: eligible record count
-- - top_brand_records: record count for the leading label
-- - top 5/10/20 concentration: share of eligible records
--   represented by the corresponding highest-ranked labels
--
-- These are record-concentration metrics, NOT market shares.
-- They should not be interpreted as sales concentration or as
-- proof of market competitiveness.
-- ============================================================

WITH indonesia_records AS (
    SELECT DISTINCT record_id
    FROM product_countries
    WHERE LOWER(TRIM(country_tag)) = 'en:indonesia'
),

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

brand_distribution AS (
    SELECT
        brand_tag,
        COUNT(*) AS recorded_product_records
    FROM single_brand_records
    GROUP BY brand_tag
),

ranked_brands AS (
    SELECT
        brand_tag,
        recorded_product_records,

        ROW_NUMBER() OVER (
            ORDER BY
                recorded_product_records DESC,
                brand_tag
        ) AS brand_rank

    FROM brand_distribution
)

SELECT
    COUNT(*) AS distinct_brand_labels,

    SUM(recorded_product_records) AS records_in_analysis,

    MAX(
        CASE
            WHEN brand_rank = 1
            THEN recorded_product_records
        END
    ) AS top_brand_records,

    ROUND(
        100.0 * SUM(
            CASE
                WHEN brand_rank <= 5
                THEN recorded_product_records
                ELSE 0
            END
        ) / NULLIF(SUM(recorded_product_records), 0),
        2
    ) AS top_5_record_concentration_pct,

    ROUND(
        100.0 * SUM(
            CASE
                WHEN brand_rank <= 10
                THEN recorded_product_records
                ELSE 0
            END
        ) / NULLIF(SUM(recorded_product_records), 0),
        2
    ) AS top_10_record_concentration_pct,

    ROUND(
        100.0 * SUM(
            CASE
                WHEN brand_rank <= 20
                THEN recorded_product_records
                ELSE 0
            END
        ) / NULLIF(SUM(recorded_product_records), 0),
        2
    ) AS top_20_record_concentration_pct

FROM ranked_brands;
