# Data Cleaning Rules

## 1. Purpose

This document records the cleaning decisions applied to the Open Food Facts product database for the Global Food Brand Landscape Analysis project.

The objective is to improve the consistency of analytical outputs while preserving the original source tables and making each transformation transparent and reproducible.

Cleaning rules are limited to specific, identified data-quality issues. They do not imply that all remaining category or brand labels have been semantically verified.

## 2. Source and Data Structure

The analysis uses a Parquet dataset from Open Food Facts, processed in DuckDB.

The following tables have been created:

- `product_records`: core product-record table.
- `product_countries`: product-to-country-tag bridge table.
- `product_categories`: original product-to-category-tag bridge table.
- `product_brands`: original product-to-brand-tag bridge table.
- `product_categories_clean`: derived category bridge table excluding three identified invalid category labels.
- `product_brands_clean`: derived brand bridge table with normalized brand tags.

The bridge tables represent one-to-many relationships. A single product record may be associated with multiple country, category, or brand tags.

`record_id` is a technical identifier for the materialized dataset snapshot. It is not a permanent Open Food Facts product identifier.

## 3. Category Tag Cleaning

### 3.1 Issue identified

The initial category bridge table contains tags that indicate an unknown or undefined category rather than a substantive food category.

The following normalized values were identified:

| Normalized tag | Tag assignments | Affected records |
|---|---:|---:|
| `en:undefined` | 34,974 | 34,974 |
| `en:null` | 1,197 | 1,197 |
| `en:unknown` | 58 | 58 |
| **Total** | **36,229** | **36,229** |

These counts are based on case-insensitive matching after trimming surrounding whitespace.

### 3.2 Cleaning rule

Exclude the following normalized tag values from valid category analysis:

- `en:undefined`
- `en:null`
- `en:unknown`

The exclusion condition uses `LOWER(TRIM(category_tag))` so that capitalization and surrounding whitespace do not bypass the rule.

The original values remain preserved in `product_categories`. The exclusion is applied only when creating `product_categories_clean`.

### 3.3 Rationale

These values do not identify substantive food categories and would distort category counts if treated as valid categories.

Product records are not removed from `product_records`. Records containing both valid and invalid category tags retain their valid category assignments. Records containing only the identified invalid tags remain in the core table but have no valid category assignment in the cleaned category table.

### 3.4 Impact assessment

The initial category bridge table contains:

| Metric | Result |
|---|---:|
| Product-category tag assignments before cleaning | 10,480,049 |
| Product records with at least one category tag | 1,936,163 |
| Distinct category tags before cleaning | 116,105 |
| Invalid tag assignments excluded | 36,229 |
| Records with at least one valid category tag | 1,900,484 |
| Records with only the identified invalid category tags | 35,679 |
| Product-category tag assignments after cleaning | 10,443,820 |
| Distinct valid category tags after cleaning | 116,099 |
| Remaining assignments matching the three invalid labels | 0 |

The assignment counts reconcile:

`10,480,049 - 36,229 = 10,443,820`

The cleaned table was validated against the three exclusion rules. The validation returned zero remaining invalid assignments.

The number of records with valid categories and the number of records containing only invalid categories reconcile with the number of records that originally had at least one category tag:

`1,900,484 + 35,679 = 1,936,163`

These metrics describe category-tag coverage in the dataset. They do not establish the completeness of category information for all product records.

## 4. Brand Tag Cleaning

### 4.1 Issue identified

The brand bridge table contains label variations in capitalization. For example, `xx:Carrefour` and `xx:carrefour` become the same normalized string after lowercasing.

An initial audit also checked for the normalized labels `en:null`, `en:unknown`, `en:undefined`, and an empty string. The query returned no matching rows. This result applies only to those specific patterns; it does not establish that all brand tags are valid.

### 4.2 Cleaning rule

Create `product_brands_clean` using the following transformations:

1. Convert brand tags to lowercase using `LOWER()`.
2. Remove surrounding whitespace using `TRIM()`.
3. Exclude `NULL` and empty brand tags.
4. Retain distinct `(record_id, brand_tag)` pairs after normalization.
5. Preserve the original `product_brands` table unchanged.

No brand is removed solely because its label appears unusual or has low frequency. No semantic merging of brands, sub-brands, or corporate entities is performed.

### 4.3 Impact assessment

| Metric | Result |
|---|---:|
| Original product-brand tag assignments | 3,313,249 |
| Product-brand pairs after cleaning | 3,312,414 |
| Difference in pair counts | 835 |
| Records with at least one brand after cleaning | 3,094,218 |
| Distinct normalized brand tags | 479,138 |
| Duplicate `(record_id, brand_tag)` pairs after cleaning | 0 |

The difference between the original and cleaned pair counts is:

`3,313,249 - 3,312,414 = 835`

This difference reflects the combined effects of normalization, exclusion of empty values, and deduplication. It must not be interpreted as the number of invalid brands, since one transformation may cause previously different labels to collapse into the same normalized pair.

Validation confirmed that the cleaned table contains no duplicate `(record_id, brand_tag)` pairs.

The 479,138 distinct normalized labels are not a verified count of unique companies or corporate brands. The count represents distinct strings after the specified transformations. Labels may still include sub-brands, ambiguous values, and naming inconsistencies.

## 5. Preservation and Traceability

The original core table and bridge tables are retained without destructive cleaning.

Cleaning transformations are implemented in derived tables so that analytical decisions can be reviewed, reproduced, or revised without overwriting the original bridge tables.

The cleaning rules are implemented in `sql/02_build_analysis_tables.sql`. The results documented here reflect the DuckDB tables and validation queries executed during the current analysis workflow.

The source Parquet file and the script's environment-specific file path should be documented separately in the project's source and reproducibility documentation.

## 6. Limitations

These cleaning rules address specific structural and label-consistency issues. They do not establish that every remaining category or brand label is semantically correct, consistently translated, or taxonomically equivalent to other labels.

Lowercasing and trimming improve string consistency but do not resolve semantic differences between brands, sub-brands, product lines, or corporate entities.

Open Food Facts records are community-contributed, and data completeness and accuracy may vary. Product-record counts, category-tag counts, and brand-tag counts describe recorded dataset coverage. They must not be interpreted directly as market size, sales volume, market share, or verified company counts.

Further normalization should be introduced only when it materially improves the validity or interpretability of a planned analysis and can be justified by explicit rules.

## 7. Status

### Category cleaning

- [x] Identified three invalid category labels.
- [x] Quantified their assignments and affected records.
- [x] Defined a non-destructive exclusion rule.
- [x] Created `product_categories_clean`.
- [x] Validated the cleaned table; remaining assignments matching the three excluded labels: 0.
- [x] Recorded the cleaned assignment count and distinct valid category-tag count.
- [ ] Assess further category normalization only if required by the analysis.

### Brand cleaning

- [x] Audited selected invalid-label patterns and capitalization variations.
- [x] Created `product_brands_clean` using lowercase normalization and trimming.
- [x] Excluded `NULL` and empty brand tags.
- [x] Validated unique `(record_id, brand_tag)` pairs; duplicate pairs: 0.
- [x] Recorded cleaned pair counts and distinct normalized brand-tag count.
- [ ] Perform semantic brand consolidation only if a specific analysis requires it and defensible mapping rules can be established.
