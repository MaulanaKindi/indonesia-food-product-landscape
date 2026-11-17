# Audit State

- **Phase:** 4 (Closed) — **GATE 6**: released as v1.1 from `main` @ `86619d6`; final score 8.75/10; no work remaining
- **Branch:** `audit/quality-improvement` (merged through PR #2, then deleted with the other merged branches)
- **Baseline:** `2ce13f6` (tag `audit-baseline`, the last commit before this audit started)
- **Audience lens:** Market Intelligence Analyst (60-second first look)
- **Time budget:** half-day, several sessions

## Baseline scores (commit 2ce13f6)

| # | Dimension | Weight | Score | Target |
|---|---|---:|---:|---:|
| D1 | Problem clarity & 60-second impression | 15% | 6 | ≥9 |
| D2 | Analytical integrity & limitations | 20% | 9 | ≥9 |
| D3 | Documentation & navigability | 10% | 8 | ≥8 |
| D4 | Reproducibility | 15% | 7 | ≥8 |
| D5 | Code & SQL quality | 15% | 8 | ≥8 |
| D6 | Validation & testing | 10% | 7 | ≥8 |
| D7 | Communication of results | 10% | 6 | ≥8 |
| D8 | Repo hygiene | 5% | 9 | ≥9 |

**Weighted overall: 7.50 / 10.**

## Final scores (after P0, P1-1, P1-5/P1-6)

| # | Dimension | Weight | Score | Target |
|---|---|---|---:|---|
| D1 | Problem clarity & 60-second impression | 15% | 9.5 | ≥9 |
| D2 | Analytical integrity & limitations | 20% | 9 | ≥9 |
| D3 | Documentation & navigability | 10% | 8.5 | ≥8 |
| D4 | Reproducibility | 15% | 8.5 | ≥8 |
| D5 | Code & SQL quality | 15% | 8 | ≥8 |
| D6 | Validation & testing | 10% | 9 | ≥8 |
| D7 | Communication of results | 10% | 8.5 | ≥8 |
| D8 | Repo hygiene | 5% | 9 | ≥9 |

**Weighted overall: 8.75 / 10.** Every dimension meets its target.

## Backlog status

| ID | Item | Status | Commit |
|---|---|---|---|
| P0-0 | Headline-number assertion script | done | `288dcd1` |
| P0-1 | README 60-second rewrite (static only) | done | `570dcef` |
| P0-2 | Data-free quick-look docs + chart one-liner | done | `77868bb` |
| P1-1 | Add 2 charts from tracked CSVs | done | `8ad05ff` |
| P1-2 | Chart captions + move chart up | done | `c5b275e` |
| P1-3 | Friendly preflight guard in run_all.py | done | `fa41464` |
| P1-4 | Plain-language glossary box | done | `570dcef` |
| P1-5a | Renderers: country names, derived shares, new role labels, re-render script | done | `46f3f04` |
| P1-5b | README static rewrite + docs/01, 02, 09, 10 + static-string guard | done | `bd7dbfa`, `e9633da`, `5d2977a` |
| P1-5c | docs/07 static, docs/08, docs/99, docs/00 | done | `2930f0a` |
| P1-6 | CI runs script 18; renderer tests; pin-test fix; generated role terminology | done | `fdf454e`, `e4aab0e`, `6da0ef8`, `755f9c7` |
| P2-1 | Chart palette accessibility | done, folded into P1-1 | — |
| P2-2 | GitHub metadata (manual) | done - description re-applied, topics verified, preview confirmed via `og:image` (2026-11-17) | `1509c45` |
| P2-3 | Optional data-free demo script | won't do - covered by the `docs/09` quick look and `support_rerender_generated_sections.py` | — |
| P2-4 | Protect `main` and document the policy | done (branch protection applied, `CONTRIBUTING.md` updated) | `5cb6a0a` |
| P2-5 | Assignment-rate two-proportion test (candidate vs approved-only) | won't do - both groups are the same 9,118 records; +7.40 pp, 95% CI 6.78 to 8.02, McNemar exact p = 1.3e-203, so the result is trivial and carries no decision value | — |
| P2-6 | Decision memo: cost basis and owner wording | done - no currency stated (vendor programmes are quote-only), owners confirmed as roles, approval line clarified | — |
| P2-7 | Pin liveness and drift check | done - `support_check_pin_liveness.py` plus tests; pin resolved and head 24 days newer on 2026-11-17; network-bound, excluded from CI | — |

## Verification notes (this session)
- `scripts/18_check_headline_numbers.py`: 101 assertions pass for 5 countries (ruff clean).
- `support_check_docs_consistency.py`: PASS — "README and Stage 7 generated sections match validated CSV outputs." (README trimmed from 170 to 144 lines by dropping one SQL example to satisfy the 150-line presentation limit.)
- `README.md`, `docs/09_reproduction.md`, `scripts/run_all.py`: static edits only; generated README blocks untouched; no headline numbers changed.
- Commits (per item, per-file `git add`): `288dcd1` (P0-0), `570dcef` (P0-1+P1-4), `c5b275e` (P1-2), `77868bb` (P0-2), `fa41464` (P1-3).
- `mypy` was not installed in this venv at the time (audit constraint: no installs); it is installed now and `mypy scripts` passes (see the P1-1 notes).

## Verification notes (P1-5)
- `46f3f04` (P1-5a): renderers now emit full country names, plain-language role labels, derived share-of-all-records columns; README country table lost the brand column; AI headline bullet shortened. New `scripts/support_rerender_generated_sections.py` re-renders generated blocks from tracked CSVs only (no DB, no charts, no Stage 16).
- `bd7dbfa`, `e9633da`, `5d2977a` (P1-5b): README static rewrite (bottom line first, plain language, business lens, fit-for-purpose, method quality, SQL blocks moved to docs/09); docs/01 glossary (old→new role names), docs/02 pin pointer, docs/09 three SQL queries, docs/10 derived-metric lineage; script 18 static-string guard.
- Final verification: docs-consistency PASS; `18_check_headline_numbers.py` = 109 assertions OK; `ruff check scripts` + `ruff format --check scripts` clean; README = 142 lines (≤150).
- Method-quality wording verified against `category_mapping_semantic_audit_summary.csv` (150 records, 130 pairs, 97/16/8/9, 61 exact-set) and `category_mapping_online_evidence_audit.csv` (48 rows, 30 supported, 18 partial).

## Verification notes (P1-1, this session)
- `scripts/support_generate_visuals.py` now emits five charts: the two existing ones plus `largest_category_group.png` (largest candidate-derived group per country, share of all country rows) and `brand_mapping_gap.png` (raw brand text vs exact-approved mapping). Both read only tracked CSVs already used by the other charts.
- Palette: countries use an Okabe-Ito subset (`#009E73`, `#56B4E9`, `#E69F00`, `#CC79A7`, `#D55E00`); the two-series charts use `#0072B2` (broad) and `#999999` (strict), deliberately disjoint from the country hues so a colour never means two different things across charts. The low-contrast teal pair (`#0B6E69`/`#72B7B2`) is gone.
- New `tests/test_generated_visuals.py` (5 tests): all five PNGs written, valid PNG signature, >5 KB; palette distinctness regression guard; chart follows the largest-share CSV row (mutation-verified); `KeyError` when `group_source_rows` or the `Brand text` metric is missing.
- README: figures renumbered 1–5 with captions (150 lines, at the ≤150 limit); `docs/09` now says "five static charts".
- Images regenerated from tracked CSVs only; no headline number changed; `data_readiness_scorecard.png` byte-identical (no code change in that function).
- Local venv synced from `requirements-dev.txt`: `mypy scripts` clean across 40 files; `pytest -q --cov=scripts` → 41 passed, 16% overall coverage (pipeline scripts need the 8 GB snapshot), `support_generate_visuals.py` 89%.

## Gate
- **Current:** GATE 6 — released. v1.1 published 2026-11-16 from `main` @ `86619d6`; both PRs merged with CI green; merged remote and local branches removed; tags `audit-baseline` and `v1.1` remain.
- **Release path:** PR #1 (`release/v1.1-stabilization` → `main`, rebase-merged to `baa52d5`) landed the stabilization branch, then PR #2 (`audit/quality-improvement` → `main`, merge commit `86619d6`) landed this audit. The two branches had edited the same documentation, so the merge was resolved deliberately: every conflicted file was compared on both sides and the audit version kept, because it already contained the stabilization content plus the audit changes.
- **History note:** because PR #1 was rebase-merged, `main` contains both the rewritten stabilization commits (`149cb7d`..`baa52d5`) and the original ones (`4ef43a3`..`2ce13f6`) reached through the audit merge. Their trees are identical, so no content is duplicated in the final state.
- **Remaining:** none. `main` is protected (required `python-and-sql` check, no force pushes, no deletion, enforced for administrators), P2-2 is closed, and P2-3 (data-free demo script) is closed as won't do because the quick-look docs and `scripts/support_rerender_generated_sections.py` already cover it. Local venv sync is done, so `mypy`, `pytest-cov`, and `pre-commit` all run locally.
- **Presentation limit:** README is exactly at the 150-line gate (`support_check_docs_consistency.py` fails above 150). Further additions must be offset by trimming prose, not by removing figures or captions.
- **Known intentional divergence:** `docs/04` and `docs/06` keep the original spec terms ("focal", "contextual peers", "coverage contrast") because they are approved records; `docs/01` §6.7 maps them to the plain-language README terms.
- **Coverage note:** renderer logic is covered by `tests/test_generated_report_rendering.py` and chart generation by `tests/test_generated_visuals.py`; mutation checks confirmed the derived-share test fails when the denominator switches to tagged records, and the largest-group test fails when the plotted CSV row changes.

## Decisions
- 1A — target role: Market Intelligence Analyst.
- 2B — time: half-day, several sessions.
- 3A — priority: README / 60-second first, then the rest.
- Do not hand-edit generated README/Stage 7 blocks; change renderers (`support_render_readme.py`, `support_render_stage7.py`) and keep `support_check_docs_consistency.py` passing.
- Do not run `scripts/11_*` or `scripts/16_*`.
- Phase 1 focus: D1, D4, D7 (brief on strong dimensions).

## Resolved questions
- Release hygiene (push/PR/tag) required an explicit user request; it was performed on 2026-11-17 as PR #1, PR #2, and tag `v1.1`.
- `docs/audit/` stays tracked. It is the record of how the published v1.1 state was scored and verified, which is what makes the 8.75/10 claim auditable rather than asserted.