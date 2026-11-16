"""Per-reporting-group audit metrics and rounding."""

from typing import Any

from support_audit_statistics import (
    CI_DESCRIPTION,
    CI_LIMITATION,
    MEAT_CENSUS,
    linearized_ratio_ci,
)


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
            int(group_id in record["_assignment_statuses"]) for record in records
        ]
        numerators = [
            int(record["_assignment_statuses"].get(group_id) == "Correct")
            for record in records
        ]
        determinate_denominators = [
            int(
                record["_assignment_statuses"].get(group_id) in {"Correct", "Incorrect"}
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
            record
            for record in determinate_records
            if group_id in record["_supported_groups"]
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
