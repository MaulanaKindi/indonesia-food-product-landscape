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

**Reason:** Labels must be supplied by a human reviewer. No precision estimate or confidence interval will be reported before those labels are complete and reviewed.

## 2026-11-06 — Publish AI-assisted mapping audit as diagnostic evidence

**Decision:** Publish the fixed-sample AI-assisted audit labels and record-level audit outputs for the 150-record Indonesian sample and separate eight-record Meat & poultry census. Keep the unlabeled human-review sample local.

**Reason:** The audit makes candidate-mapping uncertainty visible, but AI judgments are not independent human validation or ground truth. Report its estimates and sampling intervals only as conditional diagnostics, with their limitations stated alongside them.

## 2026-11-06 — Add targeted online evidence follow-up

**Decision:** Search product-identifying information online for all 48 primary-sample records with disputed or uncertain AI assessments and publish a structured evidence log.

**Reason:** Exact product pages can help resolve particular records, but the follow-up is selected by observed uncertainty. Source match quality is recorded explicitly; no population-level precision or human-ground-truth claim is derived from it.
