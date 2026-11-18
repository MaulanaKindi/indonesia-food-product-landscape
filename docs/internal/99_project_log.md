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

**Decision:** Add a largest-reporting-group chart and a brand-text versus exact-approved-mapping chart, generate all five charts only from tracked CSVs, move the country palette to an Okabe-Ito subset with series colors that are disjoint from country colors, and publish the stabilization and audit work together as v1.1.

**Reason:** The 60-second reader needs two visuals that the text cannot carry as fast: which reporting group dominates recorded rows, and how far brand-text availability sits from exact-approved brand coverage. Sharing hues between the country palette and the two-series charts would make one color mean two different things, so series colors are deliberately disjoint. Publishing the stabilization branch and the audit branch in one release keeps the README, charts, and CI gates consistent for anyone who reads only the tagged state.

**Verification:** `pytest` 41 passed; `ruff check` and `ruff format --check` clean; `mypy scripts` clean across 40 files; `sqlfluff` clean; `scripts/support_check_docs_consistency.py` passes; `scripts/18_check_headline_numbers.py` passes 109 assertions; the README is 150 lines, exactly at the presentation limit; `tests/test_generated_visuals.py` covers all five charts, palette distinctness, and the source columns each chart reads.

## 2026-11-17 - Protect main and require green checks

**Decision:** Protect `main` with a required `python-and-sql` status check that requires the branch to be up to date, reject force pushes and branch deletion, enforce the rules for administrators, and do not require pull request reviews.

**Reason:** The repository is published and versioned by tag, so the branch that carries releases should not accept unverified history. Requiring the quality job keeps a red build off `main`, while leaving reviews optional lets a solo maintainer merge a green pull request without deadlocking on a self-approval that cannot exist.

**Verification:** `GET /repos/MaulanaKindi/indonesia-food-product-landscape/branches/main/protection` returns `strict=true`, `contexts=["python-and-sql"]`, `enforce_admins=true`, `allow_force_pushes=false`, and `allow_deletions=false`; the policy and the full local check list are documented in `CONTRIBUTING.md`.

## 2026-11-17 - Add a decision memo and a verification path

**Decision:** Publish `docs/11_decision_memo.md` as a short record of decisions with evidence, confidence, effort, and a suggested owner; add a CI badge and a 60-second verification line to the README; add a "What would change these conclusions" subsection; and move the README's method diagram out because `docs/00` already carries a fuller execution-flow diagram.

**Reason:** The audit scored communication and documentation highly, but the README answered what the data shows without saying who should do what, at what cost. A memo gives executives a costed ask, gives analysts a traceable confidence statement, and gives a hiring reader evidence that conclusions are falsifiable rather than asserted. Removing the duplicate diagram keeps one home for the pipeline map and pays for the added lines inside the 150-line presentation limit.

**Verification:** `scripts/18_check_headline_numbers.py` passes 109 assertions with the new static text; `scripts/support_check_docs_consistency.py` passes, including the new `docs/11` links; `pytest` 41 passed; the README is 148 lines, within the 150-line limit; the memo introduces no number that is not already asserted against the tracked CSVs.

## 2026-11-17 - Check the coverage gaps instead of asserting them

**Decision:** Add `scripts/support_coverage_comparison.py` and `tests/test_coverage_comparison.py`, so statements that Indonesia is similar to Malaysia and below the Philippines, Singapore, and Thailand rest on a two-proportion test with a 95% Wald interval and a Bonferroni-adjusted threshold, and report the addressable universe behind each decision in the decision memo.

**Reason:** "Similar" and "below" were defensible from the counts but unfalsifiable as written. Testing them shows the Malaysia difference (+0.87 pp, 95% CI -0.11 to +1.86, p = 0.0833) is not distinguishable from noise while the other three gaps survive the adjusted threshold, which strengthens the existing wording instead of changing it. The memo's addressable-universe table also answers the executive question the previous version left open: how many records each decision can actually reach.

**Verification:** `pytest` 48 passed including the 7 new comparison tests; `ruff check` and `ruff format --check` clean; `mypy scripts` clean across 41 files; `scripts/support_coverage_comparison.py` reproduces the memo table exactly; the test asserts the same values, so a drift in `stage6_country_scope.csv` fails the build.

## 2026-11-17 - Close the cost question and cancel the assignment-rate test

**Decision:** State the memo's cost basis explicitly (no currency, because the relevant vendor programs are quote-only and publish no list price) and confirm that owners are roles; cancel the proposed assignment-rate two-proportion test.

**Reason:** The two remaining open items were an owner/cost gap and a statistics gap, and neither survives contact with the data. Owners were already roles in the memo table, so nothing needed researching; a currency figure would have to be invented, which is worse than an honest effort band. The assignment-rate comparison puts 788 and 113 on the same 9,118 records, giving +7.40 pp (95% CI 6.78 to 8.02) with a McNemar exact p of 1.3e-203, so it is significant by construction: the two views differ on the same records. A test that cannot fail adds no evidence, so it is recorded as won't do rather than built. Approval of the memo is deliberately left to the end, after the content it approves is settled.

**Verification:** the memo still introduces no unasserted number; `scripts/support_check_docs_consistency.py` and `scripts/18_check_headline_numbers.py` pass; the cancelled test adds no file, so the suite count is unchanged.

## 2026-11-17 - Check the pin instead of assuming it

**Decision:** Add `scripts/support_check_pin_liveness.py` and `tests/test_pin_liveness.py`. The script asks the Hugging Face API whether the pinned revision still resolves and how many days the public dataset has advanced, and it is documented as a network-bound check that stays out of CI.

**Reason:** The reproducibility contract is a pinned commit plus a SHA-256, but nothing verified that the commit still exists upstream, and the memo's warning that a newer snapshot could move the headline was a hypothetical. Measured on 2026-11-17 the pin resolves and the public head is 24 days newer, which turns the hypothetical into a reproducible measurement. The number is printed rather than recorded, because drift is a property of the day it is checked and a figure written into the docs would rot on the next upload.

**Verification:** `pytest` 56 passed including the 8 new pin-liveness tests; `ruff check` and `ruff format --check` clean; `mypy scripts` clean; the script exits 0 against the live API and reports `Pin resolvable : yes` with a 24-day drift; `scripts/support_check_docs_consistency.py` and `scripts/18_check_headline_numbers.py` still pass.

## 2026-11-17 - Approve the decision memo

**Decision:** Approve `docs/11_decision_memo.md` as the repository's standing guidance: decisions 1-3 are adopted, decision 4 is recorded but not scoped. Rename the table column from "Suggested owner" to "Owner" now that the decisions are approved, and relabel decision 4's owner from "Commercial data owner" to "Budget holder (future)".

**Reason:** The memo had been carrying `proposed` while its content was already settled, which made a finished document read as an unfinished one. The repository owner is the only party accountable for these decisions, so recording that approval is accurate rather than ceremonial; the wording says so plainly instead of implying an independent review. Decision 4 named a role this project does not have, so it is labeled as a future budget holder, and it stays unscoped because commissioning sales or panel data needs budget this repository does not control.

**Verification:** `docs/11` now states the approval date and approver and no longer asks for approval; the README pointer reads "an owner"; `scripts/support_check_docs_consistency.py` and `scripts/18_check_headline_numbers.py` pass; no figure changed, so `pytest` stays at 56 passed.

## 2026-11-17 - Publish v1.2

**Decision:** Publish `v1.2` from `main` as a documentation and governance release, covering the work merged after `v1.1`: the decision memo and its approval, the coverage-gap tests, the pinned-snapshot liveness check, and the repository metadata and branch-protection records.

**Reason:** The last tag pointed at `86619d6` while `main` had moved 17 commits ahead, so anyone reading the repository saw material that the published version did not claim. v1.2 makes the tag match what a reader actually sees, without touching data or logic: no headline number, mapping decision, or Stage 5-7 behavior changes, so the 8.75/10 audit score still describes the release.

**Verification:** `pytest` 56 passed; `ruff check` and `ruff format --check` clean; `mypy scripts` clean across 42 files; `sqlfluff` CP01 clean; `scripts/support_check_docs_consistency.py` passes; `scripts/18_check_headline_numbers.py` passes 109 assertions; the release notes and metadata record are in `docs/08_github_release_metadata.md`.
