# GitHub repository metadata and release records

Prepared for `MaulanaKindi/indonesia-food-product-landscape`. The description, topics, and social preview below are applied, and releases `v1.0`, `v1.1`, and `v1.2` are published.

## About

**Description:** Data-coverage study of Open Food Facts product records for Indonesia (ID), with Malaysia (MY), the Philippines (PH), and Singapore (SG) as comparison countries and Thailand (TH) as a high-coverage contrast. Re-applied on 2026-11-17, after the repository still showed an earlier wording ("Exploratory comparison ... four Southeast Asian peers") that contradicted the study-country framing; the API value and the page's `og:description` now match this text.

**Topics:** `open-food-facts`, `food-data`, `indonesia`, `southeast-asia`, `data-quality`, `market-intelligence`, `python`, `duckdb`, `sql`, `data-analysis`

**Social preview:** [`docs/img/social_preview.png`](../docs/img/social_preview.png) - 1280 x 640 PNG, generated from the project's fixed-snapshot category-tag coverage values. Applied on 2026-11-17 from **Settings → Social preview → Edit** and verified from the repository page: both `og:image` and `twitter:image` resolve to a `repository-images.githubusercontent.com` URL rather than the default preview. GitHub recommends 1280 x 640 pixels and accepts PNG/JPG/GIF under 1 MB ([instructions](https://docs.github.com/en/enterprise-cloud@latest/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview)).

## Recommended metadata for a client-facing audience

The applied description above is the full study framing. For a portfolio audience that arrives from a search result or a shared link, a shorter sentence reads better in the GitHub sidebar. Recommended replacement, 146 characters:

> Data-coverage study of Open Food Facts for Indonesia and four comparison markets: what the data supports, what it cannot, and how to reproduce it.

An alternative that names the comparison countries instead of the value proposition, 153 characters:

> Open Food Facts data-coverage study for Indonesia vs Malaysia, Philippines, Singapore and Thailand: what is usable, what is not, and how to reproduce it.

**Recommended topics (8):** `open-food-facts`, `data-quality`, `data-coverage`, `duckdb`, `python`, `sql`, `market-intelligence`, `indonesia`

The current ten topics are a superset and remain valid; the eight above drop `food-data`, `southeast-asia`, and `data-analysis` in favor of `data-coverage`, which states the actual contribution more directly.

**Social preview check.** `docs/img/social_preview.png` is unchanged and still resolves through `og:image`. It was committed in `3164c9b` and documented as generated from the fixed-snapshot category-tag coverage values, and there is no generator script in the repository, so it cannot be regenerated from tracked data without rebuilding the source. Its content was not visually re-verified for this release. If it shows only a coverage chart, it does not yet carry the "what the data supports and what it cannot" framing that the README now leads with, and replacing it with a title card that states that framing would match the new positioning better.

## Draft release note — v1.3

**Tag:** `v1.3`

**Title:** Indonesia Food Product Landscape v1.3

**Prerelease:** No.

**Notes:**

- Portfolio polish: the README now opens with a 30-second summary, key results, and what the work demonstrates, with the technical detail kept below.
- All five chart titles state the finding they show and are computed from the plotted data, so a title cannot drift from its numbers. Indonesia is highlighted against the comparison countries, and every figure has a plain-language caption.
- Adds `docs/client_one_pager.md`, a one-page brief covering the problem, approach, result, decision implications, limits, and reproduction.
- Internal working notes move to `docs/internal/` and are labeled as non-reader-facing; public wording drops internal process language such as "owner-approved".
- Spelling is normalized to American English throughout.
- No headline number, mapping decision, or Stage 5-7 logic changed in this release.

## Published releases

### v1.2 (2026-11-17)

**Tag:** `v1.2`

**Title:** Indonesia Food Product Landscape v1.2

**Release:** [Indonesia Food Product Landscape v1.2](https://github.com/MaulanaKindi/indonesia-food-product-landscape/releases/tag/v1.2) - published 2026-11-17 WIB.

**Prerelease:** No.

**Notes:**

- Documentation and governance release: a decision memo, a reproducible test of the country coverage gaps, a pinned-snapshot liveness check, and repository metadata verification. No headline number, mapping decision, or Stage 5-7 logic changed.
- `docs/11_decision_memo.md` records four decisions with evidence, confidence, effort bands, owner roles, and horizon, and states the addressable universe behind each one. Adopted 2026-11-17 by the author; decisions 1-3 are standing guidance and decision 4 is recorded but not scoped.
- Coverage gaps are now tested rather than asserted. A two-proportion test with 95% Wald intervals finds Indonesia indistinguishable from Malaysia (+0.87 pp, 95% CI -0.11 to +1.86, p = 0.0833) and clearly below the Philippines, Singapore, and Thailand; all four comparisons survive the Bonferroni-adjusted threshold of 0.0125.
- `scripts/support_check_pin_liveness.py` checks that the pinned upstream revision still resolves and reports drift from the public head, which was 24 days on 2026-11-17. It is network-bound and deliberately excluded from CI.
- Repository metadata verified: description, ten topics, and a social preview that resolves through `og:image`; `main` is protected with a required `python-and-sql` check.
- Verification: 56 tests, `ruff`, `mypy`, `sqlfluff`, documentation consistency, and the 109-assertion headline-number and static-string guard.

### v1.1 (2026-11-16)

**Tag:** `v1.1`

**Title:** Indonesia Food Product Landscape v1.1

**Release:** [Indonesia Food Product Landscape v1.1](https://github.com/MaulanaKindi/indonesia-food-product-landscape/releases/tag/v1.1) - published 2026-11-16 WIB.

**Prerelease:** No.

**Notes:**

- Stabilization: pipeline architecture refactor, hardened pinned-taxonomy integrity validation, documentation alignment, and repository quality gates (Ruff strict, mypy, pre-commit, coverage).
- Reporting: README rewritten for a 60-second first read (bottom line, decisions supported, glossary, fit-for-purpose table), plain-language country roles, and derived share-of-all-records columns.
- Five generated charts built from tracked CSVs, including two new ones (largest candidate-derived reporting group; brand text versus exact-approved mapping), on an Okabe-Ito palette that keeps country colors and series colors distinct.
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
