import csv
import importlib.util
import re
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = str(PROJECT_ROOT / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
PINNED_INPUTS_SPEC = importlib.util.spec_from_file_location(
    "pinned_inputs", PROJECT_ROOT / "scripts" / "support_pinned_inputs.py"
)
pinned_inputs = importlib.util.module_from_spec(PINNED_INPUTS_SPEC)
PINNED_INPUTS_SPEC.loader.exec_module(pinned_inputs)

STAGE5_SCRIPT = PROJECT_ROOT / "scripts" / "12_stage5_country_peer_evidence.py"
SPEC = importlib.util.spec_from_file_location(
    "stage5_country_peer_evidence", STAGE5_SCRIPT
)
stage5 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stage5)
AUDIT_SCRIPT = PROJECT_ROOT / "scripts" / "support_evaluate_mapping_audit_sample.py"
AUDIT_SPEC = importlib.util.spec_from_file_location(
    "evaluate_mapping_audit", AUDIT_SCRIPT
)
audit = importlib.util.module_from_spec(AUDIT_SPEC)
AUDIT_SPEC.loader.exec_module(audit)
QUEUE_SCRIPT = PROJECT_ROOT / "scripts" / "08_category_reporting_group_review_queues.py"
QUEUE_SPEC = importlib.util.spec_from_file_location(
    "category_review_queues", QUEUE_SCRIPT
)
review_queues = importlib.util.module_from_spec(QUEUE_SPEC)
QUEUE_SPEC.loader.exec_module(review_queues)
TAXONOMY_FETCH_SCRIPT = PROJECT_ROOT / "scripts" / "support_fetch_pinned_taxonomy.py"
TAXONOMY_FETCH_SPEC = importlib.util.spec_from_file_location(
    "fetch_pinned_taxonomy", TAXONOMY_FETCH_SCRIPT
)
taxonomy_fetch = importlib.util.module_from_spec(TAXONOMY_FETCH_SPEC)
TAXONOMY_FETCH_SPEC.loader.exec_module(taxonomy_fetch)


def test_readiness_distinguishes_brand_text_from_approved_mapping(
    synthetic_database,
) -> None:
    scorecard = stage5.build_readiness_scorecard(synthetic_database)
    indonesia = scorecard.loc[scorecard["iso_alpha2"].eq("ID")].set_index("metric")

    assert int(indonesia.loc["Brand text", "records_with_field"]) == 40
    assert (
        int(indonesia.loc["Exact-approved brand mapping", "records_with_field"]) == 20
    )
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


def test_online_evidence_audit_covers_every_selected_disputed_case() -> None:
    evidence = _read_csv(
        PROJECT_ROOT
        / "outputs"
        / "quality"
        / "category_mapping_online_evidence_audit.csv"
    )
    record_ids = [row["source_record_id"] for row in evidence]
    sample_records = _read_csv(
        PROJECT_ROOT
        / "outputs"
        / "quality"
        / "category_mapping_semantic_audit_records.csv"
    )
    expected_record_ids = {
        row["source_record_id"]
        for row in sample_records
        if any(
            status in row["candidate_assignment_statuses"].lower()
            for status in ("incorrect", "ambiguous", "insufficient evidence")
        )
        or row["assessment_status"].lower() in {"ambiguous", "insufficient_evidence"}
    }

    assert len(evidence) == 48
    assert len(set(record_ids)) == len(record_ids)
    assert set(record_ids) == expected_record_ids
    assert all(row["online_review_status"] != "not_yet_researched" for row in evidence)
    assert all(
        row["source_url"] for row in evidence if row["identifier_match"] == "yes"
    )
    assert all(
        row["identifier_match"] in {"", "yes", "no", "partial", "product_name"}
        for row in evidence
    )


def test_review_queue_candidates_match_reporting_group_framework() -> None:
    import pandas as pd

    framework = pd.DataFrame(
        {
            "group_id": ["beverages", "salty_snacks"],
            "reporting_group": ["Beverages", "Salty snacks"],
        }
    )
    anchors = pd.DataFrame({"group_id": ["beverages"]})
    crosswalk = pd.DataFrame(
        {
            "source_category_tag": ["en:drinks"],
            "candidate_group_ids": ["beverages | salty_snacks"],
            "candidate_group_labels": ["Beverages | Salty snacks"],
            "proposed_group_id": ["beverages"],
            "proposed_group_label": ["Beverages"],
            "manual_reporting_group_id": [""],
        }
    )

    review_queues.validate_reporting_group_references(framework, anchors, crosswalk)

    crosswalk.loc[0, "candidate_group_labels"] = "Beverages | Snacks"
    with pytest.raises(ValueError, match="does not match framework label"):
        review_queues.validate_reporting_group_references(framework, anchors, crosswalk)

    crosswalk.loc[0, "candidate_group_labels"] = "Beverages | Salty snacks"
    crosswalk.loc[0, "proposed_group_id"] = "unknown_group"
    with pytest.raises(ValueError, match="Unknown proposed reporting group"):
        review_queues.validate_reporting_group_references(framework, anchors, crosswalk)


def test_taxonomy_bootstrap_rejects_changed_upstream_content() -> None:
    taxonomy_fetch.validate_snapshot_metadata(
        taxonomy_fetch.EXPECTED_SIZE_BYTES,
        taxonomy_fetch.EXPECTED_SHA256,
    )

    with pytest.raises(ValueError, match="does not match the pinned snapshot"):
        taxonomy_fetch.validate_snapshot_metadata(
            taxonomy_fetch.EXPECTED_SIZE_BYTES + 1,
            taxonomy_fetch.EXPECTED_SHA256,
        )


def test_pinned_source_manifest_matches_reader_facing_documentation() -> None:
    source_note = (PROJECT_ROOT / "docs" / "02_data_source.md").read_text(
        encoding="utf-8"
    )
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    reproduction = (PROJECT_ROOT / "docs" / "09_reproduction.md").read_text(
        encoding="utf-8"
    )

    assert all(
        pinned_inputs.SNAPSHOT_COMMIT in text
        for text in (source_note, readme, reproduction)
    )
    assert all(
        pinned_inputs.SNAPSHOT_SHA256 in text
        for text in (source_note, readme, reproduction)
    )
    assert all(
        f"{pinned_inputs.SNAPSHOT_SIZE_BYTES:,}" in text
        for text in (source_note, reproduction)
    )
    assert pinned_inputs.TAXONOMY_URL in source_note
    assert pinned_inputs.TAXONOMY_RETRIEVED_ON in source_note
    assert pinned_inputs.TAXONOMY_SHA256 in source_note
    assert f"{pinned_inputs.TAXONOMY_SIZE_BYTES:,}" in source_note
    allowed_hashes = {pinned_inputs.SNAPSHOT_SHA256, pinned_inputs.TAXONOMY_SHA256}
    docs_dir = PROJECT_ROOT / "docs"
    markdown_files = [PROJECT_ROOT / "README.md", *docs_dir.rglob("*.md")]
    for markdown_file in markdown_files:
        documented_hashes = set(
            re.findall(
                r"\b[0-9A-Fa-f]{64}\b",
                markdown_file.read_text(encoding="utf-8"),
            )
        )
        assert documented_hashes <= allowed_hashes


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
        PROJECT_ROOT / "data" / "reference" / "category_reporting_group_framework.csv"
    )
    anchors = _read_csv(
        PROJECT_ROOT
        / "data"
        / "mappings"
        / "category_reporting_group_anchor_candidates.csv"
    )
    brands = _read_csv(
        PROJECT_ROOT / "data" / "mappings" / "brand_name_manual_decisions.csv"
    )
    country_mappings = _read_csv(
        PROJECT_ROOT / "data" / "mappings" / "country_tag_mapping.csv"
    )
    iso_units = _read_csv(PROJECT_ROOT / "data" / "reference" / "iso_3166_alpha2.csv")
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
    valid_iso_codes = {row["iso_alpha2"] for row in iso_units}

    assert len(valid_groups) == len(framework)
    assert len({row["reporting_group"] for row in framework}) == len(framework)
    assert all(row["review_status"] == "approved" for row in dispositions)
    assert len({row["source_category_tag"] for row in dispositions}) == len(
        dispositions
    )
    assert excluded_tags.isdisjoint(approved_group_tags)
    assert len(approved_group_tags) == len(decisions)
    assert all(row["review_status"] == "approved" for row in decisions)
    assert all(
        row["reporting_group_id"] in valid_groups
        for row in decisions
        if row["review_status"] == "approved"
    )
    assert len({row["anchor_tag"] for row in anchors}) == len(anchors)
    assert all(row["review_status"] == "candidate_only" for row in anchors)
    assert all(row["group_id"] in valid_groups for row in anchors)
    assert len({row["source_brand_name"] for row in brands}) == len(brands)
    assert all(row["review_status"] == "approved" for row in brands)
    assert len({row["source_country_tag"] for row in country_mappings}) == len(
        country_mappings
    )
    assert all(
        row["iso_alpha2"] in valid_iso_codes
        for row in country_mappings
        if row["mapping_status"] == "approved"
    )
    assert all(
        row["mapping_status"] in {"approved", "excluded", "review_required"}
        for row in country_mappings
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
