# GitHub repository metadata and release records

Prepared for `MaulanaKindi/indonesia-food-product-landscape`. The description and topics below are applied, and releases `v1.0` and `v1.1` are published. The social preview still needs to be uploaded in the repository's Settings page.

## About

**Description:** Data-coverage study of Open Food Facts product records for Indonesia (ID), with Malaysia (MY), the Philippines (PH), and Singapore (SG) as comparison countries and Thailand (TH) as a high-coverage contrast.

**Topics:** `open-food-facts`, `food-data`, `indonesia`, `southeast-asia`, `data-quality`, `market-intelligence`, `python`, `duckdb`, `sql`, `data-analysis`

**Social preview:** [`docs/img/social_preview.png`](../docs/img/social_preview.png) - 1280 x 640 PNG, generated from the project's fixed-snapshot category-tag coverage values. Upload it from **Settings → Social preview → Edit**. GitHub recommends 1280 x 640 pixels for best display and accepts PNG/JPG/GIF under 1 MB ([instructions](https://docs.github.com/en/enterprise-cloud@latest/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview)).

## Published releases

### v1.1 (2026-11-16)

**Tag:** `v1.1`

**Title:** Indonesia Food Product Landscape v1.1

**Release:** [Indonesia Food Product Landscape v1.1](https://github.com/MaulanaKindi/indonesia-food-product-landscape/releases/tag/v1.1) - published 2026-11-16 WIB.

**Prerelease:** No.

**Notes:**

- Stabilization: pipeline architecture refactor, hardened pinned-taxonomy integrity validation, documentation alignment, and repository quality gates (Ruff strict, mypy, pre-commit, coverage).
- Reporting: README rewritten for a 60-second first read (bottom line, decisions supported, glossary, fit-for-purpose table), plain-language country roles, and derived share-of-all-records columns.
- Five generated charts built from tracked CSVs, including two new ones (largest candidate-derived reporting group; brand text versus exact-approved mapping), on an Okabe-Ito palette that keeps country colours and series colours distinct.
- Verification is enforced in CI: 41 tests, `ruff`, `mypy`, `sqlfluff`, documentation consistency, and a 109-assertion headline-number and static-string guard.
- No headline number, mapping decision, or Stage 5-7 logic changed in this release.

### v1.0 (2026-11-07)

**Tag:** `v1.0` (published from commit `3164c9b`)

**Title:** Indonesia Food Product Landscape v1.0

**Release:** [Indonesia Food Product Landscape v1.0](https://github.com/MaulanaKindi/indonesia-food-product-landscape/releases/tag/v1.0) - published 2026-11-07 WIB.

**Prerelease:** No.

**Notes:**

- Adds a reproducible, descriptive comparison of product-record counts, category coverage and assignments, brand evidence, field readiness, contributor/source/year patterns, and country overlap for Indonesia, Malaysia, the Philippines, Singapore, and Thailand.
- Documents the pinned Open Food Facts snapshot, database model, analytical limits, and reproduction workflow.
- Includes a fixed 150-record AI-assisted category-mapping diagnostic and an eight-record census, with a separately logged web-evidence follow-up for 48 cases with an incorrect, ambiguous, or insufficient-evidence assessment (45 primary-sample and 3 census cases). The web follow-up is targeted and non-random; it is not human ground truth or a population precision estimate.
- Does not estimate sales, market size, market share, demand, or product availability.
- Source data and third-party reference files have terms separate from the MIT-licensed project code. Review `docs/02_data_source.md` before reuse.
