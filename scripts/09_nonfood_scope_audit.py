import hashlib
import json

import duckdb
import pandas as pd
from support_duckdb_runtime import connect_duckdb
from support_nonfood_config import (
    COUNTRY_MAPPING_FILE,
    COUNTRY_PROFILE_FILE,
    COUNTRY_SHORTLIST_FILE,
    DATA_FILE,
    DISPOSITION_FILE,
    EXPECTED_COLUMNS,
    EXPECTED_ROWS,
    EXPECTED_TAXONOMY_SHA256,
    ISO_REFERENCE_FILE,
    OUTPUT_DIR,
    TAXONOMY_FILE,
    csv_rows,
)
from support_nonfood_impact import (
    country_impact,
    sensitivity_impact,
    signal_validation,
)
from support_nonfood_review import (
    contradictions,
    recall_probe,
    review_queue,
    wood_check,
)
from support_nonfood_scope import (
    case_variant_audit,
    class_summary,
    tag_inventory,
    taxonomy_check,
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

    connection = connect_duckdb()
    try:
        parquet_profile = connection.execute(
            "DESCRIBE SELECT * FROM read_parquet(?)", [str(DATA_FILE)]
        ).fetchall()
        actual_columns = len(parquet_profile)
        actual_row = connection.execute(
            "SELECT COUNT(*) FROM read_parquet(?)", [str(DATA_FILE)]
        ).fetchone()
        assert actual_row is not None
        actual_rows = actual_row[0]
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
    if not dispositions or not required_disposition_columns.issubset(dispositions[0]):
        raise ValueError("Category disposition file has an invalid or empty schema.")
    nonfood_dispositions = [
        row for row in dispositions if row["disposition"] == "exclude_non_food"
    ]
    reviewed_tags = [row["source_category_tag"] for row in nonfood_dispositions]
    if len(reviewed_tags) != len(set(reviewed_tags)):
        raise ValueError("Non-food disposition tags must be exact and unique.")

    country_mappings = csv_rows(COUNTRY_MAPPING_FILE)
    iso_rows = csv_rows(ISO_REFERENCE_FILE)
    baseline_rows = csv_rows(COUNTRY_PROFILE_FILE)
    if not country_mappings or not iso_rows or not baseline_rows:
        raise ValueError(
            "Country mapping, ISO reference, and baseline must be non-empty."
        )
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
    return nonfood_dispositions, json.loads(TAXONOMY_FILE.read_text(encoding="utf-8"))


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

    connection.execute("CREATE TEMP TABLE class_a_tags(tag VARCHAR PRIMARY KEY)")
    connection.executemany(
        "INSERT INTO class_a_tags VALUES (?)",
        [(tag,) for tag in CLASS_A_TAGS],
    )
    connection.execute("CREATE TEMP TABLE class_d_tags(tag VARCHAR PRIMARY KEY)")
    connection.executemany(
        "INSERT INTO class_d_tags VALUES (?)",
        [(tag,) for tag in CLASS_D_TAGS],
    )
    connection.execute("CREATE TEMP TABLE manual_nonfood_tags(tag VARCHAR PRIMARY KEY)")
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
    cigarette_russe_row = connection.execute(
        """
        SELECT COUNT(*)
        FROM tag_evidence
        WHERE tag = 'en:cigarette-russes' AND class_c_match
        """
    ).fetchone()
    assert cigarette_russe_row is not None
    cigarette_russe_match = cigarette_russe_row[0]
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


def main() -> None:
    nonfood_dispositions, taxonomy = validate_inputs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with connect_duckdb() as connection:
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
