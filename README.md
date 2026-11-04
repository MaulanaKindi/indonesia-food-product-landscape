# Indonesia Food Product Landscape

Exploratory market-intelligence project using Open Food Facts product records to compare category-tag coverage and harmonized group assignments across selected countries, with exact-approved brand mapping coverage as a limitation diagnostic. The data is not a census of products sold and does not provide sales-based market shares.

The focal unit is Indonesia; Malaysia, the Philippines, and Singapore are contextual peers, while Thailand is a category-coverage contrast. Findings describe database records and mapping coverage, not products sold, demand, or commercial market shares.

## Data, Attribution, and License

The Open Food Facts source snapshot, database files, and record-level extracts are not included. The pinned source artifact is identified in [the source and provenance note](docs/01_data_source.md); its local retrieval date/method and some upstream license metadata remain unresolved. Attribute Open Food Facts as the source of the analyzed database and consult its [terms of reuse](https://world.openfoodfacts.org/terms-of-use) for applicable database/content terms.

The [MIT License](LICENSE) applies only to original project code and documentation authored for this repository. It does not relicense Open Food Facts data, third-party reference files, or data-derived outputs. Included aggregate results are snapshot-specific and are accompanied by source attribution and limitations. No raw Parquet, DuckDB database, or product-record sample should be committed.

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

The current Stage 5/6 results use the separately validated compact candidate, not the original full Stage 4 database. To rerun Stage 5/6 against the existing candidate and publish to the canonical evidence/output paths:

```powershell
.\.venv\Scripts\python.exe .\scripts\12_stage5_country_peer_evidence.py --database data\processed\global_product_landscape_stage6_candidate.duckdb --build-validation outputs\quality\stage6_candidate_build_validation.csv
.\.venv\Scripts\python.exe .\scripts\13_run_stage6_analysis.py --database data\processed\global_product_landscape_stage6_candidate.duckdb --build-validation outputs\quality\stage6_candidate_build_validation.csv
```

The Stage 6 candidate contains only the schema required for this bounded analysis; it is not a replacement or recovery copy of the full database. To create another candidate, use `scripts\15_build_stage6_candidate_database.py`; it refuses to overwrite an existing candidate or validation report, so provide unused output paths when rebuilding. The no-argument Stage 5/6 commands above the candidate workflow still target the original database.

Scripts resolve project paths relative to their own location. The normalized country profile uses the maintained mapping in `data/mappings/` and validates approved codes against `data/reference/iso_3166_alpha2.csv`. The category taxonomy audit uses the pinned Open Food Facts taxonomy snapshot in `data/reference/`; it requires the category profile generated by script 05. Script 07 drafts category reporting-group candidates from exact taxonomy ancestry, candidate anchors, and explicitly reviewed exclusions in `data/mappings/category_tag_manual_dispositions.csv`; candidate assignments remain unapproved.

Script 08 generates prioritized manual-review queues for candidate anchors, multi-group tags, diagnostic residuals, and the 1,000 highest-frequency unmatched tags. These queues do not approve mappings or automatically merge aliases.

For an automated refresh after maintained mapping inputs change, run:

```powershell
.\.venv\Scripts\python.exe .\scripts\16_refresh_harmonized_analysis.py
```

This regenerates the taxonomy-based candidate crosswalk and review queues, builds a temporary validated candidate database, regenerates Stage 5 and Stage 6 evidence, and refreshes the data-driven tables in the Stage 7 findings. It publishes the Stage 5/6 outputs and Stage 7 tables only after the candidate (13 checks) and analysis (11 checks) pass; validation reports and a refresh summary are retained under `outputs/quality/`. The temporary database is removed at the end. Exact owner-approved mapping inputs are never silently edited: only the existing deterministic single-group candidate rules are applied automatically; multi-group, unmatched, residual, and other ambiguous tags remain unresolved and visible. Review and update exact manual decisions only with evidence and explicit approval.

For the five owner-approved category decisions and their impact on ID, MY, PH, SG, and TH, the reviewed mapping, crosswalk, and queues have already been regenerated. The impact audit can be reproduced with:

```powershell
.\.venv\Scripts\python.exe .\scripts\14_stage2_selected_scope_mapping_impact.py
```

This writes tag-level counts and before/after candidate-derived and approved-only coverage to `outputs/profiling/`. The current Stage 5 evidence and Stage 6 outputs include these decisions; see [Stage 7 findings](docs/06_stage7_findings_and_recommendations.md) for updated interpretations.

Generated CSVs are written under `outputs/profiling/` and `outputs/quality/`. See [02_data_profile.md](docs/02_data_profile.md) for definitions, results, and limitations.

## Relational Database Build

The Stage 4 build requires the project virtual environment and the existing local Parquet, taxonomy, mapping, crosswalk, and country-profile inputs. No package installation is needed beyond `requirements.txt`. From the repository root, run:

```powershell
.\.venv\Scripts\python.exe .\scripts\11_build_relational_database.py
```

The builder verifies the expected source file size and SHA-256 and the pinned taxonomy SHA-256, then runs `sql/01_build_relational_database.sql` and `sql/02_validate_relational_database.sql`. It refuses to overwrite an existing database. A successful build creates `data/processed/global_product_landscape.duckdb` and `outputs/quality/database_build_validation.csv`. Review the report before using the database; a successful process exit is required for all checks to pass.

## Project Status

Initial profiling and an exploratory normalized country shortlist are available. The bounded five-tag category review, impact audit, candidate build, Stage 5 refresh, Stage 6 validation, and Stage 7 refresh are complete; broader category and brand harmonization remains intentionally incomplete. Use `scripts\16_refresh_harmonized_analysis.py` to automatically regenerate deterministic single-group candidates and all dependent analytical outputs after maintained mapping inputs change. Ambiguous values remain unresolved; the script does not add owner approvals. Stage 0 was rechecked: the local Parquet hash is verified and matches three historical Hugging Face commits, but the currently listed upstream Parquet is a different file and the actual local retrieval commit/date/method remain unknown. Source-data attribution and derivative-license review remain open; MIT applies only to original project code and documentation. Stage 8 release/recovery acceptance remains open. No backup has been created; do not create one without renewed owner approval. See the [relational schema design](docs/04_relational_schema_design.md), [analysis specification](docs/05_analysis_specification.md), [Stage 7 findings](docs/06_stage7_findings_and_recommendations.md), and [analysis workflow](docs/03_analysis_workflow.md) for assumptions and gate status; see the [business brief](docs/00_business_brief.md) for the full Definition of Done.
