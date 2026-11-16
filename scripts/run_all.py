"""Reproduce the canonical five-country analysis from its pinned source."""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_FILE = PROJECT_ROOT / "data" / "raw" / "food.parquet"
PINNED_INPUT_SCRIPTS = {
    "support_fetch_pinned_taxonomy.py",
    "00_download_snapshot.py",
}
PIPELINE = (
    "support_fetch_pinned_taxonomy.py",
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


def preflight_snapshot() -> None:
    if not SNAPSHOT_FILE.exists():
        print(
            f"{SNAPSHOT_FILE} not found; step 00 will download the pinned "
            "7.98 GB snapshot.",
            flush=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replace-scoped-database",
        action="store_true",
        help="Replace the canonical database only after a new build passes validation.",
    )
    args = parser.parse_args()

    preflight_snapshot()

    for script_name in PIPELINE:
        command = [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / script_name),
        ]
        if (
            script_name == "11_build_relational_database.py"
            and args.replace_scoped_database
        ):
            command.append("--replace-existing")
        if script_name == "16_refresh_harmonized_analysis.py":
            command.extend(("--skip-mapping-refresh", "--skip-brand-profile-refresh"))
        print(f"\nRunning {script_name}...", flush=True)
        try:
            subprocess.run(command, cwd=PROJECT_ROOT, check=True)
        except subprocess.CalledProcessError as error:
            if script_name in PINNED_INPUT_SCRIPTS:
                print(
                    f"\n{script_name} failed while preparing pinned inputs. "
                    "If you are offline, connect to the network and re-run. "
                    "To inspect the published results without any download, see "
                    "docs/09_reproduction.md (Quick look without the 8 GB download).",
                    file=sys.stderr,
                )
            raise SystemExit(error.returncode) from error
    print("\nFive-country analysis completed successfully.")


if __name__ == "__main__":
    main()
