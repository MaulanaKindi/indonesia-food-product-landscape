"""Build candidate category-to-reporting-group assignments from reviewed inputs."""

from functools import lru_cache

import pandas as pd


def build_crosswalk_artifacts(
    taxonomy: dict,
    anchors: pd.DataFrame,
    manual_dispositions: pd.DataFrame,
    manual_group_decisions: pd.DataFrame,
    category_profile: pd.DataFrame,
    framework: pd.DataFrame,
    group_labels: dict[str, str],
    manual_group_evidence_counts: dict[tuple[str, str], int],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, int]:
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

    unknown_anchors = sorted(set(anchors["anchor_tag"]) - set(taxonomy))
    if unknown_anchors:
        raise ValueError(
            f"Anchor candidates are not present in the pinned taxonomy: "
            f"{unknown_anchors}"
        )

    anchor_groups: dict[str, set[str]] = {}
    for row in anchors.itertuples(index=False):
        anchor_groups.setdefault(row.anchor_tag, set()).add(row.group_id)
    dispositions_by_tag = manual_dispositions.set_index("source_category_tag").to_dict(
        orient="index"
    )
    group_decisions_by_tag = manual_group_decisions.set_index(
        "source_category_tag"
    ).to_dict(orient="index")

    @lru_cache(maxsize=None)
    def taxonomy_depth(tag: str) -> tuple[int, int]:
        if not parents_by_tag[tag]:
            return 0, 0
        parent_depths = [taxonomy_depth(parent) for parent in parents_by_tag[tag]]
        return (
            1 + min(value[0] for value in parent_depths),
            1 + max(value[1] for value in parent_depths),
        )

    @lru_cache(maxsize=None)
    def ancestors(tag: str, active_path: tuple[str, ...] = ()) -> frozenset[str]:
        if tag in active_path:
            raise ValueError(f"Cycle detected in taxonomy at tag {tag}.")
        next_path = active_path + (tag,)
        result = {tag}
        for parent in parents_by_tag[tag]:
            result.update(ancestors(parent, next_path))
        return frozenset(result)

    crosswalk_rows = []
    assignment_totals: dict[str, int] = {}
    status_totals: dict[str, list[int]] = {}
    total_assignments = int(category_profile["records_with_value"].sum())

    for row in category_profile.itertuples(index=False):
        source_tag = row.source_value
        assignments = int(row.records_with_value)
        taxonomy_entry = taxonomy.get(source_tag)
        candidate_groups: set[str] = set()
        matched_anchors: list[str] = []
        manual_disposition = dispositions_by_tag.get(source_tag)
        manual_group_decision = group_decisions_by_tag.get(source_tag)

        if manual_disposition is not None:
            status = manual_disposition["disposition"]
            reason = manual_disposition["decision_basis"]
            taxonomy_match_status = (
                "exact_tag_match"
                if taxonomy_entry is not None
                else "not_found_in_pinned_taxonomy"
            )
            name_en = (
                taxonomy_entry.get("name", {}).get("en", "")
                if taxonomy_entry is not None
                else ""
            )
            parent_tags = (
                parents_by_tag[source_tag] if taxonomy_entry is not None else []
            )
            if taxonomy_entry is not None:
                minimum_depth, maximum_depth = taxonomy_depth(source_tag)
                multiple_parent_paths = minimum_depth != maximum_depth
            else:
                minimum_depth = None
                maximum_depth = None
                multiple_parent_paths = False
        elif taxonomy_entry is None:
            taxonomy_match_status = "not_found_in_pinned_taxonomy"
            name_en = ""
            parent_tags = []
            multiple_parent_paths = False
            minimum_depth = None
            maximum_depth = None
            if manual_group_decision is not None:
                status = "manual_group_assignment"
                candidate_groups.add(manual_group_decision["reporting_group_id"])
                reason = manual_group_decision["decision_basis"]
            else:
                status = "unmatched_taxonomy"
                reason = (
                    "Source tag is not an exact match in the pinned taxonomy; "
                    "leave unresolved for manual review."
                )
        else:
            taxonomy_match_status = "exact_tag_match"
            name_en = taxonomy_entry.get("name", {}).get("en", "")
            parent_tags = parents_by_tag[source_tag]
            candidate_ancestors = ancestors(source_tag)
            matched_anchors = sorted(candidate_ancestors.intersection(anchor_groups))
            for anchor_tag in matched_anchors:
                candidate_groups.update(anchor_groups[anchor_tag])

            minimum_depth, maximum_depth = taxonomy_depth(source_tag)
            multiple_parent_paths = minimum_depth != maximum_depth

            if manual_group_decision is not None:
                selected_group = manual_group_decision["reporting_group_id"]
                if selected_group not in candidate_groups:
                    raise ValueError(
                        f"Manual group {selected_group} for {source_tag} is not "
                        "among the groups suggested by its exact taxonomy ancestry."
                    )
                status = "manual_group_assignment"
                reason = manual_group_decision["decision_basis"]
            elif len(candidate_groups) == 1:
                status = "single_group_candidate"
                reason = (
                    "One reporting group is suggested by exact taxonomy ancestry "
                    "anchors; candidate only, not an approved mapping."
                )
            elif len(candidate_groups) > 1:
                status = "multiple_group_candidate"
                reason = (
                    "Taxonomy ancestry reaches anchors in multiple reporting groups; "
                    "retain as ambiguous for manual review."
                )
            else:
                candidate_groups.add("other_unclassified")
                status = "other_residual_candidate"
                reason = (
                    "No domain-group anchor occurs in the exact taxonomy ancestry; "
                    "Other / unclassified is a provisional residual candidate."
                )

        candidate_group_ids = sorted(candidate_groups)
        if status == "unmatched_taxonomy":
            candidate_group_ids = []
        candidate_group_labels = [
            group_labels[group_id] for group_id in candidate_group_ids
        ]
        proposed_group_id = (
            manual_group_decision["reporting_group_id"]
            if manual_group_decision is not None
            else (
                candidate_group_ids[0]
                if len(candidate_group_ids) == 1
                and status in {"single_group_candidate", "other_residual_candidate"}
                else ""
            )
        )
        proposed_group_label = (
            group_labels[proposed_group_id] if proposed_group_id else ""
        )
        if proposed_group_id:
            assignment_totals[proposed_group_id] = (
                assignment_totals.get(proposed_group_id, 0) + assignments
            )

        status_values = status_totals.setdefault(status, [0, 0])
        status_values[0] += 1
        status_values[1] += assignments

        crosswalk_rows.append(
            {
                "source_category_tag": source_tag,
                "records_with_tag": assignments,
                "taxonomy_match_status": taxonomy_match_status,
                "taxonomy_name_en": name_en,
                "known_parent_tags": " | ".join(parent_tags),
                "taxonomy_min_depth": minimum_depth,
                "taxonomy_max_depth": maximum_depth,
                "multiple_parent_paths": multiple_parent_paths,
                "matched_anchor_tags": " | ".join(matched_anchors),
                "candidate_group_ids": " | ".join(candidate_group_ids),
                "candidate_group_labels": " | ".join(candidate_group_labels),
                "proposed_group_id": proposed_group_id,
                "proposed_group_label": proposed_group_label,
                "assignment_status": status,
                "comparison_role": (
                    "primary_candidate"
                    if status in {"single_group_candidate", "manual_group_assignment"}
                    else (
                        "diagnostic_only"
                        if status == "other_residual_candidate"
                        else (
                            "excluded"
                            if status.startswith("exclude_")
                            else "unresolved"
                        )
                    )
                ),
                "manual_disposition": (
                    manual_disposition["disposition"]
                    if manual_disposition is not None
                    else (
                        "assign_reporting_group"
                        if manual_group_decision is not None
                        else ""
                    )
                ),
                "manual_reporting_group_id": (
                    manual_group_decision["reporting_group_id"]
                    if manual_group_decision is not None
                    else ""
                ),
                "manual_evidence_tags": (
                    manual_group_decision["supporting_exact_tags"]
                    if manual_group_decision is not None
                    else ""
                ),
                "manual_evidence_cooccurrence_rows": (
                    " | ".join(
                        f"{tag}={manual_group_evidence_counts[(source_tag, tag)]}"
                        for tag in manual_group_decision["supporting_exact_tags"].split(
                            "|"
                        )
                        if tag
                    )
                    if manual_group_decision is not None
                    else ""
                ),
                "candidate_rationale": reason,
            }
        )

    crosswalk = pd.DataFrame(crosswalk_rows)
    group_coverage_rows = []
    for row in framework.sort_values(
        "display_order",
        key=pd.to_numeric,
    ).itertuples(index=False):
        group_id = row.group_id
        group_rows = crosswalk.loc[crosswalk["proposed_group_id"].eq(group_id)]
        assignments = assignment_totals.get(group_id, 0)
        group_coverage_rows.append(
            {
                "group_id": group_id,
                "reporting_group": row.reporting_group,
                "comparison_role": (
                    "diagnostic_only"
                    if group_id == "other_unclassified"
                    else "primary_candidate"
                ),
                "candidate_source_tags": len(group_rows),
                "candidate_tag_record_assignments": assignments,
                "pct_of_all_category_tag_assignments": round(
                    100.0 * assignments / total_assignments, 4
                )
                if total_assignments
                else 0,
                "coverage_unit_note": (
                    "Sum of per-tag record frequencies; not distinct records or "
                    "products and may include multiple tags from one record."
                ),
            }
        )
    group_coverage = pd.DataFrame(group_coverage_rows)

    status_summary_rows = []
    for status, (tag_count, assignments) in sorted(status_totals.items()):
        status_summary_rows.append(
            {
                "assignment_status": status,
                "distinct_source_tags": tag_count,
                "tag_record_assignments": assignments,
                "pct_of_all_category_tag_assignments": round(
                    100.0 * assignments / total_assignments, 4
                )
                if total_assignments
                else 0,
            }
        )
    status_summary = pd.DataFrame(status_summary_rows)
    return crosswalk, group_coverage, status_summary, total_assignments
