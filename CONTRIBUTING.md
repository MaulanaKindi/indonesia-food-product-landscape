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
python scripts/18_check_headline_numbers.py       # headline numbers vs tracked CSVs
```

`pre-commit run --all-files` runs the ruff lint and format hooks (installed via `pre-commit install`).

One check needs the network and is therefore not part of CI:

```bash
python scripts/support_check_pin_liveness.py  # pinned revision still resolvable upstream
```

It prints whether the pinned commit still resolves and how many days the public dataset has advanced, then exits non-zero if the pin is gone.

## Tests and coverage

The test suite is synthetic and does not require the pinned dataset. Coverage is reported by CI:

```bash
python -m pytest -q --cov=scripts --cov-report=term-missing
```

A global coverage threshold is not enforced because most pipeline scripts require the pinned Open Food Facts snapshot and run as integration steps; coverage is tracked for visibility and to prevent regression on the unit-tested helpers.

## Generated documentation

The README and Stage 7 generated sections are produced by the pipeline (`scripts/run_all.py`, `scripts/16_refresh_harmonized_analysis.py`) from validated CSV outputs. Do not edit generated blocks by hand; refresh them through the pipeline and verify with `scripts/support_check_docs_consistency.py`.

## Branch and review policy

`main` is protected and is the only long-lived branch.

- Changes land through a pull request. Direct pushes, force pushes, and branch deletion on `main` are rejected, including for administrators.
- Merging requires the `python-and-sql` check from the Quality checks workflow to pass, and the branch must be up to date with `main` first.
- Pull request reviews are not required, so a maintainer can merge their own green pull request.
- Release tags (`v1.0`, `v1.1`) are cut from `main` and published with notes recorded in [`docs/08_github_release_metadata.md`](docs/08_github_release_metadata.md).