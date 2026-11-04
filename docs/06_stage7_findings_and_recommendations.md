# Stage 7 Findings and Recommendations

## Status and scope

This is the bounded descriptive interpretation of the validated Stage 6 outputs for source snapshot SHA-256 `DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A`. Scope: Indonesia (ID, focal), Malaysia (MY), Philippines (PH), and Singapore (SG) as contextual peers, plus Thailand (TH) as a category-coverage contrast.

<!-- AUTO-GENERATED: analysis-status:START -->
Stage 6 was rerun against the separately validated compact candidate database after the approved category mappings were applied. It generated 15 country-scenario rows, 300 country-category rows, and 36 mapped-brand assignment rows. The candidate build passed 13 checks and all 11 Stage 6 checks passed; the four published CSVs are byte-identical to the validated candidate run. These checks establish the tested reconciliations and arithmetic for the pinned inputs; they do not prove all mappings semantically correct or the data representative.
<!-- AUTO-GENERATED: analysis-status:END -->

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

**Interpretation:** These are the highest observed record counts in the candidate-derived assignment view. The country/category rows are not mutually exclusive: a record can be assigned to multiple groups. Candidate-derived assignments include taxonomy-based candidates that have not all received owner approval. Do not frame the table as a complete category census, unique-product variety ranking, or evidence of consumer demand.

### 3. Category assignment coverage remains a major limitation

For baseline, the number of category-tagged rows assigned to at least one substantive group differs considerably by mapping basis:

<!-- AUTO-GENERATED: category-coverage:START -->
| ISO | Category-tagged rows | Candidate-derived assigned | Candidate-derived tagged rows without assignment | Approved-only assigned | Approved-only tagged rows without assignment |
|---|---:|---:|---:|---:|---:|
| ID | 1,111 | 788 | 323 | 109 | 1,002 |
| MY | 840 | 620 | 220 | 84 | 756 |
| PH | 1,535 | 1,273 | 262 | 157 | 1,378 |
| SG | 2,074 | 1,806 | 268 | 251 | 1,823 |
| TH | 7,104 | 4,516 | 2,588 | 653 | 6,451 |
<!-- AUTO-GENERATED: category-coverage:END -->

<!-- AUTO-GENERATED: category-overlap:START -->
There are also rows assigned to multiple groups in the candidate-derived view: ID 134, MY 99, PH 177, SG 266, and TH 1,020. These overlap counts are diagnostics and must not be added to category totals as if groups formed a partition.
<!-- AUTO-GENERATED: category-overlap:END -->

**Interpretation:** The candidate-derived view gives broader coverage than the approved-only sensitivity, while neither resolves all category-tagged records. The “without assignment” value is a coverage gap, not an explanation of the underlying tag dispositions. Keep the two bases separate and do not force unresolved values into groups merely to increase coverage.

### 4. Exact-approved brand mapping is too sparse for a broad brand landscape

Stage 5 evidence reports records with an approved exact brand mapping as follows:

<!-- AUTO-GENERATED: brand-coverage:START -->
| ISO | Rows with approved exact brand mapping | Share of country rows |
|---|---:|---:|
| ID | 1 | 0.0110% |
| MY | 5 | 0.0673% |
| PH | 0 | 0.0000% |
| SG | 18 | 0.1502% |
| TH | 11 | 0.0970% |
<!-- AUTO-GENERATED: brand-coverage:END -->

<!-- AUTO-GENERATED: brand-assignment-note:START -->
Stage 6's 36 rows are assignments across scenarios, assignment bases, country-category groups, and mapped canonical names; they are not 4 distinct brands or an exhaustive brand census.
<!-- AUTO-GENERATED: brand-assignment-note:END -->

**Interpretation:** The exact-approved subset is highly selected and small. It cannot support broad brand variety, concentration, HHI, dominance, or market-share conclusions. Report the mapping coverage with any mapped-brand counts; do not generalize the mapped-only distribution to all brands in these countries.

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

## Recommendations

1. Use the record-based country totals and clearly labeled category assignment tables as descriptive evidence only. Keep ID focal, MY/PH/SG contextual, and TH as the coverage contrast.
2. Show category-tag coverage and both assignment bases alongside every category interpretation. State the overlap and unresolved-coverage limitations.
3. Keep the exact-approved brand results as a coverage diagnostic only. Do not calculate HHI or broad brand concentration from this mapping subset.
4. Preserve all three non-food scenarios. Do not replace the baseline with an exclusion scenario.
5. Do not reopen Stage 2 broadly. The five approved category decisions are now included in the validated Stage 6 outputs. Revisit an exact category, country, or brand mapping only if a concrete finding or proposed conclusion is materially affected; document the evidence, approve the change, then rerun and revalidate affected analyses.
6. Keep Stage 0 provenance and Stage 8 recovery/release work open. In particular, do not claim a known source retrieval date, extraction method, or unique upstream commit without evidence.
7. These outputs do not answer sales-based market size, market share, demand, or commercial brand dominance. If those are required business questions, identify appropriate external data before attempting those conclusions.

## Limitations

- The source is a collaboratively maintained database, not a census of products sold.
- The exact upstream commit, local retrieval date, and extraction method for the Parquet remain undetermined.
- Category coverage is low in the focal unit and varies substantially across countries.
- Candidate-derived assignments are not all owner-approved; approved-only assignments cover far fewer rows.
- Group assignments overlap, and unassigned category-tagged rows are not disposition-level explanations.
- Exact-approved brand mapping coverage is negligible in the selected country scope.
- `code` is not a validated unique product identifier; source rows remain the primary measurement unit.
- Stage 6 technical validations do not establish semantic mapping truth, representativeness, or commercial validity.

## Evidence and reproducibility

- Specification and decisions: `docs/05_analysis_specification.md`
- Workflow and quality gates: `docs/03_analysis_workflow.md`
- Country evidence: `outputs/profiling/stage5_country_peer_evidence.csv`
- Stage 6 scope: `outputs/analysis/stage6_country_scope.csv`
- Stage 6 category results: `outputs/analysis/stage6_country_category.csv`
- Stage 6 mapped brand results: `outputs/analysis/stage6_country_brand.csv`
- Stage 6 checks: `outputs/analysis/stage6_validation.csv`
- Compact Stage 6 database: `data/processed/global_product_landscape_stage6_candidate.duckdb` (scope-limited analytical candidate, not a replacement for the full Stage 4 database)
- Candidate build checks: `outputs/quality/stage6_candidate_build_validation.csv` (13 passed)
- Re-run the candidate workflow using the commands documented in `README.md` and `docs/03_analysis_workflow.md`; default Stage 5/6 paths still target the original full database.
