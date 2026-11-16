# Claim-to-Evidence Lineage

Use this page to follow a headline result from its pinned or reviewed inputs through the transformation, published evidence, and validation. The canonical source-row key is `source_record_id`; it is a row ordinal for the pinned Parquet snapshot, not a real-world product identifier.

## Shared path

```text
Pinned Parquet + versioned reference/mapping inputs
  -> scripts/00-09 and sql/01_build_relational_database.sql
  -> canonical five-country DuckDB tables
  -> sql/03_stage6_analysis.sql or scripts/12_stage5_country_peer_evidence.py
  -> outputs/analysis/*.csv and outputs/profiling/*.csv
  -> generated README/Stage 7 sections
```

The snapshot commit, expected byte size, and SHA-256 are in [`data/reference/pinned_sources.json`](../data/reference/pinned_sources.json) and [`docs/02_data_source.md`](02_data_source.md). The relational table grain and keys are described in [`docs/05_relational_schema_design.md`](05_relational_schema_design.md). The tracked mapping CSVs are reviewed inputs; generated candidate crosswalks are evidence and do not approve a mapping by themselves.

## Main claims

| Claim in the portfolio | Authoritative inputs and transformation | Published evidence | Definition, validation, and limit |
|---|---|---|---|
| Country record counts and category-tag coverage | Pinned `countries_tags` and `categories_tags`; country mapping inputs; [`sql/01_build_relational_database.sql`](../sql/01_build_relational_database.sql); [`sql/03_stage6_analysis.sql`](../sql/03_stage6_analysis.sql) | [`stage6_country_scope.csv`](../outputs/analysis/stage6_country_scope.csv); [`stage6_validation.csv`](../outputs/analysis/stage6_validation.csv) | Denominators and country roles are in [`docs/06_analysis_specification.md`](06_analysis_specification.md). Counts are source records assigned to ISO units; country totals may overlap and do not measure market size or sales. |
| Candidate-derived versus approved-only category assignments | [`category_reporting_group_framework.csv`](../data/reference/category_reporting_group_framework.csv); [`category_tag_reporting_group_manual_decisions.csv`](../data/mappings/category_tag_reporting_group_manual_decisions.csv); [`category_tag_manual_dispositions.csv`](../data/mappings/category_tag_manual_dispositions.csv); stages [`07`](../scripts/07_category_reporting_group_draft.py) and [`08`](../scripts/08_category_reporting_group_review_queues.py); [`sql/03_stage6_analysis.sql`](../sql/03_stage6_analysis.sql) | [`stage6_country_category.csv`](../outputs/analysis/stage6_country_category.csv); [`category_mapping_semantic_audit_summary.csv`](../outputs/quality/category_mapping_semantic_audit_summary.csv) | Candidate-derived taxonomy assignments are not all explicitly approved. Group assignments overlap; the AI-assisted semantic audit is diagnostic, not human ground truth. |
| Exact-approved brand mapping coverage | [`brand_name_manual_decisions.csv`](../data/mappings/brand_name_manual_decisions.csv); [`sql/03_stage6_analysis.sql`](../sql/03_stage6_analysis.sql); Stage 5 evidence calculation | [`stage6_country_brand.csv`](../outputs/analysis/stage6_country_brand.csv); [`stage5_country_peer_evidence.csv`](../outputs/profiling/stage5_country_peer_evidence.csv) | Exact source-text matches only. Coverage is sparse and selected; it is not a broad brand census, HHI, market share, or sales concentration. |
| Field readiness, contributor patterns, and source-tag diagnostics | Pinned source columns and country assignments; [`scripts/12_stage5_country_peer_evidence.py`](../scripts/12_stage5_country_peer_evidence.py) and [`scripts/support_stage5_readiness.py`](../scripts/support_stage5_readiness.py) | [`data_readiness_scorecard.csv`](../outputs/profiling/data_readiness_scorecard.csv); [`contributor_year_diagnostics.csv`](../outputs/profiling/contributor_year_diagnostics.csv); [`source_tag_coverage.csv`](../outputs/profiling/source_tag_coverage.csv) | Metric definitions and denominators are in [`docs/09_reproduction.md`](09_reproduction.md). Creation time is not launch time; contributor/source patterns do not prove bulk import or explain coverage. |
| Sampled semantic-audit and targeted online follow-up results | Fixed sample membership plus reviewed AI labels; [`scripts/support_evaluate_mapping_audit_sample.py`](../scripts/support_evaluate_mapping_audit_sample.py); evidence URLs and review notes | [`category_mapping_semantic_audit_records.csv`](../outputs/quality/category_mapping_semantic_audit_records.csv); [`category_mapping_online_evidence_audit.csv`](../outputs/quality/category_mapping_online_evidence_audit.csv) | The sample method, uncertainty labels, and selective follow-up limits are documented in [`docs/09_reproduction.md`](09_reproduction.md). AI judgments are not independent human annotation; the online sample is targeted, not a population estimate. |

## Generated presentation and checks

[`scripts/16_refresh_harmonized_analysis.py`](../scripts/16_refresh_harmonized_analysis.py) coordinates analysis refresh. [`scripts/support_render_readme.py`](../scripts/support_render_readme.py) and [`scripts/support_render_stage7.py`](../scripts/support_render_stage7.py) render the generated report sections from validated CSVs. The chart renderer reads the same analysis outputs. The refresh checks the candidate database and analysis before publishing refreshed outputs; [`scripts/support_check_docs_consistency.py`](../scripts/support_check_docs_consistency.py) independently checks local Markdown links and that README/Stage 7 generated values still match the tracked CSV evidence.

For the full sequence and reproducibility boundaries, see [`docs/09_reproduction.md`](09_reproduction.md). For interpreted findings and decision guidance, see [`docs/07_stage7_findings_and_recommendations.md`](07_stage7_findings_and_recommendations.md).
