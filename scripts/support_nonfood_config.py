"""Shared input paths and audit constants for non-food scope analysis."""

import csv
from pathlib import Path

from support_pinned_inputs import (
    SNAPSHOT_COLUMN_COUNT,
    SNAPSHOT_ROW_COUNT,
    TAXONOMY_SHA256,
)
from support_pinned_inputs import (
    TAXONOMY_FILE as TAXONOMY_FILE,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "food.parquet"


DISPOSITION_FILE = (
    PROJECT_ROOT / "data" / "mappings" / "category_tag_manual_dispositions.csv"
)


COUNTRY_MAPPING_FILE = PROJECT_ROOT / "data" / "mappings" / "country_tag_mapping.csv"


ISO_REFERENCE_FILE = PROJECT_ROOT / "data" / "reference" / "iso_3166_alpha2.csv"


COUNTRY_PROFILE_FILE = (
    PROJECT_ROOT / "outputs" / "profiling" / "normalized_country_profile.csv"
)


COUNTRY_SHORTLIST_FILE = (
    PROJECT_ROOT / "outputs" / "profiling" / "country_comparison_shortlist.csv"
)


OUTPUT_DIR = PROJECT_ROOT / "outputs" / "profiling"


EXPECTED_ROWS = SNAPSHOT_ROW_COUNT


EXPECTED_COLUMNS = SNAPSHOT_COLUMN_COUNT


EXPECTED_TAXONOMY_SHA256 = TAXONOMY_SHA256


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


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))
