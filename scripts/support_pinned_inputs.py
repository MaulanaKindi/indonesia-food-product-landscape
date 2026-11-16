"""Shared paths and integrity metadata for pinned external inputs."""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_FILE = PROJECT_ROOT / "data" / "reference" / "pinned_sources.json"
MANIFEST = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))

SNAPSHOT = MANIFEST["open_food_facts_snapshot"]
SNAPSHOT_REPOSITORY = SNAPSHOT["repository"]
SNAPSHOT_COMMIT = SNAPSHOT["commit"]
SNAPSHOT_URL = SNAPSHOT["url"]
SNAPSHOT_FILE = PROJECT_ROOT / SNAPSHOT["path"]
SNAPSHOT_SIZE_BYTES = SNAPSHOT["size_bytes"]
SNAPSHOT_SHA256 = SNAPSHOT["sha256"]
SNAPSHOT_ROW_COUNT = SNAPSHOT["row_count"]
SNAPSHOT_COLUMN_COUNT = SNAPSHOT["column_count"]

TAXONOMY = MANIFEST["open_food_facts_category_taxonomy"]
TAXONOMY_RETRIEVED_ON = TAXONOMY["retrieved_on"]
TAXONOMY_URL = TAXONOMY["url"]
TAXONOMY_FILE = PROJECT_ROOT / TAXONOMY["path"]
TAXONOMY_SIZE_BYTES = TAXONOMY["size_bytes"]
TAXONOMY_SHA256 = TAXONOMY["sha256"]
TAXONOMY_NODE_COUNT = TAXONOMY["node_count"]
