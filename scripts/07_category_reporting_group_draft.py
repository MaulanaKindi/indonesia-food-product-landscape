import hashlib
import json
from pathlib import Path

import pandas as pd

from support_category_coverage import (
    build_country_coverage,
    validate_manual_group_evidence,
)
from support_category_crosswalk import build_crosswalk_artifacts
from support_pinned_inputs import TAXONOMY_FILE, TAXONOMY_SHA256


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANUAL_DISPOSITION_FILE = (
    PROJECT_ROOT / "data" / "mappings" / "category_tag_manual_dispositions.csv"
)
MANUAL_GROUP_DECISION_FILE = (
    PROJECT_ROOT
    / "data"
    / "mappings"
    / "category_tag_reporting_group_manual_decisions.csv"
)
FRAMEWORK_FILE = (
    PROJECT_ROOT / "data" / "reference" / "category_reporting_group_framework.csv"
)
ANCHOR_FILE = (
    PROJECT_ROOT
    / "data"
    / "mappings"
    / "category_reporting_group_anchor_candidates.csv"
)
COUNTRY_MAPPING_FILE = PROJECT_ROOT / "data" / "mappings" / "country_tag_mapping.csv"
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "food.parquet"
CATEGORY_PROFILE_FILE = (
    PROJECT_ROOT / "outputs" / "profiling" / "category_tag_profile.csv"
)
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "profiling"
EXPECTED_TAXONOMY_SHA256 = TAXONOMY_SHA256


def main() -> None:
    for input_file in (
        TAXONOMY_FILE,
        FRAMEWORK_FILE,
        ANCHOR_FILE,
        MANUAL_DISPOSITION_FILE,
        MANUAL_GROUP_DECISION_FILE,
        COUNTRY_MAPPING_FILE,
        CATEGORY_PROFILE_FILE,
        DATA_FILE,
    ):
        if not input_file.is_file():
            raise FileNotFoundError(f"Required input not found: {input_file}")

    taxonomy_bytes = TAXONOMY_FILE.read_bytes()
    taxonomy_sha256 = hashlib.sha256(taxonomy_bytes).hexdigest().upper()
    if taxonomy_sha256 != EXPECTED_TAXONOMY_SHA256:
        raise ValueError(
            "Pinned category taxonomy checksum does not match the documented "
            f"snapshot. Expected {EXPECTED_TAXONOMY_SHA256}; "
            f"found {taxonomy_sha256}."
        )
    taxonomy = json.loads(taxonomy_bytes)
    framework = pd.read_csv(FRAMEWORK_FILE, dtype=str)
    anchors = pd.read_csv(ANCHOR_FILE, dtype=str)
    manual_dispositions = pd.read_csv(
        MANUAL_DISPOSITION_FILE,
        dtype=str,
        keep_default_na=False,
    )
    manual_group_decisions = pd.read_csv(
        MANUAL_GROUP_DECISION_FILE,
        dtype=str,
        keep_default_na=False,
    )
    country_mapping = pd.read_csv(
        COUNTRY_MAPPING_FILE,
        dtype=str,
        encoding="utf-8-sig",
        keep_default_na=False,
    )
    category_profile = pd.read_csv(
        CATEGORY_PROFILE_FILE,
        dtype={"source_value": str},
    )

    required_framework_columns = {
        "group_id",
        "reporting_group",
        "display_order",
        "framework_status",
    }
    required_disposition_columns = {
        "source_category_tag",
        "disposition",
        "review_status",
        "decision_basis",
        "canonical_category_tag",
        "reviewed_on",
    }
    required_group_decision_columns = {
        "source_category_tag",
        "reporting_group_id",
        "review_status",
        "decision_basis",
        "supporting_exact_tags",
        "reviewed_on",
    }
    required_anchor_columns = {
        "anchor_tag",
        "group_id",
        "candidate_rationale",
        "review_status",
    }
    required_profile_columns = {"source_value", "records_with_value"}
    required_country_columns = {
        "source_country_tag",
        "iso_alpha2",
        "country_name",
        "mapping_status",
    }
    for label, frame, required in (
        ("framework", framework, required_framework_columns),
        ("anchor candidates", anchors, required_anchor_columns),
        (
            "manual category dispositions",
            manual_dispositions,
            required_disposition_columns,
        ),
        (
            "manual reporting-group decisions",
            manual_group_decisions,
            required_group_decision_columns,
        ),
        ("country mapping", country_mapping, required_country_columns),
        ("category profile", category_profile, required_profile_columns),
    ):
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"{label} is missing columns: {sorted(missing)}")

    if framework["group_id"].duplicated().any():
        raise ValueError("Reporting-group framework contains duplicate group IDs.")
    if category_profile["source_value"].duplicated().any():
        raise ValueError("Category profile contains duplicate source tags.")
    unknown_dispositions = set(manual_dispositions["source_category_tag"]) - set(
        category_profile["source_value"]
    )
    if unknown_dispositions:
        raise ValueError(
            "Manual category dispositions reference tags absent from the profile: "
            f"{sorted(unknown_dispositions)}"
        )
    if anchors.duplicated(["anchor_tag", "group_id"]).any():
        raise ValueError("Anchor candidates contain duplicate tag/group pairs.")
    if manual_dispositions["source_category_tag"].duplicated().any():
        raise ValueError("Manual category dispositions contain duplicate source tags.")
    if manual_group_decisions["source_category_tag"].duplicated().any():
        raise ValueError(
            "Manual reporting-group decisions contain duplicate source tags."
        )
    if not manual_group_decisions["review_status"].eq("approved").all():
        raise ValueError("Manual reporting-group decisions must be approved.")
    if not manual_group_decisions["decision_basis"].str.strip().ne("").all():
        raise ValueError(
            "Manual reporting-group decisions must include a decision basis."
        )
    if not manual_dispositions["review_status"].eq("approved").all():
        raise ValueError("Manual category dispositions must be approved.")
    allowed_dispositions = {"exclude_placeholder", "exclude_non_food"}
    invalid_dispositions = (
        set(manual_dispositions["disposition"]) - allowed_dispositions
    )
    if invalid_dispositions:
        raise ValueError(
            f"Unsupported manual category dispositions: {sorted(invalid_dispositions)}"
        )
    if not manual_dispositions["canonical_category_tag"].eq("").all():
        raise ValueError("Excluded category tags must not have a canonical tag.")
    if country_mapping["source_country_tag"].duplicated().any():
        raise ValueError("Country-tag mapping contains duplicate source tags.")
    if not anchors["review_status"].eq("candidate_only").all():
        raise ValueError("All anchor candidates must remain marked candidate_only.")

    group_labels = dict(zip(framework["group_id"], framework["reporting_group"]))
    if "other_unclassified" not in group_labels:
        raise ValueError("Reporting-group framework must include other_unclassified.")
    unknown_groups = set(anchors["group_id"]) - set(group_labels)
    unknown_decision_groups = set(manual_group_decisions["reporting_group_id"]) - set(
        group_labels
    )
    if unknown_groups:
        raise ValueError(
            f"Anchor candidates reference unknown group IDs: {sorted(unknown_groups)}"
        )
    if unknown_decision_groups:
        raise ValueError(
            "Manual reporting-group decisions reference unknown group IDs: "
            f"{sorted(unknown_decision_groups)}"
        )
    unknown_group_decisions = set(manual_group_decisions["source_category_tag"]) - set(
        category_profile["source_value"]
    )
    if unknown_group_decisions:
        raise ValueError(
            "Manual reporting-group decisions reference tags absent from the "
            f"category profile: {sorted(unknown_group_decisions)}"
        )
    manual_group_evidence_counts = validate_manual_group_evidence(
        manual_group_decisions,
        taxonomy,
        category_profile,
    )
    overlapping_decisions = set(manual_group_decisions["source_category_tag"]) & set(
        manual_dispositions["source_category_tag"]
    )
    if overlapping_decisions:
        raise ValueError(
            "Tags cannot have both a category exclusion and a reporting-group "
            f"decision: {sorted(overlapping_decisions)}"
        )

    crosswalk, group_coverage, status_summary, total_assignments = (
        build_crosswalk_artifacts(
            taxonomy=taxonomy,
            anchors=anchors,
            manual_dispositions=manual_dispositions,
            manual_group_decisions=manual_group_decisions,
            category_profile=category_profile,
            framework=framework,
            group_labels=group_labels,
            manual_group_evidence_counts=manual_group_evidence_counts,
        )
    )
    country_group_coverage, country_overlap = build_country_coverage(
        crosswalk=crosswalk,
        country_mapping=country_mapping,
        framework=framework,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    crosswalk.to_csv(
        OUTPUT_DIR / "category_reporting_group_candidate_crosswalk.csv",
        index=False,
    )
    group_coverage.to_csv(
        OUTPUT_DIR / "category_reporting_group_candidate_coverage.csv",
        index=False,
    )
    status_summary.to_csv(
        OUTPUT_DIR / "category_reporting_group_candidate_status_summary.csv",
        index=False,
    )
    country_group_coverage.to_csv(
        OUTPUT_DIR / "category_reporting_group_candidate_country_coverage.csv",
        index=False,
    )
    country_overlap.to_csv(
        OUTPUT_DIR / "category_reporting_group_candidate_country_overlap.csv",
        index=False,
    )

    print("Category reporting-group candidate crosswalk completed.")
    print(
        f"Observed tags: {len(crosswalk):,}; "
        f"tag-record assignments: {total_assignments:,}"
    )
    for row in status_summary.itertuples(index=False):
        print(
            f"{row.assignment_status}: {row.distinct_source_tags:,} tags, "
            f"{row.tag_record_assignments:,} tag-record assignments "
            f"({row.pct_of_all_category_tag_assignments:.4f}%)"
        )
    print(f"Outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
