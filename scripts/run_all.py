"""Reproduce the canonical five-country analysis from its pinned source."""

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PIPELINE = (
    "00_download_snapshot.py",
    "01_dataset_profile.py",
    "02_quality_checks.py",
    "03_country_profile.py",
    "04_normalized_country_profile.py",
    "05_category_brand_profile.py",
    "06_category_taxonomy_audit.py",
    "07_category_reporting_group_draft.py",
    "08_category_reporting_group_review_queues.py",
    "09_nonfood_scope_audit.py",
    "11_build_relational_database.py",
    "16_refresh_harmonized_analysis.py",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replace-scoped-database",
        action="store_true",
        help="Replace the canonical database only after a new build passes validation.",
    )
    args = parser.parse_args()

    for script_name in PIPELINE:
        command = [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / script_name),
        ]
        if script_name == "11_build_relational_database.py" and args.replace_scoped_database:
            command.append("--replace-existing")
        print(f"\nRunning {script_name}...", flush=True)
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)
    print("\nFive-country analysis completed successfully.")


if __name__ == "__main__":
    main()
