CREATE TEMP TABLE stage6_country_role AS
SELECT *
FROM (
    VALUES
        ('ID', 'focal'),
        ('MY', 'peer_context'),
        ('PH', 'peer_context'),
        ('SG', 'peer_context'),
        ('TH', 'coverage_contrast')
) AS selected_country (iso_alpha2, comparison_role);

CREATE TEMP TABLE stage6_scenario AS
SELECT *
FROM (
    VALUES
        ('baseline', 1),
        ('exclude_A_B_except_strong_food_signals', 2),
        ('exclude_all_A_B', 3)
) AS scenarios (scenario, scenario_order);

CREATE TEMP TABLE stage6_category_basis AS
SELECT *
FROM (
    VALUES
        ('candidate_derived', 1),
        ('approved_only', 2)
) AS bases (assignment_basis, basis_order);

CREATE TEMP TABLE stage6_record_scope AS
SELECT
    country.iso_alpha2,
    role.comparison_role,
    record.source_record_id,
    record.code,
    (
        record.categories_tags IS NOT NULL
        AND len(list_distinct(record.categories_tags)) > 0
    ) AS has_category_tags,
    flags.has_class_a_or_b,
    flags.has_strong_food_signals
FROM record_country AS country
JOIN stage6_country_role AS role
    USING (iso_alpha2)
JOIN source_product_record AS record
    USING (source_record_id)
CROSS JOIN LATERAL (
    SELECT
        (
            EXISTS (
                SELECT 1
                FROM record_category_tag AS tag
                WHERE tag.source_record_id = record.source_record_id
                  AND tag.source_category_tag IN (
                      'en:non-food-products',
                      'en:non-food-stuff',
                      'fr:produits-non-alimentaires',
                      'en:not-food',
                      'pt:not-food',
                      'pt:non-edible',
                      'en:open-products-facts',
                      'en:open-pet-food-facts',
                      'en:open-beauty-facts'
                  )
            )
            OR EXISTS (
                SELECT 1
                FROM record_category_tag AS tag
                JOIN category_tag_group_decision AS decision
                    USING (source_category_tag)
                WHERE tag.source_record_id = record.source_record_id
                  AND decision.manual_disposition = 'exclude_non_food'
            )
        ) AS has_class_a_or_b,
        (
            record.nova_group IS NOT NULL
            AND lower(record.nutriscore_grade) IN ('a', 'b', 'c', 'd', 'e')
            AND record.ingredients_n >= 2
        ) AS has_strong_food_signals
) AS flags;

CREATE TEMP TABLE stage6_scenario_record AS
SELECT
    scope.iso_alpha2,
    scope.comparison_role,
    scenario.scenario,
    scenario.scenario_order,
    scope.source_record_id,
    scope.code,
    scope.has_category_tags,
    scope.has_class_a_or_b,
    scope.has_strong_food_signals
FROM stage6_record_scope AS scope
CROSS JOIN stage6_scenario AS scenario
WHERE scenario.scenario = 'baseline'
   OR NOT scope.has_class_a_or_b
   OR (
       scenario.scenario = 'exclude_A_B_except_strong_food_signals'
       AND scope.has_strong_food_signals
   );

CREATE TEMP TABLE stage6_country_summary AS
WITH totals AS (
    SELECT
        iso_alpha2,
        comparison_role,
        scenario,
        scenario_order,
        COUNT(*) AS source_rows,
        COUNT(DISTINCT code) AS distinct_codes,
        COUNT(*) FILTER (WHERE has_category_tags)
            AS source_rows_with_category_tags,
        COUNT(*) FILTER (WHERE has_class_a_or_b)
            AS included_rows_with_class_a_or_b,
        COUNT(*) FILTER (
            WHERE has_class_a_or_b AND has_strong_food_signals
        ) AS retained_a_b_rows_with_strong_food_signals
    FROM stage6_scenario_record
    GROUP BY iso_alpha2, comparison_role, scenario, scenario_order
),
baseline AS (
    SELECT
        iso_alpha2,
        source_rows AS baseline_source_rows,
        distinct_codes AS baseline_distinct_codes
    FROM totals
    WHERE scenario = 'baseline'
)
SELECT
    totals.iso_alpha2,
    totals.comparison_role,
    totals.scenario,
    totals.scenario_order,
    totals.source_rows,
    totals.distinct_codes,
    totals.source_rows_with_category_tags,
    ROUND(
        100.0 * totals.source_rows_with_category_tags
        / NULLIF(totals.source_rows, 0),
        4
    ) AS category_tags_coverage_pct,
    totals.included_rows_with_class_a_or_b,
    totals.retained_a_b_rows_with_strong_food_signals,
    baseline.baseline_source_rows - totals.source_rows AS excluded_source_rows
FROM totals
JOIN baseline USING (iso_alpha2);

CREATE TEMP TABLE stage6_record_category_assignment AS
WITH tag_group AS (
    SELECT DISTINCT
        tag.source_category_tag,
        candidate.reporting_group_id,
        'candidate_derived' AS assignment_basis
    FROM record_category_tag AS tag
    JOIN category_tag_group_candidate AS candidate
        USING (source_category_tag)
    WHERE candidate.candidate_role IN (
            'single_group_candidate',
            'manual_group_assignment'
        )
      AND candidate.comparison_role = 'primary_candidate'
      AND candidate.reporting_group_id <> 'other_unclassified'

    UNION

    SELECT DISTINCT
        tag.source_category_tag,
        decision.selected_group_id AS reporting_group_id,
        'approved_only' AS assignment_basis
    FROM record_category_tag AS tag
    JOIN category_tag_group_decision AS decision
        USING (source_category_tag)
    WHERE decision.selected_group_id IS NOT NULL
      AND decision.selected_group_id <> 'other_unclassified'
),
record_group AS (
    SELECT DISTINCT
        tag.source_record_id,
        tag_group.source_category_tag,
        tag_group.reporting_group_id,
        tag_group.assignment_basis
    FROM record_category_tag AS tag
    JOIN tag_group USING (source_category_tag)
)
SELECT DISTINCT
    scenario.iso_alpha2,
    scenario.comparison_role,
    scenario.scenario,
    scenario.scenario_order,
    record_group.assignment_basis,
    record_group.source_category_tag,
    record_group.reporting_group_id,
    scenario.source_record_id
FROM stage6_scenario_record AS scenario
JOIN record_group
    ON scenario.source_record_id = record_group.source_record_id;

CREATE TEMP TABLE stage6_category_assignment_coverage AS
SELECT
    iso_alpha2,
    comparison_role,
    scenario,
    scenario_order,
    assignment_basis,
    COUNT(DISTINCT source_record_id)
        AS source_rows_assigned_to_any_substantive_group
FROM stage6_record_category_assignment
GROUP BY
    iso_alpha2,
    comparison_role,
    scenario,
    scenario_order,
    assignment_basis;

CREATE TEMP TABLE stage6_group_overlap AS
WITH per_record AS (
    SELECT
        iso_alpha2,
        comparison_role,
        scenario,
        scenario_order,
        assignment_basis,
        source_record_id,
        COUNT(DISTINCT reporting_group_id) AS group_count
    FROM stage6_record_category_assignment
    GROUP BY
        iso_alpha2,
        comparison_role,
        scenario,
        scenario_order,
        assignment_basis,
        source_record_id
)
SELECT
    iso_alpha2,
    comparison_role,
    scenario,
    scenario_order,
    assignment_basis,
    COUNT(*) FILTER (WHERE group_count > 1)
        AS source_rows_in_multiple_groups
FROM per_record
GROUP BY iso_alpha2, comparison_role, scenario, scenario_order, assignment_basis;

CREATE TEMP TABLE stage6_category_group_counts AS
SELECT
    assignment.iso_alpha2,
    assignment.comparison_role,
    assignment.scenario,
    assignment.scenario_order,
    assignment.assignment_basis,
    assignment.reporting_group_id,
    COUNT(DISTINCT assignment.source_record_id) AS group_source_rows,
    COUNT(DISTINCT record.code) AS group_distinct_codes
FROM stage6_record_category_assignment AS assignment
JOIN source_product_record AS record
    USING (source_record_id)
GROUP BY
    assignment.iso_alpha2,
    assignment.comparison_role,
    assignment.scenario,
    assignment.scenario_order,
    assignment.assignment_basis,
    assignment.reporting_group_id;

CREATE TEMP TABLE stage6_brand_coverage AS
SELECT
    assignment.iso_alpha2,
    assignment.comparison_role,
    assignment.scenario,
    assignment.scenario_order,
    assignment.assignment_basis,
    assignment.reporting_group_id,
    COUNT(DISTINCT assignment.source_record_id) AS category_group_source_rows,
    COUNT(DISTINCT brand.source_record_id) AS source_rows_with_brand_text,
    COUNT(DISTINCT brand.source_record_id) FILTER (
        WHERE mapping.review_status = 'approved'
    ) AS source_rows_with_approved_brand_mapping,
    COUNT(DISTINCT mapping.canonical_brand_name) FILTER (
        WHERE mapping.review_status = 'approved'
    ) AS approved_canonical_brand_names_present
FROM stage6_record_category_assignment AS assignment
LEFT JOIN record_brand_source_value AS brand
    ON assignment.source_record_id = brand.source_record_id
LEFT JOIN brand_name_mapping AS mapping
    ON brand.source_brand_name = mapping.source_brand_name
GROUP BY
    assignment.iso_alpha2,
    assignment.comparison_role,
    assignment.scenario,
    assignment.scenario_order,
    assignment.assignment_basis,
    assignment.reporting_group_id;

CREATE TEMP TABLE stage6_canonical_brand_assignment AS
SELECT DISTINCT
    assignment.iso_alpha2,
    assignment.comparison_role,
    assignment.scenario,
    assignment.scenario_order,
    assignment.assignment_basis,
    assignment.reporting_group_id,
    mapping.canonical_brand_name,
    assignment.source_record_id
FROM stage6_record_category_assignment AS assignment
JOIN record_brand_source_value AS brand
    ON assignment.source_record_id = brand.source_record_id
JOIN brand_name_mapping AS mapping
    ON brand.source_brand_name = mapping.source_brand_name
WHERE mapping.review_status = 'approved';

CREATE TEMP TABLE stage6_canonical_brand_counts AS
SELECT
    iso_alpha2,
    comparison_role,
    scenario,
    scenario_order,
    assignment_basis,
    reporting_group_id,
    canonical_brand_name,
    COUNT(DISTINCT source_record_id) AS canonical_brand_record_assignments
FROM stage6_canonical_brand_assignment
GROUP BY
    iso_alpha2,
    comparison_role,
    scenario,
    scenario_order,
    assignment_basis,
    reporting_group_id,
    canonical_brand_name;

COPY (
    SELECT
        '{{SNAPSHOT_ID}}' AS snapshot_sha256,
        summary.iso_alpha2,
        summary.comparison_role,
        summary.scenario,
        summary.source_rows,
        summary.distinct_codes,
        summary.source_rows_with_category_tags,
        summary.category_tags_coverage_pct,
        summary.included_rows_with_class_a_or_b,
        summary.retained_a_b_rows_with_strong_food_signals,
        summary.excluded_source_rows
    FROM stage6_country_summary AS summary
    ORDER BY
        summary.iso_alpha2,
        summary.scenario_order
) TO '{{ANALYSIS_OUTPUT_DIR}}/stage6_country_scope.csv'
    (HEADER, DELIMITER ',');

COPY (
    SELECT
        '{{SNAPSHOT_ID}}' AS snapshot_sha256,
        country.iso_alpha2,
        country.comparison_role,
        country.scenario,
        basis.assignment_basis,
        group_ref.reporting_group_id,
        group_ref.reporting_group_label,
        country.source_rows AS country_source_rows,
        country.distinct_codes AS country_distinct_codes,
        country.source_rows_with_category_tags,
        country.category_tags_coverage_pct,
        COALESCE(group_count.group_source_rows, 0) AS group_source_rows,
        COALESCE(group_count.group_distinct_codes, 0) AS group_distinct_codes,
        COALESCE(
            assignment_coverage.source_rows_assigned_to_any_substantive_group,
            0
        ) AS source_rows_assigned_to_any_substantive_group,
        country.source_rows_with_category_tags
            - COALESCE(
                assignment_coverage
                    .source_rows_assigned_to_any_substantive_group,
                0
            ) AS category_tagged_rows_without_substantive_group_assignment,
        ROUND(
            100.0 * COALESCE(
                assignment_coverage
                    .source_rows_assigned_to_any_substantive_group,
                0
            ) / NULLIF(country.source_rows_with_category_tags, 0),
            4
        ) AS substantive_group_assignment_coverage_of_category_tagged_rows_pct,
        ROUND(
            100.0 * COALESCE(group_count.group_source_rows, 0)
            / NULLIF(country.source_rows, 0),
            4
        ) AS group_share_of_country_rows_pct,
        ROUND(
            100.0 * COALESCE(group_count.group_source_rows, 0)
            / NULLIF(country.source_rows_with_category_tags, 0),
            4
        ) AS group_share_of_category_tagged_rows_pct,
        COALESCE(overlap.source_rows_in_multiple_groups, 0)
            AS source_rows_in_multiple_groups,
        COALESCE(brand_coverage.category_group_source_rows, 0)
            AS category_group_source_rows_for_brand_coverage,
        COALESCE(brand_coverage.source_rows_with_brand_text, 0)
            AS source_rows_with_brand_text,
        COALESCE(brand_coverage.source_rows_with_approved_brand_mapping, 0)
            AS source_rows_with_approved_brand_mapping,
        ROUND(
            100.0 * COALESCE(
                brand_coverage.source_rows_with_approved_brand_mapping, 0
            ) / NULLIF(country.source_rows, 0),
            4
        ) AS approved_brand_mapping_coverage_of_country_rows_pct,
        ROUND(
            100.0 * COALESCE(
                brand_coverage.source_rows_with_approved_brand_mapping, 0
            ) / NULLIF(brand_coverage.category_group_source_rows, 0),
            4
        ) AS approved_brand_mapping_coverage_of_category_group_rows_pct,
        COALESCE(brand_coverage.approved_canonical_brand_names_present, 0)
            AS approved_canonical_brand_names_present
    FROM stage6_country_summary AS country
    CROSS JOIN stage6_category_basis AS basis
    CROSS JOIN reporting_group AS group_ref
    LEFT JOIN stage6_category_group_counts AS group_count
        ON group_count.iso_alpha2 = country.iso_alpha2
       AND group_count.comparison_role = country.comparison_role
       AND group_count.scenario = country.scenario
       AND group_count.assignment_basis = basis.assignment_basis
       AND group_count.reporting_group_id = group_ref.reporting_group_id
    LEFT JOIN stage6_category_assignment_coverage AS assignment_coverage
        ON assignment_coverage.iso_alpha2 = country.iso_alpha2
       AND assignment_coverage.comparison_role = country.comparison_role
       AND assignment_coverage.scenario = country.scenario
       AND assignment_coverage.assignment_basis = basis.assignment_basis
    LEFT JOIN stage6_group_overlap AS overlap
        ON overlap.iso_alpha2 = country.iso_alpha2
       AND overlap.comparison_role = country.comparison_role
       AND overlap.scenario = country.scenario
       AND overlap.assignment_basis = basis.assignment_basis
    LEFT JOIN stage6_brand_coverage AS brand_coverage
        ON brand_coverage.iso_alpha2 = country.iso_alpha2
       AND brand_coverage.comparison_role = country.comparison_role
       AND brand_coverage.scenario = country.scenario
       AND brand_coverage.assignment_basis = basis.assignment_basis
       AND brand_coverage.reporting_group_id = group_ref.reporting_group_id
    WHERE group_ref.reporting_group_id <> 'other_unclassified'
    ORDER BY
        country.iso_alpha2,
        country.scenario_order,
        basis.basis_order,
        group_ref.display_order
) TO '{{ANALYSIS_OUTPUT_DIR}}/stage6_country_category.csv'
    (HEADER, DELIMITER ',');

COPY (
    SELECT
        '{{SNAPSHOT_ID}}' AS snapshot_sha256,
        counts.iso_alpha2,
        counts.comparison_role,
        counts.scenario,
        counts.assignment_basis,
        counts.reporting_group_id,
        group_ref.reporting_group_label,
        counts.canonical_brand_name,
        brand_coverage.category_group_source_rows,
        brand_coverage.source_rows_with_approved_brand_mapping
            AS mapped_brand_record_assignment_denominator,
        counts.canonical_brand_record_assignments,
        ROUND(
            100.0 * counts.canonical_brand_record_assignments
            / NULLIF(
                brand_coverage.source_rows_with_approved_brand_mapping,
                0
            ),
            4
        ) AS share_of_mapped_brand_record_assignments_pct
    FROM stage6_canonical_brand_counts AS counts
    JOIN stage6_brand_coverage AS brand_coverage
        ON counts.iso_alpha2 = brand_coverage.iso_alpha2
       AND counts.comparison_role = brand_coverage.comparison_role
       AND counts.scenario = brand_coverage.scenario
       AND counts.assignment_basis = brand_coverage.assignment_basis
       AND counts.reporting_group_id = brand_coverage.reporting_group_id
    JOIN reporting_group AS group_ref
        ON counts.reporting_group_id = group_ref.reporting_group_id
    ORDER BY
        counts.iso_alpha2,
        counts.scenario_order,
        counts.assignment_basis,
        group_ref.display_order,
        counts.canonical_brand_name
) TO '{{ANALYSIS_OUTPUT_DIR}}/stage6_country_brand.csv'
    (HEADER, DELIMITER ',');
