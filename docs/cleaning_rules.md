# Data Cleaning Rules

## 1. Purpose

This document records the cleaning decisions applied to the Open Food Facts product database for the Global Food Brand Landscape Analysis project.

The objective is to improve the consistency of analytical outputs while preserving the original source values and making each transformation transparent and reproducible.

## 2. Source and Data Structure

The analysis uses a Parquet dataset from Open Food Facts.

The following tables have been created in DuckDB:

- `product_records`: core product-record table.
- `product_countries`: product-to-country-tag bridge table.
- `product_categories`: product-to-category-tag bridge table.
- `product_brands`: product-to-brand-tag bridge table.

The bridge tables represent one-to-many relationships. A single product record may be associated with multiple country, category, or brand tags.

## 3. Category Tag Cleaning

### Issue identified

The initial category bridge table contains tags that indicate an unknown or undefined category rather than a substantive food category.

The following values were identified:

| Original tag | Tag assignments | Affected records |
|---|---:|---:|
| `en:undefined` | 34,974 | 34,974 |
| `en:null` | 1,197 | 1,197 |
| `en:unknown` | 58 | 58 |
| **Total** | **36,229** | **36,229** |

These counts are based on case-insensitive matching after trimming surrounding whitespace.

### Cleaning rule

Exclude the following normalized tag values from valid category analysis:

- `en:undefined`
- `en:null`
- `en:unknown`

The original values remain preserved in `product_categories`. The exclusions are applied only when creating the derived analytical table, `product_categories_clean`.

### Rationale

These values do not identify substantive food categories and would distort category counts if treated as valid categories.

Product records are not removed from `product_records`. Records that contain both valid and invalid category tags retain their valid category assignments. Records containing only these invalid tags remain in the core table but have no valid category assignment in the cleaned category table.

### Impact assessment

The initial category bridge table contains:

- 10,480,049 product-category tag assignments.
- 1,936,163 product records with at least one category tag.
- 116,105 distinct category tags before cleaning.

The initial audit identified:

- 36,229 invalid tag assignments.
- 1,900,484 records with at least one valid category tag.
- 35,679 records whose category tags consist only of the identified invalid values.

The expected number of assignments in `product_categories_clean` is 10,443,820, provided the cleaning rule is applied as specified.

The number of distinct valid category tags after cleaning must be calculated from the derived table and is not assumed in advance.

## 4. Preservation and Traceability

The original core table and bridge tables are retained without destructive cleaning.

Cleaning transformations are implemented in derived tables so that analytical decisions can be reviewed, reproduced, or revised without rebuilding the source data solely to reverse a cleaning decision.

## 5. Limitations

This rule addresses only three explicitly identified invalid category labels. It does not establish that every remaining category tag is semantically correct, consistently translated, or taxonomically equivalent to other tags.

Further normalization should be introduced only where it materially improves the validity or interpretability of the planned analysis.

## 6. Status

- [x] Identified the three invalid category labels.
- [x] Quantified their assignments and affected records.
- [x] Defined a non-destructive exclusion rule.
- [ ] Created and validated `product_categories_clean`.
- [ ] Reviewed further category normalization needs.
