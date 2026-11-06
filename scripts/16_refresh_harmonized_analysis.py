"""Refresh deterministic category harmonization and its validated analysis outputs."""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
PROFILE_DIR = OUTPUTS_DIR / "profiling"
QUALITY_DIR = OUTPUTS_DIR / "quality"
ANALYSIS_DIR = OUTPUTS_DIR / "analysis"
STAGE7_FILE = PROJECT_ROOT / "docs" / "06_stage7_findings_and_recommendations.md"
README_FILE = PROJECT_ROOT / "README.md"
BASELINE_DATABASE = PROCESSED_DIR / "global_product_landscape_five_country.duckdb"
BASELINE_VALIDATION = QUALITY_DIR / "database_build_validation_five_country.csv"
STAGE5_FILE = PROFILE_DIR / "stage5_country_peer_evidence.csv"
STAGE5_NAME = "stage5_country_peer_evidence.csv"
READINESS_FILE = PROFILE_DIR / "data_readiness_scorecard.csv"
CONTRIBUTOR_FILE = PROFILE_DIR / "contributor_year_diagnostics.csv"
YEARLY_FILE = PROFILE_DIR / "record_creation_year.csv"
SOURCE_TAG_FILE = PROFILE_DIR / "source_tag_coverage.csv"
OVERLAP_FILE = PROFILE_DIR / "country_code_overlap.csv"
FOOD_GROUP_FILE = PROFILE_DIR / "food_groups_crosscheck.csv"
SEMANTIC_AUDIT_RECORDS_FILE = (
    QUALITY_DIR / "category_mapping_semantic_audit_records.csv"
)
SEMANTIC_AUDIT_SUMMARY_FILE = (
    QUALITY_DIR / "category_mapping_semantic_audit_summary.csv"
)
SEMANTIC_AUDIT_GROUP_FILE = (
    QUALITY_DIR / "category_mapping_semantic_audit_by_group.csv"
)
VISUAL_DIR = PROJECT_ROOT / "docs" / "img"
VISUAL_NAMES = (
    "category_coverage.png",
    "category_assignment_coverage.png",
    "data_readiness_scorecard.png",
)
STAGE6_OUTPUTS = (
    "stage6_country_scope.csv",
    "stage6_country_category.csv",
    "stage6_country_brand.csv",
    "stage6_validation.csv",
)
STAGE6_CANDIDATE_VALIDATION = QUALITY_DIR / "stage6_candidate_build_validation.csv"
SUMMARY_FILE = QUALITY_DIR / "harmonization_refresh_summary.csv"
COUNTRIES = ("ID", "MY", "PH", "SG", "TH")
COUNTRY_ROLES = {
    "ID": "Focal",
    "MY": "Contextual peer",
    "PH": "Contextual peer",
    "SG": "Contextual peer",
    "TH": "Coverage contrast",
}
STAGE7_MARKERS = {
    "executive-summary": (
        "<!-- AUTO-GENERATED: executive-summary:START -->",
        "<!-- AUTO-GENERATED: executive-summary:END -->",
    ),
    "analysis-status": (
        "<!-- AUTO-GENERATED: analysis-status:START -->",
        "<!-- AUTO-GENERATED: analysis-status:END -->",
    ),
    "country-scope": (
        "<!-- AUTO-GENERATED: country-scope:START -->",
        "<!-- AUTO-GENERATED: country-scope:END -->",
    ),
    "top-groups": (
        "<!-- AUTO-GENERATED: top-groups:START -->",
        "<!-- AUTO-GENERATED: top-groups:END -->",
    ),
    "category-coverage": (
        "<!-- AUTO-GENERATED: category-coverage:START -->",
        "<!-- AUTO-GENERATED: category-coverage:END -->",
    ),
    "category-overlap": (
        "<!-- AUTO-GENERATED: category-overlap:START -->",
        "<!-- AUTO-GENERATED: category-overlap:END -->",
    ),
    "brand-coverage": (
        "<!-- AUTO-GENERATED: brand-coverage:START -->",
        "<!-- AUTO-GENERATED: brand-coverage:END -->",
    ),
    "brand-assignment-note": (
        "<!-- AUTO-GENERATED: brand-assignment-note:START -->",
        "<!-- AUTO-GENERATED: brand-assignment-note:END -->",
    ),
    "nonfood-sensitivity": (
        "<!-- AUTO-GENERATED: nonfood-sensitivity:START -->",
        "<!-- AUTO-GENERATED: nonfood-sensitivity:END -->",
    ),
    "data-readiness": (
        "<!-- AUTO-GENERATED: data-readiness:START -->",
        "<!-- AUTO-GENERATED: data-readiness:END -->",
    ),
    "contributor-diagnostics": (
        "<!-- AUTO-GENERATED: contributor-diagnostics:START -->",
        "<!-- AUTO-GENERATED: contributor-diagnostics:END -->",
    ),
    "country-code-overlap": (
        "<!-- AUTO-GENERATED: country-code-overlap:START -->",
        "<!-- AUTO-GENERATED: country-code-overlap:END -->",
    ),
    "food-groups-crosscheck": (
        "<!-- AUTO-GENERATED: food-groups-crosscheck:START -->",
        "<!-- AUTO-GENERATED: food-groups-crosscheck:END -->",
    ),
    "semantic-mapping-audit": (
        "<!-- AUTO-GENERATED: semantic-mapping-audit:START -->",
        "<!-- AUTO-GENERATED: semantic-mapping-audit:END -->",
    ),
}
README_MARKERS = {
    "headline-metrics": (
        "<!-- AUTO-GENERATED: headline-metrics:START -->",
        "<!-- AUTO-GENERATED: headline-metrics:END -->",
    ),
    "country-comparison": (
        "<!-- AUTO-GENERATED: country-comparison:START -->",
        "<!-- AUTO-GENERATED: country-comparison:END -->",
    ),
    "readiness-scorecard": (
        "<!-- AUTO-GENERATED: readiness-scorecard:START -->",
        "<!-- AUTO-GENERATED: readiness-scorecard:END -->",
    ),
}


def run_script(script_name: str, *arguments: str) -> None:
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / script_name),
        *arguments,
    ]
    print(f"\nRunning {script_name}...", flush=True)
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def load_semantic_audit_outputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    records = read_csv(SEMANTIC_AUDIT_RECORDS_FILE)
    summary = read_csv(SEMANTIC_AUDIT_SUMMARY_FILE)
    groups = read_csv(SEMANTIC_AUDIT_GROUP_FILE)
    required_summary_columns = {
        "analysis_scope",
        "sampling_frame_records",
        "records_reviewed",
        "candidate_assignment_pairs",
        "correct_assignments",
        "incorrect_assignments",
        "ambiguous_assignments",
        "insufficient_evidence_assignments",
        "exact_set_matches",
        "record_exact_set_agreement_all_records",
        "determinate_record_denominator",
        "record_exact_set_agreement_determinate_only",
        "record_exact_set_ci_low",
        "record_exact_set_ci_high",
        "ambiguous_record_count",
        "ambiguity_rate",
        "insufficient_evidence_record_count",
        "insufficient_evidence_rate",
        "taxonomy_only_candidate_assignment_pairs",
        "taxonomy_only_correct_assignments",
        "taxonomy_only_incorrect_assignments",
        "taxonomy_only_ambiguous_assignments",
        "taxonomy_only_insufficient_evidence_assignments",
        "taxonomy_only_determinate_denominator",
        "taxonomy_only_precision_ci_low",
        "taxonomy_only_precision_ci_high",
        "manual_overlap_correct_assignments",
        "manual_overlap_incorrect_assignments",
        "manual_overlap_ambiguous_assignments",
        "manual_overlap_insufficient_evidence_assignments",
        "manual_overlap_determinate_denominator",
        "manual_overlap_precision_ci_low",
        "manual_overlap_precision_ci_high",
        "manual_exact_overlap_assignment_pairs",
        "determinate_assignment_precision",
        "determinate_precision_ci_low",
        "determinate_precision_ci_high",
        "confirmed_assignment_share_all_pairs",
        "confirmed_share_ci_low",
        "confirmed_share_ci_high",
        "food_groups_comparable_records",
        "food_groups_exact_set_matches",
        "food_groups_exact_match_rate",
        "food_groups_any_overlap_records",
        "food_groups_any_overlap_rate",
        "determinate_records_with_supported_groups_missing_from_candidate",
        "determinate_reviewer_supported_group_pairs_missing_from_candidate",
    }
    if not required_summary_columns.issubset(summary.columns):
        raise ValueError(
            "Semantic audit summary is missing required columns: "
            f"{sorted(required_summary_columns - set(summary.columns))}"
        )
    expected_scopes = {"primary_sample", "meat_poultry_census"}
    if (
        len(summary) != 2
        or summary["analysis_scope"].duplicated().any()
        or set(summary["analysis_scope"]) != expected_scopes
    ):
        raise ValueError(
            "Semantic audit summary must contain the primary sample and "
            "separate Meat & poultry census."
        )
    primary = summary.loc[summary["analysis_scope"].eq("primary_sample")].iloc[0]
    census = summary.loc[
        summary["analysis_scope"].eq("meat_poultry_census")
    ].iloc[0]
    if (
        int(primary["sampling_frame_records"]) != 1_111
        or int(primary["records_reviewed"]) != 150
        or int(census["sampling_frame_records"]) != 8
        or int(census["records_reviewed"]) != 8
        or len(records) != 158
        or records["sampling_design"].value_counts().to_dict()
        != {"primary_sample": 150, "meat_poultry_census": 8}
    ):
        raise ValueError("Semantic audit outputs do not match the reviewed sample.")
    if set(records["sampling_design"]) != expected_scopes:
        raise ValueError("Semantic audit record output has unexpected scope values.")
    if not {
        "reporting_group_id",
        "analysis_scope",
        "candidate_assignment_records",
        "correct_assignments",
        "incorrect_assignments",
        "ambiguous_assignments",
        "insufficient_evidence_assignments",
        "determinate_assignment_denominator",
        "determinate_assignment_precision",
        "determinate_precision_ci_low",
        "determinate_precision_ci_high",
    }.issubset(groups.columns):
        raise ValueError("Semantic audit per-group output is incomplete.")
    if (
        set(groups["analysis_scope"]) != expected_scopes
        or len(groups) != 20
        or groups.duplicated(["analysis_scope", "reporting_group_id"]).any()
    ):
        raise ValueError("Semantic audit per-group output has unexpected scope or rows.")
    for row in summary.itertuples(index=False):
        classified_pairs = sum(
            int(getattr(row, column))
            for column in (
                "correct_assignments",
                "incorrect_assignments",
                "ambiguous_assignments",
                "insufficient_evidence_assignments",
            )
        )
        group_pairs = int(
            groups.loc[
                groups["analysis_scope"].eq(row.analysis_scope),
                "candidate_assignment_records",
            ].astype(int).sum()
        )
        if (
            classified_pairs != int(row.candidate_assignment_pairs)
            or group_pairs != int(row.candidate_assignment_pairs)
        ):
            raise ValueError(
                f"Semantic audit assignment totals do not reconcile for "
                f"{row.analysis_scope}."
            )
    return records, summary, groups


def validate_report(path: Path, expected_rows: int, label: str) -> pd.DataFrame:
    report = read_csv(path)
    required = {"actual_value", "expected_value", "status"}
    if len(report) != expected_rows or not required.issubset(report.columns):
        raise ValueError(f"{label} report is incomplete or malformed: {path}")
    if not (
        report["status"].eq("passed")
        & report["actual_value"].eq(report["expected_value"])
    ).all():
        raise ValueError(f"{label} report contains failed checks: {path}")
    return report


def replace_generated_section(
    document: str,
    section_name: str,
    content: str,
) -> str:
    start_marker, end_marker = STAGE7_MARKERS[section_name]
    if document.count(start_marker) != 1 or document.count(end_marker) != 1:
        raise ValueError(
            f"Expected exactly one pair of Stage 7 markers for {section_name}."
        )
    start = document.index(start_marker) + len(start_marker)
    end = document.index(end_marker)
    if start >= end:
        raise ValueError(f"Stage 7 markers are out of order: {section_name}")
    return document[:start] + "\n" + content.rstrip() + "\n" + document[end:]


def replace_readme_section(
    document: str,
    section_name: str,
    content: str,
) -> str:
    start_marker, end_marker = README_MARKERS[section_name]
    if document.count(start_marker) != 1 or document.count(end_marker) != 1:
        raise ValueError(
            f"Expected exactly one pair of README markers for {section_name}."
        )
    start = document.index(start_marker) + len(start_marker)
    end = document.index(end_marker)
    if start >= end:
        raise ValueError(f"README markers are out of order: {section_name}")
    return document[:start] + "\n" + content.rstrip() + "\n" + document[end:]


def render_readme(
    document: str,
    country_evidence: pd.DataFrame,
    scope: pd.DataFrame,
    categories: pd.DataFrame,
    readiness: pd.DataFrame,
    semantic_audit_summary: pd.DataFrame,
) -> str:
    scope_baseline = scope.loc[scope["scenario"].eq("baseline")].set_index(
        "iso_alpha2"
    )
    evidence_by_country = country_evidence.set_index("iso_alpha2")
    candidate = categories.loc[
        categories["scenario"].eq("baseline")
        & categories["assignment_basis"].eq("candidate_derived")
    ].drop_duplicates("iso_alpha2").set_index("iso_alpha2")
    approved = categories.loc[
        categories["scenario"].eq("baseline")
        & categories["assignment_basis"].eq("approved_only")
    ].drop_duplicates("iso_alpha2").set_index("iso_alpha2")
    readiness_by_field = readiness.set_index(["iso_alpha2", "metric"])

    indonesia = scope_baseline.loc["ID"]
    peers = [
        float(scope_baseline.loc[iso, "category_tags_coverage_pct"])
        for iso in ("MY", "PH", "SG")
    ]
    id_candidate = candidate.loc["ID"]
    id_approved = approved.loc["ID"]
    id_brand = evidence_by_country.loc["ID"]
    audit = semantic_audit_summary.loc[
        semantic_audit_summary["analysis_scope"].eq("primary_sample")
    ].iloc[0]
    audit_unresolved = int(audit["ambiguous_assignments"]) + int(
        audit["insufficient_evidence_assignments"]
    )
    headline = "\n".join(
        [
            (
                f"- **Category coverage:** {float(indonesia['category_tags_coverage_pct']):.1f}% "
                f"of Indonesian records are tagged, versus {min(peers):.1f}%–"
                f"{max(peers):.1f}% in the contextual peers and "
                f"{float(scope_baseline.loc['TH', 'category_tags_coverage_pct']):.1f}% "
                "in Thailand, the separate coverage contrast."
            ),
            (
                f"- **Category assignments in Indonesia:** "
                f"{int(id_candidate['source_rows_assigned_to_any_substantive_group']):,} "
                f"of {int(indonesia['source_rows_with_category_tags']):,} tagged "
                f"records ({float(id_candidate['substantive_group_assignment_coverage_of_category_tagged_rows_pct']):.1f}%) "
                f"receive at least one candidate-derived group; "
                f"{int(id_approved['source_rows_assigned_to_any_substantive_group']):,} "
                f"({float(id_approved['substantive_group_assignment_coverage_of_category_tagged_rows_pct']):.1f}%) "
                "do under the stricter approved-only view."
            ),
            (
                f"- **Brand evidence:** raw brand text is present for "
                f"{float(readiness_by_field.loc[('ID', 'Brand text'), 'coverage_pct']):.1f}% "
                f"of Indonesian records, while exact-approved mapping covers only "
                f"{float(id_brand['approved_brand_mapping_coverage_pct_of_country_rows']):.2f}%."
            ),
            (
                f"- **AI-assisted mapping check:** {int(audit['correct_assignments'])}/"
                f"{int(audit['candidate_assignment_pairs'])} candidate assignments "
                f"were judged correct ({int(audit['manual_exact_overlap_assignment_pairs'])} "
                f"also have exact-manual mappings); {int(audit['incorrect_assignments'])} disagreed "
                f"and {audit_unresolved} were unresolved. Exact group-set agreement "
                f"was {int(audit['exact_set_matches'])}/"
                f"{int(audit['records_reviewed'])} "
                f"({100 * float(audit['record_exact_set_agreement_all_records']):.1f}%). "
                "AI assessment, not human ground truth; "
                "[record-level audit](outputs/quality/category_mapping_semantic_audit_records.csv)."
            ),
        ]
    )
    document = replace_readme_section(document, "headline-metrics", headline)

    country_rows = []
    for iso in COUNTRIES:
        row = scope_baseline.loc[iso]
        candidate_row = candidate.loc[iso]
        approved_row = approved.loc[iso]
        brand_row = evidence_by_country.loc[iso]
        country_rows.append(
            f"| {iso} | {COUNTRY_ROLES[iso]} | {int(row['source_rows']):,} | "
            f"{int(row['source_rows_with_category_tags']):,} | "
            f"{float(row['category_tags_coverage_pct']):.2f}% | "
            f"{int(candidate_row['source_rows_assigned_to_any_substantive_group']):,} "
            f"({float(candidate_row['substantive_group_assignment_coverage_of_category_tagged_rows_pct']):.1f}%) | "
            f"{int(approved_row['source_rows_assigned_to_any_substantive_group']):,} "
            f"({float(approved_row['substantive_group_assignment_coverage_of_category_tagged_rows_pct']):.1f}%) | "
            f"{int(brand_row['source_rows_with_approved_brand_mapping']):,} "
            f"({float(brand_row['approved_brand_mapping_coverage_pct_of_country_rows']):.2f}%) |"
        )
    document = replace_readme_section(
        document,
        "country-comparison",
        "\n".join(
            [
                "| Country | Role | Records | Category-tagged | Tag coverage | Candidate-derived assigned | Approved-only assigned | Exact-approved brand mapped |",
                "|---|---|---:|---:|---:|---:|---:|---:|",
                *country_rows,
            ]
        ),
    )

    readiness_metrics = (
        ("Brand text", "Brand text"),
        ("Category tags", "Category tags"),
        ("Ingredient text", "Ingredients"),
        ("Numeric nutrition value", "Numeric nutrition"),
        ("Valid Nutri-Score (A-E)", "Valid Nutri-Score"),
        ("Packaging information", "Packaging"),
        ("Label information", "Labels"),
        ("Exact-approved brand mapping", "Exact-approved brand map"),
    )
    readiness_rows = []
    for iso in COUNTRIES:
        cells = [
            f"{float(readiness_by_field.loc[(iso, metric), 'coverage_pct']):.1f}%"
            for metric, _ in readiness_metrics
        ]
        readiness_rows.append(f"| {iso} | " + " | ".join(cells) + " |")
    document = replace_readme_section(
        document,
        "readiness-scorecard",
        "\n".join(
            [
                "| ISO | Brand text | Category tags | Ingredients | Numeric nutrition | Valid Nutri-Score | Packaging | Labels | Exact-approved brand map |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
                *readiness_rows,
            ]
        ),
    )
    return document


def render_stage7(
    document: str,
    country_evidence: pd.DataFrame,
    scope: pd.DataFrame,
    categories: pd.DataFrame,
    brands: pd.DataFrame,
    readiness: pd.DataFrame,
    contributors: pd.DataFrame,
    source_tags: pd.DataFrame,
    overlap: pd.DataFrame,
    food_groups: pd.DataFrame,
    semantic_audit_records: pd.DataFrame,
    semantic_audit_summary: pd.DataFrame,
    semantic_audit_groups: pd.DataFrame,
    candidate_check_count: int,
    stage6_check_count: int,
) -> str:
    evidence_by_country = country_evidence.set_index("iso_alpha2")
    scope_baseline = scope.loc[scope["scenario"].eq("baseline")].set_index(
        "iso_alpha2"
    )
    readiness_by_field = readiness.set_index(["iso_alpha2", "metric"])
    contributors_by_country = contributors.set_index("iso_alpha2")
    source_tags = source_tags.copy()
    source_tags["source_rank"] = pd.to_numeric(
        source_tags["source_rank"], errors="raise"
    )
    overlap = overlap.copy()
    overlap["jaccard_index"] = pd.to_numeric(
        overlap["jaccard_index"], errors="raise"
    )
    candidate_categories = categories.loc[
        categories["scenario"].eq("baseline")
        & categories["assignment_basis"].eq("candidate_derived")
    ].copy()
    approved_categories = categories.loc[
        categories["scenario"].eq("baseline")
        & categories["assignment_basis"].eq("approved_only")
    ].copy()
    candidate_categories["group_source_rows"] = pd.to_numeric(
        candidate_categories["group_source_rows"], errors="raise"
    )
    id_row = scope_baseline.loc["ID"]
    id_category_rows = candidate_categories.loc[
        candidate_categories["iso_alpha2"].eq("ID")
    ].iloc[0]
    id_approved_row = approved_categories.loc[
        approved_categories["iso_alpha2"].eq("ID")
    ].iloc[0]
    top5_shares = pd.to_numeric(
        contributors_by_country["top_5_creator_share_pct"], errors="raise"
    )
    highest_overlap = overlap.sort_values(
        ["jaccard_index", "country_a", "country_b"],
        ascending=[False, True, True],
    ).iloc[0]
    headline = "\n".join(
        [
            (
                f"- **Recorded category coverage:** Indonesia has "
                f"{float(id_row['category_tags_coverage_pct']):.1f}% tagged "
                f"records; the contextual peers range from "
                f"{min(float(scope_baseline.loc[iso, 'category_tags_coverage_pct']) for iso in ('MY', 'PH', 'SG')):.1f}% "
                f"to {max(float(scope_baseline.loc[iso, 'category_tags_coverage_pct']) for iso in ('MY', 'PH', 'SG')):.1f}%, "
                f"while Thailand is {float(scope_baseline.loc['TH', 'category_tags_coverage_pct']):.1f}%."
            ),
            (
                f"- **Category assignments in Indonesia:** "
                f"{int(id_category_rows['source_rows_assigned_to_any_substantive_group']):,} "
                f"of {int(id_row['source_rows_with_category_tags']):,} tagged "
                f"records ({float(id_category_rows['substantive_group_assignment_coverage_of_category_tagged_rows_pct']):.1f}%) "
                f"are assigned in the candidate-derived view; the approved-only "
                f"view assigns {int(id_approved_row['source_rows_assigned_to_any_substantive_group']):,} "
                f"({float(id_approved_row['substantive_group_assignment_coverage_of_category_tagged_rows_pct']):.1f}%)."
            ),
            (
                f"- **Brand and field readiness:** raw brand text is present for "
                f"{float(readiness_by_field.loc[('ID', 'Brand text'), 'coverage_pct']):.1f}% "
                f"of Indonesian records, but exact-approved brand mappings cover "
                f"{float(readiness_by_field.loc[('ID', 'Exact-approved brand mapping'), 'coverage_pct']):.2f}%; "
                f"numeric nutrition data is present for "
                f"{float(readiness_by_field.loc[('ID', 'Numeric nutrition value'), 'coverage_pct']):.1f}%."
            ),
            (
                f"- **Contributor concentration:** the top five creators account "
                f"for {float(contributors_by_country.loc['ID', 'top_5_creator_share_pct']):.1f}% "
                f"of Indonesian records; across the selected countries the range "
                f"is {top5_shares.min():.1f}%–{top5_shares.max():.1f}%. This is a "
                "record-concentration diagnostic, not proof of data fragility."
            ),
            (
                f"- **Identifier overlap:** the largest code-based Jaccard value "
                f"is {100 * float(highest_overlap['jaccard_index']):.4f}% "
                f"({highest_overlap['country_a']}–{highest_overlap['country_b']}); "
                f"{int(highest_overlap['shared_source_record_ids']):,} shared "
                "source-record IDs are reported separately."
            ),
        ]
    )
    document = replace_generated_section(document, "executive-summary", headline)
    document = replace_generated_section(
        document,
        "analysis-status",
        (
            "Stage 6 was rerun against the separately validated five-country candidate "
            "database after the approved category mappings were applied. It "
            f"generated {len(scope):,} country-scenario rows, "
            f"{len(categories):,} country-category rows, and {len(brands):,} "
            "mapped-brand assignment rows. The candidate build passed "
            f"{candidate_check_count} checks and all {stage6_check_count} "
            "Stage 6 checks passed; the four published CSVs are byte-identical "
            "to the validated candidate run. These checks establish the tested "
            "reconciliations and arithmetic for the pinned inputs; they do not "
            "prove all mappings semantically correct or the data representative."
        ),
    )

    country_rows = []
    for iso in COUNTRIES:
        row = scope_baseline.loc[iso]
        country_rows.append(
            f"| {iso} | {COUNTRY_ROLES[iso]} | {int(row['source_rows']):,} "
            f"| {int(row['source_rows_with_category_tags']):,} "
            f"| {float(row['category_tags_coverage_pct']):.4f}% |"
        )
    document = replace_generated_section(
        document,
        "country-scope",
        "\n".join(
            [
                "| ISO | Role | Source rows | Rows with `categories_tags` | Category-tag coverage |",
                "|---|---|---:|---:|---:|",
                *country_rows,
            ]
        ),
    )

    top_group_rows = []
    for iso in COUNTRIES:
        rows = candidate_categories.loc[
            candidate_categories["iso_alpha2"].eq(iso)
        ].nlargest(3, "group_source_rows")
        if len(rows) != 3:
            raise ValueError(f"Expected three candidate groups for {iso}.")
        first, second, third = rows.itertuples(index=False)
        top_group_rows.append(
            f"| {iso} | {first.reporting_group_label} | "
            f"{int(first.group_source_rows):,} | "
            f"{float(first.group_share_of_country_rows_pct):.4f}% | "
            f"{second.reporting_group_label} | "
            f"{int(second.group_source_rows):,} | "
            f"{third.reporting_group_label} | "
            f"{int(third.group_source_rows):,} |"
        )
    document = replace_generated_section(
        document,
        "top-groups",
        "\n".join(
            [
                "| ISO | Largest group | Rows | Share of country rows | Next largest | Rows | Third largest | Rows |",
                "|---|---|---:|---:|---|---:|---|---:|",
                *top_group_rows,
            ]
        ),
    )

    coverage_rows = []
    for iso in COUNTRIES:
        country_categories = categories.loc[
            categories["iso_alpha2"].eq(iso)
            & categories["scenario"].eq("baseline")
        ]
        by_basis = country_categories.drop_duplicates("assignment_basis").set_index(
            "assignment_basis"
        )
        candidate = by_basis.loc["candidate_derived"]
        approved = by_basis.loc["approved_only"]
        coverage_rows.append(
            f"| {iso} | {int(candidate['source_rows_with_category_tags']):,} "
            f"| {int(candidate['source_rows_assigned_to_any_substantive_group']):,} "
            f"| {int(candidate['category_tagged_rows_without_substantive_group_assignment']):,} "
            f"| {int(approved['source_rows_assigned_to_any_substantive_group']):,} "
            f"| {int(approved['category_tagged_rows_without_substantive_group_assignment']):,} |"
        )
    document = replace_generated_section(
        document,
        "category-coverage",
        "\n".join(
            [
                "| ISO | Category-tagged rows | Candidate-derived assigned | Candidate-derived tagged rows without assignment | Approved-only assigned | Approved-only tagged rows without assignment |",
                "|---|---:|---:|---:|---:|---:|",
                *coverage_rows,
            ]
        ),
    )
    overlap_counts = []
    for iso in COUNTRIES:
        rows = candidate_categories.loc[
            candidate_categories["iso_alpha2"].eq(iso)
        ]
        if rows.empty:
            raise ValueError(f"Candidate category results are missing {iso}.")
        overlap_counts.append(
            f"{iso} {int(rows.iloc[0]['source_rows_in_multiple_groups']):,}"
        )
    document = replace_generated_section(
        document,
        "category-overlap",
        (
            "There are also rows assigned to multiple groups in the "
            "candidate-derived view: "
            + ", ".join(overlap_counts[:-1])
            + f", and {overlap_counts[-1]}. These overlap counts are diagnostics "
            "and must not be added to category totals as if groups formed a "
            "partition."
        ),
    )

    brand_rows = []
    for iso in COUNTRIES:
        row = evidence_by_country.loc[iso]
        brand_rows.append(
            f"| {iso} | {int(row['source_rows_with_approved_brand_mapping']):,} "
            f"| {float(row['approved_brand_mapping_coverage_pct_of_country_rows']):.4f}% |"
        )
    document = replace_generated_section(
        document,
        "brand-coverage",
        "\n".join(
            [
                "| ISO | Rows with approved exact brand mapping | Share of country rows |",
                "|---|---:|---:|",
                *brand_rows,
            ]
        ),
    )
    document = replace_generated_section(
        document,
        "brand-assignment-note",
        (
            f"Stage 6's {len(brands):,} rows are assignments across scenarios, "
            "assignment bases, country-category groups, and mapped canonical "
            f"names; they are not {brands['canonical_brand_name'].nunique():,} "
            "distinct brands or an exhaustive brand census."
        ),
    )

    sensitivity_rows = []
    for iso in COUNTRIES:
        country_scenarios = scope.loc[scope["iso_alpha2"].eq(iso)].set_index(
            "scenario"
        )
        except_strong = int(
            country_scenarios.loc[
                "exclude_A_B_except_strong_food_signals", "excluded_source_rows"
            ]
        )
        all_a_b = int(
            country_scenarios.loc["exclude_all_A_B", "excluded_source_rows"]
        )
        sensitivity_rows.append(f"| {iso} | {except_strong:,} | {all_a_b:,} |")
    document = replace_generated_section(
        document,
        "nonfood-sensitivity",
        "\n".join(
            [
                "| ISO | `exclude_A_B_except_strong_food_signals` | `exclude_all_A_B` |",
                "|---|---:|---:|",
                *sensitivity_rows,
            ]
        ),
    )

    readiness_metrics = (
        ("Brand text", "Brand text"),
        ("Category tags", "Category tags"),
        ("Ingredient text", "Ingredient text"),
        ("Numeric nutrition value", "Numeric nutrition"),
        ("Valid Nutri-Score (A-E)", "Nutri-Score"),
        ("Packaging information", "Packaging"),
        ("Label information", "Labels"),
        ("Exact-approved brand mapping", "Exact-approved brand map"),
    )
    readiness_rows = []
    for iso in COUNTRIES:
        values = [
            f"{float(readiness_by_field.loc[(iso, metric), 'coverage_pct']):.1f}%"
            for metric, _ in readiness_metrics
        ]
        readiness_rows.append(
            f"| {iso} | " + " | ".join(values) + " |"
        )
    document = replace_generated_section(
        document,
        "data-readiness",
        "\n".join(
            [
                "| ISO | Brand text | Category tags | Ingredient text | Numeric nutrition | Valid Nutri-Score | Packaging | Labels | Exact-approved brand map |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
                *readiness_rows,
            ]
        ),
    )

    contributor_rows = []
    for iso in COUNTRIES:
        row = contributors_by_country.loc[iso]
        peak_year = int(row["peak_creation_year"])
        contributor_rows.append(
            f"| {iso} | {int(row['unique_creators']):,} | "
            f"{float(row['top_5_creator_share_pct']):.2f}% | {peak_year} | "
            f"{float(row['peak_year_share_of_dated_records_pct']):.2f}% | "
            f"{float(row['peak_day_share_of_dated_records_pct']):.2f}% |"
        )
    document = replace_generated_section(
        document,
        "contributor-diagnostics",
        "\n".join(
            [
                "| ISO | Distinct creator values | Top-five creator share | Peak creation year | Peak-year share of dated rows | Peak-day share of dated rows |",
                "|---|---:|---:|---:|---:|---:|",
                *contributor_rows,
                "",
                "Top three `data_sources_tags` by record count for Indonesia and Thailand:",
                "",
                "| ISO | Source tag | Records | Country-record share | Category-tag coverage within source-tagged records |",
                "|---|---|---:|---:|---:|",
                *[
                    f"| {row.iso_alpha2} | `{row.data_source_tag}` | "
                    f"{int(row.tagged_records):,} | "
                    f"{float(row.share_of_country_records_pct):.2f}% | "
                    f"{float(row.category_tag_coverage_pct):.2f}% |"
                    for row in source_tags.loc[
                        source_tags["iso_alpha2"].isin(("ID", "TH"))
                    ]
                    .sort_values(["iso_alpha2", "source_rank"])
                    .groupby("iso_alpha2", sort=True)
                    .head(3)
                    .itertuples(index=False)
                ],
            ]
        ),
    )

    overlap_rows = [
        f"| {row.country_a} | {row.country_b} | {int(row.shared_codes):,} | "
        f"{int(row.shared_source_record_ids):,} | "
        f"{100 * float(row.jaccard_index):.4f}% |"
        for row in overlap.itertuples(index=False)
    ]
    document = replace_generated_section(
        document,
        "country-code-overlap",
        "\n".join(
            [
                "| Country A | Country B | Shared codes | Shared source-record IDs | Code Jaccard index |",
                "|---|---|---:|---:|---:|",
                *overlap_rows,
            ]
        ),
    )

    food_group_rows = [
        f"| {row.iso_alpha2} | {int(row.records_with_food_group_tags):,} | "
        f"{int(row.records_with_crosswalked_food_groups):,} | "
        f"{int(row.records_compared):,} | "
        f"{float(row.exact_group_set_match_pct):.2f}% | "
        f"{float(row.any_group_overlap_pct):.2f}% |"
        for row in food_groups.itertuples(index=False)
    ]
    document = replace_generated_section(
        document,
        "food-groups-crosscheck",
        "\n".join(
            [
                "| ISO | Rows with food-group tags | Rows covered by diagnostic crosswalk | Rows compared to candidate groups | Exact group-set agreement | Any group overlap |",
                "|---|---:|---:|---:|---:|---:|",
                *food_group_rows,
            ]
        ),
    )

    audit_primary = semantic_audit_summary.loc[
        semantic_audit_summary["analysis_scope"].eq("primary_sample")
    ].iloc[0]
    audit_census = semantic_audit_summary.loc[
        semantic_audit_summary["analysis_scope"].eq("meat_poultry_census")
    ].iloc[0]
    meat_census_group = semantic_audit_groups.loc[
        semantic_audit_groups["analysis_scope"].eq("meat_poultry_census")
        & semantic_audit_groups["reporting_group_id"].eq("meat_poultry")
    ].iloc[0]

    def assignment_rate(
        correct: int,
        incorrect: int,
    ) -> str:
        denominator = correct + incorrect
        if denominator == 0:
            return "Not estimable"
        return f"{correct}/{denominator} ({100 * correct / denominator:.1f}%)"

    def interval(low: str, high: str) -> str:
        if not low or not high:
            return "Not reported"
        return f"{100 * float(low):.1f}%–{100 * float(high):.1f}%"

    group_rows = []
    primary_groups = semantic_audit_groups.loc[
        semantic_audit_groups["analysis_scope"].eq("primary_sample")
    ].sort_values("reporting_group_id")
    for row in primary_groups.itertuples(index=False):
        determined = int(row.determinate_assignment_denominator)
        ratio = (
            f"{int(row.correct_assignments)}/{determined} "
            f"({100 * int(row.correct_assignments) / determined:.1f}%)"
            if determined
            else "Not estimable"
        )
        group_rows.append(
            f"| `{row.reporting_group_id}` | "
            f"{int(row.candidate_assignment_records)} | "
            f"{int(row.correct_assignments)} | "
            f"{int(row.incorrect_assignments)} | "
            f"{int(row.ambiguous_assignments)} | "
            f"{int(row.insufficient_evidence_assignments)} | "
            f"{ratio} | "
            f"{interval(row.determinate_precision_ci_low, row.determinate_precision_ci_high)} |"
        )

    provenance_rows = [
        (
            "Taxonomy-only",
            int(audit_primary["taxonomy_only_candidate_assignment_pairs"]),
            int(audit_primary["taxonomy_only_correct_assignments"]),
            int(audit_primary["taxonomy_only_incorrect_assignments"]),
            int(audit_primary["taxonomy_only_ambiguous_assignments"]),
            int(audit_primary["taxonomy_only_insufficient_evidence_assignments"]),
            int(audit_primary["taxonomy_only_determinate_denominator"]),
            audit_primary["taxonomy_only_precision_ci_low"],
            audit_primary["taxonomy_only_precision_ci_high"],
        ),
        (
            "Also exact-manual mapped",
            int(audit_primary["manual_exact_overlap_assignment_pairs"]),
            int(audit_primary["manual_overlap_correct_assignments"]),
            int(audit_primary["manual_overlap_incorrect_assignments"]),
            int(audit_primary["manual_overlap_ambiguous_assignments"]),
            int(audit_primary["manual_overlap_insufficient_evidence_assignments"]),
            int(audit_primary["manual_overlap_determinate_denominator"]),
            audit_primary["manual_overlap_precision_ci_low"],
            audit_primary["manual_overlap_precision_ci_high"],
        ),
    ]
    provenance_table = []
    for (
        label,
        pairs,
        correct,
        incorrect,
        ambiguous,
        insufficient,
        determinate,
        ci_low,
        ci_high,
    ) in provenance_rows:
        provenance_table.append(
            f"| {label} | {pairs} | {correct} | {incorrect} | {ambiguous} | "
            f"{insufficient} | {assignment_rate(correct, incorrect)} | "
            f"{interval(ci_low, ci_high)} |"
        )

    official_source_rows = []
    sourced_records = semantic_audit_records.loc[
        semantic_audit_records["external_evidence_reference"].str.strip().ne("")
    ].sort_values("source_record_id")
    for row in sourced_records.itertuples(index=False):
        rationale = row.rationale.replace("|", "\\|")
        product_name = row.product_name.replace("|", "\\|")
        sources = "; ".join(
            f"[Official source]({url.strip()})"
            for url in row.external_evidence_reference.split("|")
            if url.strip()
        )
        official_source_rows.append(
            f"| {row.source_record_id} | {product_name} | "
            f"{rationale} | {sources} ({row.external_evidence_access_date}) |"
        )

    audit_section = "\n".join(
        [
            "### Primary sample and separate census",
            "",
            "The primary sample contains "
            f"{int(audit_primary['records_reviewed'])} of "
            f"{int(audit_primary['sampling_frame_records']):,} Indonesian "
            "category-tagged records, selected deterministically by MD5 rank. "
            "The separate Meat & poultry census is reported descriptively and "
            "is not pooled with the primary estimate.",
            "",
            "| Scope | Records reviewed | Candidate group pairs | Correct | Incorrect | Ambiguous | Insufficient evidence | Confirmed share of all pairs | Exact-set matches |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            (
                f"| Primary sample | {int(audit_primary['records_reviewed'])}/"
                f"{int(audit_primary['sampling_frame_records']):,} | "
                f"{int(audit_primary['candidate_assignment_pairs'])} | "
                f"{int(audit_primary['correct_assignments'])} | "
                f"{int(audit_primary['incorrect_assignments'])} | "
                f"{int(audit_primary['ambiguous_assignments'])} | "
                f"{int(audit_primary['insufficient_evidence_assignments'])} | "
                f"{100 * float(audit_primary['confirmed_assignment_share_all_pairs']):.1f}% | "
                f"{int(audit_primary['exact_set_matches'])}/"
                f"{int(audit_primary['records_reviewed'])} "
                f"({100 * float(audit_primary['record_exact_set_agreement_all_records']):.1f}%) |"
            ),
            (
                f"| Meat & poultry census | {int(audit_census['records_reviewed'])}/"
                f"{int(audit_census['sampling_frame_records'])} | "
                f"{int(audit_census['candidate_assignment_pairs'])} | "
                f"{int(audit_census['correct_assignments'])} | "
                f"{int(audit_census['incorrect_assignments'])} | "
                f"{int(audit_census['ambiguous_assignments'])} | "
                f"{int(audit_census['insufficient_evidence_assignments'])} | "
                f"{100 * float(audit_census['confirmed_assignment_share_all_pairs']):.1f}% | "
                f"{int(audit_census['exact_set_matches'])}/"
                f"{int(audit_census['records_reviewed'])} "
                f"({100 * float(audit_census['record_exact_set_agreement_all_records']):.1f}%) |"
            ),
            "",
            "### Assignment-level estimates and provenance",
            "",
            f"Primary-sample determinate assignment precision is "
            f"{assignment_rate(int(audit_primary['correct_assignments']), int(audit_primary['incorrect_assignments']))}; "
            f"its approximate 95% interval is "
            f"{interval(audit_primary['determinate_precision_ci_low'], audit_primary['determinate_precision_ci_high'])}. "
            f"Counting ambiguous and insufficient-evidence assignments as not confirmed, "
            f"the all-pairs confirmed share is "
            f"{int(audit_primary['correct_assignments'])}/"
            f"{int(audit_primary['candidate_assignment_pairs'])} "
            f"({100 * float(audit_primary['confirmed_assignment_share_all_pairs']):.1f}%), "
            f"with interval "
            f"{interval(audit_primary['confirmed_share_ci_low'], audit_primary['confirmed_share_ci_high'])}.",
            "",
            "| Candidate provenance | Pairs | Correct | Incorrect | Ambiguous | Insufficient evidence | Determinate precision | Approximate 95% interval |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
            *provenance_table,
            "",
            "The combined 130 pairs include 26 pairs also supported by an exact-manual mapping; they are not all taxonomy-only candidates. Taxonomy-only precision is "
            f"{assignment_rate(int(audit_primary['taxonomy_only_correct_assignments']), int(audit_primary['taxonomy_only_incorrect_assignments']))}; "
            "the overlap subset is shown separately because its agreement differs.",
            "",
            "### Per-group determinate precision",
            "",
            "Precision uses correct / (correct + incorrect); ambiguous and insufficient-evidence pairs are excluded from that denominator but remain visible below. Intervals are omitted for groups with fewer than 10 candidate pairs or zero observed residual variance.",
            "",
            "| Reporting group | Candidate pairs | Correct | Incorrect | Ambiguous | Insufficient evidence | Determinate precision | Approximate 95% interval |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
            *group_rows,
            "",
            "In the separate census, the Meat & poultry group has "
            f"{int(meat_census_group['correct_assignments'])}/"
            f"{int(meat_census_group['candidate_assignment_records'])} supported "
            "assignments; no sampling interval applies.",
            "",
            "### Record-level agreement, uncertainty, and diagnostic comparison",
            "",
            f"Exact-set agreement across all primary records is "
            f"{int(audit_primary['exact_set_matches'])}/"
            f"{int(audit_primary['records_reviewed'])} "
            f"({100 * float(audit_primary['record_exact_set_agreement_all_records']):.1f}%; "
            f"approximate 95% interval "
            f"{interval(audit_primary['record_exact_set_ci_low'], audit_primary['record_exact_set_ci_high'])}). "
            f"Among the {int(audit_primary['determinate_record_denominator'])} determinate records, "
            f"it is {int(audit_primary['exact_set_matches'])}/"
            f"{int(audit_primary['determinate_record_denominator'])} "
            f"({100 * float(audit_primary['record_exact_set_agreement_determinate_only']):.1f}%). "
            f"Record-level ambiguity was {int(audit_primary['ambiguous_record_count'])}/"
            f"{int(audit_primary['records_reviewed'])} "
            f"({100 * float(audit_primary['ambiguity_rate']):.1f}%); insufficient evidence was "
            f"{int(audit_primary['insufficient_evidence_record_count'])}/"
            f"{int(audit_primary['records_reviewed'])} "
            f"({100 * float(audit_primary['insufficient_evidence_rate']):.1f}%).",
            "",
            f"Among determinate records, the reviewer supported {int(audit_primary['determinate_reviewer_supported_group_pairs_missing_from_candidate'])} "
            f"group pairs absent from the candidate sets, across "
            f"{int(audit_primary['determinate_records_with_supported_groups_missing_from_candidate'])} records. "
            "This is an AI-label omission diagnostic, not objective recall.",
            "",
            f"The diagnostic `food_groups_tags` cross-check exactly matched "
            f"{int(audit_primary['food_groups_exact_set_matches'])}/"
            f"{int(audit_primary['food_groups_comparable_records'])} comparable "
            f"records ({100 * float(audit_primary['food_groups_exact_match_rate']):.1f}%) "
            f"and had any overlap for {int(audit_primary['food_groups_any_overlap_records'])}/"
            f"{int(audit_primary['food_groups_comparable_records'])} "
            f"({100 * float(audit_primary['food_groups_any_overlap_rate']):.1f}%). "
            "These tags are not a gold standard and did not inform the independent labels.",
            "",
            "### Error analysis and external evidence",
            "",
            "- Taxonomy ancestry can create semantically misleading assignments: three of the eight Meat & poultry census errors involved sauce products whose category ancestry includes meat-based sauces, although product information did not establish meat as an ingredient. Do not equate a flavor name or broad ancestor tag with product composition.",
            "- Source category tags can be contradictory or noisy. The sampled Happy Cola record carried beverage-branch tags, while the Sprite Zero record included vegetable/lettuce tags; external product information helped assess those specific cases.",
            "- Several disagreements involve broad group boundaries (for example, products that plausibly fit both a base-food and snack/dessert group). These cases indicate a need for more operational group definitions, not an automatic rule to force one label.",
            "- The primary-sample omission diagnostic above identifies candidate-coverage cases for targeted review; it is not an objective recall estimate. Do not change mappings or candidate rules from these AI labels alone.",
            "",
            "Selected official product-page checks are recorded alongside the affected records:",
            "",
            "| Record ID | Product | Sourced evidence and reviewer inference | Reference |",
            "|---|---|---|---|",
            *official_source_rows,
            "",
            "### Method and limitations",
            "",
            "The 150-record sample is a fixed MD5-ranked sample, not a literal random draw. Approximate 95% intervals use first-order Taylor linearization with a finite-population correction, conditional on the hash ordering approximating simple random sampling without replacement; sparse per-group intervals are suppressed. These intervals describe sampling uncertainty only, not the reliability, calibration, or independence of AI judgments. The assessment is AI-assisted, not human annotation: the separate-context reviewer received product fields but not category tags or candidate mappings, while the coordinating workflow had previously inspected those materials. Reviewer confidence is self-assessed, not calibrated.",
            "",
            "No mappings, candidate-generation rules, source records, or original analytical results were changed. The 8-record Meat & poultry census is descriptive and is not pooled into the primary estimate.",
            "",
            "Record-level annotations, product evidence, source URLs, and generated metrics: [semantic audit records](../outputs/quality/category_mapping_semantic_audit_records.csv), [review labels](../outputs/quality/category_mapping_semantic_audit_labels.csv), [overall metrics](../outputs/quality/category_mapping_semantic_audit_summary.csv), and [per-group metrics](../outputs/quality/category_mapping_semantic_audit_by_group.csv).",
        ]
    )
    document = replace_generated_section(
        document,
        "semantic-mapping-audit",
        audit_section,
    )
    return document


def validate_stage5_output(path: Path) -> pd.DataFrame:
    evidence = read_csv(path)
    if len(evidence) != len(COUNTRIES) or evidence["iso_alpha2"].nunique() != len(COUNTRIES):
        raise ValueError(
            f"Stage 5 evidence must contain {len(COUNTRIES)} selected ISO units: {path}"
        )
    missing_countries = set(COUNTRIES) - set(evidence["iso_alpha2"])
    if missing_countries:
        raise ValueError(
            f"Stage 5 evidence is missing selected units: {sorted(missing_countries)}"
        )
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    if not BASELINE_DATABASE.is_file() or not BASELINE_VALIDATION.is_file():
        raise FileNotFoundError(
            "The validated five-country Stage 4 database and report are required."
        )
    validate_report(BASELINE_VALIDATION, 15, "Stage 4")
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)

    run_script("05_category_brand_profile.py")
    brand_mapping_validation = read_csv(
        PROFILE_DIR / "brand_name_manual_mapping_validation.csv"
    )
    brand_decisions = read_csv(
        PROJECT_ROOT / "data" / "mappings" / "brand_name_manual_decisions.csv"
    )
    if len(brand_mapping_validation) != len(brand_decisions):
        raise ValueError("Brand mapping validation does not cover every approved decision.")

    with tempfile.TemporaryDirectory(
        prefix=".harmonization_candidate_",
        dir=PROCESSED_DIR,
    ) as candidate_temp, tempfile.TemporaryDirectory(
        prefix=".harmonization_refresh_",
        dir=OUTPUTS_DIR,
    ) as refresh_temp:
        candidate_dir = Path(candidate_temp)
        refresh_dir = Path(refresh_temp)
        candidate_database = candidate_dir / "candidate.duckdb"
        candidate_validation = candidate_dir / "candidate_validation.csv"
        stage5_output = refresh_dir / STAGE5_NAME
        readiness_output = refresh_dir / READINESS_FILE.name
        contributor_output = refresh_dir / CONTRIBUTOR_FILE.name
        yearly_output = refresh_dir / YEARLY_FILE.name
        source_tag_output = refresh_dir / SOURCE_TAG_FILE.name
        overlap_output = refresh_dir / OVERLAP_FILE.name
        food_groups_output = refresh_dir / FOOD_GROUP_FILE.name
        visual_output_dir = refresh_dir / "img"
        stage6_output_dir = refresh_dir / "analysis"

        run_script("07_category_reporting_group_draft.py")
        run_script("08_category_reporting_group_review_queues.py")
        run_script(
            "15_build_stage6_candidate_database.py",
            "--output",
            str(candidate_database),
            "--validation-output",
            str(candidate_validation),
        )
        candidate_report = validate_report(
            candidate_validation, 15, "Stage 6 candidate"
        )

        run_script(
            "12_stage5_country_peer_evidence.py",
            "--database",
            str(candidate_database),
            "--build-validation",
            str(candidate_validation),
            "--output",
            str(stage5_output),
            "--readiness-output",
            str(readiness_output),
            "--contributor-output",
            str(contributor_output),
            "--yearly-output",
            str(yearly_output),
            "--source-tag-output",
            str(source_tag_output),
            "--overlap-output",
            str(overlap_output),
            "--food-groups-output",
            str(food_groups_output),
        )
        stage5_evidence = validate_stage5_output(stage5_output)

        run_script(
            "13_run_stage6_analysis.py",
            "--database",
            str(candidate_database),
            "--build-validation",
            str(candidate_validation),
            "--country-evidence",
            str(stage5_output),
            "--output-dir",
            str(stage6_output_dir),
        )
        stage6_validation = validate_report(
            stage6_output_dir / "stage6_validation.csv", 11, "Stage 6"
        )
        scope = read_csv(stage6_output_dir / "stage6_country_scope.csv")
        categories = read_csv(stage6_output_dir / "stage6_country_category.csv")
        brands = read_csv(stage6_output_dir / "stage6_country_brand.csv")
        readiness = read_csv(readiness_output)
        contributors = read_csv(contributor_output)
        source_tags = read_csv(source_tag_output)
        overlap = read_csv(overlap_output)
        food_groups = read_csv(food_groups_output)
        (
            semantic_audit_records,
            semantic_audit_summary,
            semantic_audit_groups,
        ) = load_semantic_audit_outputs()
        if len(scope) != 15 or len(categories) != 300:
            raise ValueError("Stage 6 output row counts do not match the approved scope.")

        run_script(
            "generate_visuals.py",
            "--analysis-dir",
            str(stage6_output_dir),
            "--readiness",
            str(readiness_output),
            "--output-dir",
            str(visual_output_dir),
        )

        current_stage7 = STAGE7_FILE.read_text(encoding="utf-8")
        refreshed_stage7 = render_stage7(
            current_stage7,
            stage5_evidence,
            scope,
            categories,
            brands,
            readiness,
            contributors,
            source_tags,
            overlap,
            food_groups,
            semantic_audit_records,
            semantic_audit_summary,
            semantic_audit_groups,
            len(candidate_report),
            len(stage6_validation),
        )
        staged_stage7 = refresh_dir / STAGE7_FILE.name
        staged_stage7.write_text(refreshed_stage7, encoding="utf-8")
        current_readme = README_FILE.read_text(encoding="utf-8")
        refreshed_readme = render_readme(
            current_readme,
            stage5_evidence,
            scope,
            categories,
            readiness,
            semantic_audit_summary,
        )
        staged_readme = refresh_dir / README_FILE.name
        staged_readme.write_text(refreshed_readme, encoding="utf-8")
        staged_candidate_validation = (
            refresh_dir / STAGE6_CANDIDATE_VALIDATION.name
        )
        candidate_report_to_publish = read_csv(candidate_validation)
        if "database_file" in candidate_report_to_publish.columns:
            candidate_report_to_publish["database_file"] = (
                "temporary candidate (removed after successful refresh)"
            )
        candidate_report_to_publish.to_csv(
            staged_candidate_validation,
            index=False,
            encoding="utf-8",
        )

        summary = pd.DataFrame(
            [
                ("category_crosswalk", "completed", "scripts/07_category_reporting_group_draft.py"),
                ("review_queues", "completed", "scripts/08_category_reporting_group_review_queues.py"),
                ("brand_mapping_validation", f"{len(brand_mapping_validation)} exact values validated", "outputs/profiling/brand_name_manual_mapping_validation.csv"),
                ("readiness_and_contributor_diagnostics", "five-country scorecard, creator/year and source-tag diagnostics, identifier overlap, and food-groups cross-check generated", "outputs/profiling/"),
                ("candidate_validation", "15/15 passed", "outputs/quality/stage6_candidate_build_validation.csv"),
                ("stage5_evidence", f"{len(stage5_evidence)} selected units validated", "outputs/profiling/stage5_country_peer_evidence.csv"),
                ("stage6_analysis", "11/11 passed", "outputs/analysis/"),
                ("semantic_mapping_audit", "AI-assisted audit outputs validated and included in generated findings", "outputs/quality/category_mapping_semantic_audit_*.csv"),
                ("stage7_findings", "dynamic result tables refreshed", "docs/06_stage7_findings_and_recommendations.md"),
            ],
            columns=("step", "result", "evidence"),
        )
        staged_summary = refresh_dir / SUMMARY_FILE.name
        summary.to_csv(staged_summary, index=False, encoding="utf-8")

        (stage5_output).replace(STAGE5_FILE)
        readiness_output.replace(READINESS_FILE)
        contributor_output.replace(CONTRIBUTOR_FILE)
        yearly_output.replace(YEARLY_FILE)
        source_tag_output.replace(SOURCE_TAG_FILE)
        overlap_output.replace(OVERLAP_FILE)
        food_groups_output.replace(FOOD_GROUP_FILE)
        VISUAL_DIR.mkdir(parents=True, exist_ok=True)
        for visual_name in VISUAL_NAMES:
            (visual_output_dir / visual_name).replace(VISUAL_DIR / visual_name)
        for output_name in STAGE6_OUTPUTS:
            (stage6_output_dir / output_name).replace(ANALYSIS_DIR / output_name)
        staged_candidate_validation.replace(STAGE6_CANDIDATE_VALIDATION)
        staged_summary.replace(SUMMARY_FILE)
        staged_readme.replace(README_FILE)
        staged_stage7.replace(STAGE7_FILE)

    print("Automated harmonization refresh completed.")
    print("Candidate-database checks passed: 15")
    print("Stage 6 checks passed: 11")
    print(f"Stage 5 ISO units: {len(stage5_evidence)}")
    print(f"Stage 6 outputs: {ANALYSIS_DIR}")
    print(f"Stage 7 findings: {STAGE7_FILE}")
    print(f"Refresh summary: {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
