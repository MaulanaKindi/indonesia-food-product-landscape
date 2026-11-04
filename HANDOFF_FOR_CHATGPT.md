# Project Handoff for ChatGPT

**Purpose:** Give a new assistant enough verified project context to continue work without depending on this VS Code/Copilot conversation.
**Project root:** `D:\Projects\indonesia-food-product-landscape`
**Prepared:** 2026-11-04
**Current position:** The bounded category review now covers eight exact tags, and four exact brand spellings were approved as two evidence-based pairs. The automated refresh (`scripts/16_refresh_harmonized_analysis.py`) rebuilt the crosswalk and review queues, refreshed brand validation, validated a temporary Stage 6 candidate (15 checks), refreshed Stage 5 (107 units), reran Stage 6 (11 checks), and regenerated Stage 7 tables. The mapping totals are 59 category decisions and 60 brand source values across 13 canonical groups; broad unresolved values remain unresolved. The original full Stage 4 database was not changed and the temporary candidate was removed. Local Stage 8 preflight verified the Parquet and pinned-taxonomy hashes, retained 15/15 Stage 4, 15/15 candidate, and 11/11 Stage 6 checks, and 107 Stage 5 units. Python 3.13.0, DuckDB 2.0.0, and pandas 3.1.0 were recorded. No clean-room rebuild was attempted because it would require replacing the existing 15.1-GB database, and no backup is permitted. The two additional-three impact-audit CSVs are small aggregate evidence and are allowlisted for Git. A separate local `sanitized-main` rewrites all 36 historical commits, and no tree reachable from it contains the four legacy sample-record paths. All reviewed harmonization, evidence, and documentation changes are included on the candidate branch. The original local `main` and public `origin/main` remain unchanged and still reference the old history. No force-push has occurred; explicit approval is required before publication. A force-push cannot revoke prior clones or guarantee removal of cached GitHub objects. Stage 0 is accepted for the scoped portfolio with historical retrieval and license-scope limitations documented. Final Stage 8 release acceptance remains open.

> This handoff is a navigation and continuity document, not a replacement for the source-of-truth documentation and generated evidence listed below. If a number or status differs, check the linked current output and the latest project-log entry. Older project-log entries preserve historical states and may have been superseded by later decisions.

## 1. Instructions for the next assistant

Before making recommendations or edits:

1. Read this handoff and the project documents in `docs/`, especially the business brief, source/provenance note, data profile, workflow, schema design, analysis specification, and project log.
2. Verify important claims against the current files and generated CSVs. Do not rely solely on this handoff or on an old conversation summary.
3. Keep `docs/` and the SQL/Python scripts as the project source of truth. Update directly related documentation when changing a decision, method, or output.
4. Do not treat Stage 2 as fully harmonized. Eight exact category decisions and four exact brand spellings were impact-reviewed; keep the remaining broad category and brand backlog parked unless new evidence establishes material impact.
5. The latest automated Stage 5/6 outputs were produced from a temporary compact candidate; its retained validation report has 15 passed checks and Stage 6 has 11. Stage 7 is current for this candidate-backed run. The temporary candidate was removed. Any older persistent `data/processed/global_product_landscape_stage6_candidate.duckdb` is not the database used by the latest automated run and may contain an earlier mapping.
6. Preserve the existing source data and database. Do not overwrite or rebuild the large database casually. The Stage 4 builder intentionally refuses to overwrite an existing database. Do not create a backup unless the owner explicitly changes the prior no-backup instruction.
7. Keep interpretations descriptive and bounded. Open Food Facts records are not a census of products sold and do not support sales, market-share, revenue, demand, or commercial-dominance claims.
8. If documents conflict, identify the specific conflict and distinguish historical notes from current decisions before changing anything.
9. Follow the agreed project operating principle:
   - **Analysis flow:** data and approved mappings → scripts/SQL → outputs/evidence → documentation.
   - **Control loop:** outputs can trigger a specific, impact-based harmonization review; approved changes return to the inputs for the affected analysis, which must be rerun and validated.
   - **Maintenance:** maintain the information architecture and update this handoff when a material project decision, workflow, file location, output, or status changes.
   - **Quality control:** explicitly check for garbage-in/garbage-out at source, mapping, denominator, transformation, and output levels. A passing SQL reconciliation does not prove that mappings are semantically correct or the data is representative.
10. Do not equate complete harmonization with zero GIGO risk. Avoid forced classifications; leave weakly supported values unresolved and report the resulting coverage limitations.

Suggested first response in a new ChatGPT conversation: confirm understanding of the project, owner-approved decisions, current stage statuses, important limits, and next tasks; point out any unresolved contradiction before proceeding.

## 2. Project purpose and intended deliverable

The project is an exploratory market-intelligence analysis of recorded product variety and brand distribution in Open Food Facts, with Indonesia as the focal geography. It combines source profiling, quality investigation, reviewed mappings, a reproducible DuckDB relational build, SQL-based descriptive analysis, and business interpretation.

The intended comparison is of **records in this snapshot**, by selected ISO 3166-1 country/territory units and project reporting groups. It is not a measurement of every product available in a market. The original business brief also mentions brand distribution/concentration, but the available exact-approved brand mappings are too sparse to support broad concentration analysis. The accepted current scope explicitly defers HHI and broad concentration claims.

Primary project purpose and completion criteria: [`docs/00_business_brief.md`](docs/00_business_brief.md).

### Operating principle and GIGO control

- **Analysis flow:** data and approved mappings → scripts/SQL → outputs/evidence → documentation.
- **Control loop:** a result may trigger only a specific, impact-based harmonization review. Once approved, the mapping change becomes an input and the affected SQL/analysis must be rerun and validated.
- **Maintenance:** maintain the project's file/folder architecture and update this handoff when material decisions, workflows, outputs, locations, or statuses change.
- **Quality control:** verify source/snapshot identity, mapping evidence/status and coverage, measurement unit and denominator, transformation logic, and output reconciliation before drawing conclusions.
- Full harmonization is not a guarantee against garbage-in/garbage-out. It can reduce some mapping uncertainty, but forced or weakly evidenced classifications can create false certainty. Explicit unresolved values and measured coverage gaps are preferable to unsupported completeness.

Stage 6's 11 passed checks establish specified structural and denominator reconciliations for the pinned inputs; they do **not** establish semantic correctness of every mapping, representativeness of Open Food Facts, or validity of commercial conclusions.

## 3. Source data, provenance, and analytical limits

### Dataset and pinned artifact

- Source: Open Food Facts Product Database, via the Hugging Face dataset at `https://huggingface.co/datasets/openfoodfacts/product-database`.
- Local source file: `data/raw/food.parquet` (about 7.98 GB; excluded from Git).
- Observed dataset: **4,828,207 rows**, **111 columns**.
- SHA-256 / snapshot ID: `DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A`.
- The local file is a transformed Parquet conversion of Open Food Facts daily JSONL dumps, not the original unmodified JSONL dump.
- The source and derived database are large. Do not upload the Parquet or the approximately 14 GB DuckDB database to ChatGPT merely to provide context; documents, scripts, schema, and generated CSV outputs are the practical handoff set.

### Stage 0 — accepted for scoped portfolio with explicit limitations

The local source SHA-256 and size match metadata for `food.parquet` in three Hugging Face commits checked on 2026-10-26, but the exact historical retrieval commit, local retrieval date, and local download method have **not** been determined. The owner accepts these as explicitly documented unknowns. Commit `31f31c441274c095718cc88ae582030a5a615415` is selected as a reproducible content reference only; it is not asserted to be the source of the local download. A bounded project-file audit on 2026-10-29 found no contemporaneous local retrieval record. Windows reports last-write time `2026-10-23 14:43:35` local time, but this is not reliable proof of download time because file copies/restores can change timestamps; no user-level browser/download history was inspected.

On 2026-11-04 the local file was rehashed: `7,975,461,945` bytes and SHA-256 `DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A`. The current Hugging Face `main` commit is `e5ed2fae58c2ce58d26a1298f61c7d40b1bd1e4a`; its `food.parquet` metadata reports `8,029,922,066` bytes and SHA-256 `84D9D985BB1262EE1F8B71770ADA9ADA2F87F0B40B8A37BC99917111FB0E95E6`. The current upstream file therefore differs from the local pinned file; do not silently replace the local snapshot. Current-main API metadata is not evidence that the local file came from that commit.

The documented metadata check found these matching commits:

- `31f31c441274c095718cc88ae582030a5a615415` (2026-10-23)
- `0273016bf1a86da29ccb1b22a487574f0c9a31ea` (2026-10-23)
- `99d7ba5bcb35b693300108f43cfaeee508b7e915` (2026-10-22)

Do not guess a retrieval date or method. The Open Food Facts terms describe ODbL 1.0 for the database, DbCL 1.0 for individual contents, and CC BY-SA 3.0 for images; this project does not use images. The Hugging Face card/API also labels the repository `AGPL-3.0` and `ODbL` without clarifying AGPL's scope. The owner accepts public release of reviewed aggregate results with Open Food Facts attribution and links to the terms, while excluding the source Parquet, databases, record-level extracts, and taxonomy. MIT applies only to original project code/documentation; no MIT license is asserted for data-derived outputs. Whether an aggregate is a Produced Work or Derivative Database and what the AGPL metadata covers are not legally determined; see [`docs/01_data_source.md`](docs/01_data_source.md). This is not legal advice.

The taxonomy reference is separately pinned: `data/reference/off_categories_taxonomy_2026-10-25.json`, SHA-256 `EB03AEFABAE4C6269B5FBC3E89160F8DA84CA3300A53787E27EAB5FE2D1020D5`, with 14,774 taxonomy nodes. The product snapshot date is unknown, so this taxonomy cannot be assumed contemporaneous.

See [`docs/01_data_source.md`](docs/01_data_source.md) for source evidence, observed claims, license notes, references, and the precise provenance gaps.

### Essential interpretation rules

- A source row is a **product record**, not necessarily a unique real-world product.
- `code` is not a validated unique key. There are **61 duplicate-code groups**, none of which are exact duplicates across all source fields. Keep source rows; do not deduplicate on code or timestamp.
- Report source-row counts as primary. Distinct-code counts are diagnostics only and must never be called “unique products.”
- A record may map to multiple countries, categories, or brands; category/country/group totals may overlap. Do not sum overlapping assignments as a global total.
- Open Food Facts coverage is collaborative and uneven. Missing tags, contributor behavior, category coverage, mapping decisions, and the snapshot’s unknown timing all affect comparability.
- Do not infer missing categories from NOVA, Nutri-Score, ingredients, or `food_groups_tags`; the latter is diagnostic-only.
- Do not claim representativeness, causation, sales share, market share, revenue, consumer demand, or commercial dominance from record counts.

## 4. Stage history and current decisions

### Stage 0 — source and provenance: **accepted for scoped portfolio with explicit limitations**

The local file identity, size, hash, and an immutable content-matching reference are recorded. The historical retrieval event remains unknown and is explicitly accepted as a limitation; license conditions and unresolved metadata are disclosed for the scoped aggregate publication.

### Stage 1 — initial profiling and quality: **complete for bounded profiling**

The profiling includes dataset structure/missingness, source country tags, an ISO-normalized country profile, category/brand tags, taxonomy matching, category reporting-group candidate evidence, manual review queues, duplicate-code investigation, and non-food scope/sensitivity analysis. The country mapping is a reconstructed working baseline with a historical discrepancy documented in the profile; current database country denominators reconcile for the built snapshot.

Important measured data quality:

- 4,828,207 source rows and 111 source fields.
- 61 duplicated non-null `code` groups, 61 rows beyond first occurrences; no pair is an exact duplicate across all source fields. Preserve them.
- 4,769,998 rows have an approved ISO mapping, about 98.7944%; 237 ISO units are represented in the current country profile. The reference table contains 249 ISO units.
- Product categories and brands are incomplete and unevenly mapped. Do not interpret absence of a category or brand as absence from the actual market.
- Non-food scope is handled through a full baseline plus two record-level A/B sensitivity scenarios; Class C remains discovery-only and strong/other food signals are not treated as blanket proof to reclassify Indonesia records.

See [`docs/02_data_profile.md`](docs/02_data_profile.md), [`docs/01_data_source.md`](docs/01_data_source.md), and validation outputs in `outputs/profiling/` and `outputs/quality/`.

### Stage 2 — measurement rules and harmonization: **sufficient to proceed, not complete**

This status is intentional and owner-approved. Do **not** resume a full taxonomy/brand review for completeness alone. Mapping work is deferred; return to one specific unresolved mapping only if a concrete schema or measured result shows it materially affects the approved question.

Current documented state includes:

- The working country mapping is used as the current baseline, with the historical reconstruction caveat disclosed.
- Ten substantive reporting-group labels are maintained in `data/reference/category_reporting_group_framework.csv`; `Other / unclassified` is diagnostic-only.
- Current workflow records 59 approved exact-tag category group decisions. The eight bounded decisions include the initial five and the later assignments `en:chocolate-milks` → `beverages`, `en:coconut-waters` → `beverages`, and `en:yogurt-drinks` → `dairy_eggs`.
- Many category values remain unresolved: the current crosswalk records 838 multi-group tags and 106,211 taxonomy-unmatched tags. Candidate assignment is not the same as approval.
- The reproducible selected-scope impact audit is `scripts/14_stage2_selected_scope_mapping_impact.py`; the default `initial-five` set preserves the original files, and `--decision-set additional-three` writes separate outputs for the later batch. The additional-three outputs are `outputs/profiling/stage2_selected_scope_mapping_tag_impact_additional_three.csv` and `outputs/profiling/stage2_selected_scope_mapping_coverage_delta_additional_three.csv`.
- Exact brand mappings cover 60 source `brands` text values across 13 canonical groups. Four recently reviewed exact values map `Fairprice`/`FairPrice` to `FairPrice` and `Nestle`/`Nestlé` to `Nestlé`; no broader alias or tag-based merge is implied. Do not split multi-brand strings, infer identities beyond reviewed evidence, or treat unmapped values as normalized brands.
- Keep category candidate-derived and approved-only assignment results separately labeled.
- Preserve the full record baseline and both agreed non-food A/B sensitivity cases; never treat Class C as an exclusion. For Indonesia, non-category signals are diagnostic-only.

Stage 2’s practical conclusion is “enough for the bounded analysis, with mapping limitations disclosed,” not “all values harmonized.”

### Stage 3 — relational design: **complete / approved**

The approved physical target is a DuckDB file at `data/processed/global_product_landscape.duckdb`. The logical and physical design:

- Preserves all 111 source columns and each physical Parquet source row.
- Uses the source file hash as snapshot ID and a one-based Parquet row ordinal / `source_record_id` for source-row identity.
- Does not treat `code` as a primary key.
- Represents country/category/brand-tag links through association tables and retains exact raw values and mapping status.
- Stores taxonomy parent relationships separately; preserves unresolved, excluded, candidate, and approved category mapping states separately.
- Preserves raw `brands` text separately from `brands_tags`; the model does not yet create a fully normalized brand entity or split brand text.
- Uses validation queries rather than declared foreign-key constraints for referenced mappings.

See [`docs/04_relational_schema_design.md`](docs/04_relational_schema_design.md) and `sql/01_build_relational_database.sql`.

### Stage 4 — reproducible database build: **complete for the pinned snapshot**

The guarded builder is `scripts/11_build_relational_database.py`; SQL is `sql/01_build_relational_database.sql` plus `sql/02_validate_relational_database.sql`. It validates source/taxonomy hashes and refuses to overwrite an existing database. Existing build passed all **15** documented checks, including:

- 4,828,207 records and all 111 source columns.
- All 61 duplicate-code groups retained.
- 10,480,049 category-tag assignments, 5,079,894 exact source-country-tag assignments (`record_country_source_tag`), and 3,313,249 brand-tag assignments reconciled. The deduplicated record-to-ISO bridge (`record_country`) contains 5,004,567 rows.
- Exact reconciliation across 237 normalized country units; 249 ISO reference entries.

The build validation report is `outputs/quality/database_build_validation.csv`. The database is a reproducible derivative, not the source of truth. Rebuild only when appropriate and preserve the current database unless the owner explicitly directs replacement.

#### Verified storage footprint and efficiency trade-off

A read-only DuckDB audit on 2026-10-29 reported:

- Parquet source: `7,975,461,945` bytes (~7.98 GB decimal / 7.43 GiB).
- DuckDB file: `15,109,992,448` bytes (~15.11 GB decimal / 14.07 GiB).
- DuckDB `PRAGMA database_size`: 14.0 GiB displayed; 57,588 used 256-KiB blocks, 52 free blocks, WAL 0 bytes.
- The database has 16 tables and 15 unique indexes.
- Important large relation row counts: source records 4,828,207; category-tag bridge 10,480,049; exact country-tag bridge 5,079,894; deduplicated record-to-ISO bridge 5,004,567; brand-tag bridge 3,313,249.

This is not a Parquet file copied into an uncompressed container. The DuckDB source table retains all 111 source columns and raw array values; relational bridge tables separately materialize many of those same category/country/brand relationships, and unique indexes support key guarantees. That overlap is intentional for the approved raw-preservation and queryable relational design, but it does increase storage. DuckDB also stores its own compressed column segments; no per-table byte-accurate allocation breakdown has been established here, so do not claim a precise percentage of file size attributable to any one table or index.

Current source plus database occupy about 23.09 GB decimal (~21.5 GiB), before outputs, reference files, or backups. This footprint is an explicit reproducibility/performance-versus-storage trade-off to revisit if the owner prioritizes reducing disk use. Safe options to evaluate (not yet implemented) include avoiding persistence of the full raw landing table by querying the pinned Parquet as the canonical source, storing only fields required by analytical queries, and testing whether every unique index is required by validation or workload. Any redesign must preserve the immutable source, analytical lineage, all agreed checks, and recovery capability. Do not remove the existing database or indexes based only on size; rebuild a separate candidate and benchmark/reconcile it before replacement.

### Stage 5 — analysis specification and scope: **complete / approved**

The owner-approved analytical country roles are:

- **ID / Indonesia:** focal unit.
- **MY / Malaysia, PH / Philippines, SG / Singapore:** contextual peers.
- **TH / Thailand:** separate category-coverage contrast, not an equivalent peer.
- **VN / Vietnam and KH / Cambodia:** not in the Stage 6 scope.

The 107 ISO units meeting the existing 1,000-row screening floor are evidence/candidate context only, not automatically selected peers. The floor is exploratory and is not a representativeness guarantee.

Selected country evidence:

| ISO | Role | Source rows | Distinct codes (diagnostic) | Rows with category tags | Category-tag coverage |
|---|---|---:|---:|---:|---:|
| ID | Focal | 9,118 | 9,118 | 1,111 | 12.1847% |
| MY | Contextual peer | 7,426 | 7,426 | 840 | 11.3116% |
| PH | Contextual peer | 9,176 | 9,176 | 1,535 | 16.7284% |
| SG | Contextual peer | 11,986 | 11,986 | 2,074 | 17.3035% |
| TH | Coverage contrast | 11,343 | 11,343 | 7,104 | 62.6289% |

These are source-record counts from the pinned snapshot. Category-tag coverage is the share of country-assigned rows with non-empty `categories_tags`; coverage differences limit category comparisons.

Approved analysis decisions:

- Source rows are primary; distinct-code counts are separate diagnostics.
- Main category view combines single-group taxonomy candidates and owner-approved decisions but must be labeled **candidate-derived**; show the narrower **approved-only** view as a sensitivity.
- Use the ten substantive reporting groups only. Omit diagnostic `other_unclassified` from primary group results.
- Allow category overlap; report rows assigned to multiple substantive groups.
- Report category-tagged rows without a substantive group assignment as a coverage gap, not as a detailed diagnosis of why they are unassigned.
- Use only exact approved mappings for the complete `brands` source text. Preserve the sparse mapped-only denominator.
- Do not calculate HHI or broad brand-concentration metrics. Do not make market-share or sales-based claims.
- Keep `baseline`, `exclude_A_B_except_strong_food_signals`, and `exclude_all_A_B` side by side; baseline is never removed.

The 107-unit evidence file is `outputs/profiling/stage5_country_peer_evidence.csv`; it is generated by `scripts/12_stage5_country_peer_evidence.py`.

### Stage 6 — SQL analysis and validation: **complete for the approved bounded scope**

The runner is `scripts/13_run_stage6_analysis.py`; SQL is `sql/03_stage6_analysis.sql` and `sql/04_stage6_validation.sql`. It reads the database in read-only mode, checks the build report and expected snapshot hash, stages CSVs in a temporary directory, validates, then publishes outputs only if checks pass.

The latest Stage 5/6 outputs were generated from a temporary compact candidate built from current category and brand mappings. Its retained validation report contains 15 passing checks, including exact comparison of the required source projection and country/category/brand bridges against the original full database; the candidate was removed after the run. It is not a full database replacement. An older persistent `data/processed/global_product_landscape_stage6_candidate.duckdb` may contain an earlier mapping and is not the source of the latest outputs. The original Stage 4 database was not overwritten.

Published outputs under `outputs/analysis/`:

1. `stage6_country_scope.csv` — 15 rows (five countries × three scenarios); country source rows, diagnostic distinct codes, category-tag coverage and A/B sensitivity.
2. `stage6_country_category.csv` — 300 rows; per-country, scenario, assignment basis and reporting-group measures, overlap, category assignment coverage gaps, and exact-approved brand mapping coverage.
3. `stage6_country_brand.csv` — 159 exact-approved canonical-brand assignment rows with mapped-only denominators. This is a sparse selected subset, not a complete brand landscape.
4. `stage6_validation.csv` — 11 checks, all passing.

The outputs are pinned to snapshot SHA-256 `DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A`. All 11 checks passed, and the four published CSVs are byte-identical to the validated candidate-run files:

- Country scope: `5c0908af73cef4b2eb25912319c958a1c2003a80615f3a40b463a4dc3f542933`
- Country category: `e790a662dec98ceaa90ee45983cfa9086b7d2349e82dc45e6e582dcf0d4bc163`
- Country brand: `98678b3faf82f2edd5f9b00af82b38ca2e966c9cd8132cb2c50214952a647a87`
- Validation: `5cfe6eaf9e1869743a997d20fc55ebff94948240548c16511895bd0786f1dff1`

All 11 report rows have `status=passed`, with actual equal to expected:

`selected_country_units`; `sensitivity_scenarios`; `substantive_reporting_groups`; `country_baseline_row_reconciliation_mismatches`; `country_sensitivity_row_or_code_mismatches`; `missing_code_rows_in_selected_scope`; `diagnostic_other_rows_in_primary_category_assignment`; `approved_only_assignment_without_decision`; `brand_assignments_without_approved_mapping`; `brand_assignment_denominator_mismatches`; `category_assignment_coverage_errors`.

Category baseline coverage snapshot:

| Country | Basis | Category-tagged rows | Assigned to >=1 substantive group | Tagged rows without a substantive assignment | Rows assigned to multiple groups |
|---|---|---:|---:|---:|---:|
| ID | Candidate-derived | 1,111 | 788 | 323 | 134 |
| ID | Approved-only | 1,111 | 109 | 1,002 | 5 |
| MY | Candidate-derived | 840 | 620 | 220 | 99 |
| MY | Approved-only | 840 | 84 | 756 | 3 |
| PH | Candidate-derived | 1,535 | 1,273 | 262 | 177 |
| PH | Approved-only | 1,535 | 157 | 1,378 | 10 |
| SG | Candidate-derived | 2,074 | 1,806 | 268 | 266 |
| SG | Approved-only | 2,074 | 251 | 1,823 | 8 |
| TH | Candidate-derived | 7,104 | 4,516 | 2,588 | 1,020 |
| TH | Approved-only | 7,104 | 653 | 6,451 | 77 |

Important detail: group assignments can overlap. “Assigned to at least one group” is a distinct source-row count, while multi-group counts are diagnostic; these should not be summed to imply a partition. The unassigned count is calculated as category-tagged rows minus rows assigned at least one substantive group; it is not a disposition-level explanation.

Rerun the current Stage 5/6 workflow from the project root with:

```powershell
.\.venv\Scripts\python.exe .\scripts\12_stage5_country_peer_evidence.py --database data\processed\global_product_landscape_stage6_candidate.duckdb --build-validation outputs\quality\stage6_candidate_build_validation.csv
.\.venv\Scripts\python.exe .\scripts\13_run_stage6_analysis.py --database data\processed\global_product_landscape_stage6_candidate.duckdb --build-validation outputs\quality\stage6_candidate_build_validation.csv
```

Expected behavior: fail explicitly if required inputs, snapshot, or checks are wrong; it should not publish staged outputs on validation failure.

## 5. Current stage/status table

| Stage | Status | Notes |
|---|---|---|
| 0 — Source/provenance | Accepted for scoped portfolio with explicit limitations | Local hash and immutable content-matching reference documented; historical retrieval commit/date/method unknown by owner acceptance. Current upstream `main` differs. Attribution and applicable terms are disclosed; no data-derived output is claimed under MIT. |
| 1 — Initial profiling/quality | Complete to bounded scope | Evidence and limitations documented; no destructive deduplication. |
| 2 — Measurement/harmonization | Bounded reopening complete; broader work remains parked | Five exact category decisions approved and impact-audited; full harmonization is not claimed. |
| 3 — Relational design | Complete | DuckDB, row ordinal identity, raw value preservation, mapping status separation. |
| 4 — Database build | Full database preserved; Stage 6 candidate validated | Compact candidate has 13 passed checks; it is not a full database replacement. |
| 5 — Analysis specification/scope | Complete | Country roles and denominators approved. |
| 6 — SQL analysis/validation | Complete for the approved bounded scope | Candidate-backed Stage 5 evidence is current; canonical Stage 6 outputs passed all 11 checks. |
| 7 — Findings/recommendations | Refreshed | Findings reflect current candidate-backed outputs and continue to disclose analytical limitations. |
| 8 — Release/recovery acceptance | Preflight started; release/recovery documentation and publication checks pending | The owner revised the Definition of Done: backup creation and restore testing are not required due to storage constraints. No backup has been created; do not create one. Complete the other repository, reproducibility, and integrity checks. |

The workflow and quality gates are in [`docs/03_analysis_workflow.md`](docs/03_analysis_workflow.md). The business brief's Definition of Done remains the final completion standard; Stage 6 completion does not mean the whole project is done.

## 6. Important project evolution / decision trail

This is a concise reconstruction of the significant decisions; the complete chronological log remains `docs/99_project_log.md`.

1. **Information architecture and traceability:** repository was organized around source data, mappings, reference data, documentation, scripts, SQL, and generated outputs. Documentation and logs were made the persistent source of project decisions rather than relying on chat history.
2. **Profiling before analysis:** profiling/quality scripts and CSV evidence established source size, field structure, identifiers, country coverage, categories, brands, taxonomy match, and non-food signals.
3. **Identifier rule:** duplicate `code` values were investigated; because the repeated rows conflict, all source rows are retained and `code` is not the raw-table primary key.
4. **Country mapping:** an explicit approved ISO mapping is used. A historical reconstructed-mapping discrepancy remains documented; current build denominators reconcile, so no wholesale country-map redo was authorized.
5. **Category taxonomy approach:** taxonomy ancestry and explicit candidate anchors are used to produce candidate mapping evidence, not automatic approvals. Multi-group, unmatched, residual, and excluded tags remain distinct; `Other / unclassified` stays diagnostic-only.
6. **Exact category exclusions:** reviewed placeholder/non-food category tags are excluded from substantive group assignments by exact disposition while original source tags remain preserved.
7. **Non-food record scope:** full baseline remains primary; two A/B record-level sensitivities are carried alongside it. Class C is discovery-only; selected non-category Indonesia signals are diagnostics, not category inference.
8. **Stage 2 boundary and bounded reopening:** broad long-tail review remains parked. The initial five exact category decisions were impact-audited, then three taxonomy-matched category decisions and two exact brand spelling pairs were approved on 2026-11-04. The additional three category tags leave candidate-derived assigned-row coverage unchanged and increase approved-only coverage by ID +4, MY +0, PH +1, SG +12, and TH +20; SG approved-only overlap rises by two. Brand mapping coverage increases by ID +30, MY +59, PH +88, SG +323, and TH +35 rows. The current temporary candidate passed 15 checks; Stage 5/6 outputs and Stage 7 findings reflect all current decisions.
9. **Schema/build:** owner approved the DuckDB relational model and guarded reproducible build; Stage 4 built and validated against the pinned inputs.
10. **Readiness before Stage 6:** a bounded evidence-first Stage 5 check was run to address “garbage in, garbage out,” rather than redoing all of Stage 2. Evidence showed limited category and very sparse brand coverage, setting limits on claims.
11. **Peer scope:** after owner approval, ID is focal, MY/PH/SG are contextual peers, and TH is a separate coverage contrast. VN/KH are excluded from the chosen analysis.
12. **Stage 6 execution:** approved SQL and Python runner generated the result tables. A brand assignment denominator reconciliation and category assignment coverage diagnostic were added; final result has 11 passed checks and a deterministic rerun.

The log's older items can describe recommendations/pending decisions that were later resolved. Use the later approval/completion entries and current workflow/specification for current status; do not rewrite history to make past notes appear contemporaneous.

## 7. Core files and evidence map

### Read-first documentation

- [`README.md`](README.md) — repository entry point, execution instructions, current headline status.
- [`docs/00_business_brief.md`](docs/00_business_brief.md) — business objective, units, interpretation rules, deliverables, Definition of Done.
- [`docs/01_data_source.md`](docs/01_data_source.md) — source evidence, provenance, licensing/attribution, open Stage 0 items.
- [`docs/02_data_profile.md`](docs/02_data_profile.md) — profile findings and generated-output inventory.
- [`docs/03_analysis_workflow.md`](docs/03_analysis_workflow.md) — stage statuses, quality gates, and next workflow stages.
- [`docs/04_relational_schema_design.md`](docs/04_relational_schema_design.md) — schema rationale, grain, relationships, and build status.
- [`docs/05_analysis_specification.md`](docs/05_analysis_specification.md) — owner-approved Stage 5/6 scope, definitions, outputs, and limitations.
- [`docs/06_stage7_findings_and_recommendations.md`](docs/06_stage7_findings_and_recommendations.md) — bounded Stage 7 interpretation of the validated results.
- [`docs/99_project_log.md`](docs/99_project_log.md) — chronological material decisions and work history.

### Main code and mapping inputs

- `scripts/01_dataset_profile.py` through `scripts/10_*.py` — profiling, quality, taxonomy/candidate, and non-food workflows; see README and data profile for exact execution order.
- `scripts/11_build_relational_database.py` — guarded Stage 4 builder.
- `scripts/12_stage5_country_peer_evidence.py` — offline Stage 5 country evidence builder.
- `scripts/13_run_stage6_analysis.py` — Stage 6 runner; validates staged outputs before publishing them.
- `scripts/14_stage2_selected_scope_mapping_impact.py` — reproducible before/after impact audit for the initial five or additional three approved category decisions in ID/MY/PH/SG/TH.
- `scripts/15_build_stage6_candidate_database.py` — builds and validates the compact, Stage 6-only candidate without modifying the full database.
- `scripts/16_refresh_harmonized_analysis.py` — automates deterministic category-candidate regeneration, validation, Stage 5/6 refresh, and Stage 7 data-table refresh; ambiguous cases remain unresolved.
- `sql/01_build_relational_database.sql`, `sql/02_validate_relational_database.sql` — Stage 4 build and checks.
- `sql/03_stage6_analysis.sql`, `sql/04_stage6_validation.sql` — Stage 6 output logic and checks.
- `data/mappings/` — reviewed country, category, and brand inputs. Inspect current files rather than assuming old review-queue values remain current.
- `data/reference/category_reporting_group_framework.csv`, `data/reference/iso_3166_alpha2.csv`, and pinned taxonomy JSON — reference inputs.
- `requirements.txt` — Python dependencies.

### Main generated evidence

- `outputs/quality/database_build_validation.csv` — Stage 4 build checks.
- `outputs/quality/stage6_candidate_build_validation.csv` — 15 candidate validation checks for the latest temporary candidate.
- `outputs/quality/harmonization_refresh_summary.csv` — persistent summary of the last automated harmonization refresh.
- `data/processed/global_product_landscape_stage6_candidate.duckdb` — older persistent compact candidate; not the source of the latest Stage 5/6 outputs and may predate current brand mappings.
- `outputs/profiling/stage5_country_peer_evidence.csv` — country evidence across all 107 screened ISO units.
- `outputs/profiling/brand_name_manual_mapping_validation.csv` — exact-value validation for the current 60 approved brand source values.
- `outputs/profiling/stage2_selected_scope_mapping_tag_impact.csv` — per-tag source-row counts by selected country.
- `outputs/profiling/stage2_selected_scope_mapping_coverage_delta.csv` — candidate-derived and approved-only before/after coverage metrics.
- `outputs/profiling/stage2_selected_scope_mapping_tag_impact_additional_three.csv` and `outputs/profiling/stage2_selected_scope_mapping_coverage_delta_additional_three.csv` — impact evidence for the three later category decisions.
- `outputs/analysis/stage6_country_scope.csv`
- `outputs/analysis/stage6_country_category.csv`
- `outputs/analysis/stage6_country_brand.csv`
- `outputs/analysis/stage6_validation.csv`

Generated outputs may be ignored/untracked depending on local repository configuration; their local presence was verified for this handoff. Do not assume they are already attached to a ChatGPT Project or available remotely.

## 8. Suggested continuation plan

### Next: prepare final sanitized branch and request push approval

The eight-tag category impact reviews, four exact brand spelling decisions, and automated candidate-backed Stage 5/6/7 refresh are complete. After any future maintained-mapping change, run `.\.venv\Scripts\python.exe .\scripts\16_refresh_harmonized_analysis.py`; it propagates deterministic candidates and updates validated analytical outputs without auto-approving manual mappings. Stage 0's scoped publication policy and residual provenance/license limitations are documented. Local Stage 8 preflight is complete, and the additional-three aggregate audit files are allowlisted. A separate `sanitized-main` branch rewrites the 36-commit history; verification found none of the four legacy sample paths in any reachable commit tree. The reviewed worktree changes are now committed on the candidate branch. Ask for explicit force-push approval before publication. Do not push without it. Broader Stage 2 harmonization remains intentionally open.

### Before release: remaining Stage 8 checks

- The local source hash is verified; the selected immutable content reference retrieves matching bytes. The exact historical commit, local retrieval date, and method remain unknown and are accepted/documented. Do not infer them from the filesystem timestamp. No user-level browser/download history has been inspected.
- The upstream `main` Parquet observed on 2026-11-04 differs in size and SHA-256 from the pinned local Parquet. Keep the local file pinned; never silently refresh it.
- Open Food Facts attribution and links to applicable terms are documented for the reviewed aggregate outputs. The Hugging Face `AGPL-3.0` scope and legal classification of aggregates remain unresolved; do not redistribute the source Parquet, database, record-level extracts, or taxonomy.
- The project-authored code uses MIT; that license does not apply to source data or data-derived results.
- The README documents the clean rebuild prerequisites and commands. Python 3.13.0, DuckDB 2.0.0, and pandas 3.1.0 were used for the last local validation.
- The owner explicitly instructed not to create a backup and revised the Definition of Done so backup creation/restore testing are not required. Do not create a backup or restore copy. Preserve the existing database and use the separately built candidate approach already approved for storage testing.
- The source and taxonomy checksums match their pins; retained build/candidate/analysis reports pass (15/15, 15/15, and 11/11), and Stage 5 has 107 snapshot-pinned units. The source, taxonomy, and database are ignored by Git.
- A clean-room full rebuild was not repeated because the existing 15.1-GB database must be preserved; no duplicate or backup was created.
- The live GitHub `main` matches the local tracking base. The sanitized-history candidate includes the reviewed changes; the original local `main` and GitHub still retain the original history. Get explicit owner approval before force-pushing. A force-push cannot remove copies already cloned or guarantee all cached objects are purged.

### Further Stage 2 review only if new evidence warrants

The eight approved exact-tag decisions and four exact brand-spelling decisions are complete for the current bounded audits. If a later result depends materially on another unresolved category/brand/country mapping, identify the exact value and affected denominator/result, confirm any substantive decision with the owner, then make the smallest review needed and regenerate dependent evidence. Do not resume a broad unbounded review.

## 9. Environment and handoff to ChatGPT

- Project root in the present VS Code environment: `D:\Projects\indonesia-food-product-landscape`.
- Local database: `data/processed/global_product_landscape.duckdb`; source Parquet: `data/raw/food.parquet`. These are large and should not be uploaded merely for conversational context.
- Python environment used for recent Stage 6 runs: `.venv\Scripts\python.exe`.
- Current harmonization refresh command:

  ```powershell
  .\.venv\Scripts\python.exe .\scripts\16_refresh_harmonized_analysis.py
  ```

  This builds and removes a temporary candidate from current mappings. Do not rerun Stage 5/6 against the older persistent candidate file for current outputs.

- The project is a Git repository whose local `origin` points to `https://github.com/MaulanaKindi/indonesia-food-product-landscape.git`; GitHub has renamed the public repository while preserving its history. Local commits remain unpublished. Authenticate through Git Credential Manager's browser sign-in, then push `main` without force. The old repository history remains intact; the new commit deletes the old sample-record CSVs from the current branch, but historical commits may still contain them.
- Workspace edits are written directly and verified. Git was not previously initialized here, which explains why VS Code/GitHub could not save commits or synchronize; that is separate from the Copilot “Keep changes” UI. If the UI still shows that error, capture its exact text or a screenshot because the earlier message was unavailable.
- ChatGPT cannot automatically see this folder or the Copilot conversation unless the user uploads the files or connects a supported workspace/repository. For a useful handoff, create a ChatGPT Project and upload the following files from the project root.

### Upload checklist

#### Recommended context package

Upload these documentation files so ChatGPT can understand the project goal, prior decisions, source limits, workflow, schema, current analysis, and history:

- `README.md`
- `docs/00_business_brief.md`
- `docs/01_data_source.md`
- `docs/02_data_profile.md`
- `docs/03_analysis_workflow.md`
- `docs/04_relational_schema_design.md`
- `docs/05_analysis_specification.md`
- `docs/06_stage7_findings_and_recommendations.md`
- `docs/99_project_log.md`

Upload the current evidence outputs as well, especially if asking ChatGPT to interpret or write Stage 7 findings:

- `outputs/profiling/stage5_country_peer_evidence.csv`
- `outputs/quality/database_build_validation.csv`
- `outputs/analysis/stage6_country_scope.csv`
- `outputs/analysis/stage6_country_category.csv`
- `outputs/analysis/stage6_country_brand.csv`
- `outputs/analysis/stage6_validation.csv`

This package, together with `HANDOFF_FOR_CHATGPT.md`, is the recommended starting set. The CSVs provide the data evidence; documentation alone is not enough to independently interpret the current Stage 6 result tables.

#### Add these for code review or implementation work

If the next task asks ChatGPT to inspect, debug, or change the Stage 6 implementation, also upload:

- `scripts/13_run_stage6_analysis.py`
- `sql/03_stage6_analysis.sql`
- `sql/04_stage6_validation.sql`
- `data/reference/category_reporting_group_framework.csv`
- `data/mappings/category_tag_reporting_group_manual_decisions.csv`
- `data/mappings/category_tag_manual_dispositions.csv`
- `data/mappings/category_reporting_group_anchor_candidates.csv`
- `data/mappings/brand_name_manual_decisions.csv`
- `requirements.txt` if environment or dependency behavior is in scope.

For a task that specifically concerns country mapping, also upload `data/mappings/country_tag_mapping.csv` and `data/reference/iso_3166_alpha2.csv`. For a task about Stage 5 evidence generation, add `scripts/12_stage5_country_peer_evidence.py`.

#### Only for a Stage 4 schema/build task

If the next task actually involves changing or validating the relational build, additionally upload `scripts/11_build_relational_database.py`, `sql/01_build_relational_database.sql`, `sql/02_validate_relational_database.sql`, and any specific mapping/reference inputs the task touches. Do not upload every large source artifact by default.

#### Do not upload by default

- `data/raw/food.parquet` (about 7.98 GB).
- `data/processed/global_product_landscape.duckdb` (approximately 14 GB).
- `.venv/`, caches, temporary files, or credentials/secrets.

These are not needed to transfer project understanding and may exceed upload limits. Uploading the CSV evidence and relevant code is generally enough for Stage 7 synthesis or code-level discussion. If a future task truly requires executing queries over the full database, ChatGPT will need access to the data through an appropriate connected environment; the handoff documents cannot substitute for that access.

- Avoid uploading secrets or personally sensitive files. No credentials are needed to understand or continue this analytical work.
