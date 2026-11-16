"""Render generated README metrics and comparison tables."""

import pandas as pd
from support_report_common import (
    COUNTRIES,
    COUNTRY_ROLES,
    ONLINE_AUDIT_FILE,
    read_csv,
    replace_readme_section,
)


def render_readme(
    document: str,
    country_evidence: pd.DataFrame,
    scope: pd.DataFrame,
    categories: pd.DataFrame,
    readiness: pd.DataFrame,
    semantic_audit_summary: pd.DataFrame,
) -> str:
    scope_baseline = scope.loc[scope["scenario"].eq("baseline")].set_index("iso_alpha2")
    evidence_by_country = country_evidence.set_index("iso_alpha2")
    candidate = (
        categories.loc[
            categories["scenario"].eq("baseline")
            & categories["assignment_basis"].eq("candidate_derived")
        ]
        .drop_duplicates("iso_alpha2")
        .set_index("iso_alpha2")
    )
    approved = (
        categories.loc[
            categories["scenario"].eq("baseline")
            & categories["assignment_basis"].eq("approved_only")
        ]
        .drop_duplicates("iso_alpha2")
        .set_index("iso_alpha2")
    )
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
    online_audit = read_csv(ONLINE_AUDIT_FILE)
    online_source_count = int(online_audit["source_url"].ne("").sum())
    online_exact_code_count = int(online_audit["identifier_match"].eq("yes").sum())
    online_supported_count = int(
        online_audit["online_review_status"].eq("researched_supports").sum()
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
                f"- **AI + online mapping audit:** {int(audit['correct_assignments'])}/"
                f"{int(audit['candidate_assignment_pairs'])} candidate assignments "
                f"were judged correct ({int(audit['manual_exact_overlap_assignment_pairs'])} "
                f"also align with exact-reviewed mappings); {int(audit['incorrect_assignments'])} disagreed "
                f"and {audit_unresolved} were unresolved. Exact group-set agreement "
                f"was {int(audit['exact_set_matches'])}/"
                f"{int(audit['records_reviewed'])} "
                f"({100 * float(audit['record_exact_set_agreement_all_records']):.1f}%). "
                f"Online follow-up found supporting product evidence for {online_supported_count}/48 cases; "
                f"{online_source_count} have a source URL and {online_exact_code_count} match the exact product code. "
                "Targeted, non-random, and not human ground truth; "
                "[AI audit](outputs/quality/category_mapping_semantic_audit_records.csv) · "
                "[online evidence](outputs/quality/category_mapping_online_evidence_audit.csv)."
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
