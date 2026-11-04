import hashlib
import json
from functools import lru_cache
from pathlib import Path

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_FILE = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "off_categories_taxonomy_2026-10-25.json"
)
MANUAL_DISPOSITION_FILE = (
    PROJECT_ROOT
    / "data"
    / "mappings"
    / "category_tag_manual_dispositions.csv"
)
MANUAL_GROUP_DECISION_FILE = (
    PROJECT_ROOT
    / "data"
    / "mappings"
    / "category_tag_reporting_group_manual_decisions.csv"
)
FRAMEWORK_FILE = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "category_reporting_group_framework.csv"
)
ANCHOR_FILE = (
    PROJECT_ROOT
    / "data"
    / "mappings"
    / "category_reporting_group_anchor_candidates.csv"
)
COUNTRY_MAPPING_FILE = (
    PROJECT_ROOT / "data" / "mappings" / "country_tag_mapping.csv"
)
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "food.parquet"
CATEGORY_PROFILE_FILE = (
    PROJECT_ROOT / "outputs" / "profiling" / "category_tag_profile.csv"
)
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "profiling"
EXPECTED_TAXONOMY_SHA256 = (
    "EB03AEFABAE4C6269B5FBC3E89160F8DA84CA3300A53787E27EAB5FE2D1020D5"
)


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
    unknown_dispositions = (
        set(manual_dispositions["source_category_tag"])
        - set(category_profile["source_value"])
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
            f"Unsupported manual category dispositions: "
            f"{sorted(invalid_dispositions)}"
        )
    if not manual_dispositions["canonical_category_tag"].eq("").all():
        raise ValueError("Excluded category tags must not have a canonical tag.")
    if country_mapping["source_country_tag"].duplicated().any():
        raise ValueError("Country-tag mapping contains duplicate source tags.")
    if not anchors["review_status"].eq("candidate_only").all():
        raise ValueError("All anchor candidates must remain marked candidate_only.")

    group_labels = dict(
        zip(framework["group_id"], framework["reporting_group"])
    )
    if "other_unclassified" not in group_labels:
        raise ValueError(
            "Reporting-group framework must include other_unclassified."
        )
    unknown_groups = set(anchors["group_id"]) - set(group_labels)
    unknown_decision_groups = (
        set(manual_group_decisions["reporting_group_id"]) - set(group_labels)
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
    unknown_group_decisions = (
        set(manual_group_decisions["source_category_tag"])
        - set(category_profile["source_value"])
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
    overlapping_decisions = (
        set(manual_group_decisions["source_category_tag"])
        & set(manual_dispositions["source_category_tag"])
    )
    if overlapping_decisions:
        raise ValueError(
            "Tags cannot have both a category exclusion and a reporting-group "
            f"decision: {sorted(overlapping_decisions)}"
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

    unknown_anchors = sorted(set(anchors["anchor_tag"]) - set(taxonomy))
    if unknown_anchors:
        raise ValueError(
            f"Anchor candidates are not present in the pinned taxonomy: "
            f"{unknown_anchors}"
        )

    anchor_groups: dict[str, set[str]] = {}
    for row in anchors.itertuples(index=False):
        anchor_groups.setdefault(row.anchor_tag, set()).add(row.group_id)
    dispositions_by_tag = manual_dispositions.set_index(
        "source_category_tag"
    ).to_dict(orient="index")
    group_decisions_by_tag = manual_group_decisions.set_index(
        "source_category_tag"
    ).to_dict(orient="index")

    @lru_cache(maxsize=None)
    def taxonomy_depth(tag: str) -> tuple[int, int]:
        if not parents_by_tag[tag]:
            return 0, 0
        parent_depths = [
            taxonomy_depth(parent)
            for parent in parents_by_tag[tag]
        ]
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
                parents_by_tag[source_tag]
                if taxonomy_entry is not None
                else []
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
            parent_tags: list[str] = []
            multiple_parent_paths = False
            minimum_depth = None
            maximum_depth = None
            if manual_group_decision is not None:
                status = "manual_group_assignment"
                candidate_groups.add(
                    manual_group_decision["reporting_group_id"]
                )
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
            matched_anchors = sorted(
                candidate_ancestors.intersection(anchor_groups)
            )
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
                and status
                in {"single_group_candidate", "other_residual_candidate"}
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
                    if status
                    in {"single_group_candidate", "manual_group_assignment"}
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
                        for tag in manual_group_decision[
                            "supporting_exact_tags"
                        ].split("|")
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
        group_rows = crosswalk.loc[
            crosswalk["proposed_group_id"].eq(group_id)
        ]
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


def build_country_coverage(
    crosswalk: pd.DataFrame,
    country_mapping: pd.DataFrame,
    framework: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    approved_countries = country_mapping.loc[
        country_mapping["mapping_status"].eq("approved")
    ].copy()
    incomplete_approved = approved_countries[
        approved_countries[["iso_alpha2", "country_name"]]
        .eq("")
        .any(axis=1)
    ]
    if not incomplete_approved.empty:
        raise ValueError(
            "Approved country mappings must have an ISO code and name: "
            f"{incomplete_approved['source_country_tag'].tolist()}"
        )

    category_map = crosswalk.loc[
        crosswalk["proposed_group_id"].ne(""),
        [
            "source_category_tag",
            "proposed_group_id",
            "assignment_status",
            "comparison_role",
        ],
    ].copy()
    if category_map["source_category_tag"].duplicated().any():
        raise ValueError("Candidate category crosswalk contains duplicate source tags.")

    group_labels = framework[["group_id", "reporting_group", "display_order"]].copy()
    with duckdb.connect() as connection:
        connection.register("candidate_category_map", category_map)
        connection.register("approved_country_map", approved_countries)
        connection.register("reporting_group_framework", group_labels)
        connection.execute(
            """
            CREATE TEMP TABLE source_records AS
            SELECT
                ROW_NUMBER() OVER () AS source_record_id,
                list_filter(
                    list_distinct(categories_tags),
                    lambda value: value IS NOT NULL AND trim(value) <> ''
                ) AS category_tags,
                list_filter(
                    list_distinct(countries_tags),
                    lambda value: value IS NOT NULL AND trim(value) <> ''
                ) AS country_tags
            FROM read_parquet(?)
            """,
            [str(DATA_FILE)],
        )
        coverage = connection.execute(
            """
            WITH country_records AS (
                SELECT DISTINCT
                    source.source_record_id,
                    country.iso_alpha2,
                    country.country_name,
                    len(source.category_tags) > 0 AS has_category_tags
                FROM source_records AS source
                CROSS JOIN UNNEST(source.country_tags)
                    AS country_tags(source_country_tag)
                INNER JOIN approved_country_map AS country
                    ON country_tags.source_country_tag = country.source_country_tag
            ),
            record_group_assignments AS (
                SELECT DISTINCT
                    country_records.source_record_id,
                    country_records.iso_alpha2,
                    country_records.country_name,
                    category_map.proposed_group_id,
                    category_map.assignment_status,
                    category_map.comparison_role
                FROM country_records
                INNER JOIN source_records AS source
                    USING (source_record_id)
                CROSS JOIN UNNEST(source.category_tags)
                    AS category_tags(source_category_tag)
                INNER JOIN candidate_category_map AS category_map
                    ON category_tags.source_category_tag =
                        category_map.source_category_tag
            ),
            country_totals AS (
                SELECT
                    iso_alpha2,
                    country_name,
                    COUNT(*) AS country_source_records,
                    COUNT(*) FILTER (
                        WHERE has_category_tags
                    ) AS country_records_with_category_tags
                FROM country_records
                GROUP BY iso_alpha2, country_name
            ),
            country_candidate_totals AS (
                SELECT
                    iso_alpha2,
                    COUNT(DISTINCT source_record_id)
                        AS records_with_any_primary_group
                FROM record_group_assignments
                WHERE comparison_role = 'primary_candidate'
                GROUP BY iso_alpha2
            ),
            country_diagnostic_totals AS (
                SELECT
                    iso_alpha2,
                    COUNT(DISTINCT source_record_id)
                        AS records_with_diagnostic_residual
                FROM record_group_assignments
                WHERE assignment_status = 'other_residual_candidate'
                GROUP BY iso_alpha2
            ),
            record_group_counts AS (
                SELECT
                    source_record_id,
                    iso_alpha2,
                    COUNT(DISTINCT proposed_group_id)
                        AS primary_group_count
                FROM record_group_assignments
                WHERE comparison_role = 'primary_candidate'
                GROUP BY source_record_id, iso_alpha2
            ),
            country_overlap AS (
                SELECT
                    iso_alpha2,
                    COUNT(*) FILTER (
                        WHERE primary_group_count > 1
                    ) AS records_with_multiple_primary_groups
                FROM record_group_counts
                GROUP BY iso_alpha2
            ),
            group_counts AS (
                SELECT
                    iso_alpha2,
                    proposed_group_id AS group_id,
                    COUNT(*) AS source_records_in_group
                FROM record_group_assignments
                GROUP BY iso_alpha2, proposed_group_id
            )
            SELECT
                totals.iso_alpha2,
                totals.country_name,
                groups.group_id,
                groups.reporting_group,
                CASE
                    WHEN groups.group_id = 'other_unclassified'
                        THEN 'diagnostic_only'
                    ELSE 'primary_candidate'
                END AS comparison_role,
                totals.country_source_records,
                totals.country_records_with_category_tags,
                COALESCE(candidate_totals.records_with_any_primary_group, 0)
                    AS records_with_any_primary_group,
                COALESCE(diagnostic_totals.records_with_diagnostic_residual, 0)
                    AS records_with_diagnostic_residual,
                COALESCE(group_counts.source_records_in_group, 0)
                    AS source_records_in_group,
                ROUND(
                    100.0 * COALESCE(group_counts.source_records_in_group, 0)
                    / NULLIF(totals.country_source_records, 0),
                    4
                ) AS pct_country_records_in_group,
                ROUND(
                    100.0 * COALESCE(group_counts.source_records_in_group, 0)
                    / NULLIF(totals.country_records_with_category_tags, 0),
                    4
                ) AS pct_category_tagged_records_in_group
            FROM country_totals AS totals
            CROSS JOIN reporting_group_framework AS groups
            LEFT JOIN country_candidate_totals AS candidate_totals
                USING (iso_alpha2)
            LEFT JOIN country_diagnostic_totals AS diagnostic_totals
                USING (iso_alpha2)
            LEFT JOIN group_counts
                ON group_counts.iso_alpha2 = totals.iso_alpha2
                AND group_counts.group_id = groups.group_id
            ORDER BY TRY_CAST(groups.display_order AS INTEGER), totals.iso_alpha2
            """
        ).fetchdf()
        overlap = connection.execute(
            """
            WITH country_records AS (
                SELECT DISTINCT
                    source.source_record_id,
                    country.iso_alpha2,
                    country.country_name,
                    len(source.category_tags) > 0 AS has_category_tags
                FROM source_records AS source
                CROSS JOIN UNNEST(source.country_tags)
                    AS country_tags(source_country_tag)
                INNER JOIN approved_country_map AS country
                    ON country_tags.source_country_tag = country.source_country_tag
            ),
            record_group_assignments AS (
                SELECT DISTINCT
                    country_records.source_record_id,
                    country_records.iso_alpha2,
                    category_map.proposed_group_id,
                    category_map.assignment_status,
                    category_map.comparison_role
                FROM country_records
                INNER JOIN source_records AS source
                    USING (source_record_id)
                CROSS JOIN UNNEST(source.category_tags)
                    AS category_tags(source_category_tag)
                INNER JOIN candidate_category_map AS category_map
                    ON category_tags.source_category_tag =
                        category_map.source_category_tag
            ),
            record_group_counts AS (
                SELECT
                    source_record_id,
                    iso_alpha2,
                    COUNT(DISTINCT proposed_group_id)
                        AS primary_group_count
                FROM record_group_assignments
                WHERE comparison_role = 'primary_candidate'
                GROUP BY source_record_id, iso_alpha2
            ),
            overlap_counts AS (
                SELECT
                    iso_alpha2,
                    COUNT(*) FILTER (
                        WHERE primary_group_count > 1
                    ) AS records_with_multiple_primary_groups
                FROM record_group_counts
                GROUP BY iso_alpha2
            ),
            candidate_counts AS (
                SELECT
                    iso_alpha2,
                    COUNT(DISTINCT source_record_id)
                        AS records_with_any_primary_group
                FROM record_group_assignments
                WHERE comparison_role = 'primary_candidate'
                GROUP BY iso_alpha2
            ),
            diagnostic_counts AS (
                SELECT
                    iso_alpha2,
                    COUNT(DISTINCT source_record_id)
                        AS records_with_diagnostic_residual
                FROM record_group_assignments
                WHERE assignment_status = 'other_residual_candidate'
                GROUP BY iso_alpha2
            )
            SELECT
                country.iso_alpha2,
                country.country_name,
                COUNT(*) AS country_source_records,
                COUNT(*) FILTER (
                    WHERE country.has_category_tags
                ) AS country_records_with_category_tags,
                COALESCE(candidate.records_with_any_primary_group, 0)
                    AS records_with_any_primary_group,
                COALESCE(diagnostic.records_with_diagnostic_residual, 0)
                    AS records_with_diagnostic_residual,
                COALESCE(overlap.records_with_multiple_primary_groups, 0)
                    AS records_with_multiple_primary_groups,
                ROUND(
                    100.0
                    * COALESCE(overlap.records_with_multiple_primary_groups, 0)
                    / NULLIF(
                        COALESCE(candidate.records_with_any_primary_group, 0),
                        0
                    ),
                    4
                ) AS pct_primary_group_records_with_overlap,
                ROUND(
                    100.0
                    * COALESCE(candidate.records_with_any_primary_group, 0)
                    / NULLIF(
                        COUNT(*) FILTER (
                            WHERE country.has_category_tags
                        ),
                        0
                    ),
                    4
                ) AS pct_category_tagged_records_with_primary_group
            FROM country_records AS country
            LEFT JOIN candidate_counts AS candidate
                USING (iso_alpha2)
            LEFT JOIN diagnostic_counts AS diagnostic
                USING (iso_alpha2)
            LEFT JOIN overlap_counts AS overlap
                USING (iso_alpha2)
            GROUP BY
                country.iso_alpha2,
                country.country_name,
                candidate.records_with_any_primary_group,
                diagnostic.records_with_diagnostic_residual,
                overlap.records_with_multiple_primary_groups
            ORDER BY country.iso_alpha2
            """
        ).fetchdf()

    coverage["coverage_unit_note"] = (
        "Source records counted once per country/group; source rows are not "
        "deduplicated by product code. Groups include single-group taxonomy "
        "candidates and approved manual decisions; unresolved multi-group and "
        "unmatched tags are excluded. Other / unclassified is diagnostic only."
    )
    overlap["overlap_unit_note"] = (
        "Primary-group overlap is the share of source records with at least one "
        "primary candidate assigned to more than one primary group. Other / "
        "unclassified residuals are diagnostic only and excluded."
    )
    return coverage, overlap


def validate_manual_group_evidence(
    decisions: pd.DataFrame,
    taxonomy: dict,
    category_profile: pd.DataFrame,
) -> dict[tuple[str, str], int]:
    profile_tags = set(category_profile["source_value"])
    evidence_pairs = []

    for row in decisions.itertuples(index=False):
        supporting_tags = [
            tag.strip()
            for tag in row.supporting_exact_tags.split("|")
            if tag.strip()
        ]
        if row.source_category_tag not in taxonomy and not supporting_tags:
            raise ValueError(
                "Manual decisions for tags absent from the pinned taxonomy must "
                f"include exact supporting tags: {row.source_category_tag}"
            )
        for supporting_tag in supporting_tags:
            if supporting_tag not in taxonomy:
                raise ValueError(
                    "Manual decision evidence is not an exact pinned taxonomy "
                    f"node: {supporting_tag}"
                )
            if supporting_tag not in profile_tags:
                raise ValueError(
                    "Manual decision evidence tag is absent from the category "
                    f"profile: {supporting_tag}"
                )
            if supporting_tag == row.source_category_tag:
                raise ValueError(
                    "A source category tag cannot be its own supporting tag: "
                    f"{supporting_tag}"
                )
            evidence_pairs.append(
                {
                    "source_category_tag": row.source_category_tag,
                    "supporting_exact_tag": supporting_tag,
                }
            )

    if not evidence_pairs:
        return {}

    evidence_frame = pd.DataFrame(evidence_pairs)
    with duckdb.connect() as connection:
        connection.register("manual_group_evidence_pairs", evidence_frame)
        cooccurrence = connection.execute(
            """
            SELECT
                evidence.source_category_tag,
                evidence.supporting_exact_tag,
                COUNT(*) AS cooccurring_source_rows
            FROM read_parquet(?) AS source
            CROSS JOIN UNNEST(source.categories_tags) AS observed(source_tag)
            INNER JOIN manual_group_evidence_pairs AS evidence
                ON observed.source_tag = evidence.source_category_tag
            WHERE list_contains(
                source.categories_tags,
                evidence.supporting_exact_tag
            )
            GROUP BY
                evidence.source_category_tag,
                evidence.supporting_exact_tag
            """,
            [str(DATA_FILE)],
        ).fetchdf()

    evidence_counts = {
        (row.source_category_tag, row.supporting_exact_tag): int(
            row.cooccurring_source_rows
        )
        for row in cooccurrence.itertuples(index=False)
    }
    missing_pairs = sorted(
        {
            (
                pair["source_category_tag"],
                pair["supporting_exact_tag"],
            )
            for pair in evidence_pairs
        }
        - set(evidence_counts)
    )
    if missing_pairs:
        raise ValueError(
            "Manual decision evidence tags do not co-occur with their source "
            f"tags in the Parquet: {missing_pairs}"
        )
    return evidence_counts


if __name__ == "__main__":
    main()
