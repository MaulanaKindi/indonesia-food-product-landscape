# Project Log

This document records important project decisions, accepted improvements, and future enhancements.

---

## ITEM-001

Type:
Decision

Title:
Use Independent Numbering by Repository Area

Decision:
Implemented

Reason:
Numbers indicate reading order in docs/ and execution order within scripts/ or sql/. They are not global identifiers shared across the repository. Data and outputs use descriptive names rather than sequence numbers.

Documentation order:

docs/00_business_brief.md
docs/01_data_source.md
docs/02_data_profile.md
docs/99_project_log.md

Status:
Completed

---

## ITEM-002

Type:
Decision

Title:
Implement Script → Output → Documentation Traceability

Recommendation:
Create explicit links between scripts, generated outputs, and documentation.

Decision:
Implemented

Reason:
Improves reproducibility, auditability, and reviewer understanding.

Target Workflow:

Script
↓
Output
↓
Documentation

Example:

scripts/04_normalized_country_profile.py
↓
outputs/profiling/normalized_country_profile.csv
↓
docs/02_data_profile.md

Status:
Completed

---

## ITEM-003

Type:
Decision

Title:
Separate Data, Scripts, SQL, Outputs, and Documentation

Decision:
Implemented

Reason:
Different project assets serve different purposes and should be organized separately.

Resulting Structure:

data/
  raw/
  mappings/
  reference/
docs/
outputs/
scripts/
sql/

Status:
Completed

---

## ITEM-004

Type:
Decision

Title:
Use Repository Documentation as Source of Truth

Decision:
Implemented

Reason:
Project knowledge should be stored in the repository rather than relying on chat history.

Affected Documents:

README.md
docs/00_business_brief.md
docs/99_project_log.md
docs/01_data_source.md
docs/02_data_profile.md

Status:
Completed

---

## ITEM-005

Type:
Decision

Title:
Outputs Directory as Analytical Evidence Repository

Decision:
Accepted

Reason:
Outputs provide auditable evidence between analysis scripts and written conclusions.

Workflow:
Data
↓
SQL / Script
↓
Output
↓
Documentation

Status:
Implemented

---

## ITEM-006

Type:
Decision

Title:
Retain Historical Profiling Results as Project Outputs

Decision:
Accepted

Reason:
Profiling outputs support documentation and should be reproducible and auditable

Action:
Regenerate profiling outputs and store them under outputs/

Status:
Completed

---

## ITEM-007

Type:
Decision

Title:
Persist Profiling and Quality Outputs as Files

Decision:
Implemented

Result:
Dataset profiling, quality checks, and country profiles write reproducible outputs under outputs/.

Status:
Completed

---

## ITEM-008

Type:
Decision

Title:
Separate Raw Data, Mappings, and Reference Inputs

Decision:
Implemented

Reason:
Raw source data, curated analytical mappings, and reference data have different ownership and lifecycle. Keep one maintained mapping as the source of truth, keep tag frequencies in generated profiling outputs, and exclude the 7.98 GB source Parquet from Git.

Result:

- `data/raw/food.parquet` contains the local source snapshot and is ignored by Git.
- `data/mappings/country_tag_mapping.csv` is the single maintained country-tag mapping.
- `data/reference/iso_3166_alpha2.csv` contains the versioned ISO reference input.
- Tag frequencies remain in generated profiling outputs rather than being duplicated in the mapping.
- Original draft suggestions were not recoverable after an interrupted mapping-file rewrite; the maintained mapping contains current decisions, not reconstructed draft history.
- `.gitignore` excludes local environment/cache artifacts and the large source dataset.
- `requirements.txt` records the Python dependencies used by the current scripts.

Status:
Completed

---

## ITEM-009

Type:
Recovery and Validation

Title:
Recover Country Mapping and Adopt Reconstructed Baseline

Decision:
Adopt reconstructed mapping as the working baseline; historical difference documented

Reason:
An interrupted CSV rewrite left the maintained mapping incomplete. Rebuild it from the 434-tag raw inventory, validate approved ISO codes against the project reference, and compare regenerated results with the saved verified profile.

Result:

- The maintained mapping contains 434 unique source tags: 361 approved, 65 excluded, and 8 requiring review.
- The normalized profile contains 237 ISO units, covers 4,769,998 records, and yields 107 units at the exploratory 1,000-record threshold.
- The source Parquet SHA-256 matches the previously recorded value (`DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A`), but the saved profile baseline differs by one Thailand record. Approved and excluded tag-record assignment totals differ from the saved baseline by two assignments in opposite directions.
- The original mapping and draft file are unavailable; saved outputs contain aggregates, not tag-level decisions. The historical discrepancy cannot be uniquely resolved from the remaining local evidence.
- The original draft suggestions were not recovered. They are explicitly not claimed as retained provenance.
- Scripts `02_quality_checks.py`, `03_country_profile.py`, and `04_normalized_country_profile.py` completed against the reorganized data paths.

Follow-up:
If an older mapping backup becomes available, compare it against the adopted baseline and reconcile the one-record/two-assignment difference. Do not describe the current mapping as an exact historical restoration.

Status:
Completed with limitation

---

## ITEM-010

Type:
Data Quality Decision

Title:
Investigate Duplicate Product Codes

Decision:
Do not use source `code` as a raw-record primary key; retain duplicate records pending a validated resolution rule

Reason:
All 61 duplicated code groups contain non-identical source rows, and 52 groups conflict on at least one product-description or assignment field. Removing rows or selecting the latest edit without a validated source rule could change analytical results.

Result:

- `scripts/02_quality_checks.py` now generates `outputs/quality/duplicate_code_investigation.csv` with the differing fields and a compact comparison of source attributes and revision metadata for each duplicate group.
- No duplicated code group is identical across all 111 source fields.
- Each duplicate pair has a distinct `last_modified_t` value; this alone does not establish that the later record should replace the other.
- Use a surrogate key for raw source records and preserve the source `code` as an attribute. Reconsider `code` as a natural key for a curated product entity only after documenting and validating conflict handling.
- Keep analysis record-based until an explicit deduplication rule is justified; never discard duplicates solely because `code` repeats.

Status:
Completed; deduplication policy remains open

---

## ITEM-011

Type:
Profiling Implementation

Title:
Profile Source Brand and Category Fields

Decision:
Implemented source-level coverage and frequency profiles; candidate variants remain subject to manual review

Reason:
Establish data completeness, assignment volume, value diversity, and potential alias signals before designing brand/category harmonization rules.

Result:

- `scripts/05_category_brand_profile.py` profiles the `brands_tags`, `brands`, `categories_tags`, `categories`, and supplementary `food_groups_tags` fields.
- Generated outputs include coverage summaries, exact source-value frequency profiles (including `food_group_tag_profile.csv`), case-insensitive tag-suffix candidates, and case/whitespace normalization-collision candidates.
- Source text values are not split or automatically merged. Candidate files are evidence for review, not curated mappings.
- The script is included in the documented profiling workflow.

Status:
Completed; mapping review and harmonization remain outstanding

---

## ITEM-012

Type:
Workflow Decision

Title:
Manage Delivery Through Analysis Stages and Quality Gates

Decision:
Adopt the documented stage-and-gate workflow

Reason:
The project has linked dependencies across source provenance, data-quality decisions, harmonization, schema design, SQL analysis, and backup/restore. Explicit gates prevent provisional profiling assumptions from being mistaken for final analytical rules.

Result:

- `docs/03_analysis_workflow.md` defines the stages, expected evidence, progression gates, current status, and mapping to the business brief's Definition of Done.
- The repository README links to the workflow and summarizes the outstanding completion items.
- Current active work is measurement rules and category/brand harmonization; final schema implementation is downstream of those decisions.

Status:
Implemented

---

## ITEM-013

Type:
Measurement Rule

Title:
Preserve Category Taxonomy Graph and Define Reporting Groups

Decision:
Use the versioned Open Food Facts taxonomy with `categories_tags` as the primary category basis; use `food_groups_tags` as a supplementary sensitivity check

Reason:
The Parquet retains category tags but omits hierarchy fields. The current taxonomy matches most observed tag assignments, but has multiple parent paths and does not provide a consistent numeric depth for every category. `food_groups_tags` has only 31.46% record coverage and is not sufficient as the sole category basis.

Result:

- Pinned the Open Food Facts category taxonomy snapshot under `data/reference/` and documented its URL, retrieval date, size/hash, and unknown vintage relative to the source Parquet.
- Added `scripts/06_category_taxonomy_audit.py` and outputs for exact tag matches, taxonomy depth ranges, coverage, and missing parent references.
- The audit matches 9,849 of 116,105 distinct observed tags, covering 94.8020% of tag-record assignments. A total of 4,469 matched tags have multiple taxonomy depth paths.
- The primary analytical reporting groups will be an explicit reviewed set, not a blind numeric hierarchy depth. At the time of this decision, the group list and node mappings remained to be approved.

Status:
Approach accepted; reporting-group mapping pending

---

## ITEM-014

Type:
Measurement Rule

Title:
Approve Broad Category Reporting-Group Labels

Decision:
Approve eleven broad reporting-group labels as the framework for a draft taxonomy crosswalk; this does not approve any taxonomy-node assignment

Reason:
The source taxonomy is a directed graph with uneven category breadth, so a universal numeric depth is not a consistent comparison grain. A finite business-facing grouping is needed, while exact node assignments and edge cases must remain reviewable.

Result:

- Approved labels are stored in `data/reference/category_reporting_group_framework.csv`: fruits and vegetables; cereals, potatoes and bakery; meat and poultry; fish and seafood; dairy and eggs; beverages; sweet foods and desserts; salty snacks; prepared meals; condiments, fats and spreads; and other/unclassified.
- The next deliverable is a candidate crosswalk from exact taxonomy tags to reporting groups, with reasons, multi-parent ambiguity, unmatched tags, and coverage made explicit.
- `food_groups_tags` remains supplementary because it is present on 31.4658% of source records; its reproducible source-value profile is generated by `scripts/05_category_brand_profile.py`.

Status:
Group labels approved; taxonomy crosswalk and category coverage review pending

---

## ITEM-015

Type:
Profiling Implementation

Title:
Draft Taxonomy-to-Reporting-Group Crosswalk

Decision:
Generate traceable candidate mappings from exact taxonomy ancestry; do not treat them as approved analytical assignments

Reason:
The approved reporting-group labels need a reproducible draft crosswalk that exposes multi-parent ambiguity, residual categories, and source tags absent from the pinned taxonomy before analytical use.

Result:

- Added `data/mappings/category_reporting_group_anchor_candidates.csv` with 41 exact taxonomy anchor/group candidates, all explicitly marked `candidate_only`.
- Added `scripts/07_category_reporting_group_draft.py`; it validates the pinned taxonomy checksum and candidate inputs, then inherits candidate groups through exact parent paths. It does not use text similarity.
- Generated `category_reporting_group_candidate_crosswalk.csv`, `category_reporting_group_candidate_coverage.csv`, and `category_reporting_group_candidate_status_summary.csv` under `outputs/profiling/`.
- Of 116,105 observed category tags, 7,889 are single-group candidates (6,688,760 tag-record assignments), 882 are multi-group candidates (449,063 assignments), 1,078 are residual `Other / unclassified` candidates (2,797,475 assignments), and 106,256 are absent from the pinned taxonomy (544,751 assignments).
- Assignment totals count source-tag frequencies, not distinct records or products. The residual and ambiguous values require review; no generated assignment is final.
- Generated per-country/group record coverage and overlap outputs for 237 ISO units. Across the 107 units with at least 1,000 source records, median category-tag coverage is 33.4218%; median primary-group coverage among category-tagged records is 84.2795%; and median overlap among primary-group records is 15.0794%.
- Indonesia has category tags on 1,111 of 9,118 country-assigned records; 786 receive at least one primary-group candidate, and 132 of those have assignments in multiple primary groups. The diagnostic residual appears on 651 Indonesia records; some may also have a primary-group assignment.
- Independently reconciled each country denominator against `outputs/profiling/normalized_country_profile.csv`; all 237 ISO-unit record counts match exactly.

Status:
Draft generated and documented; manual crosswalk, ambiguous-tag treatment, and coverage review pending

---

## ITEM-016

Type:
Measurement Rule

Title:
Keep Other Category Residual Diagnostic Only

Decision:
Retain `Other / unclassified` as a diagnostic reconciliation bucket, but exclude it from primary category comparisons; keep ambiguous and unmatched tags unresolved pending review

Reason:
The candidate residual covers 26.6933% of category tag-record assignments and is not a homogeneous business category. Including it as a primary group could obscure meaningful differences. Category-tag coverage and overlap also vary materially across countries, particularly for Indonesia.

Result:

- Candidate crosswalk output now labels residual assignments `diagnostic_only`; per-country residual counts remain visible but are excluded from primary group coverage and overlap calculations.
- The business brief, workflow, data profile, README, and project log document the rule.
- Indonesia has category tags on 1,111 of 9,118 country-assigned records; 786 have a primary-group candidate and 132 of those span multiple primary groups. The separate diagnostic residual appears on 651 records; some of these may also have a primary-group assignment.

Status:
Policy approved and implemented; exact taxonomy-node mapping and unresolved-value review remain pending

---

## ITEM-017

Type:
Profiling Implementation

Title:
Prioritize Manual Category Mapping Review

Decision:
Create evidence-led review queues without automatically approving anchors, aliases, exclusions, or reporting-group assignments

Reason:
The candidate crosswalk exposes high-frequency ambiguity and taxonomy mismatches. Review should begin with assignments that affect the most observations while keeping source evidence and uncertainty explicit.

Result:

- Added `scripts/08_category_reporting_group_review_queues.py`, which verifies the pinned taxonomy checksum and generates anchor, ambiguous-tag, residual-tag, and high-frequency unmatched-tag queues.
- All 41 proposed anchors are exact taxonomy nodes with observed descendants; the audit is structural and does not certify semantic correctness.
- The ambiguous queue includes all 882 tags. Its 18 highest-priority tags account for 261,526 tag-record assignments.
- The residual queue includes all 1,078 residual tags. Its 37 highest-priority tags account for 2,423,947 assignments; `Other / unclassified` remains diagnostic-only.
- The unmatched priority queue includes the 1,000 highest-frequency unmatched tags, covering 343,223 of 544,751 unmatched tag-record assignments (63.01%). Lower-frequency unmatched tags remain unresolved.
- Sampled source records indicate `en:undefined` is a missing-value placeholder; `en:groceries` is too broad for a single group; `en:fruits-based-foods` is a plausible but unverified spelling/alias lead; and non-food tags such as `nl:beauty` need explicit out-of-scope treatment. At this point, no disposition had been written into the analytical crosswalk.

Status:
Queues generated and documented; owner review and approval of dispositions pending

---

## ITEM-018

Type:
Measurement Rule

Title:
Exclude Category Placeholders and Confirmed Non-Food Tags

Decision:
Exclude `en:undefined` from category assignments and explicitly exclude 28 reviewed non-food/personal-care tags from food-category analysis; preserve all source values and rationales

Reason:
The placeholder does not identify a category, and sampled category values/source records confirm the selected household, personal-care, and cosmetics tags are outside the food-analysis scope. Exclusion is limited to exact reviewed tags; it is not a broad automated rule.

Result:

- Added `data/mappings/category_tag_manual_dispositions.csv` with one placeholder and 28 non-food dispositions, each marked approved and justified.
- Updated `scripts/07_category_reporting_group_draft.py` to apply only those exact approved dispositions and retain them in the crosswalk as excluded.
- The 29 exclusions cover 56,090 source-tag assignments: 34,795 for the placeholder and 21,295 for non-food tags.
- The crosswalk now has 106,227 still-unmatched tags and 488,661 assignments. The top 1,000 unmatched tags cover 288,173 assignments (58.97%); the rest remain unresolved.
- `en:groceries` remains too broad to place; `en:fruits-based-foods` remains a possible but unverified alias; multi-group tags remain unresolved pending boundary decisions.

Status:
Exact exclusions approved and implemented; remaining mapping review pending

---

## ITEM-019

Type:
Non-Food Scope Audit and Measurement Rule

Title:
Measure Non-Food Record Scope and Report A/B Sensitivity

Decision:
Keep the full dataset as the primary baseline; report two A/B record-exclusion scenarios as sensitivity analyses. Keep Class A separate from the reviewed disposition mapping, keep Class C discovery-only, and use non-category food signals for Indonesia as diagnostics only.

Reason:
Category-tag exclusions do not measure record-level scope or country impact. Contributor flags, reviewed exact exclusions, pattern candidates, and food-confirming tags have different evidential meanings. A/B records can also carry strong food signals, so applying a blanket record-level exclusion as the primary rule could remove food records.

Result:

- Added `scripts/09_nonfood_scope_audit.py` for deterministic, offline analysis and `scripts/10_online_validation.py` for dated external-source checks using Hub metadata without downloading the Parquet file.
- Verified the Parquet preconditions (4,828,207 rows and 111 columns) and pinned taxonomy SHA-256. Regenerated the candidate category crosswalk after the exact `nl:Beauty` disposition was approved: the current mapping has 29 non-food tags plus one placeholder; the crosswalk reports 21,311 non-food tag-record assignments, 34,795 placeholder assignments, and 106,226 unresolved tags covering 488,645 assignments.
- Confirmed `nl:beauty` has 4,223 rows and 4,223 distinct codes, while exact `nl:Beauty` has 16 rows and 16 distinct codes. The case-folded total is 4,239 rows and 4,239 distinct codes; all 16 codes carrying `nl:Beauty` are additional to the lowercase tag. The mapping preserves each exact tag separately.
- Offline strongest-class results: A = 908 rows / 908 distinct codes; B = 13,980 / 13,980; C = 1,235 / 1,235; D = 272 / 272; unflagged = 4,811,812 rows / 4,811,752 distinct codes. The outputs also retain the complete overlap matrix. Class C is not an exclusion class.
- Country impacts cover all 237 mapped ISO units and reconcile exactly to `normalized_country_profile.csv`. Indonesia has 9,118 baseline rows, with 7 A, 56 B, and 0 C rows; 1,111 rows (12.184690%) have `categories_tags`.
- Two A/B rows meet the defined strong-food-signal criteria. The baseline and both sensitivity scenarios are present globally and per ISO unit; the all-A/B scenario excludes 14,888 rows globally, while the scenario retaining the two strong-signal rows excludes 14,886. Indonesia's two sensitivity scenarios each exclude 63 rows.
- The `fr:wood` check found zero rows outside the specified floor-covering tag. The pinned taxonomy check, contradiction sample, signal validation, and discovery/review queues are retained in the generated outputs.
- All 11 offline `nonfood_scope_*.csv` outputs were byte-identical across two consecutive successful runs. Baseline country counts matched all 237 ISO units. Online validation found three listed Hub commits with matching Parquet hash and size, but the originating commit, local retrieval date, and extraction method remain not determined. The nine-row claim log contains 4 supported, 2 partially supported, and 3 not-verified results; none was contradicted.
- Documented the outputs and evidence in `docs/01_data_source.md`, `docs/02_data_profile.md`, and `docs/03_analysis_workflow.md`. No conclusions about market size or sales are inferred from these record counts.

Status:
Audit complete; owner-approved reporting policy documented; source retrieval provenance and remaining category/brand mapping decisions remain open

---

## ITEM-020

Type:
Category Reporting-Group Decision

Title:
Resolve the 18 Highest-Volume Multi-Group Tags

Decision:
Approve one primary reporting group for each of the 18 highest-volume multi-group tags, using the finished product type rather than assigning every taxonomy ancestry or ingredient path. Preserve the taxonomy candidates and rationale; do not generalize these decisions to similar tags.

Reason:
The reviewed tags accounted for 261,526 tag-record assignments and were the 18 P1 items in the ambiguous queue. Exact taxonomy ancestry can represent ingredients, composition, or a broad parent group rather than the best single reporting group for a finished product. A consistent primary assignment prevents automatic multi-counting for these tags while preserving other legitimate group overlaps at the source-record level.

Result:

- Added `data/mappings/category_tag_reporting_group_manual_decisions.csv` with 18 exact-tag decisions, owner-approved status, group IDs, rationale, and review date.
- Updated `scripts/07_category_reporting_group_draft.py` to validate decisions against the category profile, taxonomy ancestry, and approved reporting-group framework; include approved assignments in per-group and per-country coverage; and keep the taxonomy-derived candidate groups visible in the crosswalk.
- Regenerated the category crosswalk and review queues with scripts `07` and `08`. The 18 tags now have `manual_group_assignment` status (261,526 tag-record assignments); 864 remaining ambiguous tags (187,537 assignments) remain unresolved. No other multi-group tags were automatically assigned.
- Regenerated group assignment totals. Approved manual assignments are included in primary candidate coverage; residual `Other / unclassified` remains diagnostic-only. Country denominators match `normalized_country_profile.csv` for all 237 ISO units.
- The owner-approved grouping rule is: dairy desserts, yogurts, milkfat, and butter to Dairy & eggs; honey to Sweet foods & desserts; tomato sauces, jams, and preserves to Condiments, fats & spreads; potato crisps to Salty snacks; dairy drinks to Beverages; compotes to Fruits & vegetables; and vegetable soups to Prepared meals. Each exact tag and rationale is listed in the mapping input.
- Updated `docs/02_data_profile.md` and `docs/03_analysis_workflow.md`. The overall category crosswalk remains provisional; remaining ambiguous, unmatched, and residual values require review.

Status:
18 exact-tag decisions implemented; remaining category and brand mapping review pending

---

## ITEM-021

Type:
Category and Brand Harmonization Decision

Title:
Apply Ten Supported Category Assignments and an Initial Brand Text Batch

Decision:
Implement the owner's approval of ten exact-tag reporting-group assignments supported by co-occurring taxonomy tags, and normalize the approved initial brand-text batch using case/whitespace-only mappings. Preserve all source values and leave unrelated candidates unresolved.

Reason:
The ten category tags were absent from the pinned taxonomy, so an exact taxonomy alias could not be asserted. Their reviewed source records co-carried exact taxonomy tags that support the approved reporting groups. The brand candidates differed only by case and/or whitespace; a separate exact-value mapping preserves auditability and avoids broad automated merges.

Result:

- Expanded `data/mappings/category_tag_reporting_group_manual_decisions.csv` from 18 to 28 approved exact-tag decisions. The ten additional source tags are `en:fruits-based-foods`, `en:poultry-meals`, `en:beef-dishes`, `en:labeled-cheeses`, `en:aoc-cheeses`, `en:ravioli`, `en:raw-cured-ham`, `fr:boudins`, `en:lemonade`, and `en:spice-mix`.
- Added `supporting_exact_tags` to the category decision input. Updated `scripts/07_category_reporting_group_draft.py` to require exact taxonomy-node evidence for approved tags absent from the taxonomy, validate exact co-occurrence in the Parquet, and write both evidence tags and their source-row co-occurrence counts to the crosswalk. These assignments do not claim taxonomy aliases.
- The evidence check confirmed co-occurrence counts of 38,389/38,389 for `en:fruits-based-foods`; 7,037/7,037 for `en:poultry-meals`; 3,215/3,215 for `en:beef-dishes`; 2,029/2,029 for `en:labeled-cheeses`; 2,011/2,011 for `en:aoc-cheeses`; 1,934/1,934 for `en:ravioli`; 1,917/1,918 for `en:raw-cured-ham`; 1,352/1,352 for `fr:boudins`; 1,544/1,550 beverage/soda evidence rows for `en:lemonade`; and 1,602/1,603 condiment/spice evidence rows for `en:spice-mix`. Exact per-support-tag counts are in `outputs/profiling/category_reporting_group_candidate_crosswalk.csv`.
- The refreshed crosswalk reports 28 manual assignments (322,564 tag-record assignments), 864 unresolved multi-group tags (187,537 assignments), 1,078 diagnostic residual tags (2,797,475 assignments), and 106,216 unmatched tags (427,607 assignments). Country/category outputs reconcile exactly to `normalized_country_profile.csv` for all 237 ISO units; all 107 shortlisted units are present. Indonesia remains at 9,118 country-assigned rows, with 1,111 rows carrying category tags, 786 with a primary-group candidate, and 651 with a diagnostic residual tag.
- Added `data/mappings/brand_name_manual_decisions.csv` with 56 exact source `brands` values mapped to 11 approved canonical text groups. The mappings only change case and/or whitespace; they do not split multi-brand strings, map `brands_tags`, or modify the Parquet. Updated `scripts/05_category_brand_profile.py` to validate every exact source value and create `outputs/profiling/brand_name_manual_mapping_validation.csv`. These source values occur on 128,587 rows in total.
- Regenerated the category review queues. All nine script 07/08 outputs were byte-identical across consecutive runs; all 11 script 05 outputs were byte-identical across consecutive runs. Python compilation and country-denominator reconciliation passed.
- Updated `docs/02_data_profile.md` and `docs/03_analysis_workflow.md` with the approved decisions, evidence, current counts, outputs, and remaining review scope.

Status:
Ten supported category decisions and the initial brand text batch implemented; broader category mapping, brand-tag/multi-brand rules, and remaining unresolved values stay open for owner review

---

## ITEM-022

Type:
Category Reporting-Group Decision

Title:
Resolve the Next 23 High-Frequency Multi-Group Tags

Decision:
Apply the owner's approval of the recommended reporting group for 23 exact tags from the next-highest-frequency portion of the multi-group queue. Keep `en:cheese-spreads` unresolved because its co-occurring exact tags support both dairy and spread classifications.

Reason:
The recommendations were based on exact taxonomy tags co-occurring in source rows and deterministic product-record examples. The selected reporting group reflects the reviewed finished product type; decisions apply only to the listed exact tags and are not generalized to similar categories.

Result:

- Added 23 exact-tag decisions to `data/mappings/category_tag_reporting_group_manual_decisions.csv`, each with supporting exact taxonomy tags, review rationale, and date. Their total is 62,371 tag-record assignments. The reviewed tags are `en:ketchup`, `en:plain-fermented-dairy-desserts`, `en:apple-compotes`, `en:greek-style-yogurts`, `en:plain-yogurts`, `en:flower-honeys`, `en:strawberry-jams`, `en:cereal-based-drinks`, `en:flavoured-milks`, `en:flavoured-potato-crisps`, `en:potato-crisps-in-sunflower-oil`, `en:oat-based-drinks`, `fr:fromages-blancs`, `en:citrus-jams`, `en:entremets-mousses-and-creamy-puddings`, `en:apricot-jams`, `en:creamy-puddings`, `en:fruits-in-syrup`, `en:cow-milk-yogurts`, `en:marmalades`, `en:coconut-oils`, `en:potted-meats`, and `en:cream-of-vegetable-soups`.
- Updated crosswalk outputs contain 51 manual group assignments (384,935 tag-record assignments); 841 multi-group tags (125,166 assignments) remain unresolved. `en:cheese-spreads` remains among them with 2,542 tag-record assignments.
- Current group tag-record assignment totals are Fruits & vegetables 538,538; Cereals, potatoes & bakery 707,840; Meat & poultry 756,142; Fish & seafood 315,314; Dairy & eggs 870,834; Beverages 1,099,112; Sweet foods & desserts 1,289,885; Salty snacks 192,809; Prepared meals 384,529; Condiments, fats & spreads 918,692; and diagnostic-only Other / unclassified 2,797,475. Group totals overlap and are not record counts.
- The country outputs reconcile exactly with `normalized_country_profile.csv` for all 237 ISO units; all 107 shortlisted units are present. Indonesia remains at 9,118 country-assigned rows, 1,111 category-tagged rows, 786 rows with a primary-group candidate, 132 with multiple primary groups, and 651 with a diagnostic residual.
- The remaining 1,000-tag unmatched priority queue covers 227,485 of 427,607 unmatched tag-record assignments (53.20%). The refreshed ambiguous queue contains 841 tags and 125,166 tag-record assignments.
- Scripts 07 and 08 were rerun; all nine generated outputs were byte-identical across consecutive runs. Exact country denominators passed reconciliation.
- Updated `docs/02_data_profile.md` and `docs/03_analysis_workflow.md`. Raw Parquet values were not changed.

Status:
23 exact-tag decisions implemented; `en:cheese-spreads` and remaining category ambiguity stay unresolved for owner review

---

## ITEM-023

Type:
Information Architecture Decision

Title:
Remove Superseded Non-Food Script and Processed Code Lists

Decision:
Remove the legacy `non_food.py` script and its three code-list CSVs from `data/processed/`. Keep `scripts/09_nonfood_scope_audit.py` and its reproducible `outputs/profiling/nonfood_scope_*.csv` evidence as the maintained non-food audit workflow.

Reason:
The legacy script is not referenced by the current README, documentation, or active scripts. Its regex-driven tiers, case-folding, code-level grouping, and limited `code,tier` exports do not follow the current audit definitions or reporting units, and duplicate codes can obscure row-level counts. Retaining it alongside the maintained audit would create competing, misleading artifacts.

Result:

- Deleted `non_food.py` and `data/processed/nonfood_codes_A_strong.csv`, `data/processed/nonfood_codes_B_likely.csv`, and `data/processed/nonfood_codes_C_review.csv`.
- Kept the source Parquet, mappings, official audit script, and eleven generated `nonfood_scope_*.csv` profiling outputs unchanged.
- No dependencies or workflow references required updating; the README workflow already uses the maintained `scripts/` pipeline and does not list `data/processed/`.

Status:
Legacy artifacts removed; maintained non-food audit remains in `scripts/` and `outputs/profiling/`

---

## ITEM-024

Type:
Workflow and Relational Design Decision

Title:
Defer Further Stage 2 Mapping Review and Begin Stage 3

Decision:
Treat Stage 2 harmonization as sufficient to proceed to relational design, but not as fully complete. Pause additional category/brand review batches unless a concrete schema or analysis need makes a specific mapping decision material. Begin Stage 3 with a provisional logical schema draft; do not implement the physical database or SQL DDL until the owner reviews and approves the logical design.

Reason:
Reviewing every long-tail category or brand value before database design would be costly and may have little analytical impact. The current model can preserve source values and represent approved, candidate, excluded, and unresolved statuses without forcing premature harmonization. Targeted review can resume if design or validation demonstrates that a specific unresolved rule changes an intended result.

Result:

- Updated `docs/03_analysis_workflow.md` to mark Stage 2 sufficient to proceed with mapping backlog deferred and Stage 3 in progress.
- Added `docs/04_relational_schema_design.md` with a provisional logical entity/grain proposal, relationship sketch, preservation and mapping rules, open owner decisions, and Stage 3 exit criteria.
- The draft preserves each of the 4,828,207 source rows, does not use `code` as a primary key or deduplicate duplicate-code records, separates exact source-tag associations from canonical country/category assignments, and defers a canonical brand entity until multi-brand and `brands`/`brands_tags` semantics are approved.
- Updated `README.md` to link the draft and accurately state that no physical database or SQL build exists yet.
- No files were added to `sql/`; Stage 4 DDL is gated on owner approval of Stage 3 grains, keys, and relationships.

Status:
Stage 2 sufficient to advance with targeted mapping review deferred; Stage 3 logical design draft awaiting owner review

---

## ITEM-025

Type:
Relational Design and Database Build Decision

Title:
Approve DuckDB Relational Model and Build the Current Snapshot

Decision:
The owner approved a DuckDB database file, full 111-column source landing, source-file-hash snapshot identity, and separate preservation of exact `brands` text and `brands_tags`. Keep category candidates separate from approved group decisions and do not resume broad Stage 2 mapping review. Implemented and validated the initial relational database for the current pinned snapshot.

Reason:
The project can now begin analysis specification from a stable, traceable record-level model without deduplicating source rows or forcing unresolved category and brand values into canonical assignments.

Result:

- Added `sql/01_build_relational_database.sql`, `sql/02_validate_relational_database.sql`, and `scripts/11_build_relational_database.py`.
- Created `data/processed/global_product_landscape.duckdb` (15,109,992,448 bytes) and `outputs/quality/database_build_validation.csv`.
- Preserved 4,828,207 source rows and all 111 source columns; the source table adds `source_record_id`, `snapshot_id`, and `source_row_ordinal`. All 61 known duplicate-code groups remain present.
- Loaded the 249 ISO reference units; the 237 units in the normalized country profile reconcile exactly.
- Reconciled 10,480,049 category-tag, 5,079,894 country-tag, and 3,313,249 brand-tag record assignments against the source arrays. All 15 build checks passed, and the database reopened successfully for independent inspection.
- Updated the schema, workflow, README, and `.gitignore`. Stage 3 design and Stage 4 build are complete for this pinned snapshot; Stage 5 analysis specification is next.

Status:
Stage 3 complete; Stage 4 complete for the current pinned snapshot; further Stage 2 mapping review remains deferred.

---

## ITEM-026

Type:
Analysis Scope Recommendation

Title:
Draft Stage 5 Analysis Specification for Owner Review

Decision:
Prepared a recommendation draft for Stage 5; no new analytical scope decisions are treated as approved. Do not start Stage 6 SQL until the owner resolves the listed pending decisions.

Reason:
The project has a validated relational database and existing coverage evidence, but peer comparability, use of taxonomy-derived category candidates, and the scope of brand-concentration metrics require explicit decisions before analysis results are produced.

Result:

- Added `docs/05_analysis_specification.md` with evidence-based recommendations for country scope, category mapping status, source-record unit, brand coverage/concentration, and the previously agreed non-food sensitivity scenarios.
- The draft records the current 107-unit/1,000-row screening set as candidate countries, not a final peer list. It highlights Indonesia's 9,118 rows and 1,111 rows with category tags (12.1847%).
- It proposes candidate-derived and approved-only category views separately, and recommends deferring broad HHI claims while brand mapping remains limited to 56 exact values across 11 canonical groups.
- Updated `docs/03_analysis_workflow.md` and `README.md` to mark Stage 5 draft ready for owner decisions. No analytical SQL or Stage 6 outputs were created.

Status:
Stage 5 specification draft ready for owner review; Stage 6 not started.

---

## ITEM-027

Type:
Analysis Scope Decision

Title:
Approve Bounded Stage 5 Measurement Rules

Decision:
Approved source rows as the primary unit, with distinct-code counts diagnostic only; approved a candidate-derived category view with an approved-only sensitivity view; approved limiting brand reporting to the currently mapped canonical groups and deferring HHI/broad concentration claims; reaffirmed the baseline and both A/B non-food sensitivities, Class C discovery-only treatment, and diagnostic-only non-category signals for Indonesia. Approved the 107-unit, 1,000-row country shortlist as a candidate set, not a final peer list. Final peer selection remains pending a bounded review of country coverage evidence.

Reason:
These choices make the upcoming analysis useful without pretending unresolved product identity, candidate category mapping, or partial brand mapping are fully harmonized. A single focused review supports peer selection without restarting broad Stage 2 mapping work or introducing arbitrary quality cutoffs.

Result:

- Updated `docs/05_analysis_specification.md` with owner-approved decisions and one remaining Stage 5 gate: final country peer selection from the existing 107-unit candidate set after a compact evidence review.
- Updated the workflow and README to reflect Stage 5 as in progress and Stage 6 as not started.
- No Stage 6 SQL or analytical outputs were created.

Status:
Stage 5 decisions mostly approved; final country peer selection pending evidence review.

---

## ITEM-028

Type:
Stage 5 Evidence and Recommendation

Title:
Profile Country Candidates for Final Peer Selection

Decision:
Generated a deterministic, snapshot-pinned evidence table for the 107 countries meeting the existing 1,000-row screen. Recommend Malaysia (MY), Philippines (PH), and Singapore (SG) as a small primary candidate peer set for owner review; consider Thailand (TH) as a coverage-contrast case and Vietnam (VN)/Cambodia (KH) as optional extended context. This is a recommendation, not an owner-approved final peer list.

Reason:
The peer decision should use a bounded, reproducible coverage review rather than record volume alone or an expanded mapping-review batch. Country category-tag coverage and exact approved brand-mapping coverage differ substantially and must be visible before comparison.

Result:

- Added `scripts/12_stage5_country_peer_evidence.py` and generated `outputs/profiling/stage5_country_peer_evidence.csv` for all 107 screened country units.
- The output includes source rows and distinct codes separately, category-tag coverage, candidate-derived and approved-only group-assigned row coverage, approved exact brand mapping coverage, and A/B flagged rows. It is pinned to source SHA-256 `DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A`.
- Category-tag coverage across the 107 units ranges from 2.9863% to 99.0960% (median 33.4218%); approved exact brand mappings cover a median 0.4363% of country rows, and 11 units have zero mapped rows.
- Indonesia has 9,118 source rows, 1,111 rows with category tags (12.1847%), 786 rows assigned at least one primary candidate group, 106 rows assigned at least one approved category group, one row with an approved exact brand mapping (0.0110%), and 63 A/B-flagged rows.
- The peer-evidence output was regenerated and confirmed byte-identical.
- Updated the Stage 5 specification, workflow, data profile output inventory, README, and project log. No Stage 6 SQL or analytical outputs were created.

Status:
Stage 5 evidence review complete; final peer set awaits owner confirmation; Stage 6 not started.

---

## ITEM-029

Type:
Risk-Based Data Readiness Review

Title:
Assess Stage 2 Reopen Need Before Peer Selection

Decision:
Do not reopen Stage 2 wholesale. The current snapshot/database and country evidence are adequate for bounded descriptive comparisons when limitations are explicit. Category results must remain split between candidate-derived and approved-only assignments; broad brand-concentration analysis is not ready because exact approved brand coverage is extremely low. Keep Stage 0 provenance limitations visible before release.

Reason:
The readiness check focused on the proposed Indonesia-centered comparison, so the cost of reviewing every remaining category or brand tag was not justified. It tested record identity impact, country denominator reconciliation, category coverage, brand-mapping coverage, and the agreed A/B sensitivity directly.

Result:

- Extended `outputs/profiling/stage5_country_peer_evidence.csv` to report source rows and distinct-code counts separately and to fail on missing codes or country denominator mismatches.
- Among the 107 screened units, 12 have within-unit repeated codes and their total row-minus-distinct-code gap is 61. Indonesia and the regional candidate units ID, MY, PH, SG, TH, VN, and KH have no within-unit gap.
- Confirmed category-tag coverage and approved-only category assignment counts are too limited for unqualified category claims; retain candidate-derived and approved-only views as separately labeled.
- Approved exact brand mapping coverage is too low for broad brand concentration or HHI in the focal/candidate set; defer those claims rather than launch an unnecessary Stage 2 brand review.
- The two A/B sensitivity definitions differ by two strong-food-signal rows overall and by zero rows in the focal/candidate regional units. Indonesia's A/B scenarios exclude 63 rows from 9,118; candidate peer exclusions range from zero to two rows.
- Updated `docs/05_analysis_specification.md` with the risk assessment, `docs/02_data_profile.md` with the updated output definition, and this decision log.
- No broad mapping review, analysis SQL, or Stage 6 outputs were created.

Status:
Risk-based readiness review complete; Stage 2 remains parked; final peer list awaits owner confirmation.

---

## ITEM-030

Type:
Stage 5 Approval and Stage 6 Analysis

Title:
Approve Country Scope and Complete Descriptive Analysis

Decision:
Owner approved Indonesia (ID) as the focal unit, MY/PH/SG as contextual peers, and TH as a separate category-coverage contrast. Vietnam and Cambodia remain outside Stage 6. Proceed with descriptive analysis using source rows as the primary unit, candidate-derived and approved-only category views, and only exact-approved brand mappings. Do not calculate HHI or make broad brand-concentration, market-share, or sales-based claims.

Reason:
The peer evidence showed that MY/PH/SG category-tag coverage is closer to Indonesia's than Thailand's, while Thailand provides a distinct higher-coverage contrast. Sparse exact-approved brand mapping and incomplete category assignments require explicit coverage limits rather than broad claims or another general Stage 2 review.

Result:

- Added the Stage 6 runner and SQL outputs for country scope, category assignments, mapped canonical-brand assignments, and validation.
- Stage 6 outputs are pinned to snapshot SHA-256 `DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A`.
- The outputs contain 15 country-scenario rows, 300 country-category rows, and 36 mapped-brand rows. Category results report category-tagged rows without a substantive group assignment separately for candidate-derived and approved-only bases.
- All 11 validation checks passed, including country and A/B reconciliation, approved-only decision linkage, brand assignment denominators, and category coverage arithmetic.
- A rerun produced byte-identical hashes for all four published CSVs, including the validation report.
- Updated the analysis specification, workflow, README, data-profile output inventory, and this log. Stage 2's broad harmonization backlog remains deferred; Stage 0 provenance remains a release-readiness limitation.

Status:
Stage 5 scope approval and Stage 6 descriptive analysis complete for the pinned snapshot; Stage 7 findings and Stage 0 release provenance remain open.

---

## ITEM-031

Type:
Quality Control and Workflow Principle

Title:
Adopt Traceable Analysis Flow and Impact-Based Harmonization Loop

Decision:
Adopt the operating principle **data and approved mappings → scripts/SQL → outputs/evidence → documentation**, with a quality-control gate against garbage-in/garbage-out. Treat harmonization as a targeted feedback loop: measured results may justify a specific, impact-based review; only approved changes return to the inputs for the affected analysis, which must then be rerun and validated. Maintain project information architecture and update the ChatGPT handoff after material changes. Do not require full Stage 2 harmonization as a blanket prerequisite.

Reason:
Full harmonization can reduce some classification uncertainty but cannot guarantee valid inputs, representative coverage, correct transformations, or sound interpretation. Forcing unresolved values into categories can create false precision. Explicit mapping status, coverage gaps, denominators, and validation are more reliable controls than completeness for its own sake.

Result:

- Added the operating flow, feedback loop, maintenance rule, and GIGO quality-control requirements to `docs/03_analysis_workflow.md` and `HANDOFF_FOR_CHATGPT.md`.
- Stage 2 remains sufficient to proceed but intentionally incomplete. Reopen only specific mappings where evidence shows material impact on an approved question.
- Stage 6's 11 checks are recognized as structural/reconciliation controls, not proof of semantic mapping correctness or representativeness.

Status:
Approved; apply to subsequent analysis and documentation maintenance.

---

## ITEM-032

Type:
Stage 7 Findings and Recommendations

Title:
Interpret Validated Stage 6 Results Within Evidence Limits

Decision:
Complete Stage 7 for the approved descriptive scope by documenting source-record counts, category-tag coverage, candidate-derived category patterns, approved-only sensitivity, category coverage gaps/overlap, sparse exact-approved brand mappings, and A/B sensitivity impact. Make no market-share, HHI, broad concentration, unique-product, or commercial-dominance claims.

Reason:
The Stage 6 outputs and checks are complete, but variable category coverage, candidate mapping status, record overlap, sparse brand mapping, and unresolved source provenance constrain interpretation. Findings should be useful without implying more certainty or representativeness than the evidence supports.

Result:

- Added `docs/06_stage7_findings_and_recommendations.md` with evidence-linked tables and explicit distinctions between observation, interpretation, recommendation, and limitation.
- Reported country scope and coverage: ID 9,118 rows / 12.1847% category-tag coverage; MY 7,426 / 11.3116%; PH 9,176 / 16.7284%; SG 11,986 / 17.3035%; TH 11,343 / 62.6289%.
- Kept category counts explicitly candidate-derived and overlapping; reported approved-only assignments as a separate narrow sensitivity and unassigned tagged rows as coverage gaps.
- Reported approved exact-brand mapping as too sparse for broad brand conclusions; retained baseline and both A/B sensitivity scenarios.
- Updated workflow, README, and ChatGPT handoff. Stage 2 broad harmonization remains deferred; reopen only specific mappings where material impact is demonstrated.

Status:
Stage 7 complete for the approved descriptive scope; Stage 0 provenance and Stage 8 release/recovery acceptance remain open.

---

## ITEM-033

Type:
Stage 0 and Stage 8 Readiness

Title:
Audit Local Provenance Evidence and Recovery Preflight

Decision:
Do not infer the source retrieval date or extraction method from the source file's filesystem timestamp. Record the bounded project-local provenance search and its limits. Begin Stage 8 with read-only database preflight, but do not create a large backup until a safe destination is selected.

Reason:
No contemporaneous local download record was found in the reviewed project docs, scripts, or outputs. The database is 15,109,992,448 bytes; C: has less than one database copy free, while D: has about 99.9 GB free. A same-volume D: backup would not protect against D: failure, and storage location is a material recovery decision.

Result:

- The local source file's Windows last-write timestamp is 2026-10-23 14:43:35 local time. It is explicitly not treated as proof of retrieval because copies/restores may change filesystem timestamps.
- The project-file audit found no contemporaneous retrieval date/method record. No user-level browser/download history was inspected.
- Reopened DuckDB in read-only mode; confirmed snapshot ID `DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A`, 16 tables, and 4,828,207 source records.
- Confirmed `record_country_source_tag` has 5,079,894 exact tag links and the deduplicated `record_country` bridge has 5,004,567 record-to-ISO rows. Clarified this distinction in workflow, schema, and handoff documentation.
- Stage 4's 15 checks and Stage 6's 11 checks remain passed. No backup or restore copy has been created.

Status:
Preflight documented; persistent backup destination and recovery test pending owner choice.

---

## ITEM-034

Type:
Storage Audit and Efficiency

Title:
Measure DuckDB Footprint and Record Storage Trade-off

Decision:
Record the measured database footprint and explain it as a relational analytical derivative, not an uncompressed copy of the Parquet. Preserve the current database; consider storage optimization only through a separately built and fully validated alternative.

Reason:
The 15.11 GB DuckDB file is materially larger than the 7.98 GB Parquet, and the owner explicitly values storage efficiency alongside analytical quality. The existing model retains the 111-column source landing and separately materializes relational bridges and unique indexes for traceability/querying. Deleting data or indexes without a validated alternative would risk lineage, analysis, and recovery.

Result:

- Read-only `PRAGMA database_size` reported 14.0 GiB rounded, 57,588 used 256-KiB blocks, 52 free blocks, and WAL size 0 bytes.
- Database contains 16 tables and 15 unique indexes. Row counts include 4,828,207 source records, 10,480,049 category-tag links, 5,079,894 source-country-tag links, 5,004,567 deduplicated record-to-ISO links, and 3,313,249 brand-tag links.
- The source plus database currently occupy about 23.09 GB decimal before other project files/backups. No precise per-table/index byte attribution has been measured.
- Documented candidate optimization directions for a future separate build: use pinned Parquet as canonical raw storage with fewer duplicated persisted columns/relations where justified; review index necessity; benchmark and rerun all validation before replacement.
- No backup, restore copy, database rewrite, index removal, or source modification was performed.

Status:
Audit documented; optimization is not implemented; preserve current database pending a validated alternative and owner approval.

## ITEM-035

Type:
Stage 2 Mapping Impact Audit

Title:
Reopen Stage 2 for Five Approved Category Decisions

Date:
2026-11-04

Decision:
Approve and measure five exact-tag reporting-group decisions within the existing Stage 6 country scope. Keep broad category and brand harmonization parked; do not infer mappings for unresolved tags.

Approved decisions:

- `en:drinkable-yogurts` → `dairy_eggs`
- `en:savory-snacks` → `salty_snacks`
- `en:chili-paste` → `condiments_fats_spreads`
- `en:juice` → `beverages`
- `en:bars-covered-with-chocolate` → `sweet_foods_desserts`

Reason:
The owner approved these exact assignments after a bounded review of in-scope records and exact-tag/co-occurrence evidence. Their assignments affect the candidate-derived and approved-only category views for ID, MY, PH, SG, and TH; therefore downstream category outputs need a measured impact review rather than silently retaining the prior mapping state.

Result:

- Added the five approved decisions to `data/mappings/category_tag_reporting_group_manual_decisions.csv`; regenerated the candidate crosswalk and review queues.
- Added reproducible audit script `scripts/14_stage2_selected_scope_mapping_impact.py`. It validates the approved decisions and crosswalk before scanning the pinned Parquet and emits `outputs/profiling/stage2_selected_scope_mapping_tag_impact.csv` and `outputs/profiling/stage2_selected_scope_mapping_coverage_delta.csv`.
- In-scope per-tag source-row counts, by country, are recorded in the tag-impact CSV. Counts can overlap across tags.
- Candidate-derived records assigned to at least one primary group changed ID 786→788 (+2), MY 619→620 (+1), PH 1,263→1,273 (+10), SG 1,805→1,806 (+1), and TH 4,497→4,516 (+19).
- Approved-only records assigned to at least one primary group changed ID 106→109 (+3), MY 82→84 (+2), PH 135→157 (+22), SG 243→251 (+8), and TH 621→653 (+32). Approved-only multi-group overlap increased by one TH row; candidate-derived overlap increased by two TH rows.
- Country source-row and category-tagged-row denominators did not change. The existing Stage 4 database, Stage 6 outputs, and Stage 7 findings remain the prior mapping baseline.
- Documentation and handoff now mark the old Stage 6/7 results historical pending a separately built and validated database candidate and Stage 6 rerun.
- No backup, overwrite, database rebuild, or source modification was performed.

Status:
The bounded Stage 2 decision and impact audit is complete. Preserve the existing database; the next analytical task is to build and validate a separate database candidate, rerun Stage 6, and then refresh Stage 7. Do not create a backup unless the owner explicitly changes the prior instruction.

## ITEM-036

Type:
Stage 0 Provenance and License Recheck

Title:
Revalidate Pinned Source Identity and Current Reuse References

Date:
2026-11-04

Decision:
Keep the existing local Parquet as the pinned source snapshot. Do not replace it with current Hugging Face `main`; the actual local retrieval commit, retrieval date, and local extraction/download method remain unknown. Keep Stage 0 open for public-release decisions about attribution, license scope, and project-authored code.

Reason:
The project is intended for public portfolio use. Rechecking source identity and current license statements helps prevent a silent source refresh or unsupported release claims, while preserving the approved immutable snapshot and not making legal conclusions.

Result:

- Rehashed `data/raw/food.parquet` locally on 2026-11-04: 7,975,461,945 bytes; SHA-256 `DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A`.
- The local size/hash continue to match three previously verified October 2026 Hugging Face commits: `31f31c441274c095718cc88ae582030a5a615415`, `0273016bf1a86da29ccb1b22a487574f0c9a31ea`, and `99d7ba5bcb35b693300108f43cfaeee508b7e915`. Matching content does not establish which commit was actually retrieved.
- The Hugging Face API reports current `main` commit `e5ed2fae58c2ce58d26a1298f61c7d40b1bd1e4a`, updated 2026-11-04 08:01 UTC. Its current `food.parquet` metadata reports 8,029,922,066 bytes and SHA-256 `84D9D985BB1262EE1F8B71770ADA9ADA2F87F0B40B8A37BC99917111FB0E95E6`; it differs from the local artifact. The current source was not downloaded and the local snapshot was not changed.
- Rechecked current Open Food Facts reuse terms: database ODbL 1.0, individual contents DbCL 1.0, and product images CC BY-SA 3.0; attribution/linking to Open Food Facts and applicable share-alike terms are required. The project does not use product images.
- Current Hugging Face card/API still lists `AGPL-3.0` and `ODbL` but does not clarify whether AGPL applies to dataset data or accompanying conversion code. Do not infer the project's own code license from this metadata.
- For publication, document source attribution and derivative treatment, resolve the Hugging Face metadata ambiguity for any data redistribution, and select a license for project-authored code. This is not a legal determination.
- No source file, database, or backup was created, replaced, or modified during this audit.

Status:
Source identity and current upstream difference are documented; actual retrieval provenance and publication-license decisions remain open. Stage 0 is partially evidenced but not closed.

---

## ITEM-037

Type:
Stage 6 Candidate Build and Findings Refresh

Title:
Validate Compact Candidate and Refresh Stage 5–7

Date:
2026-11-04

Decision:
Use a separately built, scope-limited database candidate for the current approved Stage 5/6 analysis. Preserve the existing full database and pinned source. Publish the refreshed Stage 6 outputs only after candidate and analysis validations pass.

Reason:
Five approved category decisions changed the Stage 6 mapping inputs. Rebuilding the full 15.11 GB database was unnecessary for the bounded analysis; a smaller candidate could preserve the required source evidence and bridges while reducing incremental storage use.

Result:

- Added `scripts/15_build_stage6_candidate_database.py`. The candidate at `data/processed/global_product_landscape_stage6_candidate.duckdb` is 173,551,616 bytes versus 15,109,992,448 bytes for the original database (about 98.85% smaller). It is a Stage 6-only derivative, not a full database replacement or recovery copy.
- Candidate validation passed all 13 checks, including exact Stage 6 source-projection and country/category/brand bridge comparisons against the original database.
- Regenerated the 107-unit Stage 5 evidence from the candidate and published it to `outputs/profiling/stage5_country_peer_evidence.csv`.
- Reran Stage 6 using the candidate and current country evidence. All 11 checks passed; the 15 country-scenario, 300 country-category, and 36 mapped-brand rows were published under `outputs/analysis/`. All four published CSVs match the validated candidate-run files byte-for-byte.
- Refreshed `docs/06_stage7_findings_and_recommendations.md` with the current candidate-derived and approved-only counts, group patterns, and overlap diagnostics. Updated the analysis specification, workflow, schema note, data profile, README, and handoff.
- The original database and pinned Parquet were not modified. No backup was created.

Status:
The bounded candidate-backed Stage 5–7 workflow is complete. Stage 0 provenance/release decisions and Stage 8 release/recovery acceptance remain open; broad Stage 2 harmonization remains intentionally incomplete.

---

## ITEM-038

Type:
Automated Harmonization Refresh

Title:
Automate Deterministic Mapping Propagation and Findings Refresh

Date:
2026-11-04

Decision:
Automatically regenerate deterministic single-group category candidates and downstream analysis evidence after maintained mapping inputs change. Do not auto-edit or approve owner-maintained mapping decisions. Keep ambiguous and weakly supported values unresolved.

Reason:
The owner requested automatic propagation of harmonization changes while preserving the agreed GIGO control: high-confidence, deterministic rules may be applied automatically, but ambiguous values must not be forced into groups.

Result:

- Added `scripts/16_refresh_harmonized_analysis.py` to run the category crosswalk and review queues, build a temporary compact candidate, validate it, regenerate Stage 5 and Stage 6, and refresh the data-driven tables and figures in Stage 7.
- The candidate database is temporary and removed after the run. The latest candidate validation report, Stage 5/6 outputs, refresh summary, and updated Stage 7 findings are retained.
- The full workflow completed successfully: 13/13 candidate checks, 107 Stage 5 units, and 11/11 Stage 6 checks passed. The published Stage 6 CSV hashes remain identical to the validated prior run.
- The run retained 841 multi-group tags, 106,211 taxonomy-unmatched tags, and diagnostic residuals as non-approved/unresolved rather than forcing assignments. The existing 56 owner-approved exact-tag decisions were not changed.
- Added stable generated-section markers to Stage 7 so result-dependent counts, coverage tables, overlaps, and assignment summaries are refreshed from validated CSVs.
- Updated README, workflow, and handoff with the one-command process. No backup was created, the pinned Parquet and original full database were not modified, and temporary run files were cleaned up.
- Investigated the reported VS Code “Could not keep changes” context: the workspace is writable and edits are saved directly, but this workspace has no `.git` directory. The exact UI error was not available, so the Copilot UI failure itself could not be diagnosed.

Status:
The automated candidate-to-analysis refresh is implemented and verified. Exact manual mapping decisions still require evidence and explicit approval; ambiguous cases remain unresolved. The VS Code Keep UI issue remains unverified pending its exact error message or screenshot.

---

## ITEM-039

Type:
Portfolio Packaging and GitHub Integration

Title:
Prepare Indonesia Food Product Landscape for Public GitHub

Date:
2026-11-04

Decision:
Rename the project to Indonesia Food Product Landscape. Apply MIT only to original project code/documentation, keep Open Food Facts and third-party licensing separate, and publish only reviewed mappings, documentation, code, and a small allowlist of aggregate evidence. Preserve the existing GitHub commit history.

Reason:
The project is intended as a recruiter-facing Market Intelligence Analyst portfolio. The previous public repository contained older setup/sample files and did not reflect the current scoped analysis or the owner's storage/data-sharing constraints.

Result:

- Updated project titles and scope in the README and source/analysis documents. The local folder is designated to become `D:\Projects\indonesia-food-product-landscape`; repository rename to `indonesia-food-product-landscape` was authorized.
- Added the MIT license for original project code and documentation only. Open Food Facts data, third-party references, and derived results are not relicensed by it; source attribution and derivative-use review remain open.
- Updated `.gitignore` with a reviewed aggregate-evidence allowlist. Raw Parquet, DuckDB files, pinned taxonomy JSON, generated profiling inventories, record-level outputs, and environment/cache files are excluded.
- Added only 52 current project files to the tracked tree (about 0.75 MB). Removed the four old sample-record CSVs and legacy setup notebook from the current branch; prior GitHub history was not rewritten and may still contain those older files.
- Connected the local project to the existing repository history and created three local commits: `5a70766`, `587b972`, and `5f2d117`. The commits include the required Copilot co-author trailer. No force-push or history rewrite was used.
- A non-interactive push attempt failed because GitHub credentials could not be requested in this environment. The current public GitHub branch is therefore not yet updated or renamed; user authentication and the repository rename in GitHub Settings are required before pushing and updating the local `origin` URL.
- No source data, database, or backup was modified or uploaded.

Status:
Local packaging is committed and reviewed. Public synchronization and GitHub repository rename remain pending interactive GitHub authentication; Stage 0 source/derivative licensing and Stage 8 recovery acceptance remain open.