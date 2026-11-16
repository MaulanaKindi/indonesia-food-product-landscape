"""support nonfood scope helpers."""

import duckdb
import pandas as pd

from support_nonfood_config import (
    TAXONOMY_CHECK_TAGS,
)


def tag_inventory(
    connection: duckdb.DuckDBPyConnection,
    taxonomy: dict,
    disposition_tags: set[str],
) -> pd.DataFrame:
    exact = connection.execute(
        """
        SELECT
            tag AS tag_value,
            string_agg(DISTINCT tag, ' | ' ORDER BY tag) AS source_tag_variants,
            COUNT(DISTINCT record_id) AS rows,
            COUNT(DISTINCT code) AS distinct_codes,
            bool_or(class_a_match) AS class_a_match,
            bool_or(class_b_match) AS class_b_match,
            bool_or(class_c_match) AS class_c_match,
            bool_or(class_d_match) AS class_d_match,
            min(strongest_tag_class) AS strongest_tag_class
        FROM tag_evidence
        GROUP BY tag
        """
    ).fetchdf()
    folded = connection.execute(
        """
        SELECT
            casefolded_tag AS tag_value,
            string_agg(DISTINCT tag, ' | ' ORDER BY tag) AS source_tag_variants,
            COUNT(DISTINCT record_id) AS rows,
            COUNT(DISTINCT code) AS distinct_codes,
            bool_or(class_a_match) AS class_a_match,
            bool_or(class_b_match) AS class_b_match,
            bool_or(class_c_match) AS class_c_match,
            bool_or(class_d_match) AS class_d_match,
            min(strongest_tag_class) AS strongest_tag_class
        FROM tag_evidence
        GROUP BY casefolded_tag
        """
    ).fetchdf()

    def finish(frame: pd.DataFrame, grain: str) -> pd.DataFrame:
        frame["tag_grain"] = grain
        frame["in_disposition"] = frame["source_tag_variants"].map(
            lambda values: "Y"
            if values and all(tag in disposition_tags for tag in values.split(" | "))
            else "N"
        )
        frame["exact_match_in_taxonomy"] = frame["source_tag_variants"].map(
            lambda values: "Y"
            if any(tag in taxonomy for tag in values.split(" | "))
            else "N"
        )
        for column in (
            "class_a_match",
            "class_b_match",
            "class_c_match",
            "class_d_match",
        ):
            frame[column] = frame[column].map(lambda value: "Y" if value else "N")
        return frame[
            [
                "tag_grain",
                "tag_value",
                "source_tag_variants",
                "strongest_tag_class",
                "class_a_match",
                "class_b_match",
                "class_c_match",
                "class_d_match",
                "in_disposition",
                "rows",
                "distinct_codes",
                "exact_match_in_taxonomy",
            ]
        ]

    result = pd.concat([finish(exact, "exact"), finish(folded, "casefolded")])
    return result


def case_variant_audit(
    connection: duckdb.DuckDBPyConnection,
    nonfood_dispositions: list[dict[str, str]],
) -> pd.DataFrame:
    reviewed_tags = [row["source_category_tag"] for row in nonfood_dispositions]
    reviewed_set = set(reviewed_tags)
    rows: list[dict] = []
    for reviewed_tag in sorted(reviewed_tags):
        variants = connection.execute(
            """
            SELECT
                tag,
                COUNT(DISTINCT record_id) AS rows,
                COUNT(DISTINCT code) AS distinct_codes
            FROM tag_occurrences
            WHERE casefolded_tag = lower(?)
            GROUP BY tag
            ORDER BY tag
            """,
            [reviewed_tag],
        ).fetchdf()
        for variant in variants.to_dict(orient="records"):
            rows.append(
                {
                    "reviewed_exclusion_tag": reviewed_tag,
                    "scope": "present_variant",
                    "data_tag_variant": variant["tag"],
                    "variant_covered_by_exact_disposition": (
                        "Y" if variant["tag"] in reviewed_set else "N"
                    ),
                    "rows": int(variant["rows"]),
                    "distinct_codes": int(variant["distinct_codes"]),
                    "exact_tag_rows": "",
                    "exact_tag_distinct_codes": "",
                    "casefolded_rows": "",
                    "casefolded_distinct_codes": "",
                    "casefolded_minus_exact_distinct_codes": "",
                }
            )
        totals = connection.execute(
            """
            SELECT
                COUNT(DISTINCT record_id) AS rows,
                COUNT(DISTINCT code) AS distinct_codes,
                COUNT(DISTINCT record_id) FILTER (WHERE tag = ?) AS exact_rows,
                COUNT(DISTINCT code) FILTER (WHERE tag = ?) AS exact_codes
            FROM tag_occurrences
            WHERE casefolded_tag = lower(?)
            """,
            [reviewed_tag, reviewed_tag, reviewed_tag],
        ).fetchone()
        rows.append(
            {
                "reviewed_exclusion_tag": reviewed_tag,
                "scope": "casefolded_total",
                "data_tag_variant": "",
                "variant_covered_by_exact_disposition": "N/A",
                "rows": int(totals[0]),
                "distinct_codes": int(totals[1]),
                "exact_tag_rows": int(totals[2]),
                "exact_tag_distinct_codes": int(totals[3]),
                "casefolded_rows": int(totals[0]),
                "casefolded_distinct_codes": int(totals[1]),
                "casefolded_minus_exact_distinct_codes": int(totals[1] - totals[3]),
            }
        )
    return pd.DataFrame(rows)


def taxonomy_check(taxonomy: dict) -> pd.DataFrame:
    children: dict[str, list[str]] = {tag: [] for tag in taxonomy}
    for child_tag, entry in taxonomy.items():
        for parent in entry.get("parents", []):
            if parent in children:
                children[parent].append(child_tag)
    rows = []
    for tag in TAXONOMY_CHECK_TAGS:
        entry = taxonomy.get(tag)
        names = entry.get("name", {}) if entry else {}
        rows.append(
            {
                "tag": tag,
                "exists_as_exact_node": "Y" if entry is not None else "N",
                "english_name": names.get("en", "") if isinstance(names, dict) else "",
                "direct_parents": " | ".join(sorted(entry.get("parents", [])))
                if entry
                else "",
                "direct_children_count": len(children.get(tag, [])),
            }
        )
    return pd.DataFrame(rows)


def class_summary(connection: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    strongest = connection.execute(
        """
        SELECT
            strongest_class AS group_label,
            COUNT(*) AS rows,
            COUNT(DISTINCT code) AS distinct_codes
        FROM record_flags
        GROUP BY strongest_class
        """
    ).fetchdf()
    overlap = connection.execute(
        """
        SELECT
            CASE
                WHEN NOT has_a AND NOT has_b AND NOT has_c AND NOT has_d
                    THEN 'unflagged'
                ELSE concat_ws(
                    '+',
                    CASE WHEN has_a THEN 'A' END,
                    CASE WHEN has_b THEN 'B' END,
                    CASE WHEN has_c THEN 'C' END,
                    CASE WHEN has_d THEN 'D' END
                )
            END AS group_label,
            COUNT(*) AS rows,
            COUNT(DISTINCT code) AS distinct_codes
        FROM record_flags
        GROUP BY group_label
        """
    ).fetchdf()
    total_rows, total_codes = connection.execute(
        "SELECT COUNT(*), COUNT(DISTINCT code) FROM record_flags"
    ).fetchone()
    strongest_groups = (
        "A_contributor_flag",
        "B_reviewed_exclusion",
        "C_pattern_candidate",
        "D_food_confirming",
        "unflagged",
    )
    strongest_by_group = {
        row["group_label"]: row for row in strongest.to_dict(orient="records")
    }
    strongest = pd.DataFrame(
        [
            strongest_by_group.get(
                group,
                {"group_label": group, "rows": 0, "distinct_codes": 0},
            )
            for group in strongest_groups
        ]
    )

    observed_overlaps = {
        row["group_label"]: row for row in overlap.to_dict(orient="records")
    }
    all_overlap_labels = ["unflagged"]
    class_letters = ("A", "B", "C", "D")
    for mask in range(1, 1 << len(class_letters)):
        all_overlap_labels.append(
            "+".join(
                letter
                for index, letter in enumerate(class_letters)
                if mask & (1 << index)
            )
        )
    overlap = pd.DataFrame(
        [
            observed_overlaps.get(
                label,
                {"group_label": label, "rows": 0, "distinct_codes": 0},
            )
            for label in all_overlap_labels
        ]
    )

    result = []
    for group_type, frame in (
        ("strongest_class", strongest),
        ("overlap_matrix", overlap),
    ):
        for row in frame.to_dict(orient="records"):
            result.append(
                {
                    "summary_type": group_type,
                    "group_label": row["group_label"],
                    "rows": int(row["rows"]),
                    "distinct_codes": int(row["distinct_codes"]),
                    "share_of_total_rows": float(row["rows"] / total_rows),
                    "share_of_total_distinct_codes": float(
                        row["distinct_codes"] / total_codes
                    ),
                    "row_denominator": int(total_rows),
                    "distinct_code_denominator": int(total_codes),
                }
            )
    return pd.DataFrame(result)
