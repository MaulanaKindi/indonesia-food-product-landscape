import json
import hashlib
from functools import lru_cache
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_FILE = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "off_categories_taxonomy_2026-10-25.json"
)
CATEGORY_PROFILE_FILE = (
    PROJECT_ROOT / "outputs" / "profiling" / "category_tag_profile.csv"
)
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "profiling"
TAXONOMY_SOURCE_URL = (
    "https://static.openfoodfacts.org/data/taxonomies/categories.json"
)
EXPECTED_TAXONOMY_SHA256 = (
    "EB03AEFABAE4C6269B5FBC3E89160F8DA84CA3300A53787E27EAB5FE2D1020D5"
)


def main() -> None:
    if not TAXONOMY_FILE.is_file():
        raise FileNotFoundError(f"Category taxonomy file not found: {TAXONOMY_FILE}")
    if not CATEGORY_PROFILE_FILE.is_file():
        raise FileNotFoundError(
            f"Category tag profile not found: {CATEGORY_PROFILE_FILE}. "
            "Run scripts/05_category_brand_profile.py first."
        )

    taxonomy_bytes = TAXONOMY_FILE.read_bytes()
    taxonomy_sha256 = hashlib.sha256(taxonomy_bytes).hexdigest().upper()
    if taxonomy_sha256 != EXPECTED_TAXONOMY_SHA256:
        raise ValueError(
            "Pinned category taxonomy checksum does not match the documented "
            f"snapshot. Expected {EXPECTED_TAXONOMY_SHA256}; "
            f"found {taxonomy_sha256}."
        )

    taxonomy = json.loads(taxonomy_bytes)
    category_profile = pd.read_csv(CATEGORY_PROFILE_FILE, dtype={"source_value": str})
    required_columns = {"source_value", "records_with_value"}
    missing_columns = required_columns - set(category_profile.columns)
    if missing_columns:
        raise ValueError(
            "Category tag profile is missing required columns: "
            f"{sorted(missing_columns)}"
        )
    if category_profile["source_value"].duplicated().any():
        raise ValueError("Category tag profile contains duplicate source tags.")

    parents_by_tag = {
        tag: taxonomy_entry.get("parents", [])
        for tag, taxonomy_entry in taxonomy.items()
    }
    missing_parent_tags = sorted(
        {
            parent
            for parents in parents_by_tag.values()
            for parent in parents
            if parent not in taxonomy
        }
    )

    @lru_cache(maxsize=None)
    def taxonomy_depth(tag: str) -> tuple[int, int]:
        known_parents = [
            parent
            for parent in parents_by_tag[tag]
            if parent in taxonomy
        ]
        if not known_parents:
            return 0, 0

        parent_depths = [taxonomy_depth(parent) for parent in known_parents]
        return (
            1 + min(minimum for minimum, _ in parent_depths),
            1 + max(maximum for _, maximum in parent_depths),
        )

    tag_rows = []
    for row in category_profile.itertuples(index=False):
        source_tag = row.source_value
        record_count = int(row.records_with_value)
        taxonomy_entry = taxonomy.get(source_tag)
        if taxonomy_entry is None:
            tag_rows.append(
                {
                    "source_category_tag": source_tag,
                    "records_with_tag": record_count,
                    "taxonomy_match_status": "not_found_in_pinned_taxonomy",
                    "canonical_category_tag": "",
                    "name_en": "",
                    "name_source_language": "",
                    "known_parent_tags": "",
                    "taxonomy_min_depth": None,
                    "taxonomy_max_depth": None,
                    "multiple_parent_paths": False,
                }
            )
            continue

        names = taxonomy_entry.get("name", {})
        name_en = names.get("en", "")
        name_source_language = (
            "en" if name_en else (next(iter(names), "") if names else "")
        )
        minimum_depth, maximum_depth = taxonomy_depth(source_tag)
        tag_rows.append(
            {
                "source_category_tag": source_tag,
                "records_with_tag": record_count,
                "taxonomy_match_status": "exact_tag_match",
                "canonical_category_tag": source_tag,
                "name_en": name_en,
                "name_source_language": name_source_language,
                "known_parent_tags": " | ".join(
                    parent
                    for parent in parents_by_tag[source_tag]
                    if parent in taxonomy
                ),
                "taxonomy_min_depth": minimum_depth,
                "taxonomy_max_depth": maximum_depth,
                "multiple_parent_paths": minimum_depth != maximum_depth,
            }
        )

    tag_audit = pd.DataFrame(tag_rows)
    matched = tag_audit["taxonomy_match_status"].eq("exact_tag_match")
    matched_assignments = int(tag_audit.loc[matched, "records_with_tag"].sum())
    total_assignments = int(tag_audit["records_with_tag"].sum())
    matched_tags = int(matched.sum())
    unmatched_tags = len(tag_audit) - matched_tags
    matched_multi_depth = tag_audit.loc[
        matched & tag_audit["multiple_parent_paths"], "records_with_tag"
    ]
    summary = pd.DataFrame(
        [
            {
                "taxonomy_source_url": TAXONOMY_SOURCE_URL,
                "taxonomy_snapshot_date": "2026-10-25",
                "taxonomy_nodes": len(taxonomy),
                "missing_parent_tag_references": len(
                    missing_parent_tags
                ),
                "observed_source_tags": len(tag_audit),
                "matched_source_tags": matched_tags,
                "unmatched_source_tags": unmatched_tags,
                "matched_tag_record_assignments": matched_assignments,
                "unmatched_tag_record_assignments": (
                    total_assignments - matched_assignments
                ),
                "total_tag_record_assignments": total_assignments,
                "matched_assignment_coverage_pct": round(
                    100.0 * matched_assignments / total_assignments, 4
                )
                if total_assignments
                else 0,
                "matched_tags_with_multiple_depth_paths": int(
                    tag_audit.loc[matched, "multiple_parent_paths"].sum()
                ),
                "assignments_on_tags_with_multiple_depth_paths": int(
                    matched_multi_depth.sum()
                ),
            }
        ]
    )
    depth_profile = (
        tag_audit.loc[matched]
        .groupby(
            ["taxonomy_min_depth", "taxonomy_max_depth"],
            dropna=False,
        )
        .agg(
            distinct_source_tags=("source_category_tag", "count"),
            tag_record_assignments=("records_with_tag", "sum"),
        )
        .reset_index()
        .sort_values(["taxonomy_min_depth", "taxonomy_max_depth"])
    )
    missing_parent_profile = pd.DataFrame(
        {"parent_tag_missing_from_taxonomy": missing_parent_tags},
        columns=["parent_tag_missing_from_taxonomy"],
    )

    tag_audit.to_csv(OUTPUT_DIR / "category_taxonomy_tag_audit.csv", index=False)
    summary.to_csv(
        OUTPUT_DIR / "category_taxonomy_coverage_summary.csv",
        index=False,
    )
    depth_profile.to_csv(
        OUTPUT_DIR / "category_taxonomy_depth_profile.csv",
        index=False,
    )
    missing_parent_profile.to_csv(
        OUTPUT_DIR / "category_taxonomy_missing_parents.csv",
        index=False,
    )

    result = summary.iloc[0]
    print("Category taxonomy audit completed.")
    print(
        f"Exact tag matches: {result['matched_source_tags']:,} / "
        f"{result['observed_source_tags']:,} observed source tags"
    )
    print(
        f"Matched tag-assignment coverage: "
        f"{result['matched_assignment_coverage_pct']:.4f}%"
    )
    print(
        "Matched tags with multiple taxonomy depth paths: "
        f"{result['matched_tags_with_multiple_depth_paths']:,}"
    )
    print(f"Outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
