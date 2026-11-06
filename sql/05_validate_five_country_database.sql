WITH selected_country_codes AS (
    SELECT *
    FROM (VALUES ('ID'), ('MY'), ('PH'), ('SG'), ('TH'))
        AS selected(iso_alpha2)
),
selected_source_tags AS (
    SELECT source_country_tag
    FROM read_csv_auto(
        'data/mappings/country_tag_mapping.csv',
        header = true,
        all_varchar = true
    )
    WHERE mapping_status = 'approved'
      AND iso_alpha2 IN (SELECT iso_alpha2 FROM selected_country_codes)
),
expected_source AS MATERIALIZED (
    SELECT
        CAST(source.file_row_number + 1 AS BIGINT) AS source_record_id,
        source.code,
        source.countries_tags,
        source.categories_tags,
        source.brands,
        source.brands_tags
    FROM read_parquet('data/raw/food.parquet', file_row_number = true) AS source
    WHERE EXISTS (
        SELECT 1
        FROM UNNEST(list_distinct(source.countries_tags))
            AS source_country_tag(country_tag)
        JOIN selected_source_tags AS selected
            ON source_country_tag.country_tag = selected.source_country_tag
    )
),
source_row_mismatches AS (
    SELECT COUNT(*) AS mismatch_count
    FROM expected_source AS expected
    FULL OUTER JOIN source_product_record AS actual
        USING (source_record_id)
    WHERE expected.source_record_id IS NULL
       OR actual.source_record_id IS NULL
       OR expected.code IS DISTINCT FROM actual.code
       OR expected.countries_tags IS DISTINCT FROM actual.countries_tags
       OR expected.categories_tags IS DISTINCT FROM actual.categories_tags
       OR expected.brands IS DISTINCT FROM actual.brands
),
expected_country_links AS MATERIALIZED (
    SELECT DISTINCT
        source.source_record_id,
        mapping.iso_alpha2
    FROM expected_source AS source,
    UNNEST(list_distinct(source.countries_tags))
        AS source_country_tag(country_tag)
    JOIN read_csv_auto(
        'data/mappings/country_tag_mapping.csv',
        header = true,
        all_varchar = true
    ) AS mapping
        ON source_country_tag.country_tag = mapping.source_country_tag
    WHERE mapping.mapping_status = 'approved'
      AND mapping.iso_alpha2 IN (SELECT iso_alpha2 FROM selected_country_codes)
),
country_link_mismatches AS (
    SELECT COUNT(*) AS mismatch_count
    FROM (
        (
            SELECT source_record_id, iso_alpha2
            FROM expected_country_links
            EXCEPT
            SELECT source_record_id, iso_alpha2
            FROM record_country
        )
        UNION ALL
        (
            SELECT source_record_id, iso_alpha2
            FROM record_country
            EXCEPT
            SELECT source_record_id, iso_alpha2
            FROM expected_country_links
        )
    ) AS differences
),
country_profile_mismatches AS (
    SELECT COUNT(*) AS mismatch_count
    FROM (
        SELECT
            COALESCE(reference.iso_alpha2, built.iso_alpha2) AS iso_alpha2
        FROM (
            SELECT iso_alpha2, CAST(record_count AS BIGINT) AS record_count
            FROM read_csv_auto(
                'outputs/profiling/normalized_country_profile.csv',
                header = true,
                all_varchar = true
            )
            WHERE iso_alpha2 IN (SELECT iso_alpha2 FROM selected_country_codes)
        ) AS reference
        FULL OUTER JOIN (
            SELECT iso_alpha2, COUNT(*) AS record_count
            FROM record_country
            GROUP BY iso_alpha2
        ) AS built
            ON reference.iso_alpha2 = built.iso_alpha2
        WHERE reference.iso_alpha2 IS NULL
           OR built.iso_alpha2 IS NULL
           OR reference.record_count <> built.record_count
    ) AS differences
),
source_assignments AS (
    SELECT
        (
            SELECT COUNT(*)
            FROM expected_source AS source,
            UNNEST(list_distinct(source.categories_tags))
                AS category_tag(category_tag)
            WHERE category_tag.category_tag IS NOT NULL
        ) AS category_tag_count,
        (
            SELECT COUNT(*)
            FROM expected_source AS source,
            UNNEST(list_distinct(source.countries_tags))
                AS country_tag(country_tag)
            WHERE country_tag.country_tag IS NOT NULL
        ) AS country_tag_count,
        (
            SELECT COUNT(*)
            FROM expected_source AS source,
            UNNEST(list_distinct(source.brands_tags))
                AS brand_tag(brand_tag)
            WHERE brand_tag.brand_tag IS NOT NULL
        ) AS brand_tag_count
),
built_assignments AS (
    SELECT
        (SELECT COUNT(*) FROM record_category_tag) AS category_tag_count,
        (SELECT COUNT(*) FROM record_country_source_tag) AS country_tag_count,
        (SELECT COUNT(*) FROM record_brand_tag) AS brand_tag_count
),
source_counts AS (
    SELECT
        COUNT(*) AS record_count,
        COUNT(DISTINCT source_record_id) AS distinct_record_count,
        MIN(source_row_ordinal) AS min_ordinal,
        MAX(source_row_ordinal) AS max_ordinal
    FROM source_product_record
)
SELECT 'selected_country_units' AS check_name,
       COUNT(DISTINCT iso_alpha2)::VARCHAR AS actual_value,
       '5' AS expected_value
FROM record_country
UNION ALL
SELECT 'source_product_record_rows',
       (SELECT record_count FROM source_counts)::VARCHAR,
       (SELECT COUNT(*) FROM expected_source)::VARCHAR
UNION ALL
SELECT 'distinct_source_record_ids',
       (SELECT distinct_record_count FROM source_counts)::VARCHAR,
       (SELECT COUNT(*) FROM expected_source)::VARCHAR
UNION ALL
SELECT 'source_row_ordinal_range',
       (SELECT min_ordinal::VARCHAR || '-' || max_ordinal::VARCHAR FROM source_counts),
       (
           SELECT MIN(source_record_id)::VARCHAR || '-' || MAX(source_record_id)::VARCHAR
           FROM expected_source
       )
UNION ALL
SELECT 'selected_source_record_mismatches',
       mismatch_count::VARCHAR,
       '0'
FROM source_row_mismatches
UNION ALL
SELECT 'source_column_count',
       (SELECT COUNT(*) - 3 FROM pragma_table_info('source_product_record'))::VARCHAR,
       '111'
UNION ALL
SELECT 'snapshot_metadata_rows',
       (SELECT COUNT(*) FROM data_snapshot)::VARCHAR,
       '1'
UNION ALL
SELECT 'selected_country_profile_mismatches',
       mismatch_count::VARCHAR,
       '0'
FROM country_profile_mismatches
UNION ALL
SELECT 'record_country_link_mismatches',
       mismatch_count::VARCHAR,
       '0'
FROM country_link_mismatches
UNION ALL
SELECT 'category_tag_assignment_reconciliation',
       built.category_tag_count::VARCHAR,
       source.category_tag_count::VARCHAR
FROM source_assignments AS source
CROSS JOIN built_assignments AS built
UNION ALL
SELECT 'country_tag_assignment_reconciliation',
       built.country_tag_count::VARCHAR,
       source.country_tag_count::VARCHAR
FROM source_assignments AS source
CROSS JOIN built_assignments AS built
UNION ALL
SELECT 'brand_tag_assignment_reconciliation',
       built.brand_tag_count::VARCHAR,
       source.brand_tag_count::VARCHAR
FROM source_assignments AS source
CROSS JOIN built_assignments AS built
UNION ALL
SELECT 'category_decisions_without_category_tag',
       COUNT(*)::VARCHAR,
       '0'
FROM category_tag_group_decision AS decision
LEFT JOIN category_tag AS tag USING (source_category_tag)
WHERE tag.source_category_tag IS NULL
UNION ALL
SELECT 'selected_groups_without_reporting_group',
       COUNT(*)::VARCHAR,
       '0'
FROM category_tag_group_decision AS decision
LEFT JOIN reporting_group AS group_ref
    ON decision.selected_group_id = group_ref.reporting_group_id
WHERE decision.selected_group_id IS NOT NULL
  AND group_ref.reporting_group_id IS NULL
UNION ALL
SELECT 'category_taxonomy_edges_without_nodes',
       COUNT(*)::VARCHAR,
       '0'
FROM category_taxonomy_parent AS edge
LEFT JOIN category_taxonomy_node AS child
    ON edge.child_tag = child.category_tag
   AND edge.taxonomy_version = child.taxonomy_version
LEFT JOIN category_taxonomy_node AS parent
    ON edge.parent_tag = parent.category_tag
   AND edge.taxonomy_version = parent.taxonomy_version
WHERE child.category_tag IS NULL
   OR parent.category_tag IS NULL;
