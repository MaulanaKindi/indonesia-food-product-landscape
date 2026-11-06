CREATE TABLE data_snapshot (
    snapshot_id VARCHAR PRIMARY KEY,
    source_file VARCHAR NOT NULL,
    source_sha256 VARCHAR NOT NULL UNIQUE,
    source_size_bytes UBIGINT NOT NULL,
    source_row_count BIGINT NOT NULL,
    source_column_count INTEGER NOT NULL,
    source_retrieved_on DATE,
    extraction_method VARCHAR NOT NULL
);

INSERT INTO data_snapshot
VALUES (
    '{{SNAPSHOT_ID}}',
    'data/raw/food.parquet',
    '{{SNAPSHOT_ID}}',
    7975461945,
    4828207,
    111,
    NULL,
    'not determined'
);

CREATE TEMP TABLE selected_country_source_tags AS
SELECT source_country_tag
FROM read_csv_auto(
    'data/mappings/country_tag_mapping.csv',
    header = true,
    all_varchar = true
)
WHERE mapping_status = 'approved'
  AND {{SCOPE_CODES_FILTER}};

CREATE TABLE source_product_record AS
SELECT
    CAST(file_row_number + 1 AS BIGINT) AS source_record_id,
    '{{SNAPSHOT_ID}}' AS snapshot_id,
    CAST(file_row_number + 1 AS BIGINT) AS source_row_ordinal,
    source.* EXCLUDE (file_row_number)
FROM read_parquet('data/raw/food.parquet', file_row_number = true) AS source
WHERE {{SOURCE_SCOPE_FILTER}};

CREATE UNIQUE INDEX ux_source_product_record_id
    ON source_product_record (source_record_id);
CREATE UNIQUE INDEX ux_source_product_snapshot_ordinal
    ON source_product_record (snapshot_id, source_row_ordinal);

CREATE TABLE country_unit AS
SELECT
    iso_alpha2,
    reference_name AS country_name
FROM read_csv_auto(
    'data/reference/iso_3166_alpha2.csv',
    header = true,
    all_varchar = true
);
CREATE UNIQUE INDEX ux_country_unit_iso_alpha2
    ON country_unit (iso_alpha2);

CREATE TABLE country_source_tag_mapping AS
SELECT
    source_country_tag,
    iso_alpha2,
    country_name,
    classification,
    mapping_status,
    mapping_basis,
    review_note,
    '{{COUNTRY_MAPPING_VERSION}}' AS mapping_version
FROM read_csv_auto(
    'data/mappings/country_tag_mapping.csv',
    header = true,
    all_varchar = true
);
CREATE UNIQUE INDEX ux_country_source_tag_mapping_tag
    ON country_source_tag_mapping (source_country_tag);

CREATE TABLE reporting_group AS
SELECT
    group_id AS reporting_group_id,
    reporting_group AS reporting_group_label,
    CAST(display_order AS INTEGER) AS display_order,
    framework_status
FROM read_csv_auto(
    'data/reference/category_reporting_group_framework.csv',
    header = true,
    all_varchar = true
);
CREATE UNIQUE INDEX ux_reporting_group_id
    ON reporting_group (reporting_group_id);

CREATE TABLE category_taxonomy_node AS
SELECT
    category_tag,
    name_en,
    direct_parent_tags,
    '{{TAXONOMY_VERSION}}' AS taxonomy_version
FROM taxonomy_nodes_input;
CREATE UNIQUE INDEX ux_category_taxonomy_node_tag_version
    ON category_taxonomy_node (category_tag, taxonomy_version);

CREATE TABLE category_taxonomy_parent AS
SELECT DISTINCT
    node.category_tag AS child_tag,
    parent.parent_tag,
    node.taxonomy_version
FROM category_taxonomy_node AS node,
UNNEST(node.direct_parent_tags) AS parent(parent_tag);
CREATE UNIQUE INDEX ux_category_taxonomy_parent_edge_version
    ON category_taxonomy_parent (child_tag, parent_tag, taxonomy_version);

CREATE TABLE category_tag AS
SELECT
    source_category_tag,
    CAST(records_with_tag AS BIGINT) AS records_with_tag,
    taxonomy_match_status,
    taxonomy_name_en,
    known_parent_tags,
    CAST(taxonomy_min_depth AS INTEGER) AS taxonomy_min_depth,
    CAST(taxonomy_max_depth AS INTEGER) AS taxonomy_max_depth,
    CAST(multiple_parent_paths AS BOOLEAN) AS multiple_parent_paths
FROM read_csv_auto(
    'outputs/profiling/category_reporting_group_candidate_crosswalk.csv',
    header = true,
    all_varchar = true
);
CREATE UNIQUE INDEX ux_category_tag_exact
    ON category_tag (source_category_tag);

CREATE TABLE category_tag_group_decision AS
SELECT
    source_category_tag,
    '{{CATEGORY_MAPPING_VERSION}}' AS mapping_version,
    assignment_status AS decision_status,
    CASE
        WHEN assignment_status = 'manual_group_assignment'
        THEN manual_reporting_group_id
        ELSE NULL
    END AS selected_group_id,
    manual_disposition,
    candidate_rationale AS decision_rationale,
    manual_evidence_tags AS supporting_exact_tags,
    manual_evidence_cooccurrence_rows AS evidence_cooccurrence
FROM read_csv_auto(
    'outputs/profiling/category_reporting_group_candidate_crosswalk.csv',
    header = true,
    all_varchar = true
);
CREATE UNIQUE INDEX ux_category_tag_group_decision_tag_version
    ON category_tag_group_decision (source_category_tag, mapping_version);

CREATE TABLE category_tag_group_candidate AS
SELECT DISTINCT
    crosswalk.source_category_tag,
    '{{CATEGORY_MAPPING_VERSION}}' AS mapping_version,
    candidate.reporting_group_id,
    crosswalk.assignment_status AS candidate_role,
    crosswalk.comparison_role
FROM read_csv_auto(
    'outputs/profiling/category_reporting_group_candidate_crosswalk.csv',
    header = true,
    all_varchar = true
) AS crosswalk,
UNNEST(string_split(crosswalk.candidate_group_ids, ' | '))
    AS candidate(reporting_group_id)
WHERE trim(candidate.reporting_group_id) <> '';
CREATE UNIQUE INDEX ux_category_tag_group_candidate
    ON category_tag_group_candidate (
        source_category_tag,
        mapping_version,
        reporting_group_id,
        candidate_role
    );

CREATE TABLE record_country_source_tag AS
SELECT DISTINCT
    product.source_record_id,
    source_tag.country_tag AS source_country_tag
FROM source_product_record AS product,
UNNEST(list_distinct(product.countries_tags)) AS source_tag(country_tag)
WHERE source_tag.country_tag IS NOT NULL;
CREATE UNIQUE INDEX ux_record_country_source_tag
    ON record_country_source_tag (source_record_id, source_country_tag);

CREATE TABLE record_country AS
SELECT DISTINCT
    assignment.source_record_id,
    mapping.iso_alpha2
FROM record_country_source_tag AS assignment
JOIN country_source_tag_mapping AS mapping
    ON assignment.source_country_tag = mapping.source_country_tag
JOIN country_unit AS unit
    ON mapping.iso_alpha2 = unit.iso_alpha2
WHERE mapping.mapping_status = 'approved'
  AND mapping.iso_alpha2 IS NOT NULL
  AND {{COUNTRY_ASSIGNMENT_SCOPE_FILTER}};
CREATE UNIQUE INDEX ux_record_country
    ON record_country (source_record_id, iso_alpha2);

CREATE TABLE record_category_tag AS
SELECT DISTINCT
    product.source_record_id,
    source_tag.category_tag AS source_category_tag
FROM source_product_record AS product,
UNNEST(list_distinct(product.categories_tags)) AS source_tag(category_tag)
WHERE source_tag.category_tag IS NOT NULL;
CREATE UNIQUE INDEX ux_record_category_tag
    ON record_category_tag (source_record_id, source_category_tag);

CREATE TABLE record_brand_source_value AS
SELECT
    source_record_id,
    brands AS source_brand_name
FROM source_product_record
WHERE brands IS NOT NULL
  AND trim(brands) <> '';
CREATE UNIQUE INDEX ux_record_brand_source_value
    ON record_brand_source_value (source_record_id);

CREATE TABLE brand_name_mapping AS
SELECT
    source_brand_name,
    canonical_brand_name,
    review_status,
    decision_basis,
    reviewed_on,
    '{{BRAND_MAPPING_VERSION}}' AS mapping_version
FROM read_csv_auto(
    'data/mappings/brand_name_manual_decisions.csv',
    header = true,
    all_varchar = true
);
CREATE UNIQUE INDEX ux_brand_name_mapping_source_version
    ON brand_name_mapping (source_brand_name, mapping_version);

CREATE TABLE record_brand_tag AS
SELECT DISTINCT
    product.source_record_id,
    source_tag.brand_tag AS source_brand_tag
FROM source_product_record AS product,
UNNEST(list_distinct(product.brands_tags)) AS source_tag(brand_tag)
WHERE source_tag.brand_tag IS NOT NULL;
CREATE UNIQUE INDEX ux_record_brand_tag
    ON record_brand_tag (source_record_id, source_brand_tag);
