# Project Decisions

Short records of decisions that affect scope, measurement, or reproducibility.

## 2026-11-05 — Five-country database is canonical

**Decision:** Build the analysis database for Indonesia, Malaysia, the Philippines, Singapore, and Thailand. Keep the existing full-country database optional and do not overwrite it.

**Reason:** The five-country scope directly supports the business question while keeping the clean-room build practical. The selected database is built separately and validated against the pinned source.

## 2026-11-05 — Pin source by immutable content

**Decision:** Reproduce the analysis from Hugging Face commit `31f31c441274c095718cc88ae582030a5a615415`, requiring the expected file size and SHA-256.

**Reason:** The matching immutable source reference and checksum identify the exact analysis input. The workflow verifies the downloaded or locally supplied file and does not rely on mutable `main`.

## 2026-11-05 — Keep uncertain category mappings unresolved

**Decision:** Preserve candidate-derived and exact-approved category assignments as separate reporting bases. Use `food_groups_tags` only through a documented diagnostic crosswalk.

**Reason:** More assigned records do not by themselves establish semantic correctness. The diagnostic crosswalk is not a gold standard and never feeds category assignment.

## 2026-11-05 — Separate brand-text availability from mapping coverage

**Decision:** Report non-empty source brand text separately from exact-approved brand mappings.

**Reason:** A visible brand value is not a harmonized brand identity. The approved subset remains too sparse for broad brand concentration or market-share claims.

## 2026-11-05 — Generate public-facing numbers from validated outputs

**Decision:** Generate README and Stage 7 figures from tracked CSV outputs and fail CI when generated sections drift.

**Reason:** Manual copies of counts can become inconsistent. Deterministic generation and a consistency check make the source of each published figure explicit.

## 2026-11-05 — Keep the unlabeled human-review sample private

**Decision:** Prepare a deterministic 150-record Indonesian mapping-audit sample locally and exclude it from Git.

**Reason:** This was the initial plan for a human annotation-based estimate. The 2026-11-06 decision below later authorized AI-assisted diagnostics with conditional intervals; those outputs are not human-derived accuracy estimates.

## 2026-11-06 — Publish AI-assisted mapping audit as diagnostic evidence

**Decision:** Publish the fixed-sample AI-assisted audit labels and record-level audit outputs for the 150-record Indonesian sample and separate eight-record Meat & poultry census. Keep the unlabeled human-review sample local.

**Reason:** The audit makes candidate-mapping uncertainty visible, but AI judgments are not independent human validation or ground truth. Report its estimates and sampling intervals only as conditional diagnostics, with their limitations stated alongside them.

## 2026-11-06 — Add targeted online evidence follow-up

**Decision:** Search product-identifying information online for the selected 48 cases with incorrect, ambiguous, or insufficient-evidence AI assessments (45 primary-sample and 3 census cases) and publish a structured evidence log.

**Reason:** Exact product pages can help resolve particular records, but the follow-up is selected by observed uncertainty. Source match quality is recorded explicitly; no population-level precision or human-ground-truth claim is derived from it.

## 2026-11-07 — Standardize repository navigation and pipeline ownership

**Decision:** Add a repository architecture guide, use ordered lowercase snake-case names for project documentation, centralize pinned source metadata, apply one Ruff format across Python files, correct stale release and mapping counts, and skip duplicate crosswalk/review-queue generation when the full pipeline has just rebuilt those inputs.

**Reason:** The architecture map makes authoritative inputs, generated evidence, optional tasks, and output ownership easier to locate. The shared source manifest and automated style/link checks reduce drift. The full pipeline regenerates mappings before database construction; a standalone refresh still regenerates them by default. Updated links and decision counts reduce navigation and interpretation drift.

## 2026-11-07 - Standardize script roles and bound DuckDB temporary storage

**Decision:** Reserve `NN_` names for workflow stages, name reusable/developer tools `support_*.py`, split large pipeline and reporting responsibilities into focused support modules, and route DuckDB temporary spill to `data/processed/.duckdb_temp/` with a 3 GB memory limit and 50 GB spill cap.

**Reason:** The naming rule distinguishes ordered steps from helpers without assigning false pipeline order. Smaller modules make Stage 5 evidence, category mapping, non-food diagnostics, audit statistics, and generated reports easier to find and maintain. Explicit temp and memory settings keep large local rebuilds on the workspace volume and prevent unbounded use of the default system temp location.

**Verification:** Rebuilt the pinned 4,828,207-row source into the canonical five-country database with 15/15 checks passing; rebuilt the Stage 6 candidate with 15/15 checks and Stage 6 analysis with 11/11 checks. Generated report consistency passed. The rebuild used temporary spill on D: and removed it after success.

## 2026-11-07 - Avoid duplicate profile scans in the clean pipeline

**Decision:** Let `run_all.py` pass `--skip-brand-profile-refresh` to Stage 16 after Stage 05 has validated brand mappings. Standalone Stage 16 refreshes continue to run Stage 05 by default.

**Reason:** The clean run already scans the full source for category/brand profiles before building the database. Repeating that scan during the downstream refresh wastes several minutes without changing inputs or evidence.

## 2026-11-16 - Add business framing and plain-language reporting

**Decision:** Lead the README with a bottom-line answer and the decisions it supports, add a plain-language glossary and fit-for-purpose table, rename the report roles to study country, comparison country, and high-coverage contrast, add derived share-of-all-records columns, and assert headline numbers, derived metrics, and required static README strings in `scripts/18_check_headline_numbers.py`.

**Reason:** A 60-second reader needs the answer before the method, and plain-language role names reduce decoding cost. Derived shares label their denominator explicitly so tagged-record coverage is not confused with all-record coverage. Automated assertions keep published numbers and required static strings from drifting from the tracked CSVs.

**Verification:** `scripts/support_check_docs_consistency.py` passes; `scripts/18_check_headline_numbers.py` passes 109 assertions; `ruff check` and `ruff format --check` are clean; the README is 142 lines, within the 150-line presentation limit. Generated sections are re-rendered from tracked CSVs by `scripts/support_rerender_generated_sections.py` without rebuilding the database.

## 2026-11-16 - Add accessible charts and publish v1.1

**Decision:** Add a largest-reporting-group chart and a brand-text versus exact-approved-mapping chart, generate all five charts only from tracked CSVs, move the country palette to an Okabe-Ito subset with series colours that are disjoint from country colours, and publish the stabilization and audit work together as v1.1.

**Reason:** The 60-second reader needs two visuals that the text cannot carry as fast: which reporting group dominates recorded rows, and how far brand-text availability sits from exact-approved brand coverage. Sharing hues between the country palette and the two-series charts would make one colour mean two different things, so series colours are deliberately disjoint. Publishing the stabilization branch and the audit branch in one release keeps the README, charts, and CI gates consistent for anyone who reads only the tagged state.

**Verification:** `pytest` 41 passed; `ruff check` and `ruff format --check` clean; `mypy scripts` clean across 40 files; `sqlfluff` clean; `scripts/support_check_docs_consistency.py` passes; `scripts/18_check_headline_numbers.py` passes 109 assertions; the README is 150 lines, exactly at the presentation limit; `tests/test_generated_visuals.py` covers all five charts, palette distinctness, and the source columns each chart reads.

## 2026-11-17 - Protect main and require green checks

**Decision:** Protect `main` with a required `python-and-sql` status check that requires the branch to be up to date, reject force pushes and branch deletion, enforce the rules for administrators, and do not require pull request reviews.

**Reason:** The repository is published and versioned by tag, so the branch that carries releases should not accept unverified history. Requiring the quality job keeps a red build off `main`, while leaving reviews optional lets a solo maintainer merge a green pull request without deadlocking on a self-approval that cannot exist.

**Verification:** `GET /repos/MaulanaKindi/indonesia-food-product-landscape/branches/main/protection` returns `strict=true`, `contexts=["python-and-sql"]`, `enforce_admins=true`, `allow_force_pushes=false`, and `allow_deletions=false`; the policy and the full local check list are documented in `CONTRIBUTING.md`.
