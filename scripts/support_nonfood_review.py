"""support nonfood review helpers."""

import re

import duckdb
import pandas as pd
from support_nonfood_config import (
    RECALL_KEYWORDS,
)


def contradictions(connection: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    criteria = """
        (has_a OR has_b)
        AND nova_group IS NOT NULL
        AND lower(nutriscore_grade) IN ('a', 'b', 'c', 'd', 'e')
        AND ingredients_n >= 2
    """
    totals = connection.execute(
        f"""
        SELECT COUNT(*), COUNT(DISTINCT code)
        FROM record_flags
        WHERE {criteria}
        """
    ).fetchone()
    assert totals is not None
    total_rows, distinct_codes = totals
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
        totals = connection.execute(
            f"""
            SELECT COUNT(*), COUNT(DISTINCT code)
            FROM record_flags
            WHERE {candidate_condition}
                AND regexp_matches(lower(name_text), ?)
            """,
            [pattern],
        ).fetchone()
        assert totals is not None
        count, distinct_codes = totals
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

    combined_pattern = "|".join(f"({pattern})" for pattern in RECALL_KEYWORDS.values())
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
