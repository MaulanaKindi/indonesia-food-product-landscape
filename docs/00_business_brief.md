# Business Brief: Indonesia Food Product Landscape

## 1. Project Overview

| Item | Description |
|----------|----------|
| Project | Indonesia Food Product Landscape |
| Target role | Market Intelligence Analyst |
| Primary data source | Open Food Facts |
| Tools | DuckDB, SQL, Python, Git, GitHub |

This project analyzes recorded food-product records in Open Food Facts, focusing on Indonesia with Malaysia, the Philippines, and Singapore as contextual peers and Thailand as a category-coverage contrast. It combines data profiling, quality assessment, relational database design, SQL analysis, reproducible outputs, and business interpretation to demonstrate practical market-intelligence capabilities.

## 2. Business Objective

Develop a structured, evidence-based view of recorded product categories and exact-approved brand-mapping coverage in a pinned Open Food Facts snapshot. Describe how observed record counts and category-tag coverage differ across the approved country scope. Broad brand concentration is deferred because exact-approved brand mappings are too sparse.

The analysis is exploratory. Open Food Facts is a collaboratively maintained product database, not a census of products sold or a source of sales, market-share, or consumer-demand data.

## 3. Primary Business Question

Within the pinned Open Food Facts snapshot, how do country record counts, category-tag coverage, and candidate-derived versus approved-only category assignments differ across Indonesia, contextual peers, and a higher-coverage contrast, subject to mapping and data-quality limitations?

## 4. Supporting Questions

1. What are the category-tag coverage and category-assignment gaps in Indonesia and the selected comparison units?
2. How do candidate-derived and approved-only reporting-group assignments differ, including their overlap?
3. What share of records have exact-approved brand mappings, and why is that subset insufficient for broad brand-concentration claims?
4. How does Indonesia's recorded landscape compare descriptively with the contextual peers and the separate coverage contrast?

## 5. Analytical Scope

- Assess completeness, consistency, duplication, and suitability for country and category comparisons.
- Design a relational schema justified by the source data and analytical questions.
- Use SQL for profiling, transformations, schema operations, joins, CTEs, aggregations, and window functions where they add analytical value.
- Use Python where useful for orchestration, validation, file handling, and reproducible execution; SQL remains a core analytical deliverable.
- Harmonize relevant country, category, and brand values; document every material mapping, exclusion, and unresolved value.
- Select countries, including Indonesia where data quality permits, and categories only after profiling and applying documented comparability criteria.
- Translate defensible results into concise business observations, interpretations, limitations, and recommendations for further investigation.

The final country and category scope is determined by data profiling, mapping quality, coverage, and the intended comparison—not by record volume alone.

## 6. Definitions and Measurement Rules

### 6.1 Snapshot and unit of analysis

- Every result must identify the exact source snapshot used.
- A source row is a **product record**, not necessarily a unique real-world product.
- Report row-based record counts separately from counts based on distinct, validated product identifiers.
- Do not describe a count as a unique-product count until duplicate and identifier rules have been investigated, documented, and applied consistently.
- Use source rows as the primary unit because a validated product-identity and conflict-resolution rule is not available. Do not deduplicate on `code`. A record may belong to multiple countries or reporting groups; assignment totals can therefore overlap.

### 6.2 Product identifiers and duplicates

- Treat `code` as a candidate product identifier, not an assumed primary key.
- Investigate duplicate codes for exact duplicates, conflicting records, and other causes before choosing a deduplication rule.
- Never discard duplicate records solely because a duplicate exists. Record the selected rule, affected counts, and impact on analytical results.
- If a reliable unique identifier cannot be established, label results as record-based and disclose that limitation.

### 6.3 Countries and territories

- Use ISO 3166-1 alpha-2 units as the comparison geography, including listed territories.
- Map aliases to one canonical code and name; classify global, regional, historical, combined, malformed, and unresolved tags explicitly.
- Roll subnational values up to an ISO 3166-1 parent only when the mapping is supported and documented.
- Count a record once per resulting ISO unit, even when multiple source tags map to that same unit.
- Report records without an approved country mapping and any unresolved-tag coverage.

### 6.4 Categories

- Use documented source taxonomy identifiers/tags for category assignment where available.
- Declare one consistent analytical category grouping before comparing categories. Where the source taxonomy has multiple parents or inconsistent depth, define explicit reporting groups rather than assuming one universal numeric level.
- Normalize aliases and document exclusions, multi-category assignments, and missing-category coverage.
- Do not add child and parent category counts together as if they were disjoint.
- Treat `Other / unclassified` as a diagnostic reconciliation bucket only; exclude it from primary category comparisons unless its members are separately reviewed and assigned to a substantive group.

### 6.5 Brands and concentration

- Apply only exact, owner-approved mappings of complete source `brands` text; do not split multi-brand values or infer identity from `brands_tags`.
- Report approved-mapping coverage and mapped-only assignment counts with the selected denominator clearly labeled.
- Current approved-brand coverage is too sparse and selected to support a broad brand landscape or an HHI. Defer concentration measures until identity rules and coverage are demonstrably adequate and the owner approves a defensible denominator.
- Any future record-based brand distribution remains descriptive; it is not sales share, revenue concentration, or proof of commercial dominance.

### 6.6 Country comparability and screening

- The current 1,000-record minimum is an exploratory screening floor, not a statistical guarantee or a claim of representativeness.
- Recalculate the shortlist after identifier resolution and any material quality exclusions.
- Select peer countries based on documented coverage and quality, relevant category availability, source-snapshot alignment, and analytical relevance. Do not select peers on record count alone.
- Include Indonesia as a focal comparison where data quality and coverage are adequate; report any limitations that make a direct comparison unsuitable.
- Publish the selection rules and the resulting included/excluded country and category scopes before drawing conclusions.

## 7. Data and Interpretation Principles

- Product counts represent records in Open Food Facts, not all products sold in a market.
- Recorded brand counts do not establish market share or commercial dominance.
- Brand concentration calculated from product records is not equivalent to sales concentration.
- Open Food Facts coverage, contributor activity, missing values, duplicate records, classification differences, and snapshot timing may affect cross-country comparisons.
- A product may be assigned to several countries, categories, or brands; sums across such groups may overlap.
- Distinguish observations from interpretations and recommendations. Do not imply causation from descriptive comparisons.
- Document all cleaning, mapping, exclusion, and denominator decisions with reproducible evidence.

## 8. Data Provenance Requirements

Document and retain:

- Source dataset page and exact source file or release.
- Snapshot/release date, retrieval date, and extraction/download method.
- Local file name, format, size, and SHA-256 checksum.
- Applicable license, attribution, and share-alike or other reuse obligations, verified against the upstream source.
- Tool and dependency versions needed to reproduce extraction, transformation, and analysis.

Do not infer missing provenance details. Mark them as not yet recorded and resolve them before the final reproducibility and licensing checks.

## 9. Expected Deliverables

- Business brief and reviewer-oriented root `README.md`.
- Source, extraction, licensing, and attribution documentation.
- Reproducible SQL scripts for profiling, cleaning, relational schema creation, and analysis; documented Python orchestration as needed.
- Relational schema and entity-relationship diagram.
- Data-quality log documenting key issues, decisions, and their impacts.
- Versioned, reproducible analytical outputs with clearly defined metrics and denominators.
- Business findings, limitations, and recommendations for further investigation, linked to supporting results.
- Documented database build and recovery workflow, including a validated backup restore and independent checks.

## 10. Definition of Done

The project is complete when:

1. The data source, exact snapshot, extraction method, applicable licensing, and attribution requirements are documented.
2. The relational schema is justified by the data and analytical requirements, with an ERD.
3. SQL scripts can be executed in the documented order from a clean environment when stated prerequisites are met.
4. Product, brand, country, category, denominator, and concentration definitions are explicit and applied consistently.
5. Important quality and cleaning decisions are traceable to evidence and their analytical impact is reported.
6. Key results can be regenerated and independently checked against documented validation queries or checks.
7. Business conclusions are linked to reproducible results, distinguish observations from interpretations, and state limitations.
8. The GitHub repository is understandable to a reviewer unfamiliar with the project.
9. The database can be rebuilt from the documented source data and SQL scripts in a clean environment, subject to stated prerequisites.
10. At least one database backup has been restored successfully, with table-level and data-integrity checks documented.

## 11. Current Project Status

Initial dataset profiling, quality checks, raw country-tag profiling, and an ISO-mapped exploratory country profile are available. The country shortlist currently uses a 1,000-record screening floor. Product-identifier resolution, category and brand harmonization, relational schema design, core SQL pipeline, and backup/recovery validation remain to be completed before their related conclusions can be considered final.
