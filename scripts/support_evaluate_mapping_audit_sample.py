"""Evaluate the AI-assisted record-level semantic mapping audit."""

import argparse
import csv
from pathlib import Path
from typing import Any

import duckdb

from support_audit_group_metrics import build_group_metrics, round_metrics
from support_audit_statistics import (
    CI_DESCRIPTION,
    CI_LIMITATION,
    MEAT_CENSUS,
    PRIMARY_SAMPLE,
    assignment_status,
    exact_set_status,
    linearized_ratio_ci as linearized_ratio_ci,
    metric_rates,
)

from support_pinned_inputs import SNAPSHOT_SHA256
from support_duckdb_runtime import connect_duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_FILE = (
    PROJECT_ROOT / "data" / "processed" / "global_product_landscape_five_country.duckdb"
)
SAMPLE_FILE = PROJECT_ROOT / "data" / "private" / "category_mapping_audit_sample.csv"
LABELS_FILE = (
    PROJECT_ROOT / "outputs" / "quality" / "category_mapping_semantic_audit_labels.csv"
)
RECORDS_FILE = (
    PROJECT_ROOT / "outputs" / "quality" / "category_mapping_semantic_audit_records.csv"
)
SUMMARY_FILE = (
    PROJECT_ROOT / "outputs" / "quality" / "category_mapping_semantic_audit_summary.csv"
)
GROUP_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "quality"
    / "category_mapping_semantic_audit_by_group.csv"
)
FRAMEWORK_FILE = (
    PROJECT_ROOT / "data" / "reference" / "category_reporting_group_framework.csv"
)
CROSSWALK_FILE = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "food_group_reporting_group_diagnostic_crosswalk.csv"
)

PRIMARY_SAMPLE_SIZE = 150
EXPECTED_POPULATION_SIZE = 1_111
EXPECTED_SNAPSHOT_SHA256 = SNAPSHOT_SHA256
MEAT_CENSUS_SIZE = 8
ASSESSMENT_STATUSES = {
    "assessable",
    "ambiguous",
    "insufficient_evidence",
    "no_fit",
}
ASSIGNMENT_STATUSES = {
    "Correct",
    "Incorrect",
    "Ambiguous",
    "Insufficient evidence",
}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Required audit input is missing: {path}")
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def split_group_ids(value: str) -> set[str]:
    return {item.strip() for item in value.split("|") if item.strip()}


def join_values(values: set[str] | list[str] | tuple[str, ...]) -> str:
    return "|".join(sorted(set(values)))


def validate_labels(
    labels: list[dict[str, str]],
    valid_groups: set[str],
) -> dict[int, dict[str, Any]]:
    required = {
        "source_record_id",
        "sampling_design",
        "supported_group_ids",
        "ambiguous_group_ids",
        "assessment_status",
        "confidence",
        "rationale",
        "evidence_reference",
    }
    if not labels or not required.issubset(labels[0]):
        missing = required - set(labels[0] if labels else ())
        raise ValueError(f"Audit label file is missing columns: {sorted(missing)}")

    parsed: dict[int, dict[str, Any]] = {}
    for row in labels:
        record_id = int(row["source_record_id"])
        if record_id in parsed:
            raise ValueError(f"Duplicate audit label for source record {record_id}.")
        status = row["assessment_status"].strip().lower()
        confidence = row["confidence"].strip().lower()
        sampling_design = row["sampling_design"].strip()
        if status not in ASSESSMENT_STATUSES:
            raise ValueError(
                f"Record {record_id} has invalid assessment status: {status}"
            )
        if confidence not in {"high", "medium", "low"}:
            raise ValueError(f"Record {record_id} has invalid confidence: {confidence}")
        if sampling_design not in {PRIMARY_SAMPLE, MEAT_CENSUS}:
            raise ValueError(
                f"Record {record_id} has invalid sampling design: {sampling_design}"
            )
        if not row["rationale"].strip() or not row["evidence_reference"].strip():
            raise ValueError(
                f"Record {record_id} needs rationale and evidence references."
            )

        supported = split_group_ids(row["supported_group_ids"])
        ambiguous = split_group_ids(row["ambiguous_group_ids"])
        invalid = (supported | ambiguous) - valid_groups
        if invalid:
            raise ValueError(
                f"Record {record_id} has invalid reporting groups: {sorted(invalid)}"
            )
        if supported & ambiguous:
            raise ValueError(
                f"Record {record_id} has groups marked both supported and ambiguous."
            )
        if status == "ambiguous" and not ambiguous:
            raise ValueError(
                f"Record {record_id} is ambiguous without ambiguous groups."
            )
        if status in {"insufficient_evidence", "no_fit"} and (supported or ambiguous):
            raise ValueError(
                f"Record {record_id} has group labels incompatible with {status}."
            )
        if status == "assessable" and not supported:
            raise ValueError(
                f"Record {record_id} is assessable but has no supported group."
            )

        parsed[record_id] = {
            **row,
            "sampling_design": sampling_design,
            "assessment_status": status,
            "confidence": confidence,
            "supported_groups": supported,
            "ambiguous_groups": ambiguous,
        }
    return parsed


def validate_sampling_frames(
    connection: duckdb.DuckDBPyConnection,
    sample_ids: set[int],
    labels: dict[int, dict[str, Any]],
) -> int:
    population_size = connection.execute(
        """
        SELECT COUNT(DISTINCT record.source_record_id)
        FROM source_product_record AS record
        JOIN record_country AS country USING (source_record_id)
        WHERE country.iso_alpha2 = 'ID'
          AND EXISTS (
              SELECT 1
              FROM record_category_tag AS category
              WHERE category.source_record_id = record.source_record_id
          )
        """
    ).fetchone()[0]
    if population_size != EXPECTED_POPULATION_SIZE:
        raise ValueError(
            "The primary sample frame changed: "
            f"expected {EXPECTED_POPULATION_SIZE}, found {population_size}."
        )

    labeled_primary = {
        record_id
        for record_id, row in labels.items()
        if row["sampling_design"] == PRIMARY_SAMPLE
    }
    if len(sample_ids) != PRIMARY_SAMPLE_SIZE or labeled_primary != sample_ids:
        raise ValueError(
            "Primary audit labels must match the original 150-record sample exactly."
        )

    meat_frame = {
        int(row[0])
        for row in connection.execute(
            """
            SELECT DISTINCT record.source_record_id
            FROM source_product_record AS record
            JOIN record_country AS country USING (source_record_id)
            JOIN record_category_tag AS category USING (source_record_id)
            JOIN category_tag_group_candidate AS candidate
                USING (source_category_tag)
            WHERE country.iso_alpha2 = 'ID'
              AND candidate.reporting_group_id = 'meat_poultry'
              AND candidate.candidate_role = 'single_group_candidate'
              AND candidate.comparison_role = 'primary_candidate'
            """
        ).fetchall()
    }
    labeled_meat = {
        record_id
        for record_id, row in labels.items()
        if row["sampling_design"] == MEAT_CENSUS
    }
    if len(meat_frame) != MEAT_CENSUS_SIZE or labeled_meat != meat_frame:
        raise ValueError(
            "Meat & poultry supplement must be the complete eight-record "
            f"candidate frame: expected {sorted(meat_frame)}, "
            f"labeled {sorted(labeled_meat)}."
        )
    if set(labels) != sample_ids | meat_frame:
        raise ValueError("Audit labels contain unrecognized or missing record IDs.")
    return population_size


def get_database_records(
    connection: duckdb.DuckDBPyConnection,
    record_ids: list[int],
) -> dict[int, dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT
            source_record_id,
            code,
            product_name[1].text AS product_name,
            generic_name[1].text AS generic_name,
            brands,
            categories,
            categories_tags,
            ingredients_text[1].text AS ingredients_text,
            ingredients,
            packaging,
            packaging_text[1].text AS packaging_text,
            product_quantity,
            labels,
            labels_tags,
            food_groups_tags
        FROM source_product_record
        WHERE source_record_id IN (SELECT UNNEST(?::BIGINT[]))
        """,
        [record_ids],
    ).fetchall()
    column_names = [
        "source_record_id",
        "code",
        "product_name",
        "generic_name",
        "brands",
        "categories",
        "categories_tags",
        "ingredients_text",
        "ingredients",
        "packaging",
        "packaging_text",
        "product_quantity",
        "labels",
        "labels_tags",
        "food_groups_tags",
    ]
    result = {int(row[0]): dict(zip(column_names, row)) for row in rows}
    missing = set(record_ids) - set(result)
    if missing:
        raise ValueError(f"Source product records are missing: {sorted(missing)}")
    return result


def get_group_mappings(
    connection: duckdb.DuckDBPyConnection,
    record_ids: list[int],
) -> dict[int, dict[str, Any]]:
    mappings: dict[int, dict[str, Any]] = {
        record_id: {
            "candidate_groups": set(),
            "manual_groups": set(),
            "all_candidate_groups": set(),
            "candidate_sources": {},
            "candidate_source_tags": {},
        }
        for record_id in record_ids
    }
    rows = connection.execute(
        """
        SELECT
            category.source_record_id,
            candidate.reporting_group_id,
            candidate.candidate_role,
            candidate.comparison_role,
            candidate.source_category_tag
        FROM record_category_tag AS category
        JOIN category_tag_group_candidate AS candidate
            USING (source_category_tag)
        WHERE category.source_record_id IN (SELECT UNNEST(?::BIGINT[]))
        """,
        [record_ids],
    ).fetchall()
    for record_id, group_id, role, comparison_role, source_tag in rows:
        record_id = int(record_id)
        mapping = mappings[record_id]
        mapping["all_candidate_groups"].add(group_id)
        if comparison_role == "primary_candidate" and role == "single_group_candidate":
            mapping["candidate_groups"].add(group_id)
        elif (
            comparison_role == "primary_candidate" and role == "manual_group_assignment"
        ):
            mapping["manual_groups"].add(group_id)
        if comparison_role == "primary_candidate" and role in {
            "single_group_candidate",
            "manual_group_assignment",
        }:
            mapping["candidate_sources"].setdefault(group_id, set()).add(role)
            mapping["candidate_source_tags"].setdefault(group_id, set()).add(source_tag)
    return mappings


def get_crosswalk(path: Path, valid_groups: set[str]) -> dict[str, str]:
    rows = read_csv_rows(path)
    required = {
        "food_group_tag",
        "reporting_group_id",
        "crosswalk_status",
        "mapping_basis",
    }
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"Food-group diagnostic crosswalk is malformed: {path}")
    if any(row["crosswalk_status"] != "diagnostic_only" for row in rows):
        raise ValueError("Food-group crosswalk must remain diagnostic-only.")
    mapping = {row["food_group_tag"]: row["reporting_group_id"] for row in rows}
    if len(mapping) != len(rows):
        raise ValueError("Food-group diagnostic crosswalk contains duplicate tags.")
    invalid_groups = set(mapping.values()) - valid_groups
    if invalid_groups:
        raise ValueError(
            f"Food-group diagnostic crosswalk has invalid groups: {sorted(invalid_groups)}"
        )
    return mapping


def create_record_rows(
    sample_rows: list[dict[str, str]],
    labels: dict[int, dict[str, Any]],
    database_records: dict[int, dict[str, Any]],
    group_mappings: dict[int, dict[str, Any]],
    crosswalk: dict[str, str],
) -> list[dict[str, Any]]:
    rows = []
    for record_id in sorted(labels):
        label = labels[record_id]
        product = database_records[record_id]
        mapping = group_mappings[record_id]
        candidate_groups = mapping["candidate_groups"]
        supported_groups = label["supported_groups"]
        ambiguous_groups = label["ambiguous_groups"]
        assignment_statuses = {
            group_id: assignment_status(
                group_id,
                supported_groups,
                ambiguous_groups,
                label["assessment_status"],
            )
            for group_id in candidate_groups
        }
        mapped_food_groups = {
            crosswalk[tag]
            for tag in product["food_groups_tags"] or []
            if tag in crosswalk
        }
        all_candidate_groups = mapping["all_candidate_groups"]
        comparable = bool(mapped_food_groups and all_candidate_groups)
        if not comparable:
            crosscheck_status = "not_comparable"
        elif mapped_food_groups == all_candidate_groups:
            crosscheck_status = "exact_set_match"
        elif mapped_food_groups & all_candidate_groups:
            crosscheck_status = "overlap_only"
        else:
            crosscheck_status = "no_overlap"

        sample_row = next(
            (row for row in sample_rows if int(row["source_record_id"]) == record_id),
            {},
        )
        candidate_sources = ";".join(
            f"{group_id}={join_values(roles)}"
            for group_id, roles in sorted(mapping["candidate_sources"].items())
        )
        candidate_tags = ";".join(
            f"{group_id}={join_values(tags)}"
            for group_id, tags in sorted(mapping["candidate_source_tags"].items())
            if group_id in candidate_groups
        )
        row = {
            "audit_id": sample_row.get("audit_id", ""),
            "source_record_id": record_id,
            "sampling_design": label["sampling_design"],
            "code": product["code"] or "",
            "product_name": product["product_name"] or "",
            "generic_name": product["generic_name"] or "",
            "brands": product["brands"] or "",
            "ingredients_text": product["ingredients_text"] or "",
            "ingredients": product["ingredients"] or "",
            "packaging": product["packaging"] or "",
            "packaging_text": product["packaging_text"] or "",
            "product_quantity": product["product_quantity"] or "",
            "labels": product["labels"] or "",
            "categories": product["categories"] or "",
            "categories_tags": join_values(product["categories_tags"] or []),
            "taxonomy_candidate_group_ids": join_values(candidate_groups),
            "exact_manual_group_ids": join_values(mapping["manual_groups"]),
            "candidate_source_roles_by_group": candidate_sources,
            "candidate_source_tags_by_group": candidate_tags,
            "independently_supported_group_ids": join_values(supported_groups),
            "candidate_group_ids_not_supported_by_reviewer": join_values(
                candidate_groups - supported_groups
            ),
            "reviewer_supported_group_ids_missing_from_candidate": join_values(
                supported_groups - candidate_groups
            ),
            "ambiguous_group_ids": join_values(ambiguous_groups),
            "assessment_status": label["assessment_status"],
            "reviewer_confidence": label["confidence"],
            "rationale": label["rationale"],
            "evidence_reference": label["evidence_reference"],
            "external_evidence_reference": label.get("external_evidence_reference", ""),
            "external_evidence_access_date": label.get(
                "external_evidence_access_date", ""
            ),
            "candidate_assignment_statuses": ";".join(
                f"{group_id}={status}"
                for group_id, status in sorted(assignment_statuses.items())
            ),
            "record_exact_set_status": exact_set_status(
                candidate_groups,
                supported_groups,
                ambiguous_groups,
                label["assessment_status"],
            ),
            "food_groups_tags": join_values(product["food_groups_tags"] or []),
            "diagnostic_food_group_reporting_group_ids": join_values(
                mapped_food_groups
            ),
            "diagnostic_crosscheck_status": crosscheck_status,
        }
        row["_candidate_groups"] = candidate_groups
        row["_supported_groups"] = supported_groups
        row["_ambiguous_groups"] = ambiguous_groups
        row["_assessment_status"] = label["assessment_status"]
        row["_sampling_design"] = label["sampling_design"]
        row["_assignment_statuses"] = assignment_statuses
        row["_manual_groups"] = mapping["manual_groups"]
        row["_missing_supported_groups"] = supported_groups - candidate_groups
        row["_crosscheck_comparable"] = comparable
        row["_crosscheck_status"] = crosscheck_status
        rows.append(row)
    return rows


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Refusing to write an empty audit output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DATABASE_FILE)
    parser.add_argument("--sample", type=Path, default=SAMPLE_FILE)
    parser.add_argument("--labels", type=Path, default=LABELS_FILE)
    parser.add_argument("--records-output", type=Path, default=RECORDS_FILE)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_FILE)
    parser.add_argument("--group-output", type=Path, default=GROUP_FILE)
    args = parser.parse_args()

    sample_rows = read_csv_rows(args.sample)
    if not sample_rows:
        raise ValueError(f"Primary audit sample is empty: {args.sample}")
    sample_ids = {int(row["source_record_id"]) for row in sample_rows}
    label_rows = read_csv_rows(args.labels)
    with FRAMEWORK_FILE.open(encoding="utf-8-sig", newline="") as source:
        framework_rows = list(csv.DictReader(source))
    valid_groups = {
        row["group_id"]
        for row in framework_rows
        if row["group_id"] != "other_unclassified"
    }
    labels = validate_labels(label_rows, valid_groups)

    with connect_duckdb(str(args.database), read_only=True) as connection:
        snapshot_id = connection.execute(
            "SELECT snapshot_id FROM data_snapshot"
        ).fetchone()[0]
        if snapshot_id != EXPECTED_SNAPSHOT_SHA256:
            raise ValueError(f"Unexpected source snapshot SHA-256: {snapshot_id}")
        population_size = validate_sampling_frames(connection, sample_ids, labels)
        record_ids = sorted(labels)
        database_records = get_database_records(connection, record_ids)
        group_mappings = get_group_mappings(connection, record_ids)

    crosswalk = get_crosswalk(CROSSWALK_FILE, valid_groups)
    records = create_record_rows(
        sample_rows,
        labels,
        database_records,
        group_mappings,
        crosswalk,
    )
    primary = [
        record for record in records if record["sampling_design"] == PRIMARY_SAMPLE
    ]
    meat_census = [
        record for record in records if record["sampling_design"] == MEAT_CENSUS
    ]

    summary_rows = []
    for scope, selected in (
        (PRIMARY_SAMPLE, primary),
        (MEAT_CENSUS, meat_census),
    ):
        metrics = metric_rates(
            selected,
            population_size,
        )
        is_primary = scope == PRIMARY_SAMPLE
        summary_rows.append(
            round_metrics(
                {
                    "analysis_scope": scope,
                    "sampling_frame_records": (
                        population_size if is_primary else MEAT_CENSUS_SIZE
                    ),
                    "candidate_assignment_scope": (
                        "Single-group taxonomy candidate record-group pairs; "
                        "pairs also supported by an exact-manual mapping are "
                        "counted once and shown separately."
                    ),
                    "sampling_design": (
                        "Deterministic MD5-ranked 150-record sample; "
                        "conditional SRSWOR approximation."
                        if is_primary
                        else "Census of eight Indonesian Meat & poultry candidate "
                        "records; all single-group candidate pairs on these "
                        "records are descriptive and reported separately."
                    ),
                    **metrics,
                    "confidence_interval_method": (
                        CI_DESCRIPTION if is_primary else "Not applicable: census."
                    ),
                    "confidence_interval_limitation": (
                        CI_LIMITATION
                        if is_primary
                        else "No sampling interval reported."
                    ),
                }
            )
        )

    group_rows = build_group_metrics(
        primary,
        valid_groups,
        population_size,
        PRIMARY_SAMPLE,
    ) + build_group_metrics(
        meat_census,
        valid_groups,
        population_size,
        MEAT_CENSUS,
    )
    clean_records = []
    for record in records:
        clean_records.append(
            {key: value for key, value in record.items() if not key.startswith("_")}
        )

    write_rows(args.records_output, clean_records)
    write_rows(args.summary_output, summary_rows)
    write_rows(args.group_output, [round_metrics(row) for row in group_rows])
    print(f"Record-level audit: {args.records_output}")
    print(f"Audit metrics: {args.summary_output}")
    print(f"Per-group metrics: {args.group_output}")


if __name__ == "__main__":
    main()
