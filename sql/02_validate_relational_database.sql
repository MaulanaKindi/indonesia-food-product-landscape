WITH country_reconciliation AS (
    SELECT COUNT(*) AS mismatch_count
    FROM (
        SELECT
            COALESCE(reference.iso_alpha2, built.iso_alpha2) AS iso_alpha2,
            reference.record_count AS reference_record_count,
            built.record_count AS built_record_count
        FROM (
            SELECT iso_alpha2, CAST(record_count AS BIGINT) AS record_count
            FROM read_csv_auto(
                'outputs/profiling/normalized_country_profile.csv',
                header = true,
                all_varchar = true
            )
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
record_counts AS (
    SELECT
        COUNT(*) AS source_record_rows,
        COUNT(DISTINCT source_record_id) AS distinct_source_record_ids,
        MIN(source_row_ordinal) AS min_source_row_ordinal,
        MAX(source_row_ordinal) AS max_source_row_ordinal,
        COUNT(DISTINCT code) AS distinct_codes,
        COUNT(*) FILTER (WHERE code IS NOT NULL) AS rows_with_code
    FROM source_product_record
),
duplicate_code_groups AS (
    SELECT COUNT(*) AS duplicate_code_group_count
    FROM (
        SELECT code
        FROM source_product_record
        WHERE code IS NOT NULL
        GROUP BY code
        HAVING COUNT(*) > 1
    ) AS duplicates
),
source_assignment_counts AS (
    SELECT
        SUM(COALESCE(len(list_distinct(categories_tags)), 0))
            AS category_tag_assignments,
        SUM(COALESCE(len(list_distinct(countries_tags)), 0))
            AS country_tag_assignments,
        SUM(COALESCE(len(list_distinct(brands_tags)), 0))
            AS brand_tag_assignments
    FROM source_product_record
),
built_assignment_counts AS (
    SELECT
        (SELECT COUNT(*) FROM record_category_tag) AS category_tag_assignments,
        (SELECT COUNT(*) FROM record_country_source_tag) AS country_tag_assignments,
        (SELECT COUNT(*) FROM record_brand_tag) AS brand_tag_assignments
)
SELECT 'source_product_record_rows' AS check_name,
       source_record_rows::VARCHAR AS actual_value,
       '4828207' AS expected_value
FROM record_counts
UNION ALL
SELECT 'distinct_source_record_ids',
       distinct_source_record_ids::VARCHAR,
       '4828207'
FROM record_counts
UNION ALL
SELECT 'source_row_ordinal_range',
       min_source_row_ordinal::VARCHAR || '-' || max_source_row_ordinal::VARCHAR,
       '1-4828207'
FROM record_counts
UNION ALL
SELECT 'source_column_count',
       (SELECT COUNT(*) - 3 FROM pragma_table_info('source_product_record'))::VARCHAR,
       '111'
UNION ALL
SELECT 'snapshot_metadata_rows',
       (SELECT COUNT(*) FROM data_snapshot)::VARCHAR,
       '1'
UNION ALL
SELECT 'iso_country_units',
       (SELECT COUNT(*) FROM country_unit)::VARCHAR,
       '249'
UNION ALL
SELECT 'normalized_country_profile_mismatch_count',
       mismatch_count::VARCHAR,
       '0'
FROM country_reconciliation
UNION ALL
SELECT 'duplicate_code_groups',
       duplicate_code_group_count::VARCHAR,
       '61'
FROM duplicate_code_groups
UNION ALL
SELECT 'category_tag_assignment_reconciliation',
       built.category_tag_assignments::VARCHAR,
       source.category_tag_assignments::VARCHAR
FROM source_assignment_counts AS source
CROSS JOIN built_assignment_counts AS built
UNION ALL
SELECT 'country_tag_assignment_reconciliation',
       built.country_tag_assignments::VARCHAR,
       source.country_tag_assignments::VARCHAR
FROM source_assignment_counts AS source
CROSS JOIN built_assignment_counts AS built
UNION ALL
SELECT 'brand_tag_assignment_reconciliation',
       built.brand_tag_assignments::VARCHAR,
       source.brand_tag_assignments::VARCHAR
FROM source_assignment_counts AS source
CROSS JOIN built_assignment_counts AS built
UNION ALL
SELECT 'record_country_outside_iso_reference',
       COUNT(*)::VARCHAR,
       '0'
FROM record_country AS assignment
LEFT JOIN country_unit AS unit USING (iso_alpha2)
WHERE unit.iso_alpha2 IS NULL
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
