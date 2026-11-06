# Reproduce the Analysis

This guide rebuilds the canonical five-country analysis from the pinned Open Food Facts snapshot. It does not require the optional full-country database.

## Requirements

- Python 3.13
- Disk space for the 7.98 GB source Parquet and temporary build files
- A network connection for the first snapshot download

Create an environment and install the project dependencies:

```text
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe .\scripts\run_all.py
```

macOS or Linux:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/run_all.py
```

The first command in the pipeline downloads Hugging Face commit `31f31c441274c095718cc88ae582030a5a615415` to `data/raw/food.parquet`. It verifies the expected 7,975,461,945-byte size and SHA-256 `DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A`. Existing files are verified and never silently replaced. The source and DuckDB databases are excluded from Git.

## Pipeline

`scripts/run_all.py` runs the reproducible profiling, quality, mapping, scoped database build, and analysis steps in order. The canonical database is `data/processed/global_product_landscape_five_country.duckdb`, covering Indonesia, Malaysia, the Philippines, Singapore, and Thailand. The full database is optional and is not required for this portfolio.

The scoped builder filters source records to those with at least one approved country tag for the five selected countries. It preserves source rows and checks source projection, country links, assignment counts, profile reconciliation, schema shape, mapping references, and the pinned snapshot. A successful build writes a separate validation report to `outputs/quality/database_build_validation_five_country.csv`; the existing full database is not overwritten.

The refresh then builds a compact Stage 6 candidate, validates it and the analysis outputs, and updates the generated README, Stage 7 findings, tables, and charts. It publishes these outputs only after candidate and analysis checks pass. To refresh after changing mapping inputs, rebuild the canonical database first, then rerun the analysis refresh:

```powershell
.\.venv\Scripts\python.exe .\scripts\11_build_relational_database.py --replace-existing
.\.venv\Scripts\python.exe .\scripts\16_refresh_harmonized_analysis.py
```

On macOS or Linux, replace the Windows virtual-environment Python path with `.venv/bin/python`.

To rerun the complete workflow after the canonical database already exists, opt in to an atomic replacement after validation:

```text
python scripts/run_all.py --replace-scoped-database
```

## Measurement definitions

- **Country record count:** records linked to each ISO country by approved source-country tags. A source record can be linked to more than one country; country totals are not necessarily unique-product counts.
- **Category-tagged record:** at least one distinct non-null `categories_tags` value.
- **Candidate-derived assignment:** at least one group produced by the deterministic taxonomy candidate crosswalk. It is not necessarily approved.
- **Approved-only assignment:** at least one explicit, exact category decision with approved review status.
- **Brand text:** non-empty raw `brands` text. **Exact-approved brand mapping** is a separate subset matched to an explicitly approved exact source string.
- **Ingredient text:** at least one non-empty text value in `ingredients_text`.
- **Numeric nutrition:** at least one numeric value in a `nutriments` entry (`value`, `100g`, `serving`, or prepared equivalents).
- **Valid Nutri-Score:** a grade in A–E; blank and `unknown` values are not counted.
- **Packaging and labels:** at least one non-empty field, tag, or structured value in the corresponding source columns.
- **Contributor concentration:** share of country-assigned records attributed to the five most frequent non-empty `creator` values. Contributor names are not published in the aggregate output.
- **Creation year:** derived from `created_t` when it falls in the valid timestamp range used by the script. It is not a product launch year.
- **Source-tag coverage:** record counts and category-tag coverage for the most frequent `data_sources_tags`; one record can carry multiple source tags.
- **Code overlap:** Jaccard similarity between sets of non-empty product `code` values by country. Shared source-record IDs are reported separately; code overlap does not establish cross-border sales or trade.
- **Food-groups cross-check:** compares candidate group sets with an explicit `food_groups_tags` diagnostic crosswalk. It is not used to assign categories and is not a ground truth or semantic-accuracy score.

All reported rates use records in the stated country or comparison subset as the denominator unless a table explicitly names a different denominator. Repeated category assignments can overlap and should not be summed as a partition.

## AI-assisted semantic mapping audit

The completed AI-assisted audit evaluates the fixed sample of 150 Indonesian category-tagged records and separately reports a census of eight Meat & poultry candidates. Its label file contains AI-assisted judgments and evidence references; it is not human annotation or ground truth. These outputs are published as a narrowly scoped diagnostic under the project publication policy.

After building the canonical database, create the deterministic sample only if `data/private/category_mapping_audit_sample.csv` is absent; the preparation script refuses to overwrite an existing file. Then rebuild the record-level and aggregate audit outputs:

```powershell
.\.venv\Scripts\python.exe .\scripts\prepare_mapping_audit_sample.py
.\.venv\Scripts\python.exe .\scripts\evaluate_mapping_audit_sample.py
```

The evaluator verifies the pinned snapshot, the deterministic sample membership, and the exact census membership before writing the audit CSVs under `outputs/quality/`. The sample intentionally omits candidate mappings; the AI-assisted reviewer labels are stored separately in `category_mapping_semantic_audit_labels.csv`.

Assignment-level determinate precision is correct / (correct + incorrect); a separate confirmed share retains ambiguous and insufficient-evidence assignments in the denominator. Record exact-set agreement, per-group precision, uncertainty rates, and the diagnostic-only `food_groups_tags` comparison are also reported. The separate eight-record census is not pooled with the primary estimate.

Approximate 95% intervals use first-order Taylor linearization with a finite-population correction, conditional on the fixed MD5-ranked sample approximating simple random sampling without replacement. Sparse per-group intervals are suppressed, and zero-residual-variance intervals are not reported. The intervals quantify sampling uncertainty only—not AI-judgment reliability, calibration, or independence. This is AI-assisted semantic assessment, not independent human annotation; reviewer confidence is self-assessed. External product-page checks are recorded for only the specific records where they helped resolve ambiguity.

## Quality checks

The synthetic tests use a small in-memory fixture and do not require the source snapshot or a large database:

```text
python -m pytest -q
ruff check scripts tests
sqlfluff lint sql/05_validate_five_country_database.sql --dialect duckdb --rules CP01
python scripts/check_docs_consistency.py
```

The documentation checker recomputes generated README and Stage 7 sections from the tracked CSV outputs and fails if values drift. The GitHub Actions workflow runs tests, focused linters, and this consistency check on pushes and pull requests.

## Outputs and attribution

Published outputs include aggregate country/category/brand results, the field-readiness scorecard, contributor/source/year diagnostics, identifier-overlap and food-groups diagnostics, the fixed-sample AI-assisted semantic-audit labels and record-level results, validation reports, and static PNG charts. The audit output is the sole record-level exception to the publication scope and contains only the reviewed records and their product evidence; the unlabeled human-review sample and full source database are not published.

Open Food Facts data and third-party reference files have terms separate from this project's MIT-licensed code and documentation. Review [the source, attribution, and license note](./01_data_source.md) before redistribution or commercial use.
