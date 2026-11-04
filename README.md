# Indonesia Food Product Landscape

Exploratory market-intelligence project using Open Food Facts product records to compare category-tag coverage and harmonized group assignments across selected countries, with exact-approved brand mapping coverage as a limitation diagnostic. The data is not a census of products sold and does not provide sales-based market shares.

The focal unit is Indonesia; Malaysia, the Philippines, and Singapore are contextual peers, while Thailand is a category-coverage contrast. Findings describe database records and mapping coverage, not products sold, demand, or commercial market shares.

## Data, Attribution, and License

The Open Food Facts source snapshot, database files, record-level extracts, and pinned taxonomy are not included. The local Parquet is identified by its SHA-256 and a [content-matching immutable Hugging Face commit](https://huggingface.co/datasets/openfoodfacts/product-database/tree/31f31c441274c095718cc88ae582030a5a615415); this is a reproducibility reference, not evidence that the local file was historically downloaded from that commit. Its actual retrieval date/method remain unknown and are disclosed in [the source and provenance note](docs/01_data_source.md).

The [Open Food Facts terms of reuse](https://world.openfoodfacts.org/terms-of-use) describe ODbL/DbCL terms for the database and individual contents, including attribution and applicable derivative-work conditions. The Hugging Face card also lists AGPL-3.0 but does not clarify its scope. This portfolio publishes only reviewed aggregate results with attribution and source/license links; it does not independently classify those outputs under a particular data license. The MIT License applies only to original project code and documentation—not Open Food Facts data, third-party reference files, or data-derived outputs. This disclosure is not legal advice; see the source note for the accepted limitations.

## Project Documents

- [Business brief](docs/00_business_brief.md): questions, measurement rules, scope, and completion criteria.
- [Data source and provenance](docs/01_data_source.md): source information and provenance items still to complete.
- [Data profile](docs/02_data_profile.md): profiling evidence, quality findings, country mapping, and current scope.
- [Analysis workflow](docs/03_analysis_workflow.md): ordered stages, quality gates, current status, and Definition of Done traceability.
- [Relational schema design](docs/04_relational_schema_design.md): approved logical schema, physical table inventory, and Stage 4 build status.
- [Analysis specification](docs/05_analysis_specification.md): owner-approved Stage 5 scope, denominator decisions, and Stage 6 output limits.
- [Stage 7 findings and recommendations](docs/06_stage7_findings_and_recommendations.md): bounded interpretation of the validated Stage 6 outputs and their limitations.
- [Project log](docs/99_project_log.md): material project decisions and status.
- [Category reporting-group framework](data/reference/category_reporting_group_framework.csv): approved group labels; taxonomy-tag assignments remain under review.

## Repository Structure

| Path | Purpose |
|----------|----------|
| `data/raw/` | Locally supplied source snapshot; excluded from Git |
| `data/processed/` | Generated DuckDB relational database; rebuildable and not a source of truth |
| `data/mappings/` | Maintained, reviewed source-tag mappings |
| `data/reference/` | Versioned reference data used for validation |
| `docs/` | Brief, source documentation, profiles, and project decisions |
| `outputs/` | Generated profiling and quality evidence |
| `scripts/` | Reproducible profiling and validation scripts |
| `sql/` | Ordered SQL for relational database construction and validation |

Only a reviewed allowlist of country/category aggregate and validation CSVs is tracked. Generated profiling inventories, record-level evidence, source data, the pinned taxonomy file, virtual environments, caches, and DuckDB files are excluded from Git.

## Current Profiling Workflow

Prerequisites: create `data/raw/` and place the documented Open Food Facts Parquet snapshot at `data/raw/food.parquet`. The dataset is intentionally excluded from Git due to its size. Use Python and install dependencies from `requirements.txt`.

From the repository root, create the environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The workflow was last verified with Python 3.13.0, DuckDB 2.0.0, and pandas 3.1.0; Python dependencies are pinned in `requirements.txt`.

Then run the current profiling workflow:

```powershell
.\.venv\Scripts\python.exe .\scripts\01_dataset_profile.py
.\.venv\Scripts\python.exe .\scripts\02_quality_checks.py
.\.venv\Scripts\python.exe .\scripts\03_country_profile.py
.\.venv\Scripts\python.exe .\scripts\04_normalized_country_profile.py
.\.venv\Scripts\python.exe .\scripts\05_category_brand_profile.py
.\.venv\Scripts\python.exe .\scripts\06_category_taxonomy_audit.py
.\.venv\Scripts\python.exe .\scripts\07_category_reporting_group_draft.py
.\.venv\Scripts\python.exe .\scripts\08_category_reporting_group_review_queues.py
```

After the relational database is built, generate the Stage 5 country-peer evidence table with:

```powershell
.\.venv\Scripts\python.exe .\scripts\12_stage5_country_peer_evidence.py
```

This offline profiling step reads the validated DuckDB and existing country/category/non-food outputs. It writes the snapshot-pinned 107-unit evidence table to `outputs/profiling/stage5_country_peer_evidence.csv`; it does not select peers or create Stage 6 analysis results.

Run the owner-approved Stage 6 descriptive analysis with:

```powershell
.\.venv\Scripts\python.exe .\scripts\13_run_stage6_analysis.py
```

The runner checks the database build report and pinned snapshot, writes outputs to a temporary directory, validates all 11 country/category/brand reconciliation checks, and publishes results under `outputs/analysis/` only if all checks pass. The scope is ID (focal), MY/PH/SG (contextual peers), and TH (coverage contrast). Category results distinguish candidate-derived from approved-only assignments and quantify category-tagged rows without a substantive group assignment; exact-approved brand mappings are a sparse subset. The analysis does not calculate HHI or claim market share.

The current Stage 5/6 results use a separately validated temporary candidate, not the original full Stage 4 database. Use `scripts\16_refresh_harmonized_analysis.py` to regenerate the category crosswalk and review queues, validate the current category and brand mappings, build the candidate, refresh Stage 5/6, and update Stage 7. The temporary candidate is removed after a successful run. Do not use an older persistent candidate file to reproduce the current mapping outputs; it may contain an earlier brand mapping. The full Stage 4 database is not overwritten.

Scripts resolve project paths relative to their own location. The normalized country profile uses the maintained mapping in `data/mappings/` and validates approved codes against `data/reference/iso_3166_alpha2.csv`. The category taxonomy audit uses the pinned Open Food Facts taxonomy snapshot in `data/reference/`; it requires the category profile generated by script 05. Script 07 drafts category reporting-group candidates from exact taxonomy ancestry, candidate anchors, and explicitly reviewed exclusions in `data/mappings/category_tag_manual_dispositions.csv`; candidate assignments remain unapproved.

Script 08 generates prioritized manual-review queues for candidate anchors, multi-group tags, diagnostic residuals, and the 1,000 highest-frequency unmatched tags. These queues do not approve mappings or automatically merge aliases.

For an automated refresh after maintained mapping inputs change, run:

```powershell
.\.venv\Scripts\python.exe .\scripts\16_refresh_harmonized_analysis.py
```

This refreshes category and brand profiling/validation, regenerates the taxonomy-based candidate crosswalk and review queues, builds a temporary validated candidate database, regenerates Stage 5 and Stage 6 evidence, and refreshes the data-driven tables in the Stage 7 findings. It publishes the Stage 5/6 outputs and Stage 7 tables only after the candidate (15 checks) and analysis (11 checks) pass; validation reports and a refresh summary are retained under `outputs/quality/`. The temporary database is removed at the end. Exact owner-approved mapping inputs are never silently edited: only the existing deterministic single-group candidate rules are applied automatically; multi-group, unmatched, residual, and other ambiguous tags remain unresolved and visible. Review and update exact manual decisions only with evidence and explicit approval.

The initial five owner-approved category decisions and their impact on ID, MY, PH, SG, and TH can be reproduced with the default audit:

```powershell
.\.venv\Scripts\python.exe .\scripts\14_stage2_selected_scope_mapping_impact.py
```

For the three additional category decisions, run:

```powershell
.\.venv\Scripts\python.exe .\scripts\14_stage2_selected_scope_mapping_impact.py --decision-set additional-three
```

This writes separate tag-level counts and before/after candidate-derived and approved-only coverage files under `outputs/profiling/`, preserving the initial five-decision audit outputs. The current Stage 5 evidence and Stage 6 outputs include all eight category decisions and the four approved brand spelling values; see [Stage 5–6 specification](docs/05_analysis_specification.md) and [Stage 7 findings](docs/06_stage7_findings_and_recommendations.md) for measured impacts and interpretation.

Generated CSVs are written under `outputs/profiling/` and `outputs/quality/`. See [02_data_profile.md](docs/02_data_profile.md) for definitions, results, and limitations.

## Relational Database Build

The Stage 4 build requires the project virtual environment and the existing local Parquet, taxonomy, mapping, crosswalk, and country-profile inputs. No package installation is needed beyond `requirements.txt`. From the repository root, run:

```powershell
.\.venv\Scripts\python.exe .\scripts\11_build_relational_database.py
```

The builder verifies the expected source file size and SHA-256 and the pinned taxonomy SHA-256, then runs `sql/01_build_relational_database.sql` and `sql/02_validate_relational_database.sql`. It refuses to overwrite an existing database. A successful build creates `data/processed/global_product_landscape.duckdb` and `outputs/quality/database_build_validation.csv`. Review the report before using the database; a successful process exit is required for all checks to pass.

## Project Status

Initial profiling, relational design/build, and the bounded Stage 5–7 analysis are complete for the documented scope. Broader category and brand harmonization remains intentionally incomplete; unresolved values are not automatically approved. Use `scripts\16_refresh_harmonized_analysis.py` to regenerate deterministic single-group candidates and dependent analytical outputs after maintained mapping inputs change. Stage 0 is accepted for the scoped aggregate portfolio with the historical retrieval event and Hugging Face AGPL metadata scope explicitly unresolved; the source hash and a content-matching immutable reference are documented. Open Food Facts attribution and applicable terms are disclosed; MIT applies only to original project code and documentation, not data-derived outputs. Stage 8 local preflight is complete: pinned source/taxonomy checksums and retained database, candidate, Stage 5, and Stage 6 validation reports passed. The two additional-three impact-audit CSVs are small aggregate evidence and are included in the repository allowlist. The clean-room full rebuild has not been repeated because the existing 15.1-GB database must be preserved and no backup is permitted; the Parquet source and pinned taxonomy must be supplied locally because Git excludes them. On 2026-11-04, the sanitized history was force-pushed to GitHub `main` with an exact lease; the local `main` now tracks the published commit. The four legacy sample-record paths are absent from every commit tree reachable from the published branch. A force-push cannot revoke prior clones or guarantee removal of cached GitHub objects, and local Git may retain unreachable pre-rewrite objects. Stage 8 rebuild/recovery acceptance remains open pending any further approved validation; no data backup has been created. See the [relational schema design](docs/04_relational_schema_design.md), [analysis specification](docs/05_analysis_specification.md), [Stage 7 findings](docs/06_stage7_findings_and_recommendations.md), and [analysis workflow](docs/03_analysis_workflow.md) for assumptions and gate status; see the [business brief](docs/00_business_brief.md) for the full Definition of Done.
