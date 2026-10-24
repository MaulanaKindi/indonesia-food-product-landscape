# Metric Definitions

## 1. Purpose

This document defines the metrics used in the Global Food Brand Landscape Analysis project. It specifies each metric's unit of analysis, denominator, calculation logic, and interpretation limits.

The analysis uses product records and associated country, category, and brand tags from Open Food Facts. Unless explicitly stated otherwise, the metrics describe recorded database information rather than the commercial performance of the food market.

## 2. Country Landscape Metrics

### 2.1 Recorded Product Records by Country

**Definition:** Number of distinct dataset records assigned to each selected country tag, calculated using `COUNT(DISTINCT record_id)`.

**Unit:** Dataset records.

**Country selection:** Thirteen explicitly mapped country tags. Non-country labels such as `en:world` and `en:worldwide` are excluded.

**Multi-country handling:** A record assigned to multiple countries is counted once in each applicable country. Therefore, country-level totals overlap and must not be summed to estimate the number of globally unique products.

**Sensitivity check:** Compare record counts with distinct non-empty product codes. Repeated codes are not automatically deduplicated because records sharing a code may have different attributes.

**Interpretation limit:** These figures describe product records documented in Open Food Facts, not total products sold, market size, sales volume, brand market share, or consumer demand. Differences between countries may reflect both underlying product coverage and differences in database contribution and completeness.

**Scope limitation:** The analysis includes thirteen selected countries. It is not an exhaustive or statistically representative comparison of all countries.

## 3. Category Landscape Metrics

### 3.1 Recorded Product Records by Category

**Definition:** Number of distinct dataset records associated with each valid category tag in `product_categories_clean`, calculated using `COUNT(DISTINCT record_id)`.

**Unit:** Dataset records per category.

**Category selection:** Categories are derived from cleaned category-tag associations. The placeholder tags `en:null`, `en:unknown`, and `en:undefined` are excluded according to the implemented cleaning rules.

**Multi-category handling:** A record associated with multiple categories is counted once in each applicable category. Category totals therefore overlap and should not be summed to estimate the number of unique products.

**Ranking:** The category analysis identifies the top 20 categories by recorded product-record count.

**Interpretation limit:** A higher category count indicates more records associated with that category in the analyzed database. It does not establish higher sales, consumer demand, revenue, market size, or commercial importance.

### 3.2 Records with Brand Information by Category

**Definition:** Number of distinct records in a category that have at least one associated cleaned brand label in `product_brands_clean`.

**Unit:** Dataset records per category.

**Calculation logic:** A category record is considered to have brand information if its `record_id` appears in the cleaned brand bridge table with at least one valid brand association.

**Interpretation limit:** This metric measures the presence of cleaned brand information, not the accuracy or completeness of that information. A record with multiple brand labels is counted once in the branded-record count for a category.

### 3.3 Category Brand Coverage Percentage

**Definition:** Percentage of distinct records in a category that have at least one cleaned brand label.

**Formula:**

`Brand coverage (%) = Records with at least one cleaned brand label / Distinct records in the category × 100`

**Numerator:** Distinct category records with at least one association in `product_brands_clean`.

**Denominator:** Distinct records associated with the category in `product_categories_clean`.

**Unit:** Percentage.

**Interpretation limit:** The percentage measures brand-field coverage among recorded products in each category. It does not measure brand penetration in the commercial market or the proportion of market sales attributable to branded products.

**Comparison limitation:** Differences in brand coverage across categories may reflect differences in record completeness, contribution practices, or category composition. They should not automatically be interpreted as differences in market transparency or competitive structure.

### 3.4 Distinct Brand Labels by Category

**Definition:** Number of distinct cleaned brand-tag strings associated with records in a category.

**Unit:** Distinct normalized brand labels per category.

**Calculation logic:** Count distinct `brand_tag` values from the cleaned brand associations linked to records in each category.

**Interpretation limit:** This metric counts distinct normalized label strings, not verified companies, corporate groups, or independent market competitors. Different labels may refer to related brands, sub-brands, or naming variants.

### 3.5 Exploratory Brand-Label-to-Branded-Record Ratio

**Definition:** Ratio of distinct cleaned brand labels associated with a category to the number of branded records in that category, as calculated in the exploratory category query.

**Formula:**

`Exploratory ratio = Distinct brand labels in category / Branded records in category`

**Unit:** Ratio.

**Status:** Exploratory only; not a core measure of market diversity or competition.

**Interpretation limit:** This ratio is not the average number of brands per product. The numerator counts distinct labels across the category, while the denominator counts records with brand information. It is sensitive to database coverage, label normalization, category size, and the presence of sub-brands or inconsistent naming.

## 4. Indonesian Brand Landscape Metrics

### 4.1 Indonesia Record Base

**Definition:** Number of distinct dataset records associated with the selected Indonesia country tag.

**Unit:** Dataset records.

**Observed result:** 9,118 records.

**Scope:** This is the denominator for the Indonesian brand-coverage analysis. It represents records associated with the selected Indonesia tag, not all food products sold in Indonesia.

### 4.2 Records with Brand Information in Indonesia

**Definition:** Number of Indonesia-associated records with at least one cleaned brand label in `product_brands_clean`.

**Unit:** Dataset records.

**Observed result:** 3,534 records.

**Interpretation limit:** The result indicates how many records in the selected Indonesia subset have cleaned brand information. It does not establish the completeness of brand information in the Indonesian food market.

### 4.3 Records without Brand Information in Indonesia

**Definition:** Number of Indonesia-associated records without any valid association in `product_brands_clean`.

**Unit:** Dataset records.

**Observed result:** 5,584 records.

**Calculation logic:** Indonesia-associated records minus records with at least one cleaned brand label.

**Reconciliation:**

`9,118 - 3,534 = 5,584`

**Interpretation limit:** These records lack a cleaned brand association under the implemented rules. This does not prove that the corresponding physical products are unbranded.

### 4.4 Indonesian Brand Coverage Percentage

**Definition:** Percentage of Indonesia-associated records with at least one cleaned brand label.

**Formula:**

`Brand coverage (%) = Records with at least one cleaned brand label / Indonesia record base × 100`

**Numerator:** 3,534 records.

**Denominator:** 9,118 records.

**Observed result:** 38.76%.

**Interpretation limit:** The result describes brand-label coverage in the selected database subset. It is not an estimate of the proportion of Indonesian food products or sales accounted for by brands.

### 4.5 Records with Exactly One Brand Label

**Definition:** Number of Indonesia-associated records linked to exactly one distinct cleaned brand label.

**Unit:** Dataset records.

**Observed result:** 3,459 records.

**Use:** This subset forms the denominator for the Indonesian single-brand-label distribution and concentration analysis.

### 4.6 Records with Multiple Brand Labels

**Definition:** Number of Indonesia-associated records linked to more than one distinct cleaned brand label.

**Unit:** Dataset records.

**Observed result:** 75 records.

**Use:** These records are excluded from the single-brand-label distribution to avoid assigning the same record to multiple brand labels in the concentration calculation.

**Reconciliation:**

`Records with brand information = Records with exactly one brand label + Records with multiple brand labels`

`3,534 = 3,459 + 75`

**Interpretation limit:** Exclusion from the single-label analysis is a methodological choice. It does not imply that multi-label records are invalid.

### 4.7 Recorded Product Records by Brand Label in Indonesia

**Definition:** Number of records in the Indonesia subset associated with each cleaned brand label, restricted to records with exactly one cleaned brand label.

**Unit:** Dataset records per brand label.

**Ranking:** Brand labels are ranked by descending record count.

**Denominator for percentages:** 3,459 single-brand-label records.

**Formula:**

`Brand-label record percentage = Records assigned to the brand label / 3,459 × 100`

**Interpretation limit:** These percentages describe the distribution of records in the selected single-brand-label subset. They are not sales shares, revenue shares, or market shares.

**Label limitation:** Distinct labels are kept separate unless a defensible brand-mapping rule is established. Similar labels may represent related entities, but they are not automatically merged.

### 4.8 Cumulative Brand-Label Record Percentage

**Definition:** Cumulative percentage of single-brand-label records accounted for by brand labels ranked from highest to lowest record count.

**Formula:**

`Cumulative percentage at rank k = Sum of record counts for ranks 1 through k / 3,459 × 100`

**Unit:** Percentage.

**Use:** Describes how records are distributed across the most frequently recorded brand labels.

**Interpretation limit:** Cumulative record concentration must not be described as market-share concentration because the dataset contains no sales or revenue measures.

### 4.9 Top-5, Top-10, and Top-20 Record Concentration

**Definition:** Percentage of single-brand-label records associated with the five, ten, or twenty highest-ranked brand labels in the Indonesia subset.

**Formula:**

`Top-k record concentration (%) = Sum of records for the top k brand labels / 3,459 × 100`

**Observed results:**

| Metric | Recorded result |
|---|---:|
| Top-5 record concentration | 5.44% |
| Top-10 record concentration | 8.82% |
| Top-20 record concentration | 13.47% |

**Interpretation limit:** These figures measure concentration of recorded product records among the most frequently appearing labels. They do not measure market concentration, competitive intensity, or the distribution of sales across companies.

**Comparability limitation:** Results depend on the selected country tag, cleaned brand labels, single-label inclusion rule, and dataset coverage.

### 4.10 Distinct Brand Labels in the Indonesian Single-Label Analysis

**Definition:** Number of distinct cleaned brand labels represented in the Indonesian subset of records with exactly one cleaned brand label.

**Unit:** Distinct normalized brand labels.

**Observed result:** 1,754 labels.

**Interpretation limit:** This is a count of normalized label strings in the selected subset, not a verified count of unique companies or independent competitors.

## 5. General Counting and Interpretation Rules

### 5.1 Record identifiers

`record_id` identifies a row within the current materialized dataset snapshot. It is not a permanent product identifier across independent rebuilds.

### 5.2 Bridge-table associations

Country, category, and brand bridge tables represent record-to-label relationships. One record may have multiple associated labels. Counts across labels may therefore overlap.

### 5.3 Brand-label normalization

Brand metrics use `product_brands_clean`. Lowercasing, trimming, and removal of duplicate record-label pairs improve string consistency but do not establish semantic equivalence between labels.

### 5.4 Missing information

Records without a cleaned brand association are treated as records without brand information for the purpose of these metrics. Missing brand information is not interpreted as proof that a product has no brand.

### 5.5 No sales-based metrics

The project does not contain verified sales, revenue, volume, distribution, or market-share data. No metric in this document should be interpreted as a direct estimate of those quantities.

## 6. Validation and Reproducibility

The SQL validation script is `sql/06_validation_checks.sql`. It checks structural integrity and selected metric reconciliations, including brand coverage and the ordering of top-five, top-ten, and top-twenty record concentration.

The tested validation run returned zero issues across all 14 checks. This supports the internal consistency of the tested tables and calculations but does not establish source-data accuracy, completeness, or market representativeness.

Metric definitions should be revised if the SQL implementation, country mapping, cleaning rules, or analytical subset changes. Any such revision should be documented and validated against the corresponding query outputs.
