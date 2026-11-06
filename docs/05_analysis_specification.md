# Stage 5–6 Analysis Specification and Results

## Purpose and Status

This document records the owner-approved scope and measurement protocol, plus the current validated Stage 6 descriptive outputs. The owner approved Indonesia (ID) as the focal unit, Malaysia/Philippines/Singapore (MY/PH/SG) as contextual peers, and Thailand (TH) as a separate coverage contrast. These choices support descriptive comparison only; they do not establish representativeness or commercial similarity.

Stage 2 is not fully harmonized. On 2026-11-04, three additional exact category tags and two exact-text brand variant pairs were approved after evidence review. The three category decisions bring the maintained total to 59; the brand mapping now has 60 exact source values across 13 canonical groups. These changes are included in the current separately validated candidate-backed Stage 5/6 outputs. Do not resume broad category or brand review without new material evidence.

The Stage 6 results below were regenerated after the eight bounded category decisions (the earlier five plus these three additional tags) using a separately validated compact candidate built from the canonical five-country database. Stage 7 findings now reflect these current outputs.

## Evidence Baseline

| Evidence | Observed value | Implication |
|---|---:|---|
| Current source snapshot | Hugging Face commit `31f31c441274c095718cc88ae582030a5a615415`; 4,828,207 source rows; 111 source columns; SHA-256 `DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A`, verified 2026-11-04 | Pin each analysis result to this immutable snapshot and checksum. |
| Source-record identifier quality | 61 duplicate-code groups; none is an exact duplicate across all source fields | A validated product-identity and conflict-resolution rule is not available. Do not deduplicate on `code` or label distinct-code counts as unique products. |
| Country coverage | 4,769,998 rows have an approved ISO mapping (98.7944%); 237 ISO units are represented | Preserve the full record universe and report country coverage and unresolved country-tag evidence. |
| Existing country screening | The exploratory 1,000-record floor retains 107 ISO units | Use as an initial eligibility screen only, not as evidence that all 107 units are comparable peers. |
| Indonesia | 9,118 rows; 1,111 rows have `categories_tags` (12.1847%). Current candidate coverage counts 788 rows in at least one primary candidate group; 132 of those rows overlap multiple primary groups. | Indonesia passes the existing volume screen, but category coverage is limited. Keep it as the focal geography while reporting this constraint; do not use NOVA, Nutri-Score, ingredients, or food-group signals to infer missing categories. |
| Category assignment status | 59 owner-approved exact-tag group decisions; 7,889 single-group taxonomy candidates; 838 multi-group candidates; 106,211 taxonomy-unmatched tags; `Other / unclassified` is diagnostic-only | The reporting-group labels are approved, but candidate assignments are not. Category analyses need an explicit owner decision about candidate inclusion. |
| Brand mapping | 60 approved exact `brands` text values across 13 canonical groups | Apply only exact reviewed mappings; preserve unmapped values, do not split multi-brand text, and keep `brands_tags` separate. Broad brand coverage and entity identity are not established. |
| Non-food audit | Record-level A/B sensitivity outputs exist; class C is discovery-only | Keep the baseline and both agreed A/B sensitivity scenarios. Never use class C as an exclusion. |

Evidence sources: `outputs/profiling/normalized_country_coverage_summary.csv`, `country_comparison_shortlist.csv`, `nonfood_scope_country_impact.csv`, `category_reporting_group_candidate_status_summary.csv`, `category_reporting_group_candidate_country_overlap.csv`, `brand_name_manual_mapping_validation.csv`, `outputs/quality/database_build_validation_five_country.csv`, and `docs/02_data_profile.md`.

The 107-unit country shortlist is a screening artifact from the full source profile, not the current analytical comparison set. The current Stage 5 evidence table is generated from the five-country canonical database and reports the focal country, contextual peers, and coverage contrast only. It reports source rows and distinct codes separately, reconciles denominators against the scoped database, and does not imply statistical representativeness.

The saved Stage 5 CSV has been rebuilt against the validated candidate. Current candidate-derived and approved-decision counts are shown below.

### Indonesia and Potential Regional Comparators

| ISO unit | Country | Source rows | Distinct codes | Rows with category tags (%) | Primary candidate-group coverage among category-tagged rows (%) | Rows with approved exact category-group decision | Rows with approved exact brand mapping (%) | A/B-flagged rows |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| ID | Indonesia | 9,118 | 9,118 | 1,111 (12.1847%) | 70.9271% | 113 | 31 (0.3400%) | 63 |
| MY | Malaysia | 7,426 | 7,426 | 840 (11.3116%) | 73.8095% | 84 | 64 (0.8618%) | 1 |
| PH | Philippines | 9,176 | 9,176 | 1,535 (16.7284%) | 82.9316% | 158 | 88 (0.9590%) | 1 |
| SG | Singapore | 11,986 | 11,986 | 2,074 (17.3035%) | 87.0781% | 263 | 341 (2.8450%) | 1 |
| TH | Thailand | 11,343 | 11,343 | 7,104 (62.6289%) | 63.5698% | 673 | 46 (0.4055%) | 2 |
| VN | Vietnam | 1,653 | 1,653 | 396 (23.9564%) | 77.7778% | 41 | 14 (0.8469%) | 1 |
| KH | Cambodia | 1,295 | 1,295 | 301 (23.2432%) | 90.6977% | 32 | 5 (0.3861%) | 0 |

Across the 107 screened units, 12 have repeated codes within the unit and the combined source-row minus distinct-code gap is 61. The focal Indonesia unit and the proposed regional candidate units (MY, PH, SG, TH, VN, KH) have no within-country duplicate-code gap. Keep both row and distinct-code metrics in outputs; this local finding does not authorize deduplication or prove product identity.

Owner-approved scope: use **Malaysia, Philippines, and Singapore (MY, PH, SG)** as contextual peers for **Indonesia (ID)**. Their category-tag coverage (11.31%–17.30%) is relatively close to Indonesia's 12.18%. Treat **Thailand (TH)** as a separate coverage-contrast case, not a directly comparable peer, because its category-tag coverage is 62.63%. Vietnam and Cambodia are outside the approved Stage 6 scope. This scope concerns only this snapshot's measured coverage; it does not establish representativeness or commercial similarity.

The approved-only category assignments remain sparse (e.g. 113 Indonesian rows), while the candidate-derived assignment coverage is much broader. Keep both views visibly distinct. Exact-approved brand coverage increased after the two reviewed canonical mappings but remains limited in the selected scope (0.3400%–2.8450% of country rows); do not calculate broad brand concentration or HHI from it.

### Bounded Stage 2 reopening and impact (2026-11-04)

The owner approved an initial five exact-tag decisions: `en:drinkable-yogurts` → Dairy & eggs; `en:savory-snacks` → Salty snacks; `en:chili-paste` → Condiments, fats & spreads; `en:juice` → Beverages; and `en:bars-covered-with-chocolate` → Sweet foods & desserts. They were added to `data/mappings/category_tag_reporting_group_manual_decisions.csv`, and the candidate crosswalk and review queues were regenerated.

The reproducible audit is `scripts/14_stage2_selected_scope_mapping_impact.py` with its default `initial-five` decision set. It compares the mapping immediately before these five decisions with the result after that batch on the same source Parquet and country mappings. Counts are distinct source rows by country; a record can carry multiple target tags and/or be assigned to multiple groups. Tag-level counts are in `outputs/profiling/stage2_selected_scope_mapping_tag_impact.csv`; country and per-group before/after counts are in `outputs/profiling/stage2_selected_scope_mapping_coverage_delta.csv`.

| ISO unit | Drinkable yogurts | Savory snacks | Chili paste | Juice | Chocolate-covered bars |
|---|---:|---:|---:|---:|---:|
| ID | 0 | 0 | 0 | 2 | 1 |
| MY | 1 | 0 | 0 | 3 | 0 |
| PH | 1 | 18 | 0 | 4 | 1 |
| SG | 3 | 0 | 0 | 2 | 6 |
| TH | 52 | 1 | 19 | 3 | 10 |

These are per-tag record counts and may overlap across columns; they are not additive unique-record totals. Country source-row and category-tagged-row denominators did not change.

| ISO unit | Candidate-derived rows with a group: before → after | Approved-only rows with a group: before → after |
|---|---:|---:|
| ID | 786 → 788 (+2) | 106 → 109 (+3) |
| MY | 619 → 620 (+1) | 82 → 84 (+2) |
| PH | 1,263 → 1,273 (+10) | 135 → 157 (+22) |
| SG | 1,805 → 1,806 (+1) | 243 → 251 (+8) |
| TH | 4,497 → 4,516 (+19) | 621 → 653 (+32) |

The approved-only sensitivity is more affected than the candidate-derived view because many of these records already had a candidate-derived group through other tags. Multi-group overlap also rises in TH by two candidate-derived rows and one approved-only row. This was a material change to the approved-only category view, particularly in PH and TH. The current Stage 6 outputs also include the subsequent three-tag batch below. The original Stage 4 database was not overwritten.

### Additional category and brand decisions (2026-11-04)

After review of the pinned Open Food Facts taxonomy, the owner approved `en:chocolate-milks` → Beverages, `en:coconut-waters` → Beverages, and `en:yogurt-drinks` → Dairy & eggs. These assignments follow finished product type rather than adding a group from ingredient ancestry. Each tag occurs on the following number of records in the selected scope; per-tag counts may overlap:

| ISO | Chocolate milks | Coconut waters | Yogurt drinks |
|---|---:|---:|---:|
| ID | 13 | 4 | 2 |
| MY | 9 | 0 | 2 |
| PH | 6 | 1 | 8 |
| SG | 11 | 14 | 3 |
| TH | 29 | 20 | 21 |

The incremental audit is reproducible with `scripts/14_stage2_selected_scope_mapping_impact.py --decision-set additional-three`. Its outputs are `outputs/profiling/stage2_selected_scope_mapping_tag_impact_additional_three.csv` and `outputs/profiling/stage2_selected_scope_mapping_coverage_delta_additional_three.csv`. Candidate-derived assigned-row coverage did not change. Approved-only assigned-row coverage changed as follows:

| ISO | Candidate-derived rows: before → after | Approved-only rows: before → after |
|---|---:|---:|
| ID | 788 → 788 | 109 → 113 (+4) |
| MY | 620 → 620 | 84 → 84 |
| PH | 1,273 → 1,273 | 157 → 158 (+1) |
| SG | 1,806 → 1,806 | 251 → 263 (+12) |
| TH | 4,516 → 4,516 | 653 → 673 (+20) |

The assigned-group increase was in Beverages: ID +4, PH +1, SG +14, and TH +20; SG also had a two-row increase in approved-only multi-group overlap. The approved-only unique-record gain totals 37 across the selected countries. The new decisions therefore clarify semantics without increasing candidate-derived coverage, but they materially improve the approved-only view.

The owner also approved exact brand-text mappings `Fairprice` and `FairPrice` → `FairPrice`, and `Nestle` and `Nestlé` → `Nestlé`. The local source shows shared exact brand-tag evidence within each pair; `xx:nestle` is labeled Nestlé in the Open Food Facts brand-tag taxonomy (Wikidata Q160746). The mapping validation now accepts diacritic-only changes only for the explicit reviewed source values; this is not a general alias rule. Across the selected countries, approved brand-mapped rows changed as follows:

| ISO | Before → after |
|---|---:|
| ID | 1 → 31 (+30) |
| MY | 5 → 64 (+59) |
| PH | 0 → 88 (+88) |
| SG | 18 → 341 (+323) |
| TH | 11 → 46 (+35) |

The mapping now covers 60 exact source text values across 13 canonical groups. These outputs remain a selected mapping subset, not a census of brands; HHI, concentration, dominance, and market-share claims remain out of scope.

### Risk-Based Readiness Review

| Risk area | Evidence checked | Readiness assessment | Scope action |
|---|---|---|---|
| Source integrity / record grain | The original database remains unchanged. The latest temporary compact candidate passed 15 checks, including exact Stage 6 projection and bridge-content comparisons to the original database; the candidate was removed after refresh. | Structurally validated for the bounded Stage 6 schema; not a full database replacement. Source upstream commit/retrieval method is still not determined. | Keep the original database as-is; use the automated current-mapping refresh for Stage 5/6. |
| Country mapping / peer denominators | Current working mapping and normalized country profile reconcile; 98.7944% of all source rows have approved country mappings. A historical reconstructed-mapping discrepancy remains documented in the profile. | Ready for the current snapshot baseline, with the historical caveat disclosed; no need to reopen all country tags for this bounded comparison. | Use the validated current mapping; revisit a specific country tag only if a material count or interpretation issue appears. |
| Category data / harmonization | Category-tag coverage varies widely. Indonesia's coverage is 12.1847%; current Stage 6 counts 788 candidate-derived and 113 approved-only assigned rows. | Not ready for unqualified category conclusions; the current analysis provides clearly labeled candidate-derived and approved-only views. | Keep both views separate, disclose unresolved/excluded coverage, and keep the remaining long-tail review parked. |
| Brand identity / concentration | Approved exact mappings cover 31 Indonesian rows and at most 341 rows in any selected country; median coverage across all 107 candidate units is 1.0090%. | Not ready for a broad brand landscape, HHI, or concentration conclusion. | Restrict output to mapping coverage and the 13 approved canonical groups; defer concentration claims. |
| Record-level A/B sensitivity | The A/B-except-strong-signal and exclude-all-A/B scenarios differ by two rows overall; neither strong-signal row occurs in ID, MY, PH, SG, TH, VN, or KH. Exclusions for these units are ID 63, MY 1, PH 1, SG 1, TH 2, VN 1, KH 0. | Sensitivity is decision-relevant for Indonesia's record denominator but is small for the candidate peer units. | Preserve baseline and both agreed scenarios; never treat Class C as an exclusion. |

**Overall recommendation:** Do not return to Stage 2 wholesale. The bounded eight-tag category review, four exact brand-spelling decisions, candidate build, Stage 6 rerun, and Stage 7 refresh are complete. The model and record/country evidence remain suitable for descriptive country-context analysis, not broad brand concentration or unqualified category claims. Keep the candidate-derived / approved-only split, record-level A/B sensitivity, explicit coverage reporting, and approved peer roles. The immutable source commit and checksum are verified and documented.

## Recommended Analysis Protocol

The following protocol was approved for the bounded Stage 6 analysis.

### 1. Snapshot, population, and unit

- Use the pinned snapshot and identify it in Stage 6 outputs by SHA-256.
- Use source rows in the canonical five-country database as the country-analysis population; full-snapshot totals are source-profile context, not the Stage 6 denominator.
- Use `source_record_id` / source rows as the primary measurement unit. Count a row at most once within each country, country-category, or record-to-canonical-brand assignment as appropriate.
- Do not deduplicate records by `code`. A distinct-code count may be included only as a separately labeled diagnostic; never call it "unique products."
- Country, category, and brand totals may overlap. Do not sum overlapping assignments into a purported global product total.

### 2. Country scope and peer selection

- Keep all 107 ISO units meeting the existing 1,000-row screen as Stage 5 evidence; the Stage 6 scope is limited to ID, MY, PH, SG, and TH.
- Label ID as focal, MY/PH/SG as contextual peers, and TH as a coverage contrast. These roles describe the owner's analytical scope, not statistical equivalence.
- Do not invent a new numeric coverage cutoff for Stage 5. Show measured coverage for each candidate and let the owner approve any additional cutoff before interpretation.
- If no defensible peer set can be selected from available evidence, report Indonesia descriptively against the candidate-set context and state that direct peer comparison is not established.
- For country record totals, count a source row once per mapped ISO unit using `record_country`. Report total source rows, rows with an approved country mapping, unmapped/review-required country evidence, and each unit's own denominator. Country totals are not mutually exclusive.

### 3. Category scope and treatment

- Use the ten substantive labels in `category_reporting_group_framework.csv`; do not include `Other / unclassified` in primary comparisons.
- Proposed main analytical view: include exact tags assigned to one reporting group by the single-group taxonomy candidate rule plus the 59 owner-approved exact-tag decisions. Label taxonomy-derived assignments as **candidate-derived**, not owner-approved.
- Proposed narrow sensitivity view: include only the 59 owner-approved exact-tag group decisions. This makes the coverage cost of using only approved assignments visible.
- Exclude multi-group candidates, taxonomy-unmatched tags, diagnostic residuals, placeholders, and exact category tags with an explicit `exclude_non_food` disposition from substantive group assignments. Report each status separately as coverage/unresolved evidence; do not force assignments.
- In each country-category result, count a row at most once in a given reporting group, while allowing overlap between different groups. Report both the group row count divided by all rows in that ISO unit and category-tag coverage (rows with non-empty `categories_tags` divided by all rows in the unit). State that group shares can overlap and are not a partition.
- Treat the candidate country-coverage output as evidence for coverage planning, not as final analytical results: it includes unapproved single-group candidates and excludes unresolved assignments.
- Keep `food_groups_tags` as a separately labeled diagnostic sensitivity source only. Do not silently substitute it for `categories_tags` or infer product type from non-category signals.

### 4. Brand scope and metrics

- Apply only the reviewed exact `brands` source-text-to-canonical-text decisions. Preserve exact raw `brands`, exact mapping status, and unmapped/missing values.
- Do not split source brand strings; do not derive identity from `brands_tags`; do not treat unmapped source text as a normalized brand.
- In the initial pass, report brand-mapping coverage and record counts for approved canonical groups only. For each country-category, show the count of mapped source records and its share of all country-category records alongside the mapped-only denominator. Explicitly label the mapped-only distribution as partial and selected, not as a full brand landscape.
- Recommendation: defer HHI and broad concentration claims until brand identity and coverage are sufficiently complete and the owner approves a defensible denominator. If the owner requests HHI now, restrict it to the approved mapped subset, report mapping coverage beside it, and label it as concentration within that selected subset—not market concentration.
- Do not call record-based brand shares market share, revenue share, or evidence of commercial dominance.

### 5. Non-food sensitivity and Indonesia limitations

Report the following scenarios side by side, with the baseline always retained:

1. `baseline`: no record-level non-food exclusions.
2. `exclude_A_B_except_strong_food_signals`: exclude A/B-flagged rows except records meeting the existing strong-food-signal rule.
3. `exclude_all_A_B`: exclude every A/B-flagged row, including those with strong food signals.

Class C remains discovery-only in all scenarios; class D remains food-confirming and is not a non-food exclusion. Keep tag-level category exclusions separate from record-level sensitivity. Do not apply a scenario to raw data or overwrite the baseline. Report row counts and distinct-code counts in separate columns, never describe distinct codes as unique products.

For Indonesia, show the above sensitivity results and explicitly disclose the 12.1847% `categories_tags` coverage. The prior owner decision is to keep non-category signals diagnostic-only; do not use them to classify or exclude Indonesian records.

### 6. Stage 6 output families and observed status

Stage 6 SQL produces snapshot-pinned tables under `outputs/analysis/`:

- `stage6_country_scope.csv`: country source rows, distinct codes, category-tag coverage, and baseline plus both A/B scenarios.
- `stage6_country_category.csv`: per-country category-group rows, overlap diagnostics, candidate-derived vs approved-only assignments, category-tagged rows without a substantive group assignment, and approved-brand mapping coverage. The unassigned count is a coverage gap, not a disposition-level explanation.
- `stage6_country_brand.csv`: assignments to exact-approved canonical brands, with a mapped-only denominator; this is a sparse selected subset, not a full brand landscape.
- `stage6_validation.csv`: reconciliation checks for country denominators, sensitivities, category assignments, exact-approved brand mappings, brand assignment denominators, and category coverage arithmetic.

The current outputs were generated from a compact candidate built from `data/processed/global_product_landscape_five_country.duckdb`; the candidate passed 15 build/content checks. The optional full-country database was not overwritten. Stage 5 evidence covers the five selected units, and all 11 Stage 6 checks passed. No HHI, broad concentration, market-share, or sales-based metrics are calculated.

## Owner Decisions and Approval Status

| ID | Decision | Recommendation | Status |
|---|---|---|---|
| S5-01 | Country peers | Use ID as focal, MY/PH/SG as contextual peers, and TH as a separate coverage contrast; other screened units remain outside Stage 6. | Approved |
| S5-02 | Category candidate assignments | Use single-group taxonomy candidates plus the 56 approved decisions in a clearly labeled candidate-derived main view; show approved-only assignments as a sensitivity view. | Approved; current Stage 6 validated |
| S5-03 | Brand concentration | Report coverage and the 11 approved canonical groups only; defer HHI and broad concentration claims until the mapping universe/denominator is defensible. | Approved |
| S5-04 | Non-food sensitivity | Keep the baseline plus both A/B scenarios; keep class C discovery-only and non-category Indonesia signals diagnostic-only. | Previously agreed; reaffirmed |
| S5-05 | Record unit | Keep source rows primary and code distinct counts diagnostic only until a validated identifier resolution rule exists. | Approved |
| S5-06 | Efficiency boundary | Prefer one bounded, decision-relevant country evidence review; do not extend long-tail category/brand review or add arbitrary cutoffs absent a demonstrated material need. | Approved |

## Stage 5 Exit Gate

Stage 5 decisions remain current. The canonical five-country database and compact analysis candidate passed 15 checks each; the current Stage 6 run passed all 11 checks; and Stage 7 has been refreshed. The source commit and checksum were verified on 2026-11-04. The optional full-country database is not required for this analysis.
