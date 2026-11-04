WITH selected_country_count AS (
    SELECT COUNT(*) AS actual_value
    FROM stage6_country_role
),
scenario_count AS (
    SELECT COUNT(*) AS actual_value FROM stage6_scenario
),
scope_row_reconciliation AS (
    SELECT COUNT(*) AS mismatch_count
    FROM (
        SELECT
            role.iso_alpha2,
            COALESCE(summary.source_rows, 0) AS actual_rows,
            CAST(evidence.country_source_rows AS BIGINT) AS expected_rows
        FROM stage6_country_role AS role
        JOIN read_csv_auto(
            '{{COUNTRY_EVIDENCE_FILE}}',
            header = true,
            all_varchar = true
        ) AS evidence USING (iso_alpha2)
        LEFT JOIN stage6_country_summary AS summary
            ON role.iso_alpha2 = summary.iso_alpha2
           AND summary.scenario = 'baseline'
        WHERE COALESCE(summary.source_rows, 0)
            <> CAST(evidence.country_source_rows AS BIGINT)
    ) AS differences
),
sensitivity_reconciliation AS (
    SELECT COUNT(*) AS mismatch_count
    FROM (
        SELECT
            summary.iso_alpha2,
            summary.scenario,
            summary.source_rows,
            summary.distinct_codes,
            CAST(audit.included_rows AS BIGINT) AS audit_rows,
            CAST(audit.included_distinct_codes AS BIGINT) AS audit_codes
        FROM stage6_country_summary AS summary
        JOIN read_csv_auto(
            'outputs/profiling/nonfood_scope_sensitivity_impact.csv',
            header = true,
            all_varchar = true
        ) AS audit
            ON summary.iso_alpha2 = audit.iso_alpha2
           AND summary.scenario = audit.scenario
        WHERE audit.geography_level = 'country_iso'
          AND (
              summary.source_rows <> CAST(audit.included_rows AS BIGINT)
              OR summary.distinct_codes
                  <> CAST(audit.included_distinct_codes AS BIGINT)
          )
    ) AS differences
),
group_count AS (
    SELECT COUNT(*) AS actual_value
    FROM reporting_group
    WHERE reporting_group_id <> 'other_unclassified'
),
code_null_count AS (
    SELECT COUNT(*) AS actual_value
    FROM stage6_record_scope AS scope
    JOIN source_product_record AS record USING (source_record_id)
    WHERE record.code IS NULL
),
invalid_candidate_rows AS (
    SELECT COUNT(*) AS actual_value
    FROM stage6_record_category_assignment
    WHERE assignment_basis = 'candidate_derived'
      AND reporting_group_id = 'other_unclassified'
),
invalid_approved_rows AS (
    SELECT COUNT(*) AS actual_value
    FROM stage6_record_category_assignment AS assignment
    LEFT JOIN category_tag_group_decision AS decision
        ON assignment.source_category_tag = decision.source_category_tag
       AND assignment.reporting_group_id = decision.selected_group_id
    WHERE assignment.assignment_basis = 'approved_only'
      AND decision.selected_group_id IS NULL
),
brand_mapping_status AS (
    SELECT COUNT(*) AS actual_value
    FROM stage6_canonical_brand_assignment AS assignment
    LEFT JOIN brand_name_mapping AS mapping
        ON assignment.canonical_brand_name = mapping.canonical_brand_name
       AND mapping.review_status = 'approved'
    WHERE mapping.canonical_brand_name IS NULL
),
brand_assignment_reconciliation AS (
    SELECT COUNT(*) AS mismatch_count
    FROM (
        SELECT
            coverage.iso_alpha2,
            coverage.scenario,
            coverage.assignment_basis,
            coverage.reporting_group_id,
            coverage.source_rows_with_approved_brand_mapping,
            COALESCE(SUM(counts.canonical_brand_record_assignments), 0)
                AS canonical_brand_rows
        FROM stage6_brand_coverage AS coverage
        LEFT JOIN stage6_canonical_brand_counts AS counts
            ON coverage.iso_alpha2 = counts.iso_alpha2
           AND coverage.scenario = counts.scenario
           AND coverage.assignment_basis = counts.assignment_basis
           AND coverage.reporting_group_id = counts.reporting_group_id
        GROUP BY
            coverage.iso_alpha2,
            coverage.scenario,
            coverage.assignment_basis,
            coverage.reporting_group_id,
            coverage.source_rows_with_approved_brand_mapping
        HAVING coverage.source_rows_with_approved_brand_mapping
            <> COALESCE(SUM(counts.canonical_brand_record_assignments), 0)
    ) AS differences
),
category_assignment_coverage_errors AS (
    SELECT COUNT(*) AS mismatch_count
    FROM stage6_country_summary AS summary
    CROSS JOIN stage6_category_basis AS basis
    LEFT JOIN stage6_category_assignment_coverage AS assignment_coverage
        ON assignment_coverage.iso_alpha2 = summary.iso_alpha2
       AND assignment_coverage.comparison_role = summary.comparison_role
       AND assignment_coverage.scenario = summary.scenario
       AND assignment_coverage.assignment_basis = basis.assignment_basis
    WHERE summary.source_rows_with_category_tags
        < COALESCE(
            assignment_coverage.source_rows_assigned_to_any_substantive_group,
            0
        )
)
SELECT 'selected_country_units' AS check_name,
       actual_value::VARCHAR AS actual_value,
       '5' AS expected_value
FROM selected_country_count
UNION ALL
SELECT 'sensitivity_scenarios',
       actual_value::VARCHAR,
       '3'
FROM scenario_count
UNION ALL
SELECT 'substantive_reporting_groups',
       actual_value::VARCHAR,
       '10'
FROM group_count
UNION ALL
SELECT 'country_baseline_row_reconciliation_mismatches',
       mismatch_count::VARCHAR,
       '0'
FROM scope_row_reconciliation
UNION ALL
SELECT 'country_sensitivity_row_or_code_mismatches',
       mismatch_count::VARCHAR,
       '0'
FROM sensitivity_reconciliation
UNION ALL
SELECT 'missing_code_rows_in_selected_scope',
       actual_value::VARCHAR,
       '0'
FROM code_null_count
UNION ALL
SELECT 'diagnostic_other_rows_in_primary_category_assignment',
       actual_value::VARCHAR,
       '0'
FROM invalid_candidate_rows
UNION ALL
SELECT 'approved_only_assignment_without_decision',
       actual_value::VARCHAR,
       '0'
FROM invalid_approved_rows
UNION ALL
SELECT 'brand_assignments_without_approved_mapping',
       actual_value::VARCHAR,
       '0'
FROM brand_mapping_status
UNION ALL
SELECT 'brand_assignment_denominator_mismatches',
       mismatch_count::VARCHAR,
       '0'
FROM brand_assignment_reconciliation
UNION ALL
SELECT 'category_assignment_coverage_errors',
       mismatch_count::VARCHAR,
       '0'
FROM category_assignment_coverage_errors;
