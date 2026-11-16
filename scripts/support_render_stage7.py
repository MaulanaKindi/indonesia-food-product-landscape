"""Render generated findings and audit sections in the Stage 7 report."""

import pandas as pd
from support_report_common import (
    COUNTRIES,
    COUNTRY_NAMES,
    COUNTRY_ROLES,
    ONLINE_AUDIT_FILE,
    read_csv,
    replace_generated_section,
)


def _render_core_sections(
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
    candidate_check_count: int,
    stage6_check_count: int,
) -> tuple[str, pd.DataFrame, pd.DataFrame]:
    evidence_by_country = country_evidence.set_index("iso_alpha2")
    scope_baseline = scope.loc[scope["scenario"].eq("baseline")].set_index("iso_alpha2")
    readiness_by_field = readiness.set_index(["iso_alpha2", "metric"])
    contributors_by_country = contributors.set_index("iso_alpha2")
    source_tags = source_tags.copy()
    source_tags["source_rank"] = pd.to_numeric(
        source_tags["source_rank"], errors="raise"
    )
    overlap = overlap.copy()
    overlap["jaccard_index"] = pd.to_numeric(overlap["jaccard_index"], errors="raise")
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
            f"| {COUNTRY_NAMES[iso]} ({iso}) | {COUNTRY_ROLES[iso]} | {int(row['source_rows']):,} "
            f"| {int(row['source_rows_with_category_tags']):,} "
            f"| {float(row['category_tags_coverage_pct']):.4f}% |"
        )
    document = replace_generated_section(
        document,
        "country-scope",
        "\n".join(
            [
                "| Country | Role | Source rows | Rows with `categories_tags` | Category-tag coverage |",
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
            f"| {COUNTRY_NAMES[iso]} ({iso}) | {first.reporting_group_label} | "
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
                "| Country | Largest group | Rows | Share of country rows | Next largest | Rows | Third largest | Rows |",
                "|---|---|---:|---:|---|---:|---|---:|",
                *top_group_rows,
            ]
        ),
    )

    coverage_rows = []
    for iso in COUNTRIES:
        country_categories = categories.loc[
            categories["iso_alpha2"].eq(iso) & categories["scenario"].eq("baseline")
        ]
        by_basis = country_categories.drop_duplicates("assignment_basis").set_index(
            "assignment_basis"
        )
        candidate = by_basis.loc["candidate_derived"]
        approved = by_basis.loc["approved_only"]
        coverage_rows.append(
            f"| {COUNTRY_NAMES[iso]} ({iso}) | {int(candidate['source_rows_with_category_tags']):,} "
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
                "| Country | Category-tagged rows | Candidate-derived assigned | Candidate-derived tagged rows without assignment | Approved-only assigned | Approved-only tagged rows without assignment |",
                "|---|---:|---:|---:|---:|---:|",
                *coverage_rows,
            ]
        ),
    )
    overlap_counts = []
    for iso in COUNTRIES:
        rows = candidate_categories.loc[candidate_categories["iso_alpha2"].eq(iso)]
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
            f"| {COUNTRY_NAMES[iso]} ({iso}) | {int(row['source_rows_with_approved_brand_mapping']):,} "
            f"| {float(row['approved_brand_mapping_coverage_pct_of_country_rows']):.4f}% |"
        )
    document = replace_generated_section(
        document,
        "brand-coverage",
        "\n".join(
            [
                "| Country | Rows with approved exact brand mapping | Share of country rows |",
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
        country_scenarios = scope.loc[scope["iso_alpha2"].eq(iso)].set_index("scenario")
        except_strong = int(
            country_scenarios.loc[
                "exclude_A_B_except_strong_food_signals", "excluded_source_rows"
            ]
        )
        all_a_b = int(country_scenarios.loc["exclude_all_A_B", "excluded_source_rows"])
        sensitivity_rows.append(
            f"| {COUNTRY_NAMES[iso]} ({iso}) | {except_strong:,} | {all_a_b:,} |"
        )
    document = replace_generated_section(
        document,
        "nonfood-sensitivity",
        "\n".join(
            [
                "| Country | `exclude_A_B_except_strong_food_signals` | `exclude_all_A_B` |",
                "|---|---:|---:|",
                *sensitivity_rows,
            ]
        ),
    )

    return document, source_tags, overlap


def _render_readiness_sections(
    document: str,
    readiness: pd.DataFrame,
    contributors: pd.DataFrame,
    source_tags: pd.DataFrame,
    overlap: pd.DataFrame,
    food_groups: pd.DataFrame,
) -> str:
    readiness_by_field = readiness.set_index(["iso_alpha2", "metric"])
    contributors_by_country = contributors.set_index("iso_alpha2")
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
            f"| {COUNTRY_NAMES[iso]} ({iso}) | " + " | ".join(values) + " |"
        )
    document = replace_generated_section(
        document,
        "data-readiness",
        "\n".join(
            [
                "| Country | Brand text | Category tags | Ingredient text | Numeric nutrition | Valid Nutri-Score | Packaging | Labels | Exact-approved brand map |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
                *readiness_rows,
            ]
        ),
    )

    contributor_rows = []
    for iso in COUNTRIES:
        row = contributors_by_country.loc[iso]
        peak_year = int(row["peak_creation_year"])
        missing_creator_coverage = (
            f"{float(row['missing_creator_category_tag_coverage_pct']):.2f}%"
            if str(row["missing_creator_category_tag_coverage_pct"]).strip()
            else "—"
        )
        contributor_rows.append(
            f"| {iso} | {int(row['unique_creators']):,} | "
            f"{float(row['top_5_creator_share_pct']):.2f}% | {peak_year} | "
            f"{float(row['peak_year_share_of_dated_records_pct']):.2f}% | "
            f"{float(row['peak_day_share_of_dated_records_pct']):.2f}% | "
            f"{int(row['peak_creator_day_records']):,} "
            f"({float(row['peak_creator_day_share_of_country_records_pct']):.2f}%) | "
            f"{float(row['peak_creator_day_category_tag_coverage_pct']):.2f}% | "
            f"{float(row['top_5_category_tag_coverage_pct']):.2f}% | "
            f"{float(row['other_named_creator_category_tag_coverage_pct']):.2f}% | "
            f"{missing_creator_coverage} |"
        )
    document = replace_generated_section(
        document,
        "contributor-diagnostics",
        "\n".join(
            [
                "| ISO | Distinct creator values | Top-five creator share | Peak creation year | Peak-year share of dated rows | Peak-day share of dated rows | Largest one-creator/day batch (country share) | Batch category-tag coverage | Top-five category-tag coverage | Other named creators' category-tag coverage | Missing-creator category-tag coverage |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
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
        f"| {COUNTRY_NAMES[row.iso_alpha2]} ({row.iso_alpha2}) | {int(row.records_with_food_group_tags):,} | "
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
                "| Country | Rows with food-group tags | Rows covered by diagnostic crosswalk | Rows compared to candidate groups | Exact group-set agreement | Any group overlap |",
                "|---|---:|---:|---:|---:|---:|",
                *food_group_rows,
            ]
        ),
    )

    return document


def _render_semantic_audit_section(
    document: str,
    semantic_audit_records: pd.DataFrame,
    semantic_audit_summary: pd.DataFrame,
    semantic_audit_groups: pd.DataFrame,
) -> str:
    audit_primary = semantic_audit_summary.loc[
        semantic_audit_summary["analysis_scope"].eq("primary_sample")
    ].iloc[0]
    audit_census = semantic_audit_summary.loc[
        semantic_audit_summary["analysis_scope"].eq("meat_poultry_census")
    ].iloc[0]
    online_audit = read_csv(ONLINE_AUDIT_FILE)
    online_source_count = int(online_audit["source_url"].ne("").sum())
    online_exact_code_count = int(online_audit["identifier_match"].eq("yes").sum())
    online_supported_count = int(
        online_audit["online_review_status"].eq("researched_supports").sum()
    )
    online_partial_count = int(
        online_audit["online_review_status"].eq("researched_partial").sum()
    )
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
        _determinate,
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
            "These tags are not a gold standard and did not inform the AI-assisted labels.",
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
            f"The targeted online follow-up reviewed all {len(online_audit)} disputed or uncertain primary-sample records: {online_supported_count} had supporting product evidence and {online_partial_count} remained partial or unresolved. {online_source_count} records have a source URL and {online_exact_code_count} have an exact product-code match. Because records were selected by disagreement/uncertainty, these counts are not a sample-wide accuracy estimate.",
            "",
            "No mappings, candidate-generation rules, source records, or original analytical results were changed. The 8-record Meat & poultry census is descriptive and is not pooled into the primary estimate.",
            "",
            "Record-level annotations, product evidence, source URLs, and generated metrics: [semantic audit records](../outputs/quality/category_mapping_semantic_audit_records.csv), [review labels](../outputs/quality/category_mapping_semantic_audit_labels.csv), [online evidence log](../outputs/quality/category_mapping_online_evidence_audit.csv), [overall metrics](../outputs/quality/category_mapping_semantic_audit_summary.csv), and [per-group metrics](../outputs/quality/category_mapping_semantic_audit_by_group.csv).",
        ]
    )
    document = replace_generated_section(
        document,
        "semantic-mapping-audit",
        audit_section,
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
    document, source_tags, overlap = _render_core_sections(
        document,
        country_evidence,
        scope,
        categories,
        brands,
        readiness,
        contributors,
        source_tags,
        overlap,
        food_groups,
        candidate_check_count,
        stage6_check_count,
    )
    document = _render_readiness_sections(
        document, readiness, contributors, source_tags, overlap, food_groups
    )
    return _render_semantic_audit_section(
        document,
        semantic_audit_records,
        semantic_audit_summary,
        semantic_audit_groups,
    )
