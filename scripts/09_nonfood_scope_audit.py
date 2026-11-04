import csv
import hashlib
import json
import re
from pathlib import Path

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "food.parquet"
DISPOSITION_FILE = (
    PROJECT_ROOT / "data" / "mappings" / "category_tag_manual_dispositions.csv"
)
COUNTRY_MAPPING_FILE = (
    PROJECT_ROOT / "data" / "mappings" / "country_tag_mapping.csv"
)
ISO_REFERENCE_FILE = PROJECT_ROOT / "data" / "reference" / "iso_3166_alpha2.csv"
TAXONOMY_FILE = (
    PROJECT_ROOT / "data" / "reference" / "off_categories_taxonomy_2026-10-25.json"
)
COUNTRY_PROFILE_FILE = (
    PROJECT_ROOT / "outputs" / "profiling" / "normalized_country_profile.csv"
)
COUNTRY_SHORTLIST_FILE = (
    PROJECT_ROOT / "outputs" / "profiling" / "country_comparison_shortlist.csv"
)
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "profiling"

EXPECTED_ROWS = 4_828_207
EXPECTED_COLUMNS = 111
EXPECTED_TAXONOMY_SHA256 = (
    "EB03AEFABAE4C6269B5FBC3E89160F8DA84CA3300A53787E27EAB5FE2D1020D5"
)

CLASS_A_TAGS = [
    "en:non-food-products",
    "en:non-food-stuff",
    "fr:produits-non-alimentaires",
    "en:not-food",
    "pt:not-food",
    "pt:non-edible",
    "en:open-products-facts",
    "en:open-pet-food-facts",
    "en:open-beauty-facts",
]
CLASS_D_TAGS = ["en:non-open-products-facts", "en:open-food-facts"]
CLASS_C_PATTERN = (
    r"detergent|dishwash|laundry|-toys$|cosmetic|medicine|pet-food|"
    r"tobacco|cigarettes$"
)
TAXONOMY_CHECK_TAGS = [
    "en:non-food-products",
    "en:non-open-products-facts",
    "en:open-food-facts",
    "en:incorrect-product-type",
    "en:open-products-facts",
    "en:open-beauty-facts",
    "en:open-pet-food-facts",
]
RECALL_KEYWORDS = {
    "shampoo": r"\bshampoo\b",
    "shampooing": r"\bshampooing\b",
    "conditioner": r"\bconditioner\b",
    "toothpaste": r"\btoothpaste\b",
    "dentifrice": r"\bdentifrice\b",
    "tandpasta": r"\btandpasta\b",
    "deodorant": r"\bdeodorant\b",
    "lessive": r"\blessive\b",
    "toilet_paper": r"\btoilet[\s-]*paper\b|\btoiletpapier\b|\bpapier toilette\b",
    "mascara": r"\bmascara\b",
    "lipstick": r"\blipstick\b",
    "eau_de_toilette": r"\beau de toilette\b",
    "eau_de_parfum": r"\beau de parfum\b",
    "dishwash": r"\bdish[\s-]*wash(?:er|ing)?\b|\bdishwasher\b|\bvaisselle\b",
    "kattenvoer": r"\bkattenvoer\b",
    "hondenvoer": r"\bhondenvoer\b",
    "dog_food": r"\bdog food\b|\bdogfood\b",
    "cat_food": r"\bcat food\b|\bcatfood\b",
    "diapers": r"\bdiapers?\b|\bnapp(?:y|ies)\b|\bcouches?\b|\bluiers?\b",
}

SOURCE_COLUMNS = [
    "code",
    "categories_tags",
    "countries_tags",
    "brands",
    "product_name",
    "nova_group",
    "nutriscore_grade",
    "ingredients_n",
    "food_groups_tags",
]


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def validate_inputs() -> tuple[list[dict[str, str]], dict]:
    for path in (
        DATA_FILE,
        DISPOSITION_FILE,
        COUNTRY_MAPPING_FILE,
        ISO_REFERENCE_FILE,
        TAXONOMY_FILE,
        COUNTRY_PROFILE_FILE,
        COUNTRY_SHORTLIST_FILE,
    ):
        if not path.is_file():
            raise FileNotFoundError(f"Required audit input not found: {path}")

    connection = duckdb.connect()
    try:
        parquet_profile = connection.execute(
            "DESCRIBE SELECT * FROM read_parquet(?)", [str(DATA_FILE)]
        ).fetchall()
        actual_columns = len(parquet_profile)
        actual_rows = connection.execute(
            "SELECT COUNT(*) FROM read_parquet(?)", [str(DATA_FILE)]
        ).fetchone()[0]
        source_columns = {row[0] for row in parquet_profile}
    finally:
        connection.close()

    if actual_rows != EXPECTED_ROWS or actual_columns != EXPECTED_COLUMNS:
        raise ValueError(
            "Parquet precondition failed: expected "
            f"{EXPECTED_ROWS:,} rows and {EXPECTED_COLUMNS} columns; found "
            f"{actual_rows:,} rows and {actual_columns} columns."
        )
    missing_columns = set(SOURCE_COLUMNS) - source_columns
    if missing_columns:
        raise ValueError(
            f"Parquet is missing required columns: {sorted(missing_columns)}"
        )

    taxonomy_sha256 = hashlib.sha256(TAXONOMY_FILE.read_bytes()).hexdigest().upper()
    if taxonomy_sha256 != EXPECTED_TAXONOMY_SHA256:
        raise ValueError(
            "Pinned taxonomy checksum mismatch: expected "
            f"{EXPECTED_TAXONOMY_SHA256}, found {taxonomy_sha256}."
        )

    dispositions = csv_rows(DISPOSITION_FILE)
    required_disposition_columns = {
        "source_category_tag",
        "disposition",
    }
    if not dispositions or not required_disposition_columns.issubset(
        dispositions[0]
    ):
        raise ValueError("Category disposition file has an invalid or empty schema.")
    nonfood_dispositions = [
        row
        for row in dispositions
        if row["disposition"] == "exclude_non_food"
    ]
    reviewed_tags = [row["source_category_tag"] for row in nonfood_dispositions]
    if len(reviewed_tags) != len(set(reviewed_tags)):
        raise ValueError("Non-food disposition tags must be exact and unique.")

    country_mappings = csv_rows(COUNTRY_MAPPING_FILE)
    iso_rows = csv_rows(ISO_REFERENCE_FILE)
    baseline_rows = csv_rows(COUNTRY_PROFILE_FILE)
    if not country_mappings or not iso_rows or not baseline_rows:
        raise ValueError("Country mapping, ISO reference, and baseline must be non-empty.")
    if len({row["source_country_tag"] for row in country_mappings}) != len(
        country_mappings
    ):
        raise ValueError("Country mapping contains duplicate source tags.")
    required_country_columns = {
        "source_country_tag",
        "iso_alpha2",
        "country_name",
        "mapping_status",
    }
    if not required_country_columns.issubset(country_mappings[0]):
        raise ValueError("Country mapping file has an invalid schema.")
    return nonfood_dispositions, json.loads(
        TAXONOMY_FILE.read_text(encoding="utf-8")
    )


def write_csv(
    frame: pd.DataFrame,
    filename: str,
    sort_columns: list[str],
    ascending: bool | list[bool] = True,
) -> None:
    frame = frame.sort_values(
        sort_columns,
        ascending=ascending,
        kind="mergesort",
        na_position="last",
    )
    frame.to_csv(
        OUTPUT_DIR / filename,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
        na_rep="",
    )


def create_tables(
    connection: duckdb.DuckDBPyConnection,
    nonfood_dispositions: list[dict[str, str]],
) -> None:
    connection.execute(
        """
        CREATE TEMP TABLE record_base AS
        SELECT
            ROW_NUMBER() OVER () AS record_id,
            code,
            categories_tags,
            countries_tags,
            brands,
            array_to_string(
                list_transform(product_name, lambda item: item.text), ' | '
            ) AS name_text,
            nova_group,
            nutriscore_grade,
            ingredients_n,
            food_groups_tags
        FROM read_parquet(?)
        """,
        [str(DATA_FILE)],
    )

    connection.execute(
        "CREATE TEMP TABLE class_a_tags(tag VARCHAR PRIMARY KEY)"
    )
    connection.executemany(
        "INSERT INTO class_a_tags VALUES (?)",
        [(tag,) for tag in CLASS_A_TAGS],
    )
    connection.execute(
        "CREATE TEMP TABLE class_d_tags(tag VARCHAR PRIMARY KEY)"
    )
    connection.executemany(
        "INSERT INTO class_d_tags VALUES (?)",
        [(tag,) for tag in CLASS_D_TAGS],
    )
    connection.execute(
        "CREATE TEMP TABLE manual_nonfood_tags(tag VARCHAR PRIMARY KEY)"
    )
    connection.executemany(
        "INSERT INTO manual_nonfood_tags VALUES (?)",
        [(row["source_category_tag"],) for row in nonfood_dispositions],
    )

    connection.execute(
        """
        CREATE TEMP TABLE tag_occurrences_raw AS
        SELECT DISTINCT
            record_id,
            code,
            tag
        FROM record_base
        CROSS JOIN UNNEST(
            list_filter(
                list_distinct(categories_tags),
                lambda item: item IS NOT NULL AND trim(item) <> ''
            )
        ) AS category(tag)
        """
    )
    casefold_map = connection.execute(
        "SELECT DISTINCT tag FROM tag_occurrences_raw ORDER BY tag"
    ).fetchdf()
    casefold_map["casefolded_tag"] = casefold_map["tag"].map(str.casefold)
    connection.register("casefold_map_frame", casefold_map)
    connection.execute(
        """
        CREATE TEMP TABLE tag_casefold_map AS
        SELECT tag, casefolded_tag
        FROM casefold_map_frame
        """
    )
    connection.unregister("casefold_map_frame")
    connection.execute(
        """
        CREATE TEMP TABLE tag_occurrences AS
        SELECT
            occurrence.record_id,
            occurrence.code,
            occurrence.tag,
            mapping.casefolded_tag
        FROM tag_occurrences_raw AS occurrence
        JOIN tag_casefold_map AS mapping USING (tag)
        """
    )
    connection.execute("DROP TABLE tag_occurrences_raw")
    connection.execute(
        """
        CREATE TEMP TABLE tag_evidence AS
        SELECT
            occurrence.*,
            a.tag IS NOT NULL AS class_a_match,
            b.tag IS NOT NULL AS class_b_match,
            regexp_matches(occurrence.casefolded_tag, ?) AS class_c_match,
            d.tag IS NOT NULL AS class_d_match,
            CASE
                WHEN a.tag IS NOT NULL THEN 'A_contributor_flag'
                WHEN b.tag IS NOT NULL THEN 'B_reviewed_exclusion'
                WHEN regexp_matches(occurrence.casefolded_tag, ?)
                    THEN 'C_pattern_candidate'
                WHEN d.tag IS NOT NULL THEN 'D_food_confirming'
                ELSE 'unflagged'
            END AS strongest_tag_class
        FROM tag_occurrences AS occurrence
        LEFT JOIN class_a_tags AS a USING (tag)
        LEFT JOIN manual_nonfood_tags AS b USING (tag)
        LEFT JOIN class_d_tags AS d USING (tag)
        """,
        [CLASS_C_PATTERN, CLASS_C_PATTERN],
    )
    cigarette_russe_match = connection.execute(
        """
        SELECT COUNT(*)
        FROM tag_evidence
        WHERE tag = 'en:cigarette-russes' AND class_c_match
        """
    ).fetchone()[0]
    if cigarette_russe_match:
        raise ValueError("C-pattern discovery must not match en:cigarette-russes.")
    connection.execute(
        """
        CREATE TEMP TABLE record_flags AS
        WITH flags AS (
            SELECT
                record_id,
                bool_or(class_a_match) AS has_a,
                bool_or(class_b_match) AS has_b,
                bool_or(class_c_match) AS has_c,
                bool_or(class_d_match) AS has_d,
                string_agg(
                    DISTINCT CASE
                        WHEN class_a_match OR class_b_match THEN tag
                    END,
                    ' | ' ORDER BY CASE
                        WHEN class_a_match OR class_b_match THEN tag
                    END
                ) FILTER (WHERE class_a_match OR class_b_match)
                    AS matched_ab_tags
            FROM tag_evidence
            GROUP BY record_id
        )
        SELECT
            base.*,
            coalesce(flags.has_a, false) AS has_a,
            coalesce(flags.has_b, false) AS has_b,
            coalesce(flags.has_c, false) AS has_c,
            coalesce(flags.has_d, false) AS has_d,
            flags.matched_ab_tags,
            CASE
                WHEN coalesce(flags.has_a, false) THEN 'A_contributor_flag'
                WHEN coalesce(flags.has_b, false) THEN 'B_reviewed_exclusion'
                WHEN coalesce(flags.has_c, false) THEN 'C_pattern_candidate'
                WHEN coalesce(flags.has_d, false) THEN 'D_food_confirming'
                ELSE 'unflagged'
            END AS strongest_class,
            (
                len(
                    list_filter(
                        list_distinct(base.categories_tags),
                        lambda item: item IS NOT NULL AND trim(item) <> ''
                    )
                ) > 0
            ) AS has_category_tags,
            (
                len(
                    list_filter(
                        list_distinct(base.food_groups_tags),
                        lambda item: item IS NOT NULL AND trim(item) <> ''
                    )
                ) > 0
            ) AS has_food_group_tags
        FROM record_base AS base
        LEFT JOIN flags USING (record_id)
        """
    )

    connection.execute(
        """
        CREATE TEMP TABLE approved_country_tags AS
        SELECT source_country_tag, iso_alpha2, country_name
        FROM read_csv(?, all_varchar = true, header = true)
        WHERE mapping_status = 'approved'
        """,
        [str(COUNTRY_MAPPING_FILE)],
    )
    connection.execute(
        """
        CREATE TEMP TABLE country_record_assignments AS
        SELECT DISTINCT
            records.record_id,
            mapping.iso_alpha2
        FROM record_flags AS records
        CROSS JOIN UNNEST(
            list_filter(
                list_distinct(records.countries_tags),
                lambda item: item IS NOT NULL AND trim(item) <> ''
            )
        ) AS country(source_tag)
        JOIN approved_country_tags AS mapping
            ON mapping.source_country_tag = country.source_tag
        """
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
            if values
            and all(tag in disposition_tags for tag in values.split(" | "))
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
                "casefolded_minus_exact_distinct_codes": int(
                    totals[1] - totals[3]
                ),
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


def country_impact(
    connection: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    iso_rows = csv_rows(ISO_REFERENCE_FILE)
    iso_names = {
        row["iso_alpha2"]: row.get("country_name", row.get("name", ""))
        for row in iso_rows
    }
    baseline = pd.read_csv(
        COUNTRY_PROFILE_FILE,
        dtype={"iso_alpha2": str, "country_name": str},
        keep_default_na=False,
    )
    if len(baseline) != 237 or baseline["iso_alpha2"].nunique() != 237:
        raise ValueError(
            "Normalized country baseline must contain 237 unique ISO units; "
            f"found {len(baseline)} rows and {baseline['iso_alpha2'].nunique()} units."
        )
    shortlisted = baseline.loc[baseline["record_count"].astype(int) >= 1_000]
    if len(shortlisted) != 107:
        raise ValueError(
            "The 1,000-record baseline must contain 107 shortlisted ISO units; "
            f"found {len(shortlisted)}."
        )
    if "ID" not in set(baseline["iso_alpha2"]):
        raise ValueError("Indonesia (ID) is missing from normalized country profile.")
    iso_codes = sorted(baseline["iso_alpha2"].tolist())
    observed = connection.execute(
        """
        SELECT
            assignment.iso_alpha2,
            COUNT(*) AS total_records,
            COUNT(*) FILTER (
                WHERE records.strongest_class = 'A_contributor_flag'
            ) AS class_a_records,
            COUNT(*) FILTER (
                WHERE records.strongest_class = 'B_reviewed_exclusion'
            ) AS class_b_records,
            COUNT(*) FILTER (
                WHERE records.strongest_class = 'C_pattern_candidate'
            ) AS class_c_records,
            COUNT(*) FILTER (WHERE records.has_category_tags)
                AS records_with_categories_tags
        FROM country_record_assignments AS assignment
        JOIN record_flags AS records USING (record_id)
        GROUP BY assignment.iso_alpha2
        """
    ).fetchdf()
    observed_by_iso = {
        row["iso_alpha2"]: row for row in observed.to_dict(orient="records")
    }
    baseline_by_iso = {
        row["iso_alpha2"]: int(row["record_count"])
        for row in baseline.to_dict(orient="records")
    }
    if set(iso_codes) != set(baseline_by_iso):
        raise ValueError("Normalized country profile ISO keys are inconsistent.")
    if set(observed_by_iso) != set(baseline_by_iso):
        raise ValueError(
            "Country audit and normalized profile contain different ISO-unit sets."
        )

    output = []
    for iso in iso_codes:
        metric = observed_by_iso.get(iso)
        count = int(metric["total_records"]) if metric else 0
        expected = baseline_by_iso[iso]
        if count != expected:
            raise ValueError(
                "Country record reconciliation failed for "
                f"{iso} ({baseline.loc[baseline.iso_alpha2.eq(iso), 'country_name'].iloc[0]}): "
                f"audit={count:,}, normalized_country_profile={expected:,}."
            )
        class_a = int(metric["class_a_records"]) if metric else 0
        class_b = int(metric["class_b_records"]) if metric else 0
        class_c = int(metric["class_c_records"]) if metric else 0
        category_records = (
            int(metric["records_with_categories_tags"]) if metric else 0
        )
        flagged = class_a + class_b + class_c
        output.append(
            {
                "iso_alpha2": iso,
                "country_name": baseline.loc[
                    baseline.iso_alpha2.eq(iso), "country_name"
                ].iloc[0]
                or iso_names.get(iso, ""),
                "total_records": count,
                "class_a_records": class_a,
                "class_b_records": class_b,
                "class_c_records": class_c,
                "flagged_abc_records": flagged,
                "flagged_abc_share_of_total_records": (
                    flagged / count if count else 0.0
                ),
                "records_with_categories_tags": category_records,
                "categories_tags_share_of_total_records": (
                    category_records / count if count else 0.0
                ),
                "normalized_profile_record_count": expected,
                "reconciles_to_normalized_profile": "Y",
            }
        )
    return pd.DataFrame(output)


def signal_validation(connection: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    groups = [
        "A_contributor_flag",
        "B_reviewed_exclusion",
        "C_pattern_candidate",
        "D_food_confirming",
        "unflagged",
    ]
    output = []
    for scope, iso_clause in (("all_records", ""), ("ID", "AND country.iso_alpha2 = 'ID'")):
        for group in groups:
            if scope == "ID":
                if not country_exists(connection, "ID"):
                    raise ValueError("Indonesia (ID) is missing from country assignments.")
                query = f"""
                    SELECT
                        COUNT(*) AS rows,
                        COUNT(DISTINCT records.code) AS distinct_codes,
                        COUNT(*) FILTER (WHERE records.nova_group IS NOT NULL)
                            AS nova_group_rows,
                        COUNT(*) FILTER (
                            WHERE lower(records.nutriscore_grade)
                                IN ('a', 'b', 'c', 'd', 'e')
                        ) AS nutriscore_a_e_rows,
                        COUNT(*) FILTER (WHERE records.ingredients_n > 0)
                            AS ingredients_positive_rows,
                        COUNT(*) FILTER (WHERE records.has_food_group_tags)
                            AS food_groups_tag_rows
                    FROM country_record_assignments AS country
                    JOIN record_flags AS records USING (record_id)
                    WHERE records.strongest_class = ?
                    {iso_clause}
                """
                params = [group]
            else:
                query = """
                    SELECT
                        COUNT(*) AS rows,
                        COUNT(DISTINCT code) AS distinct_codes,
                        COUNT(*) FILTER (WHERE nova_group IS NOT NULL)
                            AS nova_group_rows,
                        COUNT(*) FILTER (
                            WHERE lower(nutriscore_grade) IN ('a', 'b', 'c', 'd', 'e')
                        ) AS nutriscore_a_e_rows,
                        COUNT(*) FILTER (WHERE ingredients_n > 0)
                            AS ingredients_positive_rows,
                        COUNT(*) FILTER (WHERE has_food_group_tags)
                            AS food_groups_tag_rows
                    FROM record_flags
                    WHERE strongest_class = ?
                """
                params = [group]
            metrics = connection.execute(query, params).fetchone()
            denominator = int(metrics[0])
            output.append(
                {
                    "scope": scope,
                    "strongest_class": group,
                    "rows": denominator,
                    "distinct_codes": int(metrics[1]),
                    "pct_with_nova_group": (
                        int(metrics[2]) / denominator if denominator else 0.0
                    ),
                    "pct_with_nutriscore_grade_a_to_e": (
                        int(metrics[3]) / denominator if denominator else 0.0
                    ),
                    "pct_with_ingredients_n_gt_0": (
                        int(metrics[4]) / denominator if denominator else 0.0
                    ),
                    "pct_with_nonempty_food_groups_tags": (
                        int(metrics[5]) / denominator if denominator else 0.0
                    ),
                }
            )
    return pd.DataFrame(output)


def sensitivity_impact(connection: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    connection.execute(
        """
        CREATE TEMP TABLE sensitivity_records AS
        SELECT
            record_id,
            code,
            has_category_tags,
            (has_a OR has_b) AS has_ab_flag,
            (
                (has_a OR has_b)
                AND nova_group IS NOT NULL
                AND lower(nutriscore_grade) IN ('a', 'b', 'c', 'd', 'e')
                AND ingredients_n >= 2
            ) AS has_strong_food_signals
        FROM record_flags
        """
    )
    connection.execute(
        """
        CREATE TEMP TABLE sensitivity_scenarios AS
        SELECT record_id, code, has_category_tags, has_ab_flag,
            has_strong_food_signals, 'baseline' AS scenario
        FROM sensitivity_records
        UNION ALL
        SELECT record_id, code, has_category_tags, has_ab_flag,
            has_strong_food_signals, 'exclude_all_A_B' AS scenario
        FROM sensitivity_records
        WHERE NOT has_ab_flag
        UNION ALL
        SELECT record_id, code, has_category_tags, has_ab_flag,
            has_strong_food_signals,
            'exclude_A_B_except_strong_food_signals' AS scenario
        FROM sensitivity_records
        WHERE NOT has_ab_flag OR has_strong_food_signals
        """
    )

    overall = connection.execute(
        """
        WITH scenario_totals AS (
            SELECT
                scenario,
                COUNT(*) AS included_rows,
                COUNT(DISTINCT code) AS included_distinct_codes,
                COUNT(*) FILTER (WHERE has_category_tags)
                    AS included_rows_with_categories_tags,
                COUNT(*) FILTER (WHERE has_ab_flag)
                    AS included_rows_with_A_B_flags,
                COUNT(*) FILTER (
                    WHERE has_ab_flag AND has_strong_food_signals
                ) AS retained_A_B_rows_with_strong_food_signals
            FROM sensitivity_scenarios
            GROUP BY scenario
        ),
        baseline AS (
            SELECT
                COUNT(*) AS baseline_rows,
                COUNT(DISTINCT code) AS baseline_distinct_codes
            FROM record_flags
        )
        SELECT
            totals.*,
            baseline.baseline_rows,
            baseline.baseline_distinct_codes,
            baseline.baseline_rows - totals.included_rows AS excluded_rows,
            baseline.baseline_distinct_codes
                - totals.included_distinct_codes
                AS net_distinct_code_reduction,
            totals.included_rows_with_categories_tags::DOUBLE
                / nullif(totals.included_rows, 0)
                AS categories_tags_coverage_of_included_rows
        FROM scenario_totals AS totals
        CROSS JOIN baseline
        """
    ).fetchdf()
    overall["geography_level"] = "overall"
    overall["iso_alpha2"] = ""
    overall["country_name"] = ""

    country = connection.execute(
        """
        WITH scenario_totals AS (
            SELECT
                assignment.iso_alpha2,
                mapping.country_name,
                scenario.scenario,
                COUNT(*) AS included_rows,
                COUNT(DISTINCT scenario.code) AS included_distinct_codes,
                COUNT(*) FILTER (WHERE scenario.has_category_tags)
                    AS included_rows_with_categories_tags,
                COUNT(*) FILTER (WHERE scenario.has_ab_flag)
                    AS included_rows_with_A_B_flags,
                COUNT(*) FILTER (
                    WHERE scenario.has_ab_flag
                        AND scenario.has_strong_food_signals
                ) AS retained_A_B_rows_with_strong_food_signals
            FROM sensitivity_scenarios AS scenario
            JOIN country_record_assignments AS assignment
                USING (record_id)
            JOIN (
                SELECT DISTINCT iso_alpha2, country_name
                FROM approved_country_tags
            ) AS mapping
                ON mapping.iso_alpha2 = assignment.iso_alpha2
            GROUP BY
                assignment.iso_alpha2,
                mapping.country_name,
                scenario.scenario
        ),
        baseline AS (
            SELECT
                iso_alpha2,
                included_rows AS baseline_rows,
                included_distinct_codes AS baseline_distinct_codes
            FROM scenario_totals
            WHERE scenario = 'baseline'
        )
        SELECT
            totals.scenario,
            totals.iso_alpha2,
            totals.country_name,
            totals.included_rows,
            totals.included_distinct_codes,
            totals.included_rows_with_categories_tags,
            totals.included_rows_with_A_B_flags,
            totals.retained_A_B_rows_with_strong_food_signals,
            baseline.baseline_rows,
            baseline.baseline_distinct_codes,
            baseline.baseline_rows - totals.included_rows AS excluded_rows,
            baseline.baseline_distinct_codes
                - totals.included_distinct_codes
                AS net_distinct_code_reduction,
            totals.included_rows_with_categories_tags::DOUBLE
                / nullif(totals.included_rows, 0)
                AS categories_tags_coverage_of_included_rows
        FROM scenario_totals AS totals
        JOIN baseline USING (iso_alpha2)
        """
    ).fetchdf()
    country["geography_level"] = "country_iso"

    baseline_country = country[
        country["scenario"].eq("baseline")
    ].set_index("iso_alpha2")
    normalized = pd.read_csv(
        COUNTRY_PROFILE_FILE,
        dtype={"iso_alpha2": str},
        keep_default_na=False,
    ).set_index("iso_alpha2")
    if set(baseline_country.index) != set(normalized.index):
        raise ValueError(
            "Sensitivity country baseline ISO units do not match the normalized profile."
        )
    mismatches = [
        iso
        for iso in normalized.index
        if int(baseline_country.loc[iso, "included_rows"])
        != int(normalized.loc[iso, "record_count"])
    ]
    if mismatches:
        raise ValueError(
            "Sensitivity baseline does not reconcile to normalized country profile: "
            f"{mismatches[:10]}"
        )

    combined = pd.concat([overall, country], ignore_index=True, sort=False)
    combined["reconciles_to_normalized_profile"] = ""
    combined.loc[
        combined["geography_level"].eq("country_iso")
        & combined["scenario"].eq("baseline"),
        "reconciles_to_normalized_profile",
    ] = "Y"
    combined.loc[
        combined["geography_level"].eq("overall")
        & combined["scenario"].eq("baseline"),
        "reconciles_to_normalized_profile",
    ] = "Y"
    return combined


def country_exists(connection: duckdb.DuckDBPyConnection, iso: str) -> bool:
    return (
        connection.execute(
            "SELECT COUNT(*) FROM country_record_assignments WHERE iso_alpha2 = ?",
            [iso],
        ).fetchone()[0]
        > 0
    )


def contradictions(connection: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    criteria = """
        (has_a OR has_b)
        AND nova_group IS NOT NULL
        AND lower(nutriscore_grade) IN ('a', 'b', 'c', 'd', 'e')
        AND ingredients_n >= 2
    """
    total_rows, distinct_codes = connection.execute(
        f"""
        SELECT COUNT(*), COUNT(DISTINCT code)
        FROM record_flags
        WHERE {criteria}
        """
    ).fetchone()
    sample = connection.execute(
        f"""
        SELECT
            code,
            name_text AS name,
            brands AS brand,
            matched_ab_tags AS matched_tags,
            'https://world.openfoodfacts.org/product/' || code AS off_url
        FROM record_flags
        WHERE {criteria}
        ORDER BY hash(code), code, coalesce(name_text, ''), coalesce(brands, '')
        LIMIT 15
        """
    ).fetchdf()
    summary = pd.DataFrame(
        [
            {
                "row_type": "total",
                "sample_rank": 0,
                "records": int(total_rows),
                "distinct_codes": int(distinct_codes),
                "code": "",
                "name": "",
                "brand": "",
                "matched_tags": "",
                "off_url": "",
            }
        ]
    )
    if not sample.empty:
        sample.insert(0, "sample_rank", range(1, len(sample) + 1))
        sample.insert(0, "row_type", "sample")
        sample.insert(2, "records", "")
        sample.insert(3, "distinct_codes", "")
        summary = pd.concat([summary, sample], ignore_index=True)
    return summary


def recall_probe(connection: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    candidate_condition = """
        NOT has_a AND NOT has_b AND NOT has_c
        AND nova_group IS NULL
        AND coalesce(lower(nutriscore_grade), '') NOT IN ('a', 'b', 'c', 'd', 'e')
        AND ingredients_n = 0
        AND name_text IS NOT NULL
        AND trim(name_text) <> ''
    """
    keyword_rows = []
    for keyword, pattern in RECALL_KEYWORDS.items():
        count, distinct_codes = connection.execute(
            f"""
            SELECT COUNT(*), COUNT(DISTINCT code)
            FROM record_flags
            WHERE {candidate_condition}
                AND regexp_matches(lower(name_text), ?)
            """,
            [pattern],
        ).fetchone()
        keyword_rows.append(
            {
                "row_type": "keyword_count",
                "sample_rank": 0,
                "keyword": keyword,
                "discovery_label": "discovery queue - not a mapping",
                "rows": int(count),
                "distinct_codes": int(distinct_codes),
                "code": "",
                "name": "",
                "brand": "",
                "matched_keywords": "",
                "off_url": "",
            }
        )

    combined_pattern = "|".join(
        f"({pattern})" for pattern in RECALL_KEYWORDS.values()
    )
    samples = connection.execute(
        f"""
        SELECT
            code,
            name_text AS name,
            brands AS brand,
            'https://world.openfoodfacts.org/product/' || code AS off_url
        FROM record_flags
        WHERE {candidate_condition}
            AND regexp_matches(lower(name_text), ?)
        ORDER BY hash(code), code, coalesce(name_text, ''), coalesce(brands, '')
        LIMIT 20
        """,
        [combined_pattern],
    ).fetchdf()
    for sample_rank, row in enumerate(samples.to_dict(orient="records"), start=1):
        normalized_name = str(row.get("name") or "").casefold()
        matched = [
            keyword
            for keyword, pattern in RECALL_KEYWORDS.items()
            if re.search(pattern, normalized_name)
        ]
        keyword_rows.append(
            {
                "row_type": "sample",
                "sample_rank": sample_rank,
                "keyword": "",
                "discovery_label": "discovery queue - not a mapping",
                "rows": "",
                "distinct_codes": "",
                "code": row["code"],
                "name": row["name"],
                "brand": row["brand"],
                "matched_keywords": " | ".join(matched),
                "off_url": row["off_url"],
            }
        )
    return pd.DataFrame(keyword_rows)


def review_queue(connection: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return connection.execute(
        """
        SELECT
            tag,
            CASE
                WHEN bool_or(class_a_match) AND bool_or(class_c_match) THEN 'A+C'
                WHEN bool_or(class_a_match) THEN 'A'
                ELSE 'C'
            END AS evidence_classes,
            COUNT(DISTINCT record_id) AS rows,
            COUNT(DISTINCT code) AS distinct_codes,
            '' AS owner_disposition,
            '' AS owner_note
        FROM tag_evidence
        WHERE (class_a_match OR class_c_match)
            AND NOT class_b_match
        GROUP BY tag
        ORDER BY rows DESC, tag
        """
    ).fetchdf()


def wood_check(connection: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return connection.execute(
        """
        SELECT
            code,
            brands AS brand,
            name_text AS product_name,
            array_to_string(categories_tags, ' | ') AS categories_tags,
            'https://world.openfoodfacts.org/product/' || code AS off_url
        FROM record_base
        WHERE list_contains(categories_tags, 'fr:wood')
            AND NOT list_contains(
                categories_tags,
                'fr:cork-and-bamboo-based-floor-coverings'
            )
        ORDER BY hash(code), code, coalesce(name_text, ''), coalesce(brands, '')
        """
    ).fetchdf()


def main() -> None:
    nonfood_dispositions, taxonomy = validate_inputs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with duckdb.connect() as connection:
        create_tables(connection, nonfood_dispositions)
        inventory = tag_inventory(
            connection,
            taxonomy,
            {row["source_category_tag"] for row in nonfood_dispositions},
        )
        variants = case_variant_audit(connection, nonfood_dispositions)
        summary = class_summary(connection)
        countries = country_impact(connection)
        signals = signal_validation(connection)
        sensitivity = sensitivity_impact(connection)
        conflict = contradictions(connection)
        recall = recall_probe(connection)
        queue = review_queue(connection)
        wood = wood_check(connection)
        taxonomy_frame = taxonomy_check(taxonomy)

    write_csv(
        inventory,
        "nonfood_scope_tag_inventory.csv",
        ["tag_grain", "tag_value"],
    )
    write_csv(
        variants,
        "nonfood_scope_case_variants.csv",
        ["reviewed_exclusion_tag", "scope", "data_tag_variant"],
    )
    write_csv(wood, "nonfood_scope_wood_check.csv", ["code", "product_name"])
    write_csv(
        summary,
        "nonfood_scope_class_summary.csv",
        ["summary_type", "group_label"],
    )
    write_csv(
        countries,
        "nonfood_scope_country_impact.csv",
        ["iso_alpha2"],
    )
    write_csv(
        sensitivity,
        "nonfood_scope_sensitivity_impact.csv",
        ["geography_level", "iso_alpha2", "scenario"],
    )
    write_csv(
        signals,
        "nonfood_scope_signal_validation.csv",
        ["scope", "strongest_class"],
    )
    write_csv(
        conflict,
        "nonfood_scope_contradictions.csv",
        ["sample_rank"],
    )
    write_csv(
        recall,
        "nonfood_scope_recall_probe.csv",
        ["row_type", "sample_rank", "keyword", "code"],
    )
    write_csv(
        queue,
        "nonfood_scope_review_queue.csv",
        ["rows", "tag"],
        ascending=[False, True],
    )
    write_csv(
        taxonomy_frame,
        "nonfood_scope_taxonomy_check.csv",
        ["tag"],
    )
    print("Non-food scope audit completed.")
    print(f"Parquet rows: {EXPECTED_ROWS:,}; columns: {EXPECTED_COLUMNS}")
    print(f"Reviewed exact non-food disposition tags: {len(nonfood_dispositions)}")
    print(f"Country units reconciled: {len(countries)}")
    print(
        "Sensitivity rows generated: "
        f"{len(sensitivity):,} (baseline plus two A/B exclusion scenarios)"
    )
    print(f"fr:wood records outside floor-covering tags: {len(wood):,}")
    print(f"Outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
