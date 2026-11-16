# Audit Report — Baseline

- **Baseline:** commit `2ce13f6` (tag `audit-baseline`), branch `audit/quality-improvement`
- **Audience lens:** Market Intelligence Analyst (hiring manager, ~60-second first look, then code inspection)
- **Method:** read-only inspection of README, `docs/`, `scripts/`, `sql/`, tracked `outputs/` CSVs, `requirements*.txt`, `.gitignore`, `.gitattributes`, `LICENSE`, git log/status. Pipeline scripts (incl. 11 and 16) were **not** run. `support_check_docs_consistency.py` was **not** run (needs approval); CI runs it on push/PR.

## Score table (baseline)

| # | Dimension | Weight | Score | Target | Gap |
|---|---|---:|---:|---:|---|
| D1 | Problem clarity & 60-second first impression | 15% | 6 | ≥9 | −3 |
| D2 | Analytical integrity, methodology, limitations honesty | 20% | 9 | ≥9 | 0 |
| D3 | Documentation quality & navigability | 10% | 8 | ≥8 | 0 |
| D4 | Reproducibility (clone → install → run) | 15% | 7 | ≥8 | −1 |
| D5 | Code & SQL quality | 15% | 8 | ≥8 | 0 |
| D6 | Validation & testing | 10% | 7 | ≥8 | −1 |
| D7 | Communication of results (visuals, clarity) | 10% | 6 | ≥8 | −2 |
| D8 | Repo hygiene | 5% | 9 | ≥9 | 0 |

**Weighted overall = 7.50 / 10** (target ≥8.5; no dimension <8; D1 & D2 ≥9).

## Findings (focused on D1, D4, D7; strong dimensions brief)

### D1 — 6/10 (biggest lever)
- **Evidence:** `README.md` lines 1–48. Subtitle (line 3) is clear and honest; headline numbers are present (lines 9–28); images at 30/32/48.
- **What works:** honest framing ("not a measure of food-market size or sales"), specific numbers, five-findings + decision memo.
- **Gaps (why 6):**
  1. The TL;DR "Question" (line 7) is a dense, jargon-heavy sentence ("contextual peers", "higher-coverage contrast") — a 60-second reader must decode coined terms.
  2. The 4th headline bullet (line 13, AI + online audit) is a wall of qualifiers (candidate assignments, exact-reviewed, group-set agreement, online follow-up) — highest cognitive load, placed above the fold.
  3. No plain orientation ("What this is / who it's for / how to read it") and no captions telling the reader how to read the three charts.
  4. No "see results without the 8 GB download" pointer; the reader cannot tell there is a data-free view.
  5. Reading level is high; many hyphenated coinages (candidate-derived, approved-only, exact-approved, coverage contrast) are never defined inline.
- **Next level (→9):** crisp 2–3 line orientation, plain-language headline, a small glossary of the 4 coined terms, chart captions, and a data-free quick-look pointer. Static sections only (generated blocks untouched).

### D4 — 7/10
- **Evidence:** `scripts/run_all.py` (one-command runner, cross-platform via `sys.executable` + `PROJECT_ROOT`), `requirements.txt` (exact pins), `docs/09_reproduction.md` (Windows + macOS/Linux), pinned snapshot + SHA-256, `00_download_snapshot.py` (verifies existing, downloads if absent, temp-file + cleanup).
- **What works:** one-command pipeline, exact pins, cross-platform instructions, checksum verification, tests run without the snapshot.
- **Gaps (why 7):**
  1. No friendly preflight when `data/raw/food.parquet` is missing offline: `00` attempts a network download (raw `URLError` if offline); downstream scripts assume the file exists (`FileNotFoundError`).
  2. No data-free quick path: charts are buildable **only from tracked CSVs** (`support_generate_visuals.py` reads `outputs/analysis/stage6_*.csv` and `outputs/profiling/data_readiness_scorecard.csv`), but no documented one-liner or "view results without the raw data" section.
  3. "Reproduce" lives at the bottom of README, not near the top.
- **Next level (→8.5):** friendly preflight guard in `run_all.py` (clear message + non-zero exit), plus a documented chart-regeneration one-liner from tracked CSVs.

### D7 — 6/10
- **Evidence:** `scripts/support_generate_visuals.py` (3 charts), `docs/img/{category_coverage,category_assignment_coverage,data_readiness_scorecard}.png`, README embeds at 30/32/48.
- **What works:** clean charts, takeaway-style titles, data labels, consistent palette.
- **Gaps (why 6):**
  1. Only coverage/readiness visuals; no visual for the brand-mapping gap, contributor concentration, or code overlap — all available in tracked CSVs.
  2. No captions / "how to read" in README.
  3. Charts sit mid-README, not near the top.
  4. No documented data-free regeneration.
- **Next level (→8.5):** add 2 charts from tracked CSVs (brand text vs exact-approved mapping; contributor concentration or country-code overlap), add captions, move one chart near the top.

### D2 — 9/10 (strong, brief)
Exceptional honesty: candidate vs approved-only split, duplicate-code limitation, mutable-taxonomy caveat, AI audit "not human ground truth", non-food A/B sensitivity, historical mapping discrepancy disclosed, "coverage not market size". Meets target; no change needed.

### D3 — 8/10 (strong, brief)
13 numbered, cross-linked docs incl. claim-to-evidence lineage (`docs/10_claim_lineage.md`). Dense/long (`docs/03` 504 lines) but navigable. Meets target.

### D5 — 8/10 (strong, brief)
39 scripts with `NN_` ordering + `support_` helpers, type hints, docstrings, ruff strict + mypy + pre-commit clean, `PROJECT_ROOT`-relative paths. Meets target.

### D6 — 7/10
- **Evidence:** `tests/` (4 files, 29 synthetic tests), CI (pytest/ruff/mypy/sqlfluff/docs-consistency/coverage), 15 candidate + 11 Stage 6 checks.
- **Gap:** no independent headline-number assertion script (`scripts/18_check_headline_numbers.py` absent) — docs-consistency catches generated drift, but nothing asserts the published headline numbers against tracked CSVs. Coverage 11% (documented).
- **Next level (→8.5):** add the headline-number check (P0-0).

### D8 — 9/10 (strong, brief)
Comprehensive `.gitignore`, `.gitattributes` LF, MIT `LICENSE`, conventional commits, tags `v1.0` + `audit-baseline`, no stray tracked files (`HANDOFF_FOR_CHATGPT.md` already deleted). Untracked local clutter is gitignored or out of scope.

## Number consistency (spot-check vs tracked CSVs)
All headline numbers match tracked outputs — no drift found:
- ID 9,118 rows / 1,111 tagged / 12.1847% — `stage6_country_scope.csv`, `stage5_country_peer_evidence.csv`.
- ID 788 candidate-derived / 113 approved-only — `stage5_country_peer_evidence.csv` (`source_rows_with_primary_candidate_group`, `source_rows_with_approved_group_decision`).
- ID 31 exact-approved brand (0.3400%) — `stage5_country_peer_evidence.csv`, `data_readiness_scorecard.csv`.
- MY/PH/SG/TH rows, coverage, candidate/approved, brand counts — match README tables and `stage5_country_peer_evidence.csv`.

## Backlog and status

| ID | Item | Files | Effort | Result-impact risk | Status | Commit |
|---|---|---|---|---|---|---|
| **P0-0** | Read-only headline-number assertion script | `scripts/18_check_headline_numbers.py` | S | None | done | `288dcd1` |
| **P0-1** | README 60-second rewrite (static sections) | `README.md` | M | None | done | `570dcef`, `bd7dbfa`, `07bb5fe` |
| **P0-2** | Data-free quick-look docs + chart one-liner | `README.md`, `docs/09_reproduction.md` | S | None | done | `77868bb` |
| **P1-1** | Add 2 charts from tracked CSVs + accessible palette | `support_generate_visuals.py`, `docs/img/*.png` | M | None | awaiting approval | — |
| **P1-2** | Chart captions + move one chart near top | `README.md` | S | None | done | `c5b275e` |
| **P1-3** | Friendly preflight guard when the snapshot is missing | `scripts/run_all.py` | S | Low | done | `fa41464` |
| **P1-4** | Plain-language glossary box | `README.md` | S | None | done | `570dcef` |
| **P1-5a** | Renderers: full country names, plain-language roles, derived shares, re-render script | `support_report_common.py`, `support_render_readme.py`, `support_render_stage7.py`, `18_check_headline_numbers.py`, `support_rerender_generated_sections.py` | M | None | done | `46f3f04` |
| **P1-5b** | README static rewrite + supporting docs + static-string guard | `README.md`, `docs/01`, `docs/02`, `docs/09`, `docs/10`, `18_check_headline_numbers.py` | M | None | done | `bd7dbfa`, `e9633da`, `5d2977a` |
| **P1-5c** | Static prose, architecture, release metadata, project log | `docs/07`, `docs/08`, `docs/99`, `docs/00` | S | None | done | `2930f0a`, `e4aab0e` |
| **P1-6** | CI enforcement, renderer tests, pin-test alignment | `quality.yml`, `tests/*` | S | None | done | `fdf454e`, `6da0ef8`, `755f9c7` |
| **P2-1** | Chart palette accessibility | `support_generate_visuals.py` | S | None | folded into P1-1 | — |
| **P2-2** | GitHub description/topics/social preview | manual | S | None | description done (`2930f0a`); preview upload pending | — |
| **P2-3** | Optional data-free demo script | new script | M | None | not started | — |

## Final score after implementation

| # | Dimension | Weight | Baseline | Final | Change driver |
|---|---|---:|---:|---:|---|
| D1 | Problem clarity & 60-second impression | 15% | 6 | 9.5 | Bottom line first, supported decisions, plain language, glossary, fit-for-purpose, business lens |
| D2 | Analytical integrity & limitations | 20% | 9 | 9 | Unchanged; limitations preserved verbatim in substance |
| D3 | Documentation & navigability | 10% | 8 | 8.5 | Glossary in `docs/01`, three SQL queries in `docs/09`, derived-metric lineage, architecture updated |
| D4 | Reproducibility | 15% | 7 | 8.5 | Data-free quick-look path, friendly preflight, re-render without DB, CI-enforced checks |
| D5 | Code & SQL quality | 15% | 8 | 8 | Unchanged; mypy not runnable locally, so no claim of improvement |
| D6 | Validation & testing | 10% | 7 | 9 | 109-assertion guard in CI plus seven renderer tests, mutation-verified |
| D7 | Communication of results | 10% | 6 | 7.5 | Captions, full country names, derived shares, fit-for-purpose; still three charts, palette unchanged |
| D8 | Repo hygiene | 5% | 9 | 9 | Unchanged; `docs/audit/` still untracked |

**Weighted overall = 8.65 / 10** (baseline 7.50).

Target check: overall ≥8.5 met; D1 and D2 ≥9 met. The single remaining miss is **D7 = 7.5 < 8**, which P1-1 closes (projected 8.5, overall ≈8.75).

**Intentional divergence:** `docs/04` and `docs/06` keep the approved specification terms ("focal", "contextual peers", "coverage contrast") because they are owner-approved records; `docs/01` §6.7 maps them to the plain-language README terms.

## Do NOT change
- Headline numbers: ID 9,118; 12.2% (12.1847%); 788 of 1,111 (70.9%); 113 (10.2%); 31 (0.34%); and all MY/PH/SG/TH figures.
- `data/mappings/*` (country/category/brand decisions), `data/reference/*` (taxonomy, framework, ISO).
- Stage 5–7 logic: `scripts/05,07,08,12,13,14,15,16`, `support_*`, `sql/*`.
- Generated README/Stage 7 blocks (edit renderers only, and only with an approved regeneration path).
- `data/raw/`, `*.parquet`, `*.duckdb`; `requirements.txt` versions; `LICENSE` + data-license split.
- `docs/06` owner decisions and `docs/03` numbers.

## Verification notes
- Numbers cross-checked against tracked CSVs — consistent; now enforced by `scripts/18_check_headline_numbers.py` (109 assertions) in CI.
- `scripts/support_check_docs_consistency.py` run and passing: "README and Stage 7 generated sections match validated CSV outputs."
- `pytest` 36 passed; `ruff check`/`ruff format --check` clean; `sqlfluff` clean.
- `mypy` and `pytest-cov` are not installed in the local audit venv, so CI is the authoritative check for those two steps.
- No pipeline script (including 11 and 16) was run; generated sections were re-rendered from tracked CSVs by `scripts/support_rerender_generated_sections.py`.