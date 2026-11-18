# Client One-Pager — Indonesia Food Product Landscape

**Prepared by:** [MaulanaKindi] · [maulanakindi@gmail.com] · [https://www.linkedin.com/in/maulanakinditamami/]

## The problem

A market team wants to describe the Indonesian food market from open product data. Before committing budget to a data program, it needs three answers: how much product data actually exists, how completely that data is described, and which decisions the data can support.

## Approach

1. **Pin the source.** Use one fixed Open Food Facts snapshot, identified by commit and SHA-256, so every number can be traced and reproduced later.
2. **Measure coverage, not quality.** For each country, count records and the share carrying a category tag, brand text, nutrition, ingredients, packaging, and labels.
3. **Separate two mapping views.** Report a broad automated view (candidate-derived) beside a strict reviewed view (approved-only), so the reader can see how much the answer depends on the mapping choice.

## Result

| Country | Records | Category-tagged |
|---|---:|---:|
| Indonesia (ID) — study country | 9,118 | 12.2% |
| Malaysia (MY) | 7,426 | 11.3% |
| Philippines (PH) | 9,176 | 16.7% |
| Singapore (SG) | 11,986 | 17.3% |
| Thailand (TH) — high-coverage contrast | 11,343 | 62.6% |

Indonesia sits close to Malaysia, below the Philippines and Singapore, and far below Thailand. A two-proportion test with 95% intervals finds Indonesia statistically indistinguishable from Malaysia (+0.87 pp, 95% CI -0.11 to +1.86) and clearly below the other three, including after a Bonferroni adjustment for four comparisons.

## Decision implications

- **Use** Open Food Facts as a supplementary signal for catalog coverage and field completeness.
- **Do not use it alone** for market size, share, sales, demand, or availability. The source has no sales or demand fields and is not a census.
- **Treat category assignments as provisional.** Broad mapping covers 8.64% of all Indonesian records; strict mapping covers 1.24%.
- **Commission sales, panel, or retail-scan data** before any share or demand claim.

## Limits

- Collaborative data, not a census: contributor and product selection are skewed.
- Coverage is not market size. A well-tagged country is not a bigger market.
- The mapping audit is a targeted diagnostic, not human ground truth: 97 of 130 candidate assignments were judged correct on a non-random sample.
- One pinned snapshot. A newer commit can move the numbers without any change in data quality.
- Exact-approved brand mapping covers 0.34% of Indonesian records, too sparse for brand-landscape claims.

## Reproduce in minutes

No 8 GB download is needed. Every headline number and all five charts are committed and asserted in CI.

```
git clone https://github.com/MaulanaKindi/indonesia-food-product-landscape
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
python scripts/support_check_docs_consistency.py
python scripts/18_check_headline_numbers.py
```

The full workflow, including the pinned download, is in [the reproduction guide](09_reproduction.md). Claim-to-evidence tracing is in [the claim lineage](10_claim_lineage.md).