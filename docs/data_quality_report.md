# Data Quality Report

## 1. Purpose

This report documents the main data quality characteristics and analytical limitations identified during the preparation of the Open Food Facts dataset for the Global Food Brand Landscape Analysis project.

The assessment focuses on record structure, brand and category labels, country assignments, and the consistency of derived analytical tables.

## 2. Source Dataset and Scope

The project uses a Parquet export of the Open Food Facts product database.

The source contains approximately **4.83 million product records**. The analysis focuses on product records, brand labels, product categories, and country tags.

Open Food Facts is a community-contributed database. Its records reflect the information submitted to and maintained in the database, not a complete census of products available in each market.

## 3. Key Data Quality Findings

### 3.1 Record identifiers and product codes

A sequential `record_id` was generated during data preparation to identify rows within the analysis tables.

The source `code` field is retained as a string to preserve its original representation. Source codes may repeat across records, and records sharing a code may contain different information.

Repeated codes are therefore not automatically treated as duplicates. The generated `record_id` is an analysis-row identifier, not a permanent identifier across independent rebuilds of the dataset.

### 3.2 Brand information

Brand information is incomplete across the dataset.

In the Indonesia subset, 9,118 product records were associated with the Indonesia country tag:

- Records with at least one cleaned brand label: 3,534
- Records without a cleaned brand label: 5,584
- Records with exactly one cleaned brand label: 3,459
- Records with multiple cleaned brand labels: 75

Brand coverage was **38.76%** of records in this Indonesia subset.

The brand distribution analysis uses records with exactly one cleaned brand label. This avoids counting a single record under multiple brand labels in the concentration calculation, but it excludes records with multiple labels and therefore does not represent every branded record.

Brand labels should not automatically be interpreted as distinct companies. Different labels may refer to related brands, subsidiaries, or naming variants.

### 3.3 Category information

The category bridge table expands product records into record-category associations. Consequently, one record may contribute to multiple categories.

The initial category bridge table contained 10,480,049 associations. After excluding placeholder labels such as `en:null`, `en:unknown`, and `en:undefined`, and removing duplicate record-category pairs, the cleaned table contained 10,443,820 associations.

Category record counts are therefore counts of associated records, not mutually exclusive market segments. Summing counts across categories may count the same record more than once.

### 3.4 Country information

The country bridge table expands records into record-country associations. A product record may be associated with multiple country tags.

The analysis maps 13 selected country tags to readable country names and excludes global or administrative labels from the country comparison.

Country totals may overlap and should not be summed to estimate the number of unique products in the database.

Differences between record counts and distinct source-code counts were small in some country subsets. This comparison is a sensitivity check only; it does not establish that every source code identifies a unique physical product.

### 3.5 Brand and category label normalization

The preparation process trims and normalizes labels and excludes selected placeholder values. Duplicate record-label pairs are removed from the cleaned bridge tables.

The initial brand bridge table contained 3,313,249 associations, compared with 3,312,414 associations in the cleaned table. The difference of 835 associations reflects the combined effects of cleaning and duplicate removal; it should not be interpreted as 835 invalid source records.

Normalization does not establish that different labels refer to the same underlying brand. No unsupported brand-merging rules are applied.

## 4. Validation Results

The SQL validation script contains 14 checks covering:

- Null or duplicate record identifiers
- Duplicate or invalid brand associations
- Duplicate or invalid category associations
- Duplicate or blank country associations
- Reconciliation of Indonesia brand coverage counts
- Reconciliation of single-brand record counts
- Logical ordering of top-five, top-ten, and top-twenty concentration metrics

All 14 checks returned an `issue_count` of zero in the tested analysis environment.

These results support the internal consistency of the tested tables and metrics. They do not establish that the source database is complete, error-free, representative, or free from classification errors.

## 5. Implications for Interpretation

The analysis describes the structure of recorded product and brand information in Open Food Facts. It does not measure sales, revenue, consumption, distribution, or market share.

In particular:

- Product-record counts are not sales volumes.
- Brand-record concentration is not market-share concentration.
- A high category record count does not necessarily indicate greater commercial demand.
- A low brand coverage rate may affect comparisons between countries or categories.
- Country and category counts may overlap because the underlying relationships are many-to-many.

Findings should therefore be interpreted as patterns in the available database rather than definitive estimates of the food market.

## 6. Overall Assessment

The prepared analytical tables passed the implemented structural and reconciliation checks. The dataset is suitable for exploratory analysis of recorded product, category, country, and brand-label patterns, subject to the limitations described above.

The principal remaining limitations concern source coverage, label consistency, and the absence of sales or other direct market-size measures. These limitations should be carried into the metric definitions, findings, and final project README.
