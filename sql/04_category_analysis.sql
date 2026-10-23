-- 04_category_analysis.sql
-- Purpose:
-- Analyze recorded product records and brand-label coverage
-- across the 20 categories with the most recorded product records.
--
-- Source tables:
--   product_categories_clean
--   product_brands_clean
--
-- Definitions:
--   recorded_product_records = distinct dataset records assigned to a category
--   records_with_brand = distinct category records with at least one cleaned brand label
--   distinct_brand_labels = distinct normalized brand labels in a category
--   records_with_brand_pct = percentage of category records with a brand label
--
-- Limitations:
--   Record counts are not sales, market size, or market share.
--   Products can have multiple category tags, so categories overlap.
--   Brand-label counts do not necessarily represent independent brands.
--   The exploratory brand-label ratio is not a market-diversity measure.


-- 1. Top 20 categories by recorded product records

SELECT
    category_tag,
    COUNT(DISTINCT record_id) AS recorded_product_records
FROM product_categories_clean
GROUP BY category_tag
ORDER BY recorded_product_records DESC
LIMIT 20;


-- 2. Brand-label coverage across the top 20 categories

WITH top_categories AS (
    SELECT
        category_tag,
        COUNT(DISTINCT record_id) AS recorded_product_records
    FROM product_categories_clean
    GROUP BY category_tag
    ORDER BY recorded_product_records DESC
    LIMIT 20
)
SELECT
    tc.category_tag,
    tc.recorded_product_records,
    COUNT(DISTINCT pb.record_id) AS records_with_brand,
    COUNT(DISTINCT pb.brand_tag) AS distinct_brand_labels,
    ROUND(
        100.0 * COUNT(DISTINCT pb.record_id)
        / NULLIF(tc.recorded_product_records, 0),
        2
    ) AS records_with_brand_pct
FROM top_categories AS tc
JOIN product_categories_clean AS pc
    ON pc.category_tag = tc.category_tag
LEFT JOIN product_brands_clean AS pb
    ON pb.record_id = pc.record_id
GROUP BY
    tc.category_tag,
    tc.recorded_product_records
ORDER BY tc.recorded_product_records DESC;


-- 3. Exploratory ratio: distinct brand labels relative to branded records
-- This is not average brands per product and is not a core market metric.

WITH top_categories AS (
    SELECT
        category_tag,
        COUNT(DISTINCT record_id) AS recorded_product_records
    FROM product_categories_clean
    GROUP BY category_tag
    ORDER BY recorded_product_records DESC
    LIMIT 20
),
category_brand_metrics AS (
    SELECT
        tc.category_tag,
        tc.recorded_product_records,
        COUNT(DISTINCT pb.record_id) AS records_with_brand,
        COUNT(DISTINCT pb.brand_tag) AS distinct_brand_labels
    FROM top_categories AS tc
    JOIN product_categories_clean AS pc
        ON pc.category_tag = tc.category_tag
    LEFT JOIN product_brands_clean AS pb
        ON pb.record_id = pc.record_id
    GROUP BY
        tc.category_tag,
        tc.recorded_product_records
)
SELECT
    category_tag,
    recorded_product_records,
    records_with_brand,
    distinct_brand_labels,
    ROUND(
        100.0 * records_with_brand
        / NULLIF(recorded_product_records, 0),
        2
    ) AS records_with_brand_pct,
    ROUND(
        1.0 * distinct_brand_labels
        / NULLIF(records_with_brand, 0),
        4
    ) AS distinct_brand_labels_per_branded_record
FROM category_brand_metrics
ORDER BY recorded_product_records DESC;
