# Contributing

## Setup

Requires Python 3.13.

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
```

## Checks

All checks mirror CI (`.github/workflows/quality.yml`). Run them before committing:

```bash
ruff check scripts tests          # lint
ruff format --check scripts tests # formatting
mypy scripts                      # type check
python -m pytest -q               # tests
sqlfluff lint sql/02_validate_relational_database.sql sql/05_validate_five_country_database.sql --dialect duckdb --rules CP01
python scripts/support_check_docs_consistency.py  # generated docs vs validated CSVs
```

`pre-commit run --all-files` runs the ruff lint and format hooks (installed via `pre-commit install`).

## Tests and coverage

The test suite is synthetic and does not require the pinned dataset. Coverage is reported by CI:

```bash
python -m pytest -q --cov=scripts --cov-report=term-missing
```

A global coverage threshold is not enforced because most pipeline scripts require the pinned Open Food Facts snapshot and run as integration steps; coverage is tracked for visibility and to prevent regression on the unit-tested helpers.

## Generated documentation

The README and Stage 7 generated sections are produced by the pipeline (`scripts/run_all.py`, `scripts/16_refresh_harmonized_analysis.py`) from validated CSV outputs. Do not edit generated blocks by hand; refresh them through the pipeline and verify with `scripts/support_check_docs_consistency.py`.