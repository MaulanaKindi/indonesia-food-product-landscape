-- 02_build_analysis_tables.sql
-- Build the core product-record table.
-- record_id is a technical identifier for this materialized snapshot,
-- not a permanent Open Food Facts product identifier.

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
FROM read_parquet('food.parquet');
