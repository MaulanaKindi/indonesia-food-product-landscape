"""Fetch the locally excluded category taxonomy snapshot when it is missing."""

import hashlib
import os
import tempfile
import urllib.request
from pathlib import Path

from support_pinned_inputs import (
    TAXONOMY_FILE,
    TAXONOMY_SHA256,
    TAXONOMY_SIZE_BYTES,
    TAXONOMY_URL,
)

TARGET_FILE = TAXONOMY_FILE
SOURCE_URL = TAXONOMY_URL
EXPECTED_SIZE_BYTES = TAXONOMY_SIZE_BYTES
EXPECTED_SHA256 = TAXONOMY_SHA256
CHUNK_SIZE_BYTES = 1024 * 1024


def validate_snapshot_metadata(size: int, sha256: str) -> None:
    if size != EXPECTED_SIZE_BYTES or sha256.upper() != EXPECTED_SHA256:
        raise ValueError(
            "Category taxonomy does not match the pinned snapshot: "
            f"expected {EXPECTED_SIZE_BYTES} bytes and SHA-256 "
            f"{EXPECTED_SHA256}; found {size} bytes and {sha256.upper()}. "
            "The upstream taxonomy URL is mutable; obtain the exact archived "
            "snapshot before rerunning the analysis."
        )


def hash_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(CHUNK_SIZE_BYTES), b""):
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest().upper()


def verify_file(path: Path) -> None:
    size, sha256 = hash_file(path)
    validate_snapshot_metadata(size, sha256)


def download_if_missing() -> None:
    TARGET_FILE.parent.mkdir(parents=True, exist_ok=True)
    if TARGET_FILE.exists():
        verify_file(TARGET_FILE)
        print(f"Verified existing taxonomy snapshot: {TARGET_FILE}")
        return

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".categories.json.",
            suffix=".download",
            dir=TARGET_FILE.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            digest = hashlib.sha256()
            size = 0
            request = urllib.request.Request(
                SOURCE_URL,
                headers={"User-Agent": "indonesia-food-product-landscape/1.0"},
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                while chunk := response.read(CHUNK_SIZE_BYTES):
                    temporary_file.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        validate_snapshot_metadata(size, digest.hexdigest())
        temporary_path.replace(TARGET_FILE)
        print(f"Downloaded and verified taxonomy snapshot: {TARGET_FILE}")
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


if __name__ == "__main__":
    download_if_missing()
