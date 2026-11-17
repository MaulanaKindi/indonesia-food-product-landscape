# Decision Memo — What This Data Supports

**Prepared:** 2026-11-17 · **Status:** proposed, for owner approval · **Scope:** one pinned Open Food Facts snapshot (commit and SHA-256 in [the source record](02_data_source.md))

This memo turns the study's findings into decisions with evidence, confidence, effort, and an owner. It introduces no new number: every figure below is a tracked value that `scripts/18_check_headline_numbers.py` and `scripts/support_check_docs_consistency.py` assert against the committed CSVs, or is reproducible with the script named beside it.

## Decisions

| # | Decision or action | Evidence (tracked) | Confidence | Effort (est.) | Suggested owner | Horizon |
|---|---|---|---|---|---|---|
| 1 | Use Open Food Facts as a **supplementary** signal for catalogue coverage and field completeness | 12.2% of 9,118 Indonesian records carry a category tag; brand text on 38.8%, numeric nutrition on 31.0% ([field readiness](../README.md#field-readiness)) | High for describing this snapshot; low for generalising to the market | S — reuse committed outputs, no new acquisition | Analytics lead | Now |
| 2 | Do **not** use it alone for competitor share, market size, sales, demand, or availability | The source has no sales, revenue, or demand fields and is a collaborative snapshot, not a census ([analysis specification](06_analysis_specification.md)) | High | None — an avoidance, not a task | Analytics lead | Standing |
| 3 | Treat category assignments as **provisional** | Candidate-derived assignments cover 788/9,118 records (8.64%) against 113 (1.24%) approved-only; 106,211 tags remain taxonomy-unmatched ([data profile](03_data_profile.md)) | Medium-high | M — scheduled human review of category and brand mappings | Data steward | Next planning cycle |
| 4 | Commission sales, panel, or retail-scan data before any share or demand claim | The gap is structural, not a processing issue; see [what would change these conclusions](#what-would-change-these-conclusions) | High that the gap exists | L — new licence, ingestion, and validation | Commercial data owner | Next budget cycle |

Effort is a planning estimate, not a commitment: **S** fits the existing backlog, **M** needs scheduled review capacity, **L** needs new procurement or budget.

**Cost basis.** No currency amount appears here, deliberately: the relevant vendor programmes are quote-only and publish no list price, so any figure would be unverifiable rather than informative. The **L** band on decision 4 therefore means procurement effort, not a known spend. Owners are roles rather than individuals, so the table stays valid when people change.

## What each decision can reach

| # | Addressable universe in this snapshot | Consequence |
|---|---|---|
| 1 | 1,111 Indonesian records carry a category tag; 788 receive a candidate-derived group | Category analysis can speak to at most 8.64% of Indonesian records today |
| 2 | No sales, revenue, or demand field exists | The ceiling is zero by construction, not by processing quality |
| 3 | 113 records under approved-only; 106,211 tags remain taxonomy-unmatched | The approved view is narrow; the candidate view is broader but provisional |
| 4 | Not bounded by this source | Any share or demand claim needs a new input first |

## Is the coverage gap more than noise?

The README calls Indonesia similar to Malaysia and below the Philippines and Singapore. That wording is checked rather than asserted: a two-proportion test on the tagged-record counts, with a 95% Wald interval for the difference in percentage points.

| Comparison | Difference (pp) | 95% CI (pp) | p-value | Reading |
|---|---:|---:|---:|---|
| ID vs MY | +0.87 | [-0.11, +1.86] | 0.0833 | not distinguishable |
| ID vs PH | -4.54 | [-5.56, -3.53] | <0.0001 | clearly lower |
| ID vs SG | -5.12 | [-6.07, -4.17] | <0.0001 | clearly lower |
| ID vs TH | -50.44 | [-51.56, -49.33] | <0.0001 | clearly lower |

Every conclusion holds at the Bonferroni-adjusted threshold of 0.0125 for four comparisons. Reproduce with `python scripts/support_coverage_comparison.py`; `tests/test_coverage_comparison.py` asserts these values, so a drift in the source CSV fails the build.

Two limits apply. Records are treated as independent trials, but one product code can appear in several countries and records are not a random sample of any market, so the p-values describe this snapshot rather than a population. And the test judges coverage differences only: it says nothing about whether the tagged products are the right ones.

## How far the audit evidence reaches

The AI-assisted audit judged 97 of 130 candidate group pairs correct on a fixed 150-record Indonesian sample, with exact group-set agreement of 61/150 (40.7%). The 48-case online follow-up (30 supported, 18 partial, 36 source URLs, 29 exact product-code matches) is targeted and non-random. These are diagnostics, not human ground truth, and they do not support a population precision estimate. Decision 3 is provisional for that reason, not because the mapping work is incomplete in principle.

## What would change these conclusions

- **A newer pinned snapshot.** Coverage describes one commit; a later commit can move the 12.2% headline without any change in data quality. How far the public dataset has already moved is measurable with `scripts/support_check_pin_liveness.py`, which reports drift without implying that the published figures are wrong.
- **Sales, panel, or retail-scan data.** This is the only input that converts recorded products into products sold, and would make share or demand decisions answerable.
- **An approved taxonomy and reviewed mappings.** Closing the 106,211 unmatched tags and the 838 multi-group tags would move decision 3 from provisional to approved, and would change which reporting groups are usable at all.
- **A random-sample audit with intervals.** A probability sample would replace the targeted diagnostic with an estimate that carries a confidence interval, which is what a precision claim requires.

## Non-claims

- Not a market-size, sales, demand, share, or availability estimate.
- Not evidence that products are sold or traded between the five countries; shared product codes are not market overlap.
- Not a brand-landscape or concentration (HHI) input: exact-approved brand mapping covers 0.34% of Indonesian records, too sparse for that use.

## Provenance

Source commit, size, and checksum: [data source and licensing](02_data_source.md). Metric definitions: [reproduction guide](09_reproduction.md). Claim-to-evidence trace: [claim lineage](10_claim_lineage.md). Generated results and caveats: [Stage 7 findings](07_stage7_findings_and_recommendations.md).

**Approval requested:** adopt decisions 1–3 as standing guidance, confirm the role owners named above, and decide whether to scope decision 4 for the next budget cycle.