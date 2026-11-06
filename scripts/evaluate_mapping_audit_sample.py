"""Evaluate the AI-assisted record-level semantic mapping audit."""

import argparse
import csv
import math
from pathlib import Path
from statistics import NormalDist
from typing import Any

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "global_product_landscape_five_country.duckdb"
)
SAMPLE_FILE = PROJECT_ROOT / "data" / "private" / "category_mapping_audit_sample.csv"
LABELS_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "quality"
    / "category_mapping_semantic_audit_labels.csv"
)
RECORDS_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "quality"
    / "category_mapping_semantic_audit_records.csv"
)
SUMMARY_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "quality"
    / "category_mapping_semantic_audit_summary.csv"
)
GROUP_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "quality"
    / "category_mapping_semantic_audit_by_group.csv"
)
FRAMEWORK_FILE = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "category_reporting_group_framework.csv"
)
CROSSWALK_FILE = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "food_group_reporting_group_diagnostic_crosswalk.csv"
)

PRIMARY_SAMPLE_SIZE = 150
EXPECTED_POPULATION_SIZE = 1_111
EXPECTED_SNAPSHOT_SHA256 = (
    "DA39B2C5AAF1F85B2E637B904B5FC3A29780DD7E184254F4B660CFE0CD84999A"
)
MEAT_CENSUS_SIZE = 8
PRIMARY_SAMPLE = "primary_sample"
MEAT_CENSUS = "meat_poultry_census"
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
CI_DESCRIPTION = (
    "Approximate 95% Taylor-linearization interval with finite-population "
    "correction; assumes the fixed MD5-ranked sample approximates SRSWOR."
)
CI_LIMITATION = (
    "Sampling uncertainty only; does not quantify AI-judgment reliability "
    "or independence."
)


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
            raise ValueError(f"Record {record_id} has invalid assessment status: {status}")
        if confidence not in {"high", "medium", "low"}:
            raise ValueError(f"Record {record_id} has invalid confidence: {confidence}")
        if sampling_design not in {PRIMARY_SAMPLE, MEAT_CENSUS}:
            raise ValueError(
                f"Record {record_id} has invalid sampling design: {sampling_design}"
            )
        if not row["rationale"].strip() or not row["evidence_reference"].strip():
            raise ValueError(f"Record {record_id} needs rationale and evidence references.")

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
            raise ValueError(f"Record {record_id} is ambiguous without ambiguous groups.")
        if status in {"insufficient_evidence", "no_fit"} and (supported or ambiguous):
            raise ValueError(
                f"Record {record_id} has group labels incompatible with {status}."
            )
        if status == "assessable" and not supported:
            raise ValueError(f"Record {record_id} is assessable but has no supported group.")

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


def assignment_status(
    group_id: str,
    supported_groups: set[str],
    ambiguous_groups: set[str],
    assessment_status: str,
) -> str:
    if group_id in supported_groups:
        return "Correct"
    if group_id in ambiguous_groups:
        return "Ambiguous"
    if assessment_status == "insufficient_evidence":
        return "Insufficient evidence"
    return "Incorrect"


def exact_set_status(
    candidate_groups: set[str],
    supported_groups: set[str],
    ambiguous_groups: set[str],
    assessment_status: str,
) -> str:
    if assessment_status == "insufficient_evidence":
        return "Insufficient evidence"
    if assessment_status == "ambiguous" or ambiguous_groups:
        return "Ambiguous"
    if candidate_groups == supported_groups:
        return "Agreement"
    return "Disagreement"


def linearized_ratio_ci(
    denominator_counts: list[int],
    numerator_counts: list[int],
    population_size: int,
) -> tuple[float, float] | None:
    sample_size = len(denominator_counts)
    denominator_total = sum(denominator_counts)
    if sample_size < 2 or denominator_total == 0 or sample_size >= population_size:
        return None

    estimate = sum(numerator_counts) / denominator_total
    denominator_mean = denominator_total / sample_size
    residuals = [
        numerator - estimate * denominator
        for numerator, denominator in zip(numerator_counts, denominator_counts)
    ]
    residual_mean = sum(residuals) / sample_size
    residual_variance = sum(
        (residual - residual_mean) ** 2 for residual in residuals
    ) / (sample_size - 1)
    if residual_variance <= 1e-14:
        return None

    sampling_fraction = sample_size / population_size
    variance = (
        (1 - sampling_fraction)
        * residual_variance
        / (sample_size * denominator_mean**2)
    )
    standard_error = math.sqrt(variance)
    z_value = NormalDist().inv_cdf(0.975)
    return (
        max(0.0, estimate - z_value * standard_error),
        min(1.0, estimate + z_value * standard_error),
    )


def proportion_ci(
    outcomes: list[bool],
    population_size: int,
) -> tuple[float, float] | None:
    sample_size = len(outcomes)
    if sample_size < 2 or sample_size >= population_size:
        return None
    denominator = [1] * sample_size
    numerator = [int(value) for value in outcomes]
    return linearized_ratio_ci(denominator, numerator, population_size)


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
    result = {
        int(row[0]): dict(zip(column_names, row))
        for row in rows
    }
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
            comparison_role == "primary_candidate"
            and role == "manual_group_assignment"
        ):
            mapping["manual_groups"].add(group_id)
        if (
            comparison_role == "primary_candidate"
            and role in {"single_group_candidate", "manual_group_assignment"}
        ):
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
            (
                row
                for row in sample_rows
                if int(row["source_record_id"]) == record_id
            ),
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
            "external_evidence_reference": label.get(
                "external_evidence_reference", ""
            ),
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


def metric_rates(
    records: list[dict[str, Any]],
    population_size: int,
) -> dict[str, Any]:
    selected = records
    candidate_counts = []
    correct_counts = []
    determinate_counts = []
    pair_statuses = []
    exact_matches = []
    determinate_exact = []
    ambiguous_records = []
    insufficient_records = []
    no_fit_records = []
    taxonomy_only_counts = []
    taxonomy_only_correct_counts = []
    taxonomy_only_determinate_counts = []
    manual_overlap_counts = []
    manual_overlap_correct_counts = []
    manual_overlap_determinate_counts = []
    taxonomy_only_statuses = []
    manual_overlap_statuses = []
    target_meat_pair_count = 0
    missing_supported_group_pairs = 0
    records_with_missing_supported_groups = 0

    for record in selected:
        statuses = record["_assignment_statuses"]
        target_meat_pair_count += int("meat_poultry" in statuses)
        candidate_counts.append(len(statuses))
        correct_counts.append(sum(status == "Correct" for status in statuses.values()))
        pair_statuses.extend(statuses.values())
        determinate_counts.append(
            sum(status in {"Correct", "Incorrect"} for status in statuses.values())
        )
        taxonomy_only = {
            group_id: status
            for group_id, status in statuses.items()
            if group_id not in record["_manual_groups"]
        }
        manual_overlap = {
            group_id: status
            for group_id, status in statuses.items()
            if group_id in record["_manual_groups"]
        }
        taxonomy_only_counts.append(len(taxonomy_only))
        taxonomy_only_correct_counts.append(
            sum(status == "Correct" for status in taxonomy_only.values())
        )
        taxonomy_only_determinate_counts.append(
            sum(status in {"Correct", "Incorrect"} for status in taxonomy_only.values())
        )
        manual_overlap_counts.append(len(manual_overlap))
        manual_overlap_correct_counts.append(
            sum(status == "Correct" for status in manual_overlap.values())
        )
        manual_overlap_determinate_counts.append(
            sum(status in {"Correct", "Incorrect"} for status in manual_overlap.values())
        )
        taxonomy_only_statuses.extend(taxonomy_only.values())
        manual_overlap_statuses.extend(manual_overlap.values())
        exact_matches.append(record["record_exact_set_status"] == "Agreement")
        determinate_exact.append(
            record["record_exact_set_status"] in {"Agreement", "Disagreement"}
        )
        ambiguous_records.append(record["_assessment_status"] == "ambiguous")
        insufficient_records.append(
            record["_assessment_status"] == "insufficient_evidence"
        )
        no_fit_records.append(record["_assessment_status"] == "no_fit")
        if record["record_exact_set_status"] in {"Agreement", "Disagreement"}:
            missing = len(record["_missing_supported_groups"])
            missing_supported_group_pairs += missing
            records_with_missing_supported_groups += int(missing > 0)

    assignment_total = sum(candidate_counts)
    correct_total = sum(correct_counts)
    determinate_total = sum(determinate_counts)
    precision = correct_total / determinate_total if determinate_total else None
    confirmed_share = correct_total / assignment_total if assignment_total else None
    precision_ci = (
        linearized_ratio_ci(
            determinate_counts,
            correct_counts,
            population_size,
        )
        if assignment_total and sum(determinate_counts) >= 1
        else None
    )
    confirmed_ci = (
        linearized_ratio_ci(
            candidate_counts,
            correct_counts,
            population_size,
        )
        if assignment_total
        else None
    )
    taxonomy_only_total = sum(taxonomy_only_counts)
    taxonomy_only_correct = sum(taxonomy_only_correct_counts)
    taxonomy_only_determinate = sum(taxonomy_only_determinate_counts)
    taxonomy_only_precision_ci = (
        linearized_ratio_ci(
            taxonomy_only_determinate_counts,
            taxonomy_only_correct_counts,
            population_size,
        )
        if taxonomy_only_determinate
        else None
    )
    taxonomy_only_confirmed_ci = (
        linearized_ratio_ci(
            taxonomy_only_counts,
            taxonomy_only_correct_counts,
            population_size,
        )
        if taxonomy_only_total
        else None
    )
    manual_overlap_total = sum(manual_overlap_counts)
    manual_overlap_correct = sum(manual_overlap_correct_counts)
    manual_overlap_determinate = sum(manual_overlap_determinate_counts)
    manual_overlap_precision_ci = (
        linearized_ratio_ci(
            manual_overlap_determinate_counts,
            manual_overlap_correct_counts,
            population_size,
        )
        if manual_overlap_determinate
        else None
    )
    manual_overlap_confirmed_ci = (
        linearized_ratio_ci(
            manual_overlap_counts,
            manual_overlap_correct_counts,
            population_size,
        )
        if manual_overlap_total
        else None
    )
    record_count = len(selected)
    exact_rate = sum(exact_matches) / record_count if record_count else None
    determinate_record_count = sum(determinate_exact)
    exact_determinate_rate = (
        sum(
            is_exact and is_determinate
            for is_exact, is_determinate in zip(exact_matches, determinate_exact)
        )
        / determinate_record_count
        if determinate_record_count
        else None
    )
    exact_ci = (
        proportion_ci(exact_matches, population_size)
        if record_count
        and all(record["_sampling_design"] == PRIMARY_SAMPLE for record in selected)
        else None
    )
    ambiguous_ci = (
        proportion_ci(ambiguous_records, population_size)
        if record_count
        and all(record["_sampling_design"] == PRIMARY_SAMPLE for record in selected)
        else None
    )
    insufficient_ci = (
        proportion_ci(insufficient_records, population_size)
        if record_count
        and all(record["_sampling_design"] == PRIMARY_SAMPLE for record in selected)
        else None
    )

    comparable_records = [
        record for record in selected if record["_crosscheck_comparable"]
    ]
    crosscheck_exact = sum(
        record["_crosscheck_status"] == "exact_set_match"
        for record in comparable_records
    )
    crosscheck_overlap = sum(
        record["_crosscheck_status"] in {"exact_set_match", "overlap_only"}
        for record in comparable_records
    )
    manual_overlap_pairs = sum(
        group_id in record["_manual_groups"]
        for record in selected
        for group_id in record["_candidate_groups"]
    )
    manual_overlap_records = sum(
        bool(record["_candidate_groups"] & record["_manual_groups"])
        for record in selected
    )

    return {
        "records_reviewed": record_count,
        "records_with_candidate_groups": sum(count > 0 for count in candidate_counts),
        "candidate_assignment_pairs": assignment_total,
        "correct_assignments": correct_total,
        "incorrect_assignments": pair_statuses.count("Incorrect"),
        "ambiguous_assignments": pair_statuses.count("Ambiguous"),
        "insufficient_evidence_assignments": pair_statuses.count(
            "Insufficient evidence"
        ),
        "taxonomy_only_candidate_assignment_pairs": taxonomy_only_total,
        "taxonomy_only_correct_assignments": taxonomy_only_correct,
        "taxonomy_only_incorrect_assignments": taxonomy_only_statuses.count(
            "Incorrect"
        ),
        "taxonomy_only_ambiguous_assignments": taxonomy_only_statuses.count(
            "Ambiguous"
        ),
        "taxonomy_only_insufficient_evidence_assignments": (
            taxonomy_only_statuses.count("Insufficient evidence")
        ),
        "taxonomy_only_determinate_denominator": taxonomy_only_determinate,
        "taxonomy_only_determinate_precision": (
            taxonomy_only_correct / taxonomy_only_determinate
            if taxonomy_only_determinate
            else None
        ),
        "taxonomy_only_precision_ci_low": (
            taxonomy_only_precision_ci[0] if taxonomy_only_precision_ci else None
        ),
        "taxonomy_only_precision_ci_high": (
            taxonomy_only_precision_ci[1] if taxonomy_only_precision_ci else None
        ),
        "taxonomy_only_confirmed_share": (
            taxonomy_only_correct / taxonomy_only_total
            if taxonomy_only_total
            else None
        ),
        "taxonomy_only_confirmed_ci_low": (
            taxonomy_only_confirmed_ci[0] if taxonomy_only_confirmed_ci else None
        ),
        "taxonomy_only_confirmed_ci_high": (
            taxonomy_only_confirmed_ci[1] if taxonomy_only_confirmed_ci else None
        ),
        "manual_overlap_correct_assignments": manual_overlap_correct,
        "manual_overlap_incorrect_assignments": manual_overlap_statuses.count(
            "Incorrect"
        ),
        "manual_overlap_ambiguous_assignments": manual_overlap_statuses.count(
            "Ambiguous"
        ),
        "manual_overlap_insufficient_evidence_assignments": (
            manual_overlap_statuses.count("Insufficient evidence")
        ),
        "manual_overlap_determinate_denominator": manual_overlap_determinate,
        "manual_overlap_determinate_precision": (
            manual_overlap_correct / manual_overlap_determinate
            if manual_overlap_determinate
            else None
        ),
        "manual_overlap_precision_ci_low": (
            manual_overlap_precision_ci[0] if manual_overlap_precision_ci else None
        ),
        "manual_overlap_precision_ci_high": (
            manual_overlap_precision_ci[1] if manual_overlap_precision_ci else None
        ),
        "manual_overlap_confirmed_share": (
            manual_overlap_correct / manual_overlap_total
            if manual_overlap_total
            else None
        ),
        "manual_overlap_confirmed_ci_low": (
            manual_overlap_confirmed_ci[0] if manual_overlap_confirmed_ci else None
        ),
        "manual_overlap_confirmed_ci_high": (
            manual_overlap_confirmed_ci[1] if manual_overlap_confirmed_ci else None
        ),
        "determinate_assignment_denominator": determinate_total,
        "determinate_assignment_precision": precision,
        "determinate_precision_ci_low": precision_ci[0] if precision_ci else None,
        "determinate_precision_ci_high": precision_ci[1] if precision_ci else None,
        "confirmed_assignment_share_all_pairs": confirmed_share,
        "confirmed_share_ci_low": confirmed_ci[0] if confirmed_ci else None,
        "confirmed_share_ci_high": confirmed_ci[1] if confirmed_ci else None,
        "exact_set_matches": sum(exact_matches),
        "record_exact_set_agreement_all_records": exact_rate,
        "determinate_record_denominator": determinate_record_count,
        "record_exact_set_agreement_determinate_only": exact_determinate_rate,
        "record_exact_set_ci_low": exact_ci[0] if exact_ci else None,
        "record_exact_set_ci_high": exact_ci[1] if exact_ci else None,
        "ambiguous_record_count": sum(ambiguous_records),
        "ambiguity_rate": (
            sum(ambiguous_records) / record_count if record_count else None
        ),
        "ambiguity_ci_low": ambiguous_ci[0] if ambiguous_ci else None,
        "ambiguity_ci_high": ambiguous_ci[1] if ambiguous_ci else None,
        "insufficient_evidence_record_count": sum(insufficient_records),
        "insufficient_evidence_rate": (
            sum(insufficient_records) / record_count if record_count else None
        ),
        "insufficient_evidence_ci_low": (
            insufficient_ci[0] if insufficient_ci else None
        ),
        "insufficient_evidence_ci_high": (
            insufficient_ci[1] if insufficient_ci else None
        ),
        "no_fit_record_count": sum(no_fit_records),
        "no_fit_rate": sum(no_fit_records) / record_count if record_count else None,
        "food_groups_comparable_records": len(comparable_records),
        "food_groups_exact_set_matches": crosscheck_exact,
        "food_groups_exact_match_rate": (
            crosscheck_exact / len(comparable_records)
            if comparable_records
            else None
        ),
        "food_groups_any_overlap_records": crosscheck_overlap,
        "food_groups_any_overlap_rate": (
            crosscheck_overlap / len(comparable_records)
            if comparable_records
            else None
        ),
        "manual_exact_overlap_assignment_pairs": manual_overlap_pairs,
        "manual_exact_overlap_records": manual_overlap_records,
        "target_meat_poultry_assignment_pairs": target_meat_pair_count,
        "determinate_records_with_supported_groups_missing_from_candidate": (
            records_with_missing_supported_groups
        ),
        "determinate_reviewer_supported_group_pairs_missing_from_candidate": (
            missing_supported_group_pairs
        ),
    }


def build_group_metrics(
    records: list[dict[str, Any]],
    valid_groups: set[str],
    population_size: int,
    analysis_scope: str,
) -> list[dict[str, Any]]:
    output = []
    for group_id in sorted(valid_groups):
        group_pairs = [
            (record, record["_assignment_statuses"][group_id])
            for record in records
            if group_id in record["_assignment_statuses"]
        ]
        statuses = [status for _, status in group_pairs]
        assignment_count = len(statuses)
        correct = statuses.count("Correct")
        incorrect = statuses.count("Incorrect")
        ambiguous = statuses.count("Ambiguous")
        insufficient = statuses.count("Insufficient evidence")
        determinate = correct + incorrect
        precision = correct / determinate if determinate else None
        confirmed_share = correct / assignment_count if assignment_count else None

        denominators = [
            int(group_id in record["_assignment_statuses"])
            for record in records
        ]
        numerators = [
            int(record["_assignment_statuses"].get(group_id) == "Correct")
            for record in records
        ]
        determinate_denominators = [
            int(
                record["_assignment_statuses"].get(group_id)
                in {"Correct", "Incorrect"}
            )
            for record in records
        ]
        determinate_numerators = [
            int(record["_assignment_statuses"].get(group_id) == "Correct")
            for record in records
        ]
        if analysis_scope == MEAT_CENSUS:
            precision_ci = None
            confirmed_ci = None
            precision_ci_note = "Not applicable: selected-scope census."
            confirmed_ci_note = precision_ci_note
        elif assignment_count >= 10:
            precision_ci = linearized_ratio_ci(
                determinate_denominators,
                determinate_numerators,
                population_size,
            )
            confirmed_ci = linearized_ratio_ci(
                denominators,
                numerators,
                population_size,
            )
            precision_ci_note = (
                CI_DESCRIPTION
                if precision_ci
                else "Not reported: zero observed residual variance."
            )
            confirmed_ci_note = (
                CI_DESCRIPTION
                if confirmed_ci
                else "Not reported: zero observed residual variance."
            )
        elif assignment_count:
            precision_ci = None
            confirmed_ci = None
            precision_ci_note = "Not reported: fewer than 10 candidate assignments."
            confirmed_ci_note = precision_ci_note
        else:
            precision_ci = None
            confirmed_ci = None
            precision_ci_note = (
                "Not estimable: no candidate assignments in primary sample."
            )
            confirmed_ci_note = precision_ci_note
        manual_pairs = [
            status
            for record, status in group_pairs
            if group_id in record["_manual_groups"]
        ]
        taxonomy_only_pairs = [
            status
            for record, status in group_pairs
            if group_id not in record["_manual_groups"]
        ]
        taxonomy_determinate = sum(
            status in {"Correct", "Incorrect"} for status in taxonomy_only_pairs
        )
        manual_determinate = sum(
            status in {"Correct", "Incorrect"} for status in manual_pairs
        )
        determinate_records = [
            record
            for record in records
            if record["record_exact_set_status"] in {"Agreement", "Disagreement"}
        ]
        supported_group_records = [
            record for record in determinate_records if group_id in record["_supported_groups"]
        ]
        missing_supported_group_records = [
            record
            for record in supported_group_records
            if group_id not in record["_candidate_groups"]
        ]
        output.append(
            {
                "reporting_group_id": group_id,
                "analysis_scope": analysis_scope,
                "candidate_assignment_records": assignment_count,
                "correct_assignments": correct,
                "incorrect_assignments": incorrect,
                "ambiguous_assignments": ambiguous,
                "insufficient_evidence_assignments": insufficient,
                "determinate_assignment_denominator": determinate,
                "determinate_assignment_precision": precision,
                "determinate_precision_ci_low": (
                    precision_ci[0] if precision_ci else None
                ),
                "determinate_precision_ci_high": (
                    precision_ci[1] if precision_ci else None
                ),
                "confirmed_assignment_share_all_pairs": confirmed_share,
                "confirmed_share_ci_low": confirmed_ci[0] if confirmed_ci else None,
                "confirmed_share_ci_high": confirmed_ci[1] if confirmed_ci else None,
                "taxonomy_only_assignment_pairs": len(taxonomy_only_pairs),
                "taxonomy_only_correct_assignments": taxonomy_only_pairs.count(
                    "Correct"
                ),
                "taxonomy_only_incorrect_assignments": taxonomy_only_pairs.count(
                    "Incorrect"
                ),
                "taxonomy_only_ambiguous_assignments": taxonomy_only_pairs.count(
                    "Ambiguous"
                ),
                "taxonomy_only_insufficient_evidence_assignments": (
                    taxonomy_only_pairs.count("Insufficient evidence")
                ),
                "taxonomy_only_determinate_precision": (
                    taxonomy_only_pairs.count("Correct") / taxonomy_determinate
                    if taxonomy_determinate
                    else None
                ),
                "manual_exact_overlap_assignment_pairs": len(manual_pairs),
                "manual_exact_overlap_correct_assignments": manual_pairs.count(
                    "Correct"
                ),
                "manual_exact_overlap_determinate_precision": (
                    manual_pairs.count("Correct") / manual_determinate
                    if manual_determinate
                    else None
                ),
                "determinate_records_supporting_group": len(supported_group_records),
                "supported_group_records_missing_candidate": len(
                    missing_supported_group_records
                ),
                "determinate_precision_ci_method": precision_ci_note,
                "confirmed_share_ci_method": confirmed_ci_note,
                "confidence_interval_limitation": CI_LIMITATION,
            }
        )
    return output


def round_metrics(row: dict[str, Any]) -> dict[str, Any]:
    rounded = {}
    for key, value in row.items():
        if isinstance(value, float):
            rounded[key] = round(value, 6)
        else:
            rounded[key] = value
    return rounded


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

    with duckdb.connect(str(args.database), read_only=True) as connection:
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
        record
        for record in records
        if record["sampling_design"] == PRIMARY_SAMPLE
    ]
    meat_census = [
        record
        for record in records
        if record["sampling_design"] == MEAT_CENSUS
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
                        CI_LIMITATION if is_primary else "No sampling interval reported."
                    ),
                }
            )
        )

    group_rows = (
        build_group_metrics(
            primary,
            valid_groups,
            population_size,
            PRIMARY_SAMPLE,
        )
        + build_group_metrics(
            meat_census,
            valid_groups,
            population_size,
            MEAT_CENSUS,
        )
    )
    clean_records = []
    for record in records:
        clean_records.append(
            {
                key: value
                for key, value in record.items()
                if not key.startswith("_")
            }
        )

    write_rows(args.records_output, clean_records)
    write_rows(args.summary_output, summary_rows)
    write_rows(args.group_output, [round_metrics(row) for row in group_rows])
    print(f"Record-level audit: {args.records_output}")
    print(f"Audit metrics: {args.summary_output}")
    print(f"Per-group metrics: {args.group_output}")


if __name__ == "__main__":
    main()
