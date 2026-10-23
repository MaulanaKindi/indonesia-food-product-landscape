-- 02_build_analysis_tables.sql
-- Purpose: Build four analysis tables from the full Open Food Facts Parquet source.
--
-- Tables created:
--   product_records    : Full product-record table
--   product_countries  : Product-to-country-tag bridge table
--   product_categories : Product-to-category-tag bridge table
--   product_brands     : Product-to-brand-tag bridge table
--
-- Sample CSV files are stored separately in data/ and contain
-- 100 rows each for inspection. They are not the full tables.
--
-- record_id is a technical identifier for this materialized snapshot,
-- not a permanent Open Food Facts product identifier.
--
-- Source path below is specific to the current Kaggle environment.

-- 1. Build the core product-record table
CREATE OR REPLACE TABLE product_records AS
SELECT
    ROW_NUMBER() OVER () AS record_id,
    code,
    brands,
    brands_tags,
    categories,
    categories_tags,
    countries_tags,
    completeness,
    created_t
FROM read_parquet(
    '/kaggle/input/datasets/maulanakinditamami/open-food-facts-product-database-salin-judul/food.parquet'
);

-- 2. Build the product-to-country bridge table
CREATE OR REPLACE TABLE product_countries AS
SELECT DISTINCT
    p.record_id,
    t.country_tag
FROM product_records AS p
CROSS JOIN UNNEST(p.countries_tags) AS t(country_tag)
WHERE t.country_tag IS NOT NULL
  AND TRIM(t.country_tag) <> '';

-- 3. Build the product-to-category bridge table
CREATE OR REPLACE TABLE product_categories AS
SELECT DISTINCT
    p.record_id,
    t.category_tag
FROM product_records AS p
CROSS JOIN UNNEST(p.categories_tags) AS t(category_tag)
WHERE t.category_tag IS NOT NULL
  AND TRIM(t.category_tag) <> '';

-- 4. Build the product-to-brand bridge table
CREATE OR REPLACE TABLE product_brands AS
SELECT DISTINCT
    p.record_id,
    t.brand_tag
FROM product_records AS p
CROSS JOIN UNNEST(p.brands_tags) AS t(brand_tag)
WHERE t.brand_tag IS NOT NULL
  AND TRIM(t.brand_tag) <> '';
