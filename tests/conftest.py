import datetime

import duckdb
import pytest


@pytest.fixture
def synthetic_database() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    connection.execute(
        """
        CREATE TABLE source_product_record (
            source_record_id BIGINT,
            code VARCHAR,
            creator VARCHAR,
            created_t BIGINT,
            brands VARCHAR,
            categories_tags VARCHAR[],
            ingredients_text STRUCT(lang VARCHAR, text VARCHAR)[],
            nutriments STRUCT(
                name VARCHAR,
                value DOUBLE,
                "100g" DOUBLE,
                serving DOUBLE,
                unit VARCHAR,
                prepared_value DOUBLE,
                prepared_100g DOUBLE,
                prepared_serving DOUBLE,
                prepared_unit VARCHAR
            )[],
            nutriscore_grade VARCHAR,
            packaging VARCHAR,
            packaging_tags VARCHAR[],
            packagings STRUCT(name VARCHAR)[],
            labels VARCHAR,
            labels_tags VARCHAR[],
            data_sources_tags VARCHAR[],
            food_groups_tags VARCHAR[]
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE record_country (
            source_record_id BIGINT,
            iso_alpha2 VARCHAR
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE record_category_tag (
            source_record_id BIGINT,
            source_category_tag VARCHAR
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE record_brand_source_value (
            source_record_id BIGINT,
            source_brand_name VARCHAR
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE brand_name_mapping (
            source_brand_name VARCHAR,
            canonical_brand_name VARCHAR,
            review_status VARCHAR
        )
        """
    )
    connection.execute(
        "CREATE TABLE reporting_group (reporting_group_id VARCHAR)"
    )
    connection.execute(
        """
        CREATE TABLE category_tag_group_candidate (
            source_category_tag VARCHAR,
            reporting_group_id VARCHAR
        )
        """
    )

    start = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
    records = []
    country_links = []
    category_links = []
    brand_values = []
    for record_id in range(1, 201):
        created_t = int((start + datetime.timedelta(days=record_id)).timestamp())
        records.append(
            (
                record_id,
                f"code-{record_id}",
                f"creator-{record_id % 10}",
                created_t,
                "Brand" if record_id % 2 == 0 else "",
                ["en:sample"] if record_id % 3 == 0 else [],
                (
                    [{"lang": "en", "text": "sample ingredient"}]
                    if record_id % 4 == 0
                    else []
                ),
                (
                    [{"name": "energy", "100g": 12.0}]
                    if record_id % 5 == 0
                    else []
                ),
                "A" if record_id % 7 == 0 else "unknown",
                "box" if record_id % 8 == 0 else None,
                ["en:box"] if record_id % 8 == 0 else [],
                [{"name": "box"}] if record_id % 8 == 0 else [],
                "Organic" if record_id % 10 == 0 else "",
                ["en:organic"] if record_id % 10 == 0 else [],
                ["app-synthetic"] if record_id % 3 == 0 else [],
                ["en:beverages"] if record_id % 6 == 0 else [],
            )
        )
        if record_id <= 80:
            country_links.append((record_id, "ID"))
        if 76 <= record_id <= 140:
            country_links.append((record_id, "MY"))
        if 141 <= record_id <= 180:
            country_links.append((record_id, "PH"))
        if 181 <= record_id <= 200:
            country_links.append((record_id, "SG"))
        if record_id % 3 == 0:
            category_links.append((record_id, "en:sample"))
        if record_id % 2 == 0:
            brand_values.append(
                (
                    record_id,
                    "Brand" if record_id % 4 == 0 else "Unmapped Brand",
                )
            )

    connection.executemany(
        """
        INSERT INTO source_product_record VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )
    connection.executemany("INSERT INTO record_country VALUES (?, ?)", country_links)
    connection.executemany(
        "INSERT INTO record_category_tag VALUES (?, ?)",
        category_links,
    )
    connection.execute("INSERT INTO reporting_group VALUES ('beverages')")
    connection.execute(
        "INSERT INTO category_tag_group_candidate VALUES ('en:sample', 'beverages')"
    )
    connection.executemany(
        "INSERT INTO record_brand_source_value VALUES (?, ?)",
        brand_values,
    )
    connection.execute(
        "INSERT INTO brand_name_mapping VALUES ('Brand', 'Canonical brand', 'approved')"
    )

    yield connection
    connection.close()
