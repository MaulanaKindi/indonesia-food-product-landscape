import json
import hashlib
from functools import lru_cache
from pathlib import Path

import pandas as pd

from support_pinned_inputs import TAXONOMY_FILE, TAXONOMY_SHA256

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK_FILE = (
    PROJECT_ROOT / "data" / "reference" / "category_reporting_group_framework.csv"
)
ANCHOR_FILE = (
    PROJECT_ROOT
    / "data"
    / "mappings"
    / "category_reporting_group_anchor_candidates.csv"
)
CROSSWALK_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "profiling"
    / "category_reporting_group_candidate_crosswalk.csv"
)
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "profiling"
UNMATCHED_PRIORITY_LIMIT = 1_000
EXPECTED_TAXONOMY_SHA256 = TAXONOMY_SHA256


def main() -> None:
    for input_file in (
        TAXONOMY_FILE,
        FRAMEWORK_FILE,
        ANCHOR_FILE,
        CROSSWALK_FILE,
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
    crosswalk = pd.read_csv(CROSSWALK_FILE, keep_default_na=False)
    required_crosswalk_columns = {
        "source_category_tag",
        "records_with_tag",
        "taxonomy_match_status",
        "taxonomy_name_en",
        "known_parent_tags",
        "taxonomy_min_depth",
        "taxonomy_max_depth",
        "multiple_parent_paths",
        "matched_anchor_tags",
        "candidate_group_ids",
        "candidate_group_labels",
        "proposed_group_id",
        "proposed_group_label",
        "assignment_status",
        "comparison_role",
        "manual_disposition",
        "manual_reporting_group_id",
    }
    missing = required_crosswalk_columns - set(crosswalk.columns)
    if missing:
        raise ValueError(
            f"Candidate crosswalk is missing required columns: {sorted(missing)}"
        )
    validate_reporting_group_references(framework, anchors, crosswalk)
    if crosswalk["source_category_tag"].duplicated().any():
        raise ValueError("Candidate crosswalk contains duplicate source tags.")
    if anchors["anchor_tag"].duplicated().any():
        raise ValueError(
            "Each taxonomy anchor must appear once in the review audit input."
        )
    if not anchors["review_status"].eq("candidate_only").all():
        raise ValueError(
            "Anchor review queues only accept anchors marked candidate_only."
        )

    parents_by_tag = {
        tag: taxonomy_entry.get("parents", [])
        for tag, taxonomy_entry in taxonomy.items()
    }
    missing_parents = sorted(
        {
            parent
            for parents in parents_by_tag.values()
            for parent in parents
            if parent not in taxonomy
        }
    )
    if missing_parents:
        raise ValueError(
            "Taxonomy has parent references missing from the pinned snapshot: "
            f"{missing_parents[:10]}"
        )

    @lru_cache(maxsize=None)
    def ancestors(tag: str) -> frozenset[str]:
        result = {tag}
        for parent in parents_by_tag[tag]:
            result.update(ancestors(parent))
        return frozenset(result)

    crosswalk_by_tag = crosswalk.set_index("source_category_tag")
    anchor_audit = build_anchor_audit(
        taxonomy=taxonomy,
        anchors=anchors,
        crosswalk=crosswalk,
        crosswalk_by_tag=crosswalk_by_tag,
        parents_by_tag=parents_by_tag,
        ancestors=ancestors,
    )
    ambiguous_queue = build_ambiguous_queue(crosswalk)
    residual_queue = build_residual_queue(
        crosswalk=crosswalk,
        ancestors=ancestors,
    )
    unmatched_queue = build_unmatched_queue(
        taxonomy=taxonomy,
        crosswalk=crosswalk,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    anchor_audit.to_csv(
        OUTPUT_DIR / "category_reporting_group_anchor_review.csv",
        index=False,
    )
    ambiguous_queue.to_csv(
        OUTPUT_DIR / "category_reporting_group_ambiguous_review.csv",
        index=False,
    )
    residual_queue.to_csv(
        OUTPUT_DIR / "category_reporting_group_residual_review.csv",
        index=False,
    )
    unmatched_queue.to_csv(
        OUTPUT_DIR / "category_reporting_group_unmatched_priority_review.csv",
        index=False,
    )

    unmatched_assignments = int(
        crosswalk.loc[
            crosswalk["assignment_status"].eq("unmatched_taxonomy"),
            "records_with_tag",
        ].sum()
    )
    queued_unmatched_assignments = int(unmatched_queue["records_with_tag"].sum())
    print("Category reporting-group review queues completed.")
    print(f"Anchor candidates for review: {len(anchor_audit):,}")
    print(f"Ambiguous tags for review: {len(ambiguous_queue):,}")
    print(f"Residual tags for review: {len(residual_queue):,}")
    print(
        f"Unmatched high-frequency tags queued: {len(unmatched_queue):,} "
        f"({queued_unmatched_assignments:,} / {unmatched_assignments:,} "
        "unmatched tag-record assignments)"
    )
    print(f"Outputs saved to: {OUTPUT_DIR}")


def validate_reporting_group_references(
    framework: pd.DataFrame,
    anchors: pd.DataFrame,
    crosswalk: pd.DataFrame,
) -> None:
    """Fail early when candidate IDs or labels drift from the reference framework."""
    required_framework_columns = {"group_id", "reporting_group"}
    missing = required_framework_columns - set(framework.columns)
    if missing:
        raise ValueError(
            f"Reporting-group framework is missing columns: {sorted(missing)}"
        )
    if framework["group_id"].isna().any() or framework["reporting_group"].isna().any():
        raise ValueError("Reporting-group framework contains blank IDs or labels.")
    if framework["group_id"].duplicated().any():
        raise ValueError("Reporting-group framework contains duplicate group IDs.")
    if framework["reporting_group"].duplicated().any():
        raise ValueError("Reporting-group framework contains duplicate labels.")

    labels_by_id = framework.set_index("group_id")["reporting_group"].to_dict()
    valid_ids = set(labels_by_id)
    unknown_anchor_ids = sorted(set(anchors["group_id"]) - valid_ids)
    if unknown_anchor_ids:
        raise ValueError(
            "Anchor candidates reference reporting groups absent from the "
            f"framework: {unknown_anchor_ids}"
        )

    for row in crosswalk.itertuples(index=False):
        for id_column, label_column, label_name in (
            ("candidate_group_ids", "candidate_group_labels", "candidate"),
            ("proposed_group_id", "proposed_group_label", "proposed"),
        ):
            _validate_group_id_label_pairs(
                _split_group_values(getattr(row, id_column)),
                _split_group_values(getattr(row, label_column)),
                labels_by_id,
                tag=row.source_category_tag,
                label_name=label_name,
            )

        manual_group_ids = _split_group_values(row.manual_reporting_group_id)
        unknown_manual_ids = sorted(set(manual_group_ids) - valid_ids)
        if unknown_manual_ids:
            raise ValueError(
                f"Tag {row.source_category_tag!r} references manual reporting "
                f"groups absent from the framework: {unknown_manual_ids}."
            )


def _validate_group_id_label_pairs(
    group_ids: list[str],
    labels: list[str],
    labels_by_id: dict[str, str],
    *,
    tag: str,
    label_name: str,
) -> None:
    if len(group_ids) != len(labels):
        raise ValueError(
            f"{label_name.title()} group IDs and labels do not align for tag {tag!r}."
        )
    for group_id, label in zip(group_ids, labels, strict=True):
        if group_id not in labels_by_id:
            raise ValueError(
                f"Unknown {label_name} reporting group {group_id!r} for tag {tag!r}."
            )
        if labels_by_id[group_id] != label:
            raise ValueError(
                f"{label_name.title()} label {label!r} does not match framework "
                f"label {labels_by_id[group_id]!r} for {group_id!r}."
            )


def _split_group_values(value: object) -> list[str]:
    if pd.isna(value) or not str(value).strip():
        return []
    return [part.strip() for part in str(value).split("|") if part.strip()]


def build_anchor_audit(
    taxonomy: dict,
    anchors: pd.DataFrame,
    crosswalk: pd.DataFrame,
    crosswalk_by_tag: pd.DataFrame,
    parents_by_tag: dict[str, list[str]],
    ancestors,
) -> pd.DataFrame:
    known_anchors = set(parents_by_tag)
    unknown = sorted(set(anchors["anchor_tag"]) - known_anchors)
    if unknown:
        raise ValueError(f"Candidate anchors are absent from taxonomy: {unknown}")

    observed_tags = crosswalk.loc[
        crosswalk["taxonomy_match_status"].eq("exact_tag_match"),
        "source_category_tag",
    ].tolist()
    rows = []
    for anchor in anchors.itertuples(index=False):
        descendant_tags = [
            tag for tag in observed_tags if anchor.anchor_tag in ancestors(tag)
        ]
        descendant_rows = crosswalk_by_tag.loc[descendant_tags]
        descendant_assignments = int(descendant_rows["records_with_tag"].sum())
        ambiguous_rows = descendant_rows.loc[
            descendant_rows["assignment_status"].eq("multiple_group_candidate")
        ]
        single_rows = descendant_rows.loc[
            descendant_rows["assignment_status"].eq("single_group_candidate")
        ]
        anchor_row = (
            crosswalk_by_tag.loc[anchor.anchor_tag]
            if anchor.anchor_tag in crosswalk_by_tag.index
            else None
        )
        taxonomy_entry = taxonomy[anchor.anchor_tag]
        rows.append(
            {
                "anchor_tag": anchor.anchor_tag,
                "group_id": anchor.group_id,
                "taxonomy_name_en": taxonomy_entry.get("name", {}).get("en", ""),
                "known_parent_tags": " | ".join(parents_by_tag[anchor.anchor_tag]),
                "anchor_observed_assignments": (
                    int(anchor_row["records_with_tag"]) if anchor_row is not None else 0
                ),
                "observed_descendant_tags_including_anchor": len(descendant_rows),
                "observed_descendant_tag_record_assignments": (descendant_assignments),
                "descendant_tags_with_single_group_candidate": len(single_rows),
                "descendant_assignments_with_single_group_candidate": int(
                    single_rows["records_with_tag"].sum()
                ),
                "descendant_tags_with_multiple_group_candidates": len(ambiguous_rows),
                "descendant_assignments_with_multiple_group_candidates": int(
                    ambiguous_rows["records_with_tag"].sum()
                ),
                "candidate_rationale": anchor.candidate_rationale,
                "review_status": "pending_manual_review",
                "review_note": "",
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values(["group_id", "anchor_tag"])
        .reset_index(drop=True)
    )


def build_ambiguous_queue(crosswalk: pd.DataFrame) -> pd.DataFrame:
    ambiguous = crosswalk.loc[
        crosswalk["assignment_status"].eq("multiple_group_candidate")
    ].copy()
    ambiguous["review_priority"] = ambiguous["records_with_tag"].map(
        lambda count: "P1" if count >= 5_000 else ("P2" if count >= 1_000 else "P3")
    )
    ambiguous["review_question"] = (
        "Choose the appropriate group or retain multiple assignments; do not "
        "resolve solely from broad parent paths."
    )
    ambiguous["review_decision"] = ""
    ambiguous["review_note"] = ""
    return ambiguous.sort_values(
        ["review_priority", "records_with_tag", "source_category_tag"],
        ascending=[True, False, True],
    )


def build_residual_queue(
    crosswalk: pd.DataFrame,
    ancestors,
) -> pd.DataFrame:
    residual = crosswalk.loc[
        crosswalk["assignment_status"].eq("other_residual_candidate")
    ].copy()
    observed = crosswalk.loc[
        crosswalk["taxonomy_match_status"].eq("exact_tag_match")
    ].set_index("source_category_tag")
    observed_tags = observed.index.tolist()
    descendant_counts = []
    descendant_assignments = []
    for tag in residual["source_category_tag"]:
        descendants = [
            observed_tag
            for observed_tag in observed_tags
            if tag in ancestors(observed_tag)
        ]
        descendant_counts.append(len(descendants))
        descendant_assignments.append(
            int(observed.loc[descendants, "records_with_tag"].sum())
        )
    residual["observed_descendant_tag_count"] = descendant_counts
    residual["observed_descendant_tag_record_assignments"] = descendant_assignments
    residual["review_priority"] = residual["records_with_tag"].map(
        lambda count: "P1" if count >= 10_000 else ("P2" if count >= 1_000 else "P3")
    )
    residual["review_question"] = (
        "Determine whether this broad or orthogonal taxonomy node belongs in a "
        "primary group, should remain excluded, or needs a separate rule."
    )
    residual["review_decision"] = ""
    residual["review_note"] = ""
    return residual.sort_values(
        ["review_priority", "records_with_tag", "source_category_tag"],
        ascending=[True, False, True],
    )


def build_unmatched_queue(
    taxonomy: dict,
    crosswalk: pd.DataFrame,
) -> pd.DataFrame:
    unmatched = crosswalk.loc[
        crosswalk["assignment_status"].eq("unmatched_taxonomy")
    ].copy()
    suffix_to_tags: dict[str, list[str]] = {}
    for taxonomy_tag in taxonomy:
        if ":" not in taxonomy_tag:
            continue
        suffix = taxonomy_tag.split(":", 1)[1].casefold()
        suffix_to_tags.setdefault(suffix, []).append(taxonomy_tag)

    unmatched["tag_suffix"] = unmatched["source_category_tag"].map(
        lambda tag: tag.split(":", 1)[1].casefold() if ":" in tag else tag.casefold()
    )
    unmatched["exact_suffix_taxonomy_candidates"] = [
        " | ".join(
            candidate
            for candidate in suffix_to_tags.get(row.tag_suffix, [])
            if candidate != row.source_category_tag
        )
        for row in unmatched.itertuples(index=False)
    ]
    unmatched = unmatched.sort_values(
        ["records_with_tag", "source_category_tag"],
        ascending=[False, True],
    ).head(UNMATCHED_PRIORITY_LIMIT)
    unmatched["review_priority"] = unmatched["records_with_tag"].map(
        lambda count: "P1" if count >= 10_000 else ("P2" if count >= 1_000 else "P3")
    )
    unmatched["review_question"] = unmatched["exact_suffix_taxonomy_candidates"].map(
        lambda candidates: (
            "Check whether the same suffix is a valid language/tag alias; "
            "exact suffix similarity is only a lead, not proof."
            if candidates
            else (
                "Check source vintage, spelling, non-food classification, and "
                "whether exclusion or an explicit alias is justified."
            )
        )
    )
    unmatched["review_decision"] = ""
    unmatched["review_note"] = ""
    return unmatched


if __name__ == "__main__":
    main()
