-- 03_country_analysis.sql
-- Purpose: Analyze recorded product records across 13 selected countries.
-- Source tables: product_records, product_countries, country_tag_mapping
-- Metric: Distinct dataset records assigned to each selected country.
-- Limitation: Record counts are not sales, market size, or market share.

-- 1. Country landscape
SELECT
    m.country_name,
    m.region,
    COUNT(DISTINCT pc.record_id) AS recorded_product_records
FROM product_countries AS pc
JOIN country_tag_mapping AS m
    ON LOWER(TRIM(pc.country_tag)) = m.country_tag
GROUP BY
    m.country_name,
    m.region
ORDER BY recorded_product_records DESC;


-- 2. Sensitivity check: records versus distinct valid product codes
SELECT
    m.country_name,
    COUNT(DISTINCT pc.record_id) AS record_count,
    COUNT(DISTINCT CASE
        WHEN p.code IS NOT NULL
         AND TRIM(p.code) <> ''
        THEN p.code
    END) AS unique_valid_codes
FROM product_countries AS pc
JOIN country_tag_mapping AS m
    ON LOWER(TRIM(pc.country_tag)) = m.country_tag
JOIN product_records AS p
    ON p.record_id = pc.record_id
GROUP BY m.country_name
ORDER BY record_count DESC;


-- 3. Check that global labels are excluded from the country mapping
SELECT
    country_tag,
    country_name
FROM country_tag_mapping
WHERE LOWER(TRIM(country_tag)) IN (
    'en:world',
    'en:worldwide'
);


-- 4. Check the number of countries included
SELECT COUNT(*) AS mapped_country_count
FROM country_tag_mapping;
