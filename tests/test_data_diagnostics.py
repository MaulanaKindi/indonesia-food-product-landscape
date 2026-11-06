import csv
import importlib.util
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STAGE5_SCRIPT = PROJECT_ROOT / "scripts" / "12_stage5_country_peer_evidence.py"
SPEC = importlib.util.spec_from_file_location("stage5_country_peer_evidence", STAGE5_SCRIPT)
stage5 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stage5)
AUDIT_SCRIPT = PROJECT_ROOT / "scripts" / "evaluate_mapping_audit_sample.py"
AUDIT_SPEC = importlib.util.spec_from_file_location("evaluate_mapping_audit", AUDIT_SCRIPT)
audit = importlib.util.module_from_spec(AUDIT_SPEC)
AUDIT_SPEC.loader.exec_module(audit)


def test_readiness_distinguishes_brand_text_from_approved_mapping(
    synthetic_database,
) -> None:
    scorecard = stage5.build_readiness_scorecard(synthetic_database)
    indonesia = scorecard.loc[scorecard["iso_alpha2"].eq("ID")].set_index("metric")

    assert int(indonesia.loc["Brand text", "records_with_field"]) == 40
    assert int(indonesia.loc["Exact-approved brand mapping", "records_with_field"]) == 20
    assert int(indonesia.loc["Category tags", "records_with_field"]) == 26
    assert int(indonesia.loc["Numeric nutrition value", "records_with_field"]) == 16
    assert int(indonesia.loc["Valid Nutri-Score (A-E)", "records_with_field"]) == 11


def test_country_code_overlap_uses_sets_and_reports_shared_source_records(
    synthetic_database,
) -> None:
    overlap = stage5.build_country_code_overlap(synthetic_database)
    indonesia_malaysia = overlap.loc[
        overlap["country_a"].eq("ID") & overlap["country_b"].eq("MY")
    ].iloc[0]

    assert int(indonesia_malaysia["shared_codes"]) == 5
    assert int(indonesia_malaysia["shared_source_record_ids"]) == 5
    assert indonesia_malaysia["jaccard_index"] == pytest.approx(5 / 140)
    assert len(overlap) == 6


def test_food_group_crosscheck_is_diagnostic_and_reports_its_coverage(
    synthetic_database,
    tmp_path,
) -> None:
    crosswalk = tmp_path / "food_group_crosswalk.csv"
    crosswalk.write_text(
        "food_group_tag,reporting_group_id,crosswalk_status,mapping_basis\n"
        "en:beverages,beverages,diagnostic_only,synthetic test\n",
        encoding="utf-8",
    )
    results = stage5.build_food_groups_crosscheck(synthetic_database, crosswalk)
    indonesia = results.loc[results["iso_alpha2"].eq("ID")].iloc[0]

    assert int(indonesia["records_with_food_group_tags"]) == 13
    assert int(indonesia["records_with_crosswalked_food_groups"]) == 13
    assert int(indonesia["records_compared"]) == 13
    assert int(indonesia["exact_group_set_matches"]) == 13
    assert float(indonesia["exact_group_set_match_pct"]) == 100.0


def test_audit_assignment_statuses_keep_uncertain_cases_in_denominators() -> None:
    records = [
        {
            "_assignment_statuses": {"beverages": "Correct"},
            "record_exact_set_status": "Agreement",
            "_assessment_status": "assessable",
            "_crosscheck_comparable": False,
            "_crosscheck_status": "not_comparable",
            "_manual_groups": set(),
            "_candidate_groups": {"beverages"},
            "_sampling_design": audit.PRIMARY_SAMPLE,
            "_missing_supported_groups": set(),
        },
        {
            "_assignment_statuses": {"beverages": "Ambiguous"},
            "record_exact_set_status": "Ambiguous",
            "_assessment_status": "ambiguous",
            "_crosscheck_comparable": False,
            "_crosscheck_status": "not_comparable",
            "_manual_groups": set(),
            "_candidate_groups": {"beverages"},
            "_sampling_design": audit.PRIMARY_SAMPLE,
            "_missing_supported_groups": set(),
        },
        {
            "_assignment_statuses": {"salty_snacks": "Insufficient evidence"},
            "record_exact_set_status": "Insufficient evidence",
            "_assessment_status": "insufficient_evidence",
            "_crosscheck_comparable": False,
            "_crosscheck_status": "not_comparable",
            "_manual_groups": set(),
            "_candidate_groups": {"salty_snacks"},
            "_sampling_design": audit.PRIMARY_SAMPLE,
            "_missing_supported_groups": set(),
        },
    ]
    metrics = audit.metric_rates(records, population_size=10)

    assert metrics["candidate_assignment_pairs"] == 3
    assert metrics["correct_assignments"] == 1
    assert metrics["ambiguous_assignments"] == 1
    assert metrics["insufficient_evidence_assignments"] == 1
    assert metrics["determinate_assignment_denominator"] == 1
    assert metrics["determinate_assignment_precision"] == 1
    assert metrics["confirmed_assignment_share_all_pairs"] == pytest.approx(1 / 3)
    assert metrics["record_exact_set_agreement_all_records"] == pytest.approx(1 / 3)
    assert metrics["ambiguity_rate"] == pytest.approx(1 / 3)
    assert metrics["insufficient_evidence_rate"] == pytest.approx(1 / 3)


def test_audit_ratio_interval_uses_finite_population_correction() -> None:
    interval = audit.linearized_ratio_ci(
        denominator_counts=[1, 1, 1, 1],
        numerator_counts=[1, 0, 1, 0],
        population_size=10,
    )

    assert interval == pytest.approx((0.061739, 0.938261), abs=1e-6)


def test_contributor_and_year_diagnostics_reconcile_to_country_rows(
    synthetic_database,
) -> None:
    summary, yearly = stage5.build_contributor_diagnostics(synthetic_database)
    indonesia = summary.loc[summary["iso_alpha2"].eq("ID")].iloc[0]
    indonesia_years = yearly.loc[yearly["iso_alpha2"].eq("ID")]

    assert int(indonesia["country_records"]) == 80
    assert int(indonesia["unique_creators"]) == 10
    assert int(indonesia["valid_year_records"]) == 80
    assert int(indonesia_years["year_records"].sum()) == 80
    assert int(indonesia["peak_creator_day_records"]) <= 80
    assert 0 <= float(indonesia["peak_creator_day_share_of_country_records_pct"]) <= 100
    assert 0 <= float(indonesia["top_5_category_tag_coverage_pct"]) <= 100
    assert 0 <= float(indonesia["other_named_creator_category_tag_coverage_pct"]) <= 100


def test_online_evidence_audit_covers_every_disputed_sample_record() -> None:
    evidence = _read_csv(
        PROJECT_ROOT
        / "outputs"
        / "quality"
        / "category_mapping_online_evidence_audit.csv"
    )
    record_ids = [row["source_record_id"] for row in evidence]

    assert len(evidence) == 48
    assert len(set(record_ids)) == len(record_ids)
    assert all(row["online_review_status"] != "not_yet_researched" for row in evidence)
    assert all(
        row["source_url"]
        for row in evidence
        if row["identifier_match"] == "yes"
    )
    assert all(
        row["identifier_match"] in {"", "yes", "no", "partial", "product_name"}
        for row in evidence
    )


def test_mapping_inputs_have_no_conflicting_decisions_or_invalid_groups() -> None:
    dispositions = _read_csv(
        PROJECT_ROOT / "data" / "mappings" / "category_tag_manual_dispositions.csv"
    )
    decisions = _read_csv(
        PROJECT_ROOT
        / "data"
        / "mappings"
        / "category_tag_reporting_group_manual_decisions.csv"
    )
    framework = _read_csv(
        PROJECT_ROOT
        / "data"
        / "reference"
        / "category_reporting_group_framework.csv"
    )
    food_group_crosswalk = _read_csv(
        PROJECT_ROOT
        / "data"
        / "reference"
        / "food_group_reporting_group_diagnostic_crosswalk.csv"
    )
    excluded_tags = {
        row["source_category_tag"]
        for row in dispositions
        if row["disposition"].startswith("exclude_")
        and row["review_status"] == "approved"
    }
    approved_group_tags = {
        row["source_category_tag"]
        for row in decisions
        if row["review_status"] == "approved"
    }
    valid_groups = {row["group_id"] for row in framework}

    assert excluded_tags.isdisjoint(approved_group_tags)
    assert all(
        row["reporting_group_id"] in valid_groups
        for row in decisions
        if row["review_status"] == "approved"
    )
    assert len({row["food_group_tag"] for row in food_group_crosswalk}) == len(
        food_group_crosswalk
    )
    assert all(
        row["crosswalk_status"] == "diagnostic_only"
        and row["reporting_group_id"] in valid_groups
        for row in food_group_crosswalk
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))
