# Decision Memo — What This Data Supports

**Prepared:** 2026-11-17 · **Status:** proposed, for owner approval · **Scope:** one pinned Open Food Facts snapshot (commit and SHA-256 in [the source record](02_data_source.md))

This memo turns the study's findings into decisions with evidence, confidence, effort, and an owner. It introduces no new numbers: every figure below is a tracked value that `scripts/18_check_headline_numbers.py` and `scripts/support_check_docs_consistency.py` assert against the committed CSVs.

## Decisions

| # | Decision or action | Evidence (tracked) | Confidence | Effort (est.) | Suggested owner | Horizon |
|---|---|---|---|---|---|---|
| 1 | Use Open Food Facts as a **supplementary** signal for catalogue coverage and field completeness | 12.2% of 9,118 Indonesian records carry a category tag; brand text on 38.8%, numeric nutrition on 31.0% ([field readiness](../README.md#field-readiness)) | High for describing this snapshot; low for generalising to the market | S — reuse committed outputs, no new acquisition | Analytics lead | Now |
| 2 | Do **not** use it alone for competitor share, market size, sales, demand, or availability | The source has no sales, revenue, or demand fields and is a collaborative snapshot, not a census ([analysis specification](06_analysis_specification.md)) | High | None — an avoidance, not a task | Analytics lead | Standing |
| 3 | Treat category assignments as **provisional** | Candidate-derived assignments cover 788/9,118 records (8.64%) against 113 (1.24%) approved-only; 106,211 tags remain taxonomy-unmatched ([data profile](03_data_profile.md)) | Medium-high | M — scheduled human review of category and brand mappings | Data steward | Next planning cycle |
| 4 | Commission sales, panel, or retail-scan data before any share or demand claim | The gap is structural, not a processing issue; see [what would change these conclusions](#what-would-change-these-conclusions) | High that the gap exists | L — new licence, ingestion, and validation | Commercial data owner | Next budget cycle |

Effort key: **S** fits in the existing backlog, **M** needs scheduled review capacity, **L** needs new procurement or budget. Estimates are planning aids, not commitments.

## How far the evidence reaches

- **What is strong:** record counts and field coverage are deterministic functions of a pinned snapshot, so they reproduce exactly. That is why decisions 1 and 2 rest on them.
- **What is diagnostic:** the AI-assisted audit judged 97 of 130 candidate group pairs correct on a fixed 150-record Indonesian sample, with exact group-set agreement of 61/150 (40.7%). The 48-case online follow-up (30 supported, 18 partial, 36 source URLs, 29 exact product-code matches) is targeted and non-random.
- **What follows:** these are diagnostics, not human ground truth, and they do not support a population precision estimate. Decision 3 is provisional for that reason, not because the mapping work is incomplete in principle.

## What would change these conclusions

- **A newer pinned snapshot.** Coverage is a property of one commit; a later commit can move 12.2% without any change in data quality.
- **Sales, panel, or retail-scan data.** This is the only input that converts "recorded products" into "products actually sold", and it would make decisions about share or demand answerable.
- **An approved taxonomy and reviewed mappings.** Closing the 106,211 unmatched tags and the 838 multi-group tags would move decision 3 from provisional to approved, and would change which reporting groups are usable at all.
- **A random-sample audit with intervals.** A probability sample would replace the targeted diagnostic with an estimate that carries a confidence interval, which is what a precision claim requires.

## Non-claims

- Not a market-size, sales, demand, share, or availability estimate.
- Not evidence that products are sold or traded between the five countries; shared product codes are not market overlap.
- Not a brand-landscape or concentration (HHI) input: exact-approved brand mapping covers 0.34% of Indonesian records, too sparse for that use.

## Provenance

Source commit, size, and checksum: [data source and licensing](02_data_source.md). Metric definitions: [reproduction guide](09_reproduction.md). Claim-to-evidence trace: [claim lineage](10_claim_lineage.md). Generated results and caveats: [Stage 7 findings](07_stage7_findings_and_recommendations.md).

**Approval requested:** adopt decisions 1–3 as standing guidance, and decide whether to scope decision 4 for the next budget cycle.