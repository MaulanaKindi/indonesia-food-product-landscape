# Reproduce the Analysis

This guide rebuilds the canonical five-country analysis from the pinned Open Food Facts snapshot. It does not require the optional full-country database.

## Quick look without the 8 GB download

You do not need the source snapshot, DuckDB, or network access to inspect the published results. Every number and chart in the README is committed to the repository and can be verified or regenerated from a clean clone with only the Python dependencies:

```powershell
.\.venv\Scripts\python.exe .\scripts\support_generate_visuals.py
.\.venv\Scripts\python.exe .\scripts\18_check_headline_numbers.py
```

The first command rebuilds the five static charts under `docs/img/` from tracked CSVs (`outputs/analysis/stage6_country_scope.csv`, `stage6_country_category.csv`, and `outputs/profiling/data_readiness_scorecard.csv`). The second is a read-only guard that asserts every headline number in this guide and the README against those same tracked CSVs; it fails loudly if a number drifts. On macOS or Linux, replace the Windows virtual-environment Python path with `.venv/bin/python`.

## Requirements

- Python 3.13
- Disk space for the 7.98 GB source Parquet and temporary DuckDB spill files (capped at 50 GB on the workspace volume)
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

The pipeline downloads Hugging Face commit `31f31c441274c095718cc88ae582030a5a615415` to `data/raw/food.parquet`. It verifies the expected 7,975,461,945-byte size and SHA-256 `DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A`. Before profiling, `scripts/support_fetch_pinned_taxonomy.py` retrieves the locally excluded taxonomy JSON if it is missing and verifies its file size, SHA-256, JSON syntax, and expected taxonomy structure; newly downloaded and existing local files are checked the same way. Both downloads use a temporary file and reject mismatched content before publishing it. The source, taxonomy, and DuckDB databases are excluded from Git.

The taxonomy URL is a mutable upstream endpoint, not an immutable historical URL. The checksum prevents silently using a newer taxonomy, but if the upstream no longer serves the pinned bytes, a clean clone needs an exact archived copy from an authorized source before the pipeline can run. The project does not redistribute the taxonomy JSON.

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

## Reproducibility boundaries

The core pipeline is snapshot-pinned: identical Parquet bytes, tracked mapping inputs, dependencies, and configuration should regenerate the same scoped database checks and analytical tables. The input manifest records exact source size and SHA-256. The taxonomy JSON is intentionally not distributed; a clean clone fetches the upstream endpoint and accepts it only if its pinned size and hash match. If the mutable endpoint no longer serves those exact bytes, the documented prerequisite is an authorized copy of the pinned taxonomy. Without it, the taxonomy-dependent pipeline stops rather than silently changing category results.

The generated report also includes reviewed AI-assisted audit labels and a targeted online-evidence log. The evaluator can regenerate the corresponding metrics from the pinned sample and tracked labels, but it does not recreate the original AI judgments or re-perform the historical product-page review. Those are versioned review inputs with stated limitations.

The claim-validation script [`scripts/10_online_validation.py`](../scripts/10_online_validation.py) is deliberately outside `run_all.py`: it reads current online metadata and overwrites retrieval-date-specific evidence files. Run it separately when refreshing that evidence:

```powershell
.\.venv\Scripts\python.exe .\scripts\10_online_validation.py
```

The new retrieval date and any changed web content mean these evidence files are not expected to be byte-identical across runs. The checked-in log documents the evidence used for the published claims. See the [claim-to-evidence lineage](10_claim_lineage.md) for the exact input, transformation, output, and validation path of headline results.

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

## Example SQL queries

The README shows one example query and points here for the full set. Run these against the canonical database `data/processed/global_product_landscape_five_country.duckdb`.

```sql
-- How many country records have category tags?
SELECT country.iso_alpha2,
       COUNT(DISTINCT country.source_record_id) AS records,
       COUNT(DISTINCT category.source_record_id) AS category_tagged
FROM record_country AS country
LEFT JOIN record_category_tag AS category USING (source_record_id)
GROUP BY country.iso_alpha2
ORDER BY country.iso_alpha2;
```

```sql
-- How does exact-approved brand mapping compare with raw brand text?
SELECT country.iso_alpha2,
       COUNT(DISTINCT record.source_record_id)
           FILTER (WHERE NULLIF(trim(record.brands), '') IS NOT NULL)
           AS records_with_brand_text,
       COUNT(DISTINCT brand.source_record_id)
           FILTER (WHERE mapping.review_status = 'approved')
           AS records_with_exact_approved_mapping
FROM record_country AS country
JOIN source_product_record AS record USING (source_record_id)
LEFT JOIN record_brand_source_value AS brand USING (source_record_id)
LEFT JOIN brand_name_mapping AS mapping
    ON brand.source_brand_name = mapping.source_brand_name
GROUP BY country.iso_alpha2
ORDER BY country.iso_alpha2;
```

```sql
-- Compare candidate-derived and approved-only tagged-record assignment.
SELECT country.iso_alpha2,
       COUNT(DISTINCT category.source_record_id)
           FILTER (
               WHERE candidate.candidate_role IN (
                   'single_group_candidate',
                   'manual_group_assignment'
               )
               AND candidate.comparison_role = 'primary_candidate'
               AND candidate.reporting_group_id <> 'other_unclassified'
           )
           AS candidate_assigned_records,
       COUNT(DISTINCT category.source_record_id)
           FILTER (WHERE decision.selected_group_id IS NOT NULL)
           AS approved_only_assigned_records
FROM record_country AS country
JOIN record_category_tag AS category USING (source_record_id)
LEFT JOIN category_tag_group_candidate AS candidate
    USING (source_category_tag)
LEFT JOIN category_tag_group_decision AS decision
    USING (source_category_tag)
GROUP BY country.iso_alpha2
ORDER BY country.iso_alpha2;
```

## AI-assisted semantic mapping audit

The completed AI-assisted audit evaluates the fixed sample of 150 Indonesian category-tagged records and separately reports a census of eight Meat & poultry candidates. Its label file contains AI-assisted judgments and evidence references; it is not human annotation or ground truth. A web follow-up was performed for 48 cases with incorrect, ambiguous, or insufficient-evidence AI assessments (45 from the primary sample and 3 from the separate census). The separate online evidence log documents the URL, source type, exact-code match, access date, evidence summary, and unresolved cases. This targeted follow-up is published as a diagnostic under the project publication policy.

After building the canonical database, create the deterministic sample only if `data/private/category_mapping_audit_sample.csv` is absent; the preparation script refuses to overwrite an existing file. Then rebuild the record-level and aggregate audit outputs:

```powershell
.\.venv\Scripts\python.exe .\scripts\support_prepare_mapping_audit_sample.py
.\.venv\Scripts\python.exe .\scripts\support_evaluate_mapping_audit_sample.py
```

The evaluator verifies the pinned snapshot, the deterministic sample membership, and the exact census membership before writing the audit CSVs under `outputs/quality/`. The sample intentionally omits candidate mappings; the AI-assisted reviewer labels are stored separately in `category_mapping_semantic_audit_labels.csv`.

Assignment-level determinate precision is correct / (correct + incorrect); a separate confirmed share retains ambiguous and insufficient-evidence assignments in the denominator. Record exact-set agreement, per-group precision, uncertainty rates, and the diagnostic-only `food_groups_tags` comparison are also reported. The separate eight-record census is not pooled with the primary estimate.

Approximate 95% intervals use first-order Taylor linearization with a finite-population correction, conditional on the fixed MD5-ranked sample approximating simple random sampling without replacement. Sparse per-group intervals are suppressed, and zero-residual-variance intervals are not reported. The intervals quantify sampling uncertainty only—not AI-judgment reliability, calibration, or independence. This is AI-assisted semantic assessment, not independent human annotation; reviewer confidence is self-assessed.

The follow-up online evidence log covers every selected case with an incorrect, ambiguous, or insufficient-evidence AI assessment in the primary sample and separate census. It records the URL, source type, exact-code match, access date, and a concise evidence summary. Prefer manufacturer, regulator, or official product-specification evidence; retailer listings and secondary barcode/product databases are fallback evidence and are labeled as such. A product-family or related-variant page does not count as an exact-code match. A no-result search remains unresolved, not a contradiction. Open Food Facts-derived pages are not independent corroboration of Open Food Facts data. Because the follow-up is targeted by observed disagreement/uncertainty, its 30 supporting and 18 partial findings cannot be used as sample-wide accuracy or precision estimates. See `outputs/quality/category_mapping_online_evidence_audit.csv`.

## Quality checks

The synthetic tests use a small in-memory fixture and do not require the source snapshot or a large database:

```text
python -m pytest -q
ruff check scripts tests
ruff format --check scripts tests
sqlfluff lint sql/02_validate_relational_database.sql sql/05_validate_five_country_database.sql --dialect duckdb --rules CP01
python scripts/support_check_docs_consistency.py
python scripts/18_check_headline_numbers.py
```

The documentation checker verifies local Markdown links, recomputes generated README and Stage 7 sections from tracked CSV outputs, and fails if a link or generated value drifts. The headline-number checker re-asserts every published headline number against the tracked CSVs without running the pipeline. The GitHub Actions workflow runs tests, Ruff lint and formatting checks across all Python scripts and tests, SQLFluff on standalone DuckDB validation SQL, and this consistency check on pushes and pull requests.

## Outputs and attribution

Published outputs include aggregate country/category/brand results, the field-readiness scorecard, contributor/source/year diagnostics, identifier-overlap and food-groups diagnostics, the fixed-sample AI-assisted semantic-audit labels and record-level results, the targeted online evidence log, validation reports, and static PNG charts. These audit files are the scoped record-level exception to the publication policy; the unlabeled human-review sample and full source database are not published.

Open Food Facts data and third-party reference files have terms separate from this project's MIT-licensed code and documentation. Review [the source, attribution, and license note](./02_data_source.md) before redistribution or commercial use.
