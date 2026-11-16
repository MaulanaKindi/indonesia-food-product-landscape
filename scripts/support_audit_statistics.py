"""Sampling and classification statistics for the semantic audit."""

import math
from statistics import NormalDist
from typing import Any

PRIMARY_SAMPLE = "primary_sample"

MEAT_CENSUS = "meat_poultry_census"

CI_DESCRIPTION = (
    "Approximate 95% Taylor-linearization interval with finite-population "
    "correction; assumes the fixed MD5-ranked sample approximates SRSWOR."
)

CI_LIMITATION = (
    "Sampling uncertainty only; does not quantify AI-judgment reliability "
    "or independence."
)


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
        for numerator, denominator in zip(
            numerator_counts, denominator_counts, strict=True
        )
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
    taxonomy_only_statuses: list[str] = []
    manual_overlap_statuses: list[str] = []
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
            sum(
                status in {"Correct", "Incorrect"} for status in manual_overlap.values()
            )
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
            for is_exact, is_determinate in zip(
                exact_matches, determinate_exact, strict=True
            )
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
            taxonomy_only_correct / taxonomy_only_total if taxonomy_only_total else None
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
            crosscheck_exact / len(comparable_records) if comparable_records else None
        ),
        "food_groups_any_overlap_records": crosscheck_overlap,
        "food_groups_any_overlap_rate": (
            crosscheck_overlap / len(comparable_records) if comparable_records else None
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
