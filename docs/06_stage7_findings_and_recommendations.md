# Stage 7 Findings and Recommendations

## Status and scope

This is the bounded descriptive interpretation of the validated Stage 6 outputs for source snapshot SHA-256 `DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A`. Scope: Indonesia (ID, focal), Malaysia (MY), Philippines (PH), and Singapore (SG) as contextual peers, plus Thailand (TH) as a category-coverage contrast.

<!-- AUTO-GENERATED: analysis-status:START -->
Stage 6 was rerun against the separately validated five-country candidate database after the approved category mappings were applied. It generated 15 country-scenario rows, 300 country-category rows, and 159 mapped-brand assignment rows. The candidate build passed 15 checks and all 11 Stage 6 checks passed; the four published CSVs are byte-identical to the validated candidate run. These checks establish the tested reconciliations and arithmetic for the pinned inputs; they do not prove all mappings semantically correct or the data representative.
<!-- AUTO-GENERATED: analysis-status:END -->

## Executive Summary

**Bottom line:** The snapshot supports a descriptive comparison of Open Food Facts records and category-tag coverage—not a comparison of the actual food markets.

<!-- AUTO-GENERATED: executive-summary:START -->
- **Recorded category coverage:** Indonesia has 12.2% tagged records; the contextual peers range from 11.3% to 17.3%, while Thailand is 62.6%.
- **Category assignments in Indonesia:** 788 of 1,111 tagged records (70.9%) are assigned in the candidate-derived view; the approved-only view assigns 113 (10.2%).
- **Brand and field readiness:** raw brand text is present for 38.8% of Indonesian records, but exact-approved brand mappings cover 0.34%; numeric nutrition data is present for 31.0%.
- **Contributor concentration:** the top five creators account for 87.5% of Indonesian records; across the selected countries the range is 81.7%–87.5%. This is a record-concentration diagnostic, not proof of data fragility.
- **Identifier overlap:** the largest code-based Jaccard value is 0.3152% (MY–SG); 61 shared source-record IDs are reported separately.
<!-- AUTO-GENERATED: executive-summary:END -->

**Business use:** Treat these results as a baseline for database coverage and classification quality. They do not measure products sold, demand, sales, or market share; commercial market decisions need separate, representative market or sales evidence.

## Findings

### 1. Country record counts are measurable; category coverage differs materially

<!-- AUTO-GENERATED: country-scope:START -->
| ISO | Role | Source rows | Rows with `categories_tags` | Category-tag coverage |
|---|---|---:|---:|---:|
| ID | Focal | 9,118 | 1,111 | 12.1847% |
| MY | Contextual peer | 7,426 | 840 | 11.3116% |
| PH | Contextual peer | 9,176 | 1,535 | 16.7284% |
| SG | Contextual peer | 11,986 | 2,074 | 17.3035% |
| TH | Coverage contrast | 11,343 | 7,104 | 62.6289% |
<!-- AUTO-GENERATED: country-scope:END -->

**Interpretation:** ID, MY, PH, and SG have broadly closer observed category-tag coverage to one another than to TH. TH's much higher coverage is why it is used as a separate contrast, not treated as an equivalent peer. This only describes category-tag availability in this snapshot; it does not establish statistical comparability or market representativeness.

All counts are source-record counts. The matching distinct-code counts happen to equal source rows for these five units, but this does not establish that codes identify unique real-world products.

### 2. Candidate-derived group counts show different recorded patterns, but are not approved classifications

The largest candidate-derived reporting groups by assigned source rows in each country, baseline:

<!-- AUTO-GENERATED: top-groups:START -->
| ISO | Largest group | Rows | Share of country rows | Next largest | Rows | Third largest | Rows |
|---|---|---:|---:|---|---:|---|---:|
| ID | Beverages | 231 | 2.5335% | Sweet foods & desserts | 227 | Cereals, potatoes & bakery | 140 |
| MY | Sweet foods & desserts | 184 | 2.4778% | Beverages | 151 | Cereals, potatoes & bakery | 126 |
| PH | Sweet foods & desserts | 371 | 4.0432% | Beverages | 316 | Cereals, potatoes & bakery | 189 |
| SG | Beverages | 630 | 5.2561% | Cereals, potatoes & bakery | 318 | Sweet foods & desserts | 315 |
| TH | Sweet foods & desserts | 1,235 | 10.8878% | Beverages | 1,220 | Cereals, potatoes & bakery | 705 |
<!-- AUTO-GENERATED: top-groups:END -->

**Interpretation:** These are the highest observed record counts in the candidate-derived assignment view. The country/category rows are not mutually exclusive: a record can be assigned to multiple groups. Candidate-derived assignments include taxonomy-based candidates that are not all covered by explicit approved decisions. Do not frame the table as a complete category census, unique-product variety ranking, or evidence of consumer demand.

### 3. Category assignment coverage remains a major limitation

For baseline, the number of category-tagged rows assigned to at least one substantive group differs considerably by mapping basis:

<!-- AUTO-GENERATED: category-coverage:START -->
| ISO | Category-tagged rows | Candidate-derived assigned | Candidate-derived tagged rows without assignment | Approved-only assigned | Approved-only tagged rows without assignment |
|---|---:|---:|---:|---:|---:|
| ID | 1,111 | 788 | 323 | 113 | 998 |
| MY | 840 | 620 | 220 | 84 | 756 |
| PH | 1,535 | 1,273 | 262 | 158 | 1,377 |
| SG | 2,074 | 1,806 | 268 | 263 | 1,811 |
| TH | 7,104 | 4,516 | 2,588 | 673 | 6,431 |
<!-- AUTO-GENERATED: category-coverage:END -->

<!-- AUTO-GENERATED: category-overlap:START -->
There are also rows assigned to multiple groups in the candidate-derived view: ID 136, MY 99, PH 177, SG 276, and TH 1,037. These overlap counts are diagnostics and must not be added to category totals as if groups formed a partition.
<!-- AUTO-GENERATED: category-overlap:END -->

**Interpretation:** The candidate-derived view gives broader coverage than the approved-only sensitivity, while neither resolves all category-tagged records. The “without assignment” value is a coverage gap, not an explanation of the underlying tag dispositions. Keep the two bases separate and do not force unresolved values into groups merely to increase coverage.

### 4. Exact-approved brand mapping is too sparse for a broad brand landscape

Stage 5 evidence reports records with an approved exact brand mapping as follows:

<!-- AUTO-GENERATED: brand-coverage:START -->
| ISO | Rows with approved exact brand mapping | Share of country rows |
|---|---:|---:|
| ID | 31 | 0.3400% |
| MY | 64 | 0.8618% |
| PH | 88 | 0.9590% |
| SG | 341 | 2.8450% |
| TH | 46 | 0.4055% |
<!-- AUTO-GENERATED: brand-coverage:END -->

<!-- AUTO-GENERATED: brand-assignment-note:START -->
Stage 6's 159 rows are assignments across scenarios, assignment bases, country-category groups, and mapped canonical names; they are not 6 distinct brands or an exhaustive brand census.
<!-- AUTO-GENERATED: brand-assignment-note:END -->

**Interpretation:** Coverage rose after two evidence-reviewed canonical mappings, but remains limited (0.3400%–2.8450% of rows in these selected countries) and highly selected. It cannot support broad brand variety, concentration, HHI, dominance, or market-share conclusions. Report the mapping coverage with any mapped-brand counts; do not generalize the mapped-only distribution to all brands in these countries.

### 5. The agreed non-food sensitivity has a small, visible selected-scope impact

The source-row exclusions from baseline are:

<!-- AUTO-GENERATED: nonfood-sensitivity:START -->
| ISO | `exclude_A_B_except_strong_food_signals` | `exclude_all_A_B` |
|---|---:|---:|
| ID | 63 | 63 |
| MY | 1 | 1 |
| PH | 1 | 1 |
| SG | 1 | 1 |
| TH | 2 | 2 |
<!-- AUTO-GENERATED: nonfood-sensitivity:END -->

The two sensitivity scenarios produce equal country row counts for these selected units because no A/B-flagged record in this scope met the existing strong-food-signal rule. Keep baseline and both sensitivities visible; the small count impact does not establish that classifications are error-free or that exclusions should replace the baseline.

### 6. Field availability is uneven and field-specific

The scorecard separates raw field availability from exact-approved brand harmonization. “Numeric nutrition” means at least one numeric nutrient value; a Nutri-Score is counted only for valid A–E grades.

<!-- AUTO-GENERATED: data-readiness:START -->
| ISO | Brand text | Category tags | Ingredient text | Numeric nutrition | Valid Nutri-Score | Packaging | Labels | Exact-approved brand map |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ID | 38.8% | 12.2% | 17.3% | 31.0% | 5.5% | 4.0% | 28.9% | 0.3% |
| MY | 46.2% | 11.3% | 8.6% | 39.7% | 4.6% | 3.4% | 15.1% | 0.9% |
| PH | 60.4% | 16.7% | 13.8% | 52.2% | 10.9% | 4.6% | 10.1% | 1.0% |
| SG | 64.6% | 17.3% | 13.6% | 57.6% | 11.0% | 7.4% | 14.6% | 2.8% |
| TH | 80.4% | 62.6% | 55.6% | 81.2% | 45.6% | 29.9% | 17.2% | 0.4% |
<!-- AUTO-GENERATED: data-readiness:END -->

**Interpretation:** A field's availability is not a guarantee of accuracy, freshness, or representativeness. Use each field only for questions its observed coverage can support. In particular, raw brand text availability must not be confused with exact-approved brand mapping coverage.

### 7. Contributor, source-tag, and creation-time patterns are descriptive diagnostics

The following summaries measure concentration among records and their recorded source tags. They do not establish why a record was added or whether a contributor imported products in bulk.

<!-- AUTO-GENERATED: contributor-diagnostics:START -->
| ISO | Distinct creator values | Top-five creator share | Peak creation year | Peak-year share of dated rows | Peak-day share of dated rows | Largest one-creator/day batch (country share) | Batch category-tag coverage | Top-five category-tag coverage | Other named creators' category-tag coverage | Missing-creator category-tag coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ID | 161 | 87.50% | 2025 | 29.84% | 1.41% | 127 (1.39%) | 0.79% | 7.26% | 46.67% | — |
| MY | 134 | 84.41% | 2026 | 35.27% | 2.36% | 130 (1.75%) | 12.31% | 6.89% | 35.23% | — |
| PH | 140 | 85.96% | 2026 | 27.16% | 3.59% | 328 (3.57%) | 25.91% | 10.07% | 57.53% | — |
| SG | 177 | 82.44% | 2025 | 25.29% | 0.98% | 116 (0.97%) | 20.69% | 10.43% | 49.55% | — |
| TH | 231 | 81.69% | 2025 | 18.53% | 1.15% | 130 (1.15%) | 100.00% | 61.76% | 66.49% | — |

Top three `data_sources_tags` by record count for Indonesia and Thailand:

| ISO | Source tag | Records | Country-record share | Category-tag coverage within source-tagged records |
|---|---|---:|---:|---:|
| ID | `apps` | 4,467 | 48.99% | 20.17% |
| ID | `app-xpiry` | 2,199 | 24.12% | 4.00% |
| ID | `app-smoothie-openfoodfacts` | 1,175 | 12.89% | 57.11% |
| TH | `apps` | 6,828 | 60.20% | 65.28% |
| TH | `app-smoothie-openfoodfacts` | 3,864 | 34.07% | 81.96% |
| TH | `app-macrofactor` | 2,390 | 21.07% | 36.03% |
<!-- AUTO-GENERATED: contributor-diagnostics:END -->

The yearly record table and top source-tag coverage are available in `outputs/profiling/record_creation_year.csv` and `outputs/profiling/source_tag_coverage.csv`. `created_t` is a record-creation timestamp, not a product launch date. The busiest single creator-day ranges from 116 to 328 country records (0.97%–3.57% of each country total). This does not show a country-wide mass-import event. Thailand's category-tag coverage is 62.6%; its top five creators account for 81.69% of records, and category-tag coverage is 61.76% for top-five creators versus 66.49% for other named creators. These descriptive differences cannot identify an import mechanism.

The Open Food Facts schema defines `sources[].import_t` as a source import timestamp, but the pinned 111-column snapshot used here has neither a `sources` field nor `import_t` ([product schema](https://openfoodfacts.github.io/documentation/docs/Product-Opener/schemas/schemas/product/)). Therefore, the bulk-import hypothesis is **not testable from this snapshot**. Creator-day peaks and source tags are indirect diagnostics only; no import event or automated transfer is inferred.

### 8. Product-code overlap is small and does not establish regional commerce

<!-- AUTO-GENERATED: country-code-overlap:START -->
| Country A | Country B | Shared codes | Shared source-record IDs | Code Jaccard index |
|---|---|---:|---:|---:|
| ID | MY | 13 | 13 | 0.0786% |
| ID | PH | 15 | 15 | 0.0821% |
| ID | SG | 12 | 12 | 0.0569% |
| ID | TH | 16 | 16 | 0.0783% |
| MY | PH | 13 | 13 | 0.0784% |
| MY | SG | 61 | 61 | 0.3152% |
| MY | TH | 27 | 27 | 0.1441% |
| PH | SG | 17 | 17 | 0.0804% |
| PH | TH | 11 | 11 | 0.0536% |
| SG | TH | 47 | 47 | 0.2019% |
<!-- AUTO-GENERATED: country-code-overlap:END -->

The source record remains the unit of analysis. A shared code can reflect an identifier reused in the database; it is not evidence that a product is sold, imported, or exported between the countries. The overlap output also distinguishes shared codes from records assigned to more than one country in the source.

### 9. `food_groups_tags` is a diagnostic cross-check, not an inference source

An explicit, conservative crosswalk compares food-group tags with the project's candidate-derived reporting groups. The crosswalk is marked diagnostic-only and does not feed category assignment.

<!-- AUTO-GENERATED: food-groups-crosscheck:START -->
| ISO | Rows with food-group tags | Rows covered by diagnostic crosswalk | Rows compared to candidate groups | Exact group-set agreement | Any group overlap |
|---|---:|---:|---:|---:|---:|
| ID | 731 | 723 | 723 | 23.51% | 95.02% |
| MY | 564 | 551 | 551 | 17.79% | 93.65% |
| PH | 1,171 | 1,156 | 1,156 | 18.25% | 96.02% |
| SG | 1,700 | 1,669 | 1,669 | 26.18% | 92.87% |
| TH | 4,313 | 3,932 | 3,932 | 21.80% | 96.03% |
<!-- AUTO-GENERATED: food-groups-crosscheck:END -->

Agreement is not a precision estimate or semantic validation: the food-group tags are not an independent gold standard, and only tags included in the documented crosswalk can be compared.

## AI-assisted semantic mapping audit

<!-- AUTO-GENERATED: semantic-mapping-audit:START -->
### Primary sample and separate census

The primary sample contains 150 of 1,111 Indonesian category-tagged records, selected deterministically by MD5 rank. The separate Meat & poultry census is reported descriptively and is not pooled with the primary estimate.

| Scope | Records reviewed | Candidate group pairs | Correct | Incorrect | Ambiguous | Insufficient evidence | Confirmed share of all pairs | Exact-set matches |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Primary sample | 150/1,111 | 130 | 97 | 16 | 8 | 9 | 74.6% | 61/150 (40.7%) |
| Meat & poultry census | 8/8 | 11 | 7 | 3 | 1 | 0 | 63.6% | 5/8 (62.5%) |

### Assignment-level estimates and provenance

Primary-sample determinate assignment precision is 97/113 (85.8%); its approximate 95% interval is 80.0%–91.7%. Counting ambiguous and insufficient-evidence assignments as not confirmed, the all-pairs confirmed share is 97/130 (74.6%), with interval 67.6%–81.6%.

| Candidate provenance | Pairs | Correct | Incorrect | Ambiguous | Insufficient evidence | Determinate precision | Approximate 95% interval |
|---|---:|---:|---:|---:|---:|---:|---:|
| Taxonomy-only | 104 | 83 | 8 | 4 | 9 | 83/91 (91.2%) | 85.9%–96.5% |
| Also exact-manual mapped | 26 | 14 | 8 | 4 | 0 | 14/22 (63.6%) | 50.6%–76.6% |

The combined 130 pairs include 26 pairs also supported by an exact-manual mapping; they are not all taxonomy-only candidates. Taxonomy-only precision is 83/91 (91.2%); the overlap subset is shown separately because its agreement differs.

### Per-group determinate precision

Precision uses correct / (correct + incorrect); ambiguous and insufficient-evidence pairs are excluded from that denominator but remain visible below. Intervals are omitted for groups with fewer than 10 candidate pairs or zero observed residual variance.

| Reporting group | Candidate pairs | Correct | Incorrect | Ambiguous | Insufficient evidence | Determinate precision | Approximate 95% interval |
|---|---:|---:|---:|---:|---:|---:|---:|
| `beverages` | 36 | 28 | 2 | 2 | 4 | 28/30 (93.3%) | 85.0%–100.0% |
| `condiments_fats_spreads` | 16 | 13 | 0 | 1 | 2 | 13/13 (100.0%) | Not reported |
| `dairy_eggs` | 11 | 10 | 0 | 1 | 0 | 10/10 (100.0%) | Not reported |
| `fish_seafood` | 4 | 3 | 1 | 0 | 0 | 3/4 (75.0%) | Not reported |
| `fruit_vegetables` | 3 | 0 | 3 | 0 | 0 | 0/3 (0.0%) | Not reported |
| `grains_potatoes_bakery` | 21 | 15 | 4 | 2 | 0 | 15/19 (78.9%) | 61.8%–96.1% |
| `meat_poultry` | 0 | 0 | 0 | 0 | 0 | Not estimable | Not reported |
| `prepared_meals` | 2 | 2 | 0 | 0 | 0 | 2/2 (100.0%) | Not reported |
| `salty_snacks` | 9 | 7 | 1 | 0 | 1 | 7/8 (87.5%) | Not reported |
| `sweet_foods_desserts` | 28 | 19 | 5 | 2 | 2 | 19/24 (79.2%) | 64.0%–94.3% |

In the separate census, the Meat & poultry group has 5/8 supported assignments; no sampling interval applies.

### Record-level agreement, uncertainty, and diagnostic comparison

Exact-set agreement across all primary records is 61/150 (40.7%; approximate 95% interval 33.3%–48.0%). Among the 120 determinate records, it is 61/120 (50.8%). Record-level ambiguity was 12/150 (8.0%); insufficient evidence was 18/150 (12.0%).

Among determinate records, the reviewer supported 57 group pairs absent from the candidate sets, across 50 records. This is an AI-label omission diagnostic, not objective recall.

The diagnostic `food_groups_tags` cross-check exactly matched 17/104 comparable records (16.3%) and had any overlap for 96/104 (92.3%). These tags are not a gold standard and did not inform the AI-assisted labels.

### Error analysis and external evidence

- Taxonomy ancestry can create semantically misleading assignments: three of the eight Meat & poultry census errors involved sauce products whose category ancestry includes meat-based sauces, although product information did not establish meat as an ingredient. Do not equate a flavor name or broad ancestor tag with product composition.
- Source category tags can be contradictory or noisy. The sampled Happy Cola record carried beverage-branch tags, while the Sprite Zero record included vegetable/lettuce tags; external product information helped assess those specific cases.
- Several disagreements involve broad group boundaries (for example, products that plausibly fit both a base-food and snack/dessert group). These cases indicate a need for more operational group definitions, not an automatic rule to force one label.
- The primary-sample omission diagnostic above identifies candidate-coverage cases for targeted review; it is not an objective recall estimate. Do not change mappings or candidate rules from these AI labels alone.

Selected official product-page checks are recorded alongside the affected records:

| Record ID | Product | Sourced evidence and reviewer inference | Reference |
|---|---|---|---|
| 4018050 | Sprite Zero Sugar | The product is identified as Sprite Zero. Coca-Cola Indonesia lists Sprite Zero PET as a carbonated lemon-lime beverage, supporting beverages rather than fruit/vegetables. | [Official source](https://www.coca-cola.com/id/id/brands/sprite) (2026-11-05) |
| 4273083 | Tolak Angin | The official Sido Muncul page identifies Tolak Angin as a standardized herbal preparation, describes medicinal use and dosage, and lists a traditional-medicine BPOM registration. Inference: this product is not one of the ten food reporting groups. | [Official source](https://www.sidomuncul.co.id/id/product/tolak_angin.html) (2026-11-05) |
| 841503 | Haribo happy cola | The product is identified as Happy Cola gummies; HARIBO's official product page lists glucose syrup, sugar, gelatin and confectionery ingredients, supporting sweet foods/desserts rather than beverages. | [Official source](https://www.haribo.com/en-us/products/happy-cola) (2026-11-05) |

### Method and limitations

The 150-record sample is a fixed MD5-ranked sample, not a literal random draw. Approximate 95% intervals use first-order Taylor linearization with a finite-population correction, conditional on the hash ordering approximating simple random sampling without replacement; sparse per-group intervals are suppressed. These intervals describe sampling uncertainty only, not the reliability, calibration, or independence of AI judgments. The assessment is AI-assisted, not human annotation: the separate-context reviewer received product fields but not category tags or candidate mappings, while the coordinating workflow had previously inspected those materials. Reviewer confidence is self-assessed, not calibrated.

The targeted online follow-up reviewed all 48 disputed or uncertain primary-sample records: 30 had supporting product evidence and 18 remained partial or unresolved. 36 records have a source URL and 29 have an exact product-code match. Because records were selected by disagreement/uncertainty, these counts are not a sample-wide accuracy estimate.

No mappings, candidate-generation rules, source records, or original analytical results were changed. The 8-record Meat & poultry census is descriptive and is not pooled into the primary estimate.

Record-level annotations, product evidence, source URLs, and generated metrics: [semantic audit records](../outputs/quality/category_mapping_semantic_audit_records.csv), [review labels](../outputs/quality/category_mapping_semantic_audit_labels.csv), [online evidence log](../outputs/quality/category_mapping_online_evidence_audit.csv), [overall metrics](../outputs/quality/category_mapping_semantic_audit_summary.csv), and [per-group metrics](../outputs/quality/category_mapping_semantic_audit_by_group.csv).
<!-- AUTO-GENERATED: semantic-mapping-audit:END -->

## Recommendations

1. Use the record-based country totals and clearly labeled category assignment tables as descriptive evidence only. Keep ID focal, MY/PH/SG contextual, and TH as the coverage contrast.
2. Show category-tag coverage and both assignment bases alongside every category interpretation. Use the online evidence log to prioritize specific disputed records; do not change broad mapping rules from targeted AI or web checks alone.
3. Keep the exact-approved brand results as a coverage diagnostic only. Do not calculate HHI or broad brand concentration from this mapping subset.
4. Preserve all three non-food scenarios. Do not replace the baseline with an exclusion scenario.
5. Do not reopen Stage 2 broadly. The eight bounded category decisions and four exact brand-spelling decisions are included in the validated Stage 6 outputs. Revisit an exact category, country, or brand mapping only if a concrete finding or proposed conclusion is materially affected; document the evidence, approve the change, then rerun and revalidate affected analyses.
6. Preserve the pinned source snapshot by immutable commit and verified checksum. Build the canonical five-country database from the pinned input; the full database remains optional and is not required for this analysis.
7. These outputs do not answer sales-based market size, market share, demand, or commercial brand dominance. If those are required business questions, identify appropriate external data before attempting those conclusions.

## Limitations

- The source is a collaboratively maintained database, not a census of products sold.
- The source is not representative of products sold and contains no sales or demand measures.
- Category coverage is low in the focal unit and varies substantially across countries.
- Candidate-derived assignments are not all covered by explicit approved decisions; approved-only assignments cover far fewer rows.
- Semantic audit labels are AI-assisted sample judgments, not human ground truth; ambiguous and insufficient-evidence cases remain visible.
- Group assignments overlap, and unassigned category-tagged rows are not disposition-level explanations.
- Exact-approved brand mapping coverage remains limited in the selected country scope.
- `code` is not a validated unique product identifier; source rows remain the primary measurement unit.
- Stage 6 technical validations and the `food_groups_tags` diagnostic do not establish semantic mapping truth, representativeness, or commercial validity.

## Evidence and reproducibility

- Specification and decisions: `docs/05_analysis_specification.md`
- Workflow and quality gates: `docs/03_analysis_workflow.md`
- Country evidence: `outputs/profiling/stage5_country_peer_evidence.csv`
- Field availability: `outputs/profiling/data_readiness_scorecard.csv`
- Contributor and creation-time diagnostics: `outputs/profiling/contributor_year_diagnostics.csv` and `outputs/profiling/record_creation_year.csv`
- Source-tag coverage: `outputs/profiling/source_tag_coverage.csv`
- Country-code overlap: `outputs/profiling/country_code_overlap.csv`
- `food_groups_tags` diagnostic: `outputs/profiling/food_groups_crosscheck.csv`
- Semantic audit records, labels, and metrics: `outputs/quality/category_mapping_semantic_audit_records.csv`, `outputs/quality/category_mapping_semantic_audit_labels.csv`, `outputs/quality/category_mapping_semantic_audit_summary.csv`, and `outputs/quality/category_mapping_semantic_audit_by_group.csv`
- Stage 6 scope: `outputs/analysis/stage6_country_scope.csv`
- Stage 6 category results: `outputs/analysis/stage6_country_category.csv`
- Stage 6 mapped brand results: `outputs/analysis/stage6_country_brand.csv`
- Stage 6 checks: `outputs/analysis/stage6_validation.csv`
- Canonical selected-country database: `data/processed/global_product_landscape_five_country.duckdb`
- Candidate build checks: `outputs/quality/stage6_candidate_build_validation.csv` (15 passed)
- Reproduce with `scripts/run_all.py`; details are in `docs/REPRODUCE.md`.
